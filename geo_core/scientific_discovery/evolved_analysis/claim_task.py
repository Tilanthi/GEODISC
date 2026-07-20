"""claim_task.py — the Phase-2 evolved artifact: a (CLAIM, executable TEST) pair.

Phase 2 generalises the AlphaEvolve engine to OPEN-ENDED Eureka search: the
evolved artifact is a pair

    CLAIM     : a short, quantitative natural-language statement about real data
                (e.g. "In the geochemical dataset, samples with Fe/Al > 0.5 show
                a >30% enrichment in redox-sensitive Mo consistent with anoxic
                deposition").
    run_claim : executable code that loads REAL archival data and returns an
                objective statistic + significance for the claim.

Two-gate EVALUATE (design §5):
  * Gate 1 (real-data verification, runs SANDBOXED, no network): the test must
    compute a statistically significant effect on real held-out data
    (|effect| >= EFFECT_MIN and pvalue <= PMAX). Fabricated claims (no real
    effect) fail here.
  * Gate 2 (literature novelty, runs in the orchestrator WITH network): the
    CLAIM text must not be entailed by retrieved arXiv/S2 abstracts. Textbook /
    known results fail here.

Only candidates passing BOTH gates are emitted, via discovery_store's
verification block, so they reach the genuine store through the chokepoint.

Real data: REAL whole-rock major-oxide geochemistry (columns sio2, tio2, al2o3,
feo_tot, mgo, cao, mno, na2o, k2o, p2o5; wt%), fetched from the public Gard et
al. (2019) global whole-rock compilation (Zenodo 3359791) by
scripts/fetch_geochem_data.py into $GEODISC_REAL_DATA. See real_data.py.
"""
from __future__ import annotations

import ast
import os
import re
from typing import Optional, Tuple

# Gate-1 thresholds (statistical significance on real held-out data).
EFFECT_MIN = 0.30     # |effect| (e.g. |Spearman r|) must be at least this
PMAX = 1e-3           # p-value must be at most this
ENTRY_POINT = "run_claim"

# A seed program. This claim is REAL and strongly supported by the data (gate 1
# passes — SiO2 vs MgO is the classic negative Harker fractionation trend,
# r ≈ -0.53 in the Gard et al. compilation) but KNOWN/textbook (gate 2 catches
# it). It is the floor the search must BEAT on novelty, not a goal in itself.
NAIVE_CLAIM_SEED = '''CLAIM = "In whole-rock geochemical data, a sample's SiO2 content is negatively correlated with its MgO content (silicic, more-evolved rocks are MgO-poor — the Harker fractionation trend)."


def run_claim(df_train, df_eval):
    """Test the claim on real whole-rock geochemical data on the HELD-OUT eval split.

    The headline statistic must come from df_eval (not df_train), per the
    Gate-1 leakage contract (§7.3); ``claim_uses_heldout_split`` enforces this
    before the sandbox ever runs.
    """
    from scipy.stats import spearmanr
    import numpy as np
    df = df_eval
    sio2 = df["sio2"].to_numpy(float)
    mgo = df["mgo"].to_numpy(float)
    mask = np.isfinite(sio2) & np.isfinite(mgo)
    r, p = spearmanr(sio2[mask], mgo[mask])
    return {
        "effect": float(r),
        "pvalue": float(p),
        "effect_type": "spearman_sio2_mgo",
        "summary": f"Spearman(SiO2, MgO) = {r:.3f}, p = {p:.2e}, n = {int(mask.sum())}",
    }
'''

