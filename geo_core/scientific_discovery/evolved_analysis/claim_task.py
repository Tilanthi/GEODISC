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
    "The available REAL data columns are whole-rock major oxides (wt%): sio2, "
    "tio2, al2o3, feo_tot (total Fe as FeO), mgo, cao, mno, na2o, k2o, p2o5 -- "
    "AND trace elements (ppm): v, cr, co, ni, cu, zn, rb, sr, y, zr, nb, ba, la, "
    "ce, nd (column names like zr_ppm). The TRACE elements have THINNER textbook "
    "coverage than the saturated major oxides, so prefer relations involving them "
    "(HFSE ratios like Nb/Zr or Y, REE La/Ce/Nd, LILE Rb/Sr/Ba, transition-metal "
    "Cr/Ni/V) -- that is where genuine novelty lives, not in textbook oxide "
    "trends. ALSO available (OPTIONAL + SPARSE -- only ~10% of rows have them, "
    "so ALWAYS mask NaN with df.dropna(subset=[...]) before computing): radiogenic "
    "isotopes (sr87_sr86=87Sr/86Sr, nd143_nd144=143Nd/144Nd, epsilon_nd/sr/hf, "
    "pb206/207/208_pb204, hf176_hf177) and age (Ga). Isotope cross-relations and "
    "secular/age trends have the THINNEST textbook coverage -- the richest novelty "
    "space. You may use numpy/scipy/pandas/sklearn only.\n"
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


if __name__ == "__main__":
    # self-test: the seed claim parses
    print("seed CLAIM:", parse_claim(NAIVE_CLAIM_SEED)[:60], "...")
    print("seed gate1 (expected pass):", gate1_significant(
        {"effect": 0.55, "pvalue": 1e-12}))
    print("fabricated gate1 (expected fail):", gate1_significant(
        {"effect": 0.02, "pvalue": 0.4}))