# Task system prompt for the LLM proposer. Asks for a NEW (CLAIM, run_claim)
# pair exploring a different real relationship in the geochemical columns, such
# that the claim is BOTH statistically significant AND plausibly NOT already
# textbook.
TASK_SYSTEM = (
    "You are an expert geochemist searching for a NOVEL, real statistical "
    "relationship in a global whole-rock geochemical dataset that is "
    "NOT already a well-known textbook result. You are given the current "
    "candidate (a natural-language CLAIM plus a `run_claim(df_train, df_eval)` "
    "function that tests it on real data and returns {effect, pvalue, "
    "effect_type, summary}).\n"
    "The available REAL data columns (use these EXACT names in df[col]):\n"
    "  oxides (wt%): sio2, tio2, al2o3, feo_tot, mgo, cao, mno, na2o, k2o, p2o5\n"
    "  trace elements (ppm): v_ppm, cr_ppm, co_ppm, ni_ppm, cu_ppm, zn_ppm, "
    "rb_ppm, sr_ppm, y_ppm, zr_ppm, nb_ppm, ba_ppm, la_ppm, ce_ppm, nd_ppm\n"
    "  isotopes (optional, sparse): sr87_sr86, nd143_nd144, epsilon_nd, "
    "epsilon_sr, pb206_pb204, pb207_pb204, pb208_pb204, hf176_hf177, epsilon_hf\n"
    "  age (optional, Ga)\n"
    "IMPORTANT: trace elements are named with the _ppm SUFFIX (e.g., df['nb_ppm'], "
    "NOT df['nb']). Isotopes have NO suffix. ALWAYS df.dropna(subset=[your_cols]) "
    "before computing -- isotope/age columns are sparse (~10% of rows). The TRACE "
    "elements have THINNER textbook coverage than the saturated major oxides, so "
    "prefer relations involving them (HFSE Zr/Nb/Y, REE La/Ce/Nd, LILE Rb/Sr/Ba). "
    "Correct import: from sklearn.linear_model import LinearRegression. "
    "You may use numpy/scipy/pandas/sklearn only.\n"
    "HARD RULES:\n"
    "- Keep the EXACT signature: def run_claim(df_train, df_eval)\n"
    "- Set a module-level CLAIM = \"...\" string: a specific, quantitative claim.\n"
    "- Return a dict with keys effect (a correlation/contrast magnitude in [-1,1] "
    "or a normalized contrast), pvalue (a real significance), effect_type, summary.\n"
    "- DO NOT propose a simple PAIRWISE correlation (X vs Y): almost all pairwise "
    "oxide relations are textbook (Harker/Fenner/TAS trends) and Gate 2 will "
    "reject them as already-known.\n"
    "- INSTEAD propose a NON-OBVIOUS relation of one of these forms (this is where "
    "genuine novelty lives):\n"
    "  (i) PARTIAL correlation -- X vs Y after removing a shared driver Z (e.g. "
    "MgO). On df_train fit X~Z and Y~Z (sklearn LinearRegression), predict on "
    "df_eval, then report spearmanr of the two residual vectors as `effect`.\n"
    "  (ii) RESIDUAL relation -- correlate X with the residual of Y after "
    "regressing out the dominant fractionation trend (MgO).\n"
    "  (iii) CONDITIONAL / subset -- e.g. 'among arc basalts with SiO2 > 55, X "
    "correlates with Y'.\n"
    "  (iv) INTERACTION or ratio of 3+ variables (e.g. Al2O3/Na2O vs K2O*P2O5).\n"
    "- The relationship must be genuinely significant on the held-out data. AVOID "
    "textbook basics: MgO-SiO2 (Harker), Fe-Mg covariation, total-alkali-silica "
    "(TAS), silica saturation, incompatible-element co-enrichment.\n"
    "- No file I/O, no network, no plotting. Correct and self-contained.\n"
    "RESPOND WITH EITHER:\n"
    "  (a) one or more diff blocks (<<<SEARCH>>>...<<<REPLACE>>>...<<<END>>>)\n"
    "  (b) one complete ```python``` module (CLAIM + run_claim).\n"
    "Output ONLY the diff or code, no explanation."
)

# Tier 2 — surprise / anomaly objective (env-gated, default on).
# The proposer is nudged away from significant-but-textbook confirmations toward
# claims that CONTRADICT a known expectation and still hold on the data.
SURPRISE_GUIDANCE = (
    "\n\nSURPRISE OBJECTIVE -- TEST, DON'T ASSERT: the highest-value result is one "
    "whose DATA-confirmed sign contradicts a textbook expectation. Known expected "
    "signs: Ce/Nd/La vs Nb/Zr/Y POSITIVE (incompatible coherence); Rb/Sr/Ba "
    "POSITIVE (LILE); Cr-Ni POSITIVE; MgO-SiO2 NEGATIVE (Harker); FeO-MgO POSITIVE; "
    "Na2O-K2O POSITIVE (TAS). To pursue this: COMPUTE the relation on the data "
    "FIRST, then state in the CLAIM exactly the sign and magnitude you measured. If "
    "the MEASURED sign contradicts an expectation above, that is a strong candidate; "
    "if it confirms it, report the confirmation honestly (still valid, lower "
    "novelty). Do NOT choose a direction in the claim text before computing it. "
    "Also explore unstudied pairs (isotopes, age-conditional, ratio systematics) and "
    "conditional/subset relations where a decoupling could genuinely appear. "
    "INTEGRITY (enforced): a claim whose STATED direction disagrees with its own "
    "computed effect is REJECTED by the sign-consistency guard; a recycled or "
    "hardcoded p-value is REJECTED by the p-value guard. State exactly what your "
    "run_claim computed -- never assert a contradiction the data does not show, and "
    "never frame a confirmation as 'contrary to expectation'."
)
if os.environ.get("GEODISC_SURPRISE_GUIDANCE", "1") not in ("0", "false", "False"):
    TASK_SYSTEM = TASK_SYSTEM + SURPRISE_GUIDANCE

# Tier 3 — broader repertoire (guidance; always on). These forms surface
# MECHANISMS, not confirmations, and are what the inspirations bank demonstrates.
REPERTOIRE_EXPANSION = (
    "\n\nBROADER REPERTOIRE: beyond partial/residual correlations, preferentially "
    "explore these forms -- they surface MECHANISMS, not confirmations:\n"
    "  (v) THRESHOLD / non-monotonic -- a relation that peaks or reverses above a "
    "value of Z (e.g. a ratio saturates past an element's median).\n"
    "  (vi) ANOMALY subpopulation -- a subset defined by W that shows an outlier "
    "relation the bulk population does not.\n"
    "  (vii) PREDICTIVE validity -- a ratio/combination that predicts a held-out "
    "property better than a baseline (report the R2/accuracy GAIN as `effect`).\n"
    "  (viii) LOG-RATIO systematics -- log(X/Y) vs log(Z/Y), a process-ratio array.\n"
    "Vary the analytical FORM, not just the element pair."
)
TASK_SYSTEM = TASK_SYSTEM + REPERTOIRE_EXPANSION

# 2026-07-20: pivot the proposer to the under-used, least-textbook-saturated,
# on-mission niche — radiogenic isotopes + age — in the data we already have,
# while the Proterozoic sedimentary substrate (SGP) is unavailable. This uses CPU
# productively on available, unstalled data instead of re-deriving saturated HFSE
# correlations. Disable with GEODISC_ISOTOPE_NICHE=0.
ISOTOPE_NICHE_GUIDANCE = (
    "\n\nISOTOPE / AGE NICHE (PRIORITY): the oxide/trace residual-correlation vein "
    "(Ce-Nb, Zr-Y, Cr-Ni after MgO) is TEXTBOOK-SATURATED — stop re-deriving it. "
    "Instead PREFERENTIALLY use the radiogenic-isotope columns (sr87_sr86, "
    "nd143_nd144, pb206_pb204/pb207_pb204/pb208_pb204, hf176_hf177) and the age "
    "column. These have the THINNEST textbook coverage (source/provenance tracers, "
    "on-mission for crustal evolution), and the proposer has been under-using them. "
    "Forms to try: (i) isotope-isotope coupling (e.g. Sr vs Nd isotope co-variation "
    "by rock type); (ii) isotope vs trace-element residual after MgO (does a source "
    "tracer decouple from a fractionation proxy?); (iii) age-conditional relations "
    "(does a correlation strengthen/weaken across an age threshold?); (iv) isotope "
    "ratios as predictors of a major-oxide property. ALWAYS df.dropna(subset=[your_"
    "isotope_cols]) first — these columns are SPARSE (Sr ~10%, Nd ~10%, Pb ~6%, age "
    "~2% of rows), so the held-out n will be smaller but the question is far less "
    "saturated. State the sign + p your run_claim actually computes."
)
if os.environ.get("GEODISC_ISOTOPE_NICHE", "1") not in ("0", "false", "False"):
    TASK_SYSTEM = TASK_SYSTEM + ISOTOPE_NICHE_GUIDANCE


def parse_claim(src: str) -> Optional[str]:
    """Extract the CLAIM string from a candidate module (None if absent).

    Uses a backreference (\\1) so the CLOSING quote is the same character as the
    opening quote — this lets a double-quoted claim contain apostrophes (e.g.
    "a sample's SiO2") without being truncated at the apostrophe, which
    previously fed Gate 2 an incomplete fragment and caused false 'novel' calls.
    """
    m = re.search(r'^CLAIM\s*=\s*(["\'])(.+?)\1', src, re.MULTILINE | re.DOTALL)
    return m.group(2).strip() if m else None


def claim_uses_heldout_split(src: str, entry_point: str = ENTRY_POINT) -> Tuple[bool, str]:
    """Static leakage guard (§7.3): run BEFORE the sandboxed Gate-1 eval.

    The two-gate contract is that Gate 1 reports significance on the HELD-OUT
    (eval) split. A candidate that ignores ``df_eval`` computes its headline on
    the training frame, making in-sample == out-of-sample and the gate's
    "significant on real held-out data" promise a silent lie — the §7.3 trap.
    Static analysis cannot fully prove data-flow, so this is a CONSERVATIVE
    NECESSARY check: the candidate's ``run_claim`` body must actually *read*
    ``df_eval``. Candidates that copy the ``df = df_train`` pattern and never
    touch the held-out frame are rejected before we spend a sandbox run.

    A parameter declaration does not count — in the AST it is an ``ast.arg``,
    not an ``ast.Name``, so a candidate that merely names ``df_eval`` in the
    signature is still rejected.

    Returns ``(True, "ok")`` if df_eval is read in the body, else
    ``(False, "leakage: ...")``. Never raises.
    """
    try:
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return (False, "leakage: unparseable candidate")
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == entry_point:
                for sub in ast.walk(node):
                    if (isinstance(sub, ast.Name) and sub.id == "df_eval"
                            and isinstance(sub.ctx, ast.Load)):
                        return (True, "ok")
                return (False, "leakage: held-out split (df_eval) is never read in "
                               "the body; the headline must come from df_eval, not df_train")
        # No entry point here — let the sandbox/safety layer report it; this is
        # not a leakage verdict.
        return (True, "ok")
    except Exception:  # pragma: no cover — defensive; never crash the caller
        return (False, "leakage: check-failed")


# Direction markers a claim may use to assert a correlation's sign.
# Broadened (2026-07-19 integrity fix): the surprise objective induced the
# proposer to phrase a direction as a bare adjective ("significantly negative",
# "is NEGATIVE") which the narrow original markers ("negatively correlated"...)
# missed, letting claims whose stated sign contradicted their computed effect
# through the sign-consistency guard. The bare direction words + residual/
# covariance/relat variants close that evasion. If BOTH a positive and a negative
# marker appear, direction is treated as unstated (conservative).
_POS_MARKERS = ("positively correlated", "positive correlation", "positive partial",
                "positive assoc", "positive covar", "positively covar",
                "positive residual", "positive covari", "positive relat",
                "significantly positive", "is positive", "are positive",
                "r > 0", "r>0", "positively", "positive")
_NEG_MARKERS = ("negatively correlated", "negative correlation", "negative partial",
                "negative assoc", "negative covar", "anti-correlat", "anticorrel",
                "inverse", "negative residual", "negative covari", "negative relat",
                "significantly negative", "is negative", "are negative",
                "r < 0", "r<0", "negatively", "negative")


def _claim_stated_direction(claim: str) -> Optional[str]:
    """Return 'positive'/'negative' if the claim asserts a correlation
    direction, else None (unstated/ambiguous). Never raises."""
    try:
        low = (claim or "").lower()
        pos = any(k in low for k in _POS_MARKERS)
        neg = any(k in low for k in _NEG_MARKERS)
        if pos and not neg:
            return "positive"
        if neg and not pos:
            return "negative"
        return None
    except Exception:
        return None


def _direction_consistent(claim: str, effect) -> Tuple[bool, str]:
    """Sign-consistency guard: does the claim's STATED direction match the
    computed effect's sign? Returns (ok, reason). Unstated direction -> ok."""
    stated = _claim_stated_direction(claim)
    if stated is None:
        return True, "direction unstated"
    try:
        e = float(effect)
    except (TypeError, ValueError):
        return True, "effect non-numeric"
    actual = "positive" if e >= 0 else "negative"
    if stated == actual:
        return True, "ok"
    return False, (f"sign-mismatch: claim states {stated}, effect is {actual} "
                  f"({e:+.3f})")


def gate1_significant(metrics: dict) -> Tuple[bool, str]:
    """Gate 1: is the computed effect statistically significant on real data?

    Returns (passed, reason). Conservative: missing/invalid fields fail."""
    if not isinstance(metrics, dict) or "error" in metrics:
        return False, f"gate1-failed: no valid metric ({metrics.get('error', 'missing') if isinstance(metrics, dict) else 'not a dict'})"
    try:
        effect = abs(float(metrics.get("effect", 0.0)))
        pvalue = float(metrics.get("pvalue", 1.0))
    except (TypeError, ValueError):
        return False, "gate1-failed: non-numeric effect/pvalue"
    if effect >= EFFECT_MIN and pvalue <= PMAX:
        return True, f"gate1-pass: |effect|={effect:.3f}>={EFFECT_MIN}, p={pvalue:.1e}<={PMAX}"
    return False, (f"gate1-failed: |effect|={effect:.3f} or p={pvalue:.1e} "
                   f"not significant (need |effect|>={EFFECT_MIN} and p<={PMAX})")


def gate1_pvalue_consistent(effect, pvalue, n_max) -> Tuple[bool, str]:
    """Independently sanity-check a candidate's self-reported ``pvalue`` against
    the correlation magnitude it reports, given the max available sample size.

    WHY: Gate 1 trusts the candidate's returned pvalue. A proposer can satisfy
    "significant" by returning a recycled/hardcoded tiny p — observed in the
    store (the SAME p = 5.98e-82 for r = +0.555 AND r = -0.426, which is
    impossible for two different correlations). This re-derives the p that the
    reported |r| could yield at ``n_max`` (the held-out split size — a candidate
    cannot legitimately use more) and rejects p-values that are implausibly MORE
    significant than |r| allows.

    Note: p = 0.0 for a STRONG correlation (e.g. r=0.94, n=1000) is legitimate
    underflow — scipy spearmanr returns 0.0 when the survival function underflows
    — and is NOT rejected. p = 0.0 (or any tiny p) for a WEAK correlation is caught.

    Conservative: returns (True, 'ok') if the check cannot be computed, so it
    never blocks the gate on a check-side failure."""
    try:
        if effect is None or pvalue is None or n_max is None or n_max < 5:
            return True, "ok"
        r = float(effect)
        p = float(pvalue)
        if not (-1.0 < r < 1.0):
            return True, "ok"  # |r|>=1 is degenerate; cannot bound the p
        import math
        from scipy import stats
        df = int(n_max) - 2
        t = abs(r) * math.sqrt(df / max(1e-12, 1.0 - r * r))
        recomp = 2.0 * stats.t.sf(t, df)        # smallest p |r| could yield at n_max
        FLOOR = 1e-300
        rep = max(p, FLOOR)                      # treat 0.0 (underflow) as the floor
        recomp_f = max(float(recomp), FLOOR)
        if rep < recomp_f * 1e-6:                # >6 orders too significant -> recycled/hardcoded
            return False, (f"pvalue-implausible: reported p={p:.3e} but |r|={abs(r):.3f} "
                           f"at n<={int(n_max)} implies p>={recomp_f:.3e} "
                           f"(recycled/hardcoded p-value suspected)")
        return True, "ok"
    except Exception:
        return True, "ok"


if __name__ == "__main__":
    # self-test: the seed claim parses
    print("seed CLAIM:", parse_claim(NAIVE_CLAIM_SEED)[:60], "...")
    print("seed gate1 (expected pass):", gate1_significant(
        {"effect": 0.55, "pvalue": 1e-12}))
    print("fabricated gate1 (expected fail):", gate1_significant(
        {"effect": 0.02, "pvalue": 0.4}))
