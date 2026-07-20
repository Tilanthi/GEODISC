"""run_claim_search.py — Phase-2 open-ended Eureka search driver.

Runs the two-gate EVALUATE on (CLAIM, run_claim) candidate artifacts:

    Gate 1 (real-data, SANDBOXED, no network)  -> claim_eval_worker
    Gate 2 (literature novelty, WITH network)  -> novelty_gate.check_novelty

A candidate is emitted to ``evolved_discoveries.json`` ONLY if it passes BOTH
gates. The supervisor's consumer then folds it into the genuine store through
the discovery_store chokepoint — so a claim can never bypass verification.

Run (decoupled, like the Phase-1 engine):
    PYTHONPATH=geo_core/scientific_discovery python -m evolved_analysis.run_claim_search [--steps N]

If no LLM token is set, it runs the deterministic seed through both gates
(sanity check: the known seed passes Gate 1 and is caught by Gate 2) and exits.
With a token, it also evolves N LLM-proposed candidates looking for a
significant AND novel relationship.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .claim_task import (NAIVE_CLAIM_SEED, TASK_SYSTEM, ENTRY_POINT,
                         parse_claim, gate1_significant, claim_uses_heldout_split,
                         _direction_consistent, gate1_pvalue_consistent)
from .proposer import LLMProposer, apply_diff
from .verdict_log import log_verdict
try:
    from ..discovery_store import _atomic_write  # when imported within geo_core
except ImportError:
    from discovery_store import _atomic_write     # standalone (evolved_analysis as top-level)
try:
    from . import canonical_signature as canonical  # Tier 1: known-signature pre-filter
except ImportError:
    import canonical_signature as canonical         # standalone
try:
    from . import surprise                              # Tier 2: surprise objective
except ImportError:
    import surprise                                     # standalone
try:
    from . import diversity, inspirations, data_profile  # Tier 3
except ImportError:
    import diversity, inspirations, data_profile          # standalone

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER = "evolved_analysis.claim_eval_worker"
EVOLVED_STORE = Path.home() / ".geodisc_persistent" / "evolved_discoveries.json"
try:
    import shutil
    _SANDBOX_EXEC = shutil.which("sandbox-exec")
except Exception:
    _SANDBOX_EXEC = None
_PROFILE = Path(__file__).resolve().parent / "geo_worker.sb"


def _program_hash(src: str) -> str:
    return hashlib.sha1(src.encode()).hexdigest()[:10]


def _canonical_prefilter_enabled() -> bool:
    """Tier 1 pre-filter on by default; set GEODISC_CANONICAL_PREFILTER=0 to disable."""
    return os.environ.get("GEODISC_CANONICAL_PREFILTER", "1") not in ("0", "false", "False")


_EVAL_N_CACHE: dict = {}

def _eval_n(seed: int = 42):
    """Max sample size available to a candidate (the held-out eval split), cached.

    Used by the p-value provenance guard to bound the smallest p a reported |r|
    could legitimately yield. Returns None if real data is unavailable (the guard
    then no-ops conservatively)."""
    if seed not in _EVAL_N_CACHE:
        try:
            from . import real_data
            _EVAL_N_CACHE[seed] = len(real_data.load_split(seed=seed)["eval"])
        except Exception:
            _EVAL_N_CACHE[seed] = None
    return _EVAL_N_CACHE[seed]


# --------------------------------------------------------------------------- #
# Gate 1: sandboxed real-data test                                             #
# --------------------------------------------------------------------------- #
def gate1_run(src: str, seed: int = 42, timeout: float = 90.0) -> dict:
    """Run the candidate's run_claim in a sandboxed subprocess on real data."""
    if not src or f"def {ENTRY_POINT}" not in src:
        return {"effect": 0.0, "pvalue": 1.0, "error": f"no {ENTRY_POINT}"}
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     dir=str(Path.cwd())) as tf:
        tf.write(src)
        tf.flush()
        src_path = tf.name
    try:
        env = {**os.environ,
               "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
        cmd = [sys.executable, "-m", WORKER, src_path, str(seed)]
        # Wrap in sandbox-exec when available (no-network, temp-writes-only).
        if _SANDBOX_EXEC and _PROFILE.is_file():
            cmd = [_SANDBOX_EXEC, "-f", str(_PROFILE)] + cmd
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, cwd=str(REPO_ROOT), env=env,
                              check=False)
    except subprocess.TimeoutExpired:
        return {"effect": 0.0, "pvalue": 1.0, "error": "timeout"}
    except Exception as e:
        return {"effect": 0.0, "pvalue": 1.0,
                "error": f"spawn:{type(e).__name__}:{str(e)[:80]}"}
    finally:
        try:
            Path(src_path).unlink()
        except OSError:
            pass
    out = proc.stdout.strip().splitlines()
    if not out:
        return {"effect": 0.0, "pvalue": 1.0,
                "error": (proc.stderr.strip()[:160] or "no stdout")}
    try:
        return json.loads(out[-1])
    except json.JSONDecodeError:
        return {"effect": 0.0, "pvalue": 1.0,
                "error": f"unparseable: {out[-1][:120]}"}


# --------------------------------------------------------------------------- #
# Two-gate evaluation                                                          #
# --------------------------------------------------------------------------- #
def two_gate_eval(src: str, seed: int = 42, run_gate2: bool = True,
                  dataset: str = "default") -> dict:
    """Run the leakage guard, then Gate 1, then (if it passes) Gate 2.

    Returns a full verdict dict and appends one JSONL verdict line per candidate
    (§7.2) so the search funnel stays diagnosable even when run as a subprocess
    with stdout discarded.
    """
    claim = parse_claim(src) or ""
    program_hash = _program_hash(src)

    # §7.3 — cheap static leakage guard BEFORE spending a sandbox eval. A
    # candidate that never reads the held-out (eval) split is rejected here,
    # without spawning the worker.
    ok, reason = claim_uses_heldout_split(src)
    if not ok:
        result = {
            "claim": claim,
            "program_hash": program_hash,
            "gate1": {"pass": False, "reason": reason, "metrics": {}},
            "gate2": None,
            "both_pass": False,
        }
        log_verdict(result, dataset)
        return result

    # Tier 1 — canonical-signature pre-filter: SKIP the 90-second sandbox for
    # any claim whose MEANING Gate 2 has already ruled 'known' on some prior
    # phrasing. Provably conservative: a signature only enters the registry
    # after a full Gate 2 (retrieval + LLM judge) verdict of 'known', so this
    # never blocks a relation Gate 2 hasn't already rejected — it only kills
    # re-phrasings of textbook/known relations before spending a sandbox eval.
    # Disable with GEODISC_CANONICAL_PREFILTER=0.
    if _canonical_prefilter_enabled():
        try:
            _known = canonical.is_known(claim)
        except Exception:
            _known = False
        if _known:
            result = {
                "claim": claim,
                "program_hash": program_hash,
                "gate1": {"pass": None,
                          "reason": "skipped:canonical-known-signature",
                          "metrics": {}},
                "gate2": {"pass": False, "status": "known", "n_retrieved": 0,
                          "reasoning": "canonical signature previously judged "
                                       "known by Gate 2 (sandbox skipped)"},
                "both_pass": False,
            }
            log_verdict(result, dataset)
            return result

    g1_metrics = gate1_run(src, seed=seed)
    g1_pass, g1_reason = gate1_significant(g1_metrics)

    result = {
        "claim": claim,
        "program_hash": program_hash,
        "gate1": {"pass": g1_pass, "reason": g1_reason,
                  "metrics": {k: v for k, v in g1_metrics.items() if k != "trace"}},
        "gate2": None,
        "both_pass": False,
    }

    if not g1_pass:
        log_verdict(result, dataset)
        return result  # fabricated/non-significant claim stops here

    # p-value provenance guard: independently re-derive the p the reported |r|
    # could yield at the max available n; reject recycled/hardcoded p-values (a
    # proposer can otherwise satisfy "significant" by returning a copied tiny p).
    pv_ok, pv_reason = gate1_pvalue_consistent(g1_metrics.get("effect"),
                                               g1_metrics.get("pvalue"),
                                               _eval_n(seed))
    if not pv_ok:
        result["gate1"] = {"pass": False, "reason": pv_reason,
                           "metrics": result["gate1"]["metrics"]}
        log_verdict(result, dataset)
        return result  # self-reported p is implausible for its own |r|

    # sign-consistency guard: the claim's STATED direction must match the effect
    eff = g1_metrics.get("effect")
    if eff is not None:
        d_ok, d_reason = _direction_consistent(claim, eff)
        if not d_ok:
            result["gate1"] = {"pass": False, "reason": d_reason,
                               "metrics": result["gate1"]["metrics"]}
            log_verdict(result, dataset)
            return result  # claim misstates its own finding's direction

    # Tier 2 — surprise score: does the CONFIRMED sign contradict the textbook
    # expectation for this element pair? (1.0 anomaly / 0.0 confirmation / 0.5
    # unstaged). Pure annotation for ranking/triage — never affects pass/fail.
    try:
        result["surprise"] = surprise.surprise_score(claim, surprise.sign_of(eff))
    except Exception:
        result["surprise"] = None

    if run_gate2:
        try:
            from .novelty_gate import check_novelty, novelty_tier
            nr = check_novelty(claim)
            result["gate2"] = {
                "pass": nr.novel, "status": nr.status, "n_retrieved": nr.n_retrieved,
                "reasoning": nr.reasoning[:200],
                "entailed_by": nr.entailed_by.title[:80] if nr.entailed_by else None,
            }
            result["novelty_tier"] = novelty_tier(nr)  # Tier 2: strong/weak-novel tier
            # Tier 1 — learn: a full Gate 2 'known' verdict (textbook blocklist or
            # literature-entailed) means re-phrasings of this relation should be
            # skipped before the sandbox next time. register_known is a no-op if
            # the signature is already in the registry.
            if nr.status == "known":
                try:
                    canonical.register_known(claim)
                except Exception:
                    pass
        except Exception as e:
            # Gate-2 failure is conservative: do NOT promote as novel.
            result["gate2"] = {"pass": False, "status": "gate2-error",
                               "reasoning": f"{type(e).__name__}: {str(e)[:120]}"}
    else:
        result["gate2"] = {"pass": None, "status": "skipped"}

    result["both_pass"] = bool(g1_pass and result["gate2"] and result["gate2"]["pass"] is True)
    log_verdict(result, dataset)
    return result


# --------------------------------------------------------------------------- #
# emit (only both-gate survivors, through the chokepoint-compatible shape)     #
# --------------------------------------------------------------------------- #
def _emit(verdict: dict) -> None:
    """Append a both-gate survivor to evolved_discoveries.json (bare list)."""
    if not verdict["both_pass"]:
        return
    claim = verdict["claim"]
    record = {
        "title": f"Novel verified claim: {claim[:80]}",
        "abstract": claim,
        "discovery_type": "machine_verified_claim",
        "timestamp": _now_iso(),
        "source": "evolved_analysis",
        "verification": {
            "program_hash": verdict["program_hash"],
            "metric_name": "two_gate_claim",
            "real_data_result": verdict["gate1"]["metrics"],
            "gate": {"gate1_real_data": "pass",
                     "gate2_novelty": verdict["gate2"]["status"]},
            "claim": claim,
            "effect": verdict["gate1"]["metrics"].get("effect"),
            "pvalue": verdict["gate1"]["metrics"].get("pvalue"),
            "surprise": verdict.get("surprise"),           # Tier 2
            "novelty_tier": verdict.get("novelty_tier"),   # Tier 2
        },
    }
    EVOLVED_STORE.parent.mkdir(parents=True, exist_ok=True)
    # Robust load: a truncated/corrupt staging file (e.g. process killed mid-write)
    # must not silently drop this survivor AND every future one. Default to [] and
    # continue rather than propagating JSONDecodeError into the broad except below.
    try:
        data = json.loads(EVOLVED_STORE.read_text()) if EVOLVED_STORE.exists() else []
    except (json.JSONDecodeError, OSError):
        logger.warning("[claim_search] staging file unreadable, starting fresh: %s",
                       EVOLVED_STORE)
        data = []
    if not isinstance(data, list):
        data = []
    try:
        if not any((r.get("verification") or {}).get("program_hash")
                   == verdict["program_hash"] for r in data if isinstance(r, dict)):
            data.append(record)
            # Atomic write (temp + os.replace): a timeout-kill cannot truncate the
            # staging file and poison all subsequent emits.
            _atomic_write(EVOLVED_STORE, json.dumps(data, indent=2))
            logger.info("[claim_search] ✅ EMITTED both-gate survivor: %s", claim[:70])
    except Exception as e:
        logger.warning("[claim_search] emit failed: %s", e)


def _now_iso() -> str:
    import datetime
    return datetime.datetime.now().isoformat()


def _verdict_feedback_hints(path=None, n_known: int = 5, n_failed: int = 8) -> list:
    """Closed loop: read recent verdicts and return proposer hints.

    The proposer is fed its own recent failures: gate2-known claims (textbook
    families to AVOID) and gate1-failed claims (generate STRONGER-effect
    relations). Also detects the dominant failure PATTERN (e.g. KeyError from
    wrong column names) and injects specific corrective guidance.
    """
    try:
        if path is None:
            path = Path.home() / ".geodisc_persistent" / "evolved_programs" / "claim_verdicts.jsonl"
        p = Path(path)
        if not p.is_file():
            return []
        rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
        known = [r["claim"] for r in rows
                 if r.get("outcome") == "gate2-known" and r.get("claim")][-n_known:]
        failed_rows = [r for r in rows
                       if r.get("outcome") == "gate1-failed"
                       and "sign-mismatch" not in ((r.get("gate1") or {}).get("reason") or "")
                       and r.get("claim")][-n_failed:]
        failed = [r["claim"] for r in failed_rows]
        hints = []
        if known:
            hints.append("Recent candidates REJECTED as already-known textbook -- "
                         "do NOT propose similar relations:")
            hints.extend(f"  - {c[:140]}" for c in known)
        if failed:
            hints.append("Recent candidates FAILED Gate 1 (weak or errored) -- "
                         "generate STRONGER-effect relations using EXACT column names:")
            hints.extend(f"  - {c[:140]}" for c in failed)
        # detect the dominant failure pattern + inject corrective guidance
        from collections import Counter
        cats = Counter()
        for r in failed_rows:
            g1 = r.get("gate1") or {}; m = g1.get("metrics") or {}
            reason = ((g1.get("reason") or "") + " " + str(m.get("error") or "")).lower()
            if "keyerror" in reason or "not in index" in reason:
                cats["missing-column"] += 1
            elif "nan" in reason:
                cats["nan"] += 1
            elif "module" in reason and ("not found" in reason or "no module" in reason):
                cats["bad-import"] += 1
            elif "not significant" in reason:
                cats["weak"] += 1
            else:
                cats["other"] += 1
        if cats:
            top_cat, top_n = cats.most_common(1)[0]
            total = sum(cats.values())
            if top_cat == "missing-column":
                hints.append(
                    f"FAILURE PATTERN ({top_n}/{total}): KeyError on bare element names. "
                    "The EXACT DataFrame columns are: oxides sio2/tio2/al2o3/feo_tot/mgo/"
                    "cao/mno/na2o/k2o/p2o5; traces v_ppm/cr_ppm/co_ppm/ni_ppm/cu_ppm/"
                    "zn_ppm/rb_ppm/sr_ppm/y_ppm/zr_ppm/nb_ppm/ba_ppm/la_ppm/ce_ppm/"
                    "nd_ppm (the _ppm suffix is REQUIRED -- NOT bare 'nd'/'nb'); isotopes "
                    "sr87_sr86/nd143_nd144/epsilon_nd/epsilon_sr/pb206_pb204/pb207_pb204/"
                    "pb208_pb204/hf176_hf177/epsilon_hf; age. Use these EXACT names.")
            elif top_cat == "nan":
                hints.append(
                    f"FAILURE PATTERN ({top_n}/{total}): NaN in computation. ALWAYS "
                    "df=df.dropna(subset=[your_cols]) before spearmanr/corr -- isotope/"
                    "age columns are sparse (~10% of rows).")
            elif top_cat == "weak":
                hints.append(
                    f"FAILURE PATTERN ({top_n}/{total}): |effect| < 0.30. Aim for |r|"
                    " >= 0.4; prefer co-varying element groups (HFSE Zr-Nb-Y, LREE "
                    "La-Ce-Nd, LILE Rb-Sr-Ba) and PARTIAL correlations.")
        # Integrity corrective: if recent gate1 rejections were for misstating the
        # direction or recycling a p-value (the surprise-objective's failure mode),
        # tell the proposer to compute-then-report. Closes the behavior loop.
        try:
            recent = rows[-40:]
            mm = sum("sign-mismatch" in ((r.get("gate1") or {}).get("reason") or "") for r in recent)
            pv = sum("pvalue-implausible" in ((r.get("gate1") or {}).get("reason") or "") for r in recent)
            if mm + pv >= 2:
                hints.append(
                    f"INTEGRITY ({mm} sign-mismatch + {pv} implausible-p rejections recently): "
                    "those claims were rejected because their STATED direction disagreed with the "
                    "computed effect, or their p-value was recycled/implausible. COMPUTE the relation "
                    "on the data first, then state EXACTLY the sign and p your run_claim measured. "
                    "Do not write a direction or p-value the data does not show.")
        except Exception:
            pass
        # Tier 2 — surprise nudge: if recent survivors were confirmations of a
        # textbook pair, push the proposer toward the opposite sign / an anomaly.
        try:
            recent_survivors = [(r.get("claim"), r.get("surprise"))
                                for r in rows
                                if r.get("outcome") == "both-pass"
                                and r.get("claim")][-8:]
            shint = surprise.surprise_hint(recent_survivors)
            if shint:
                hints.append(shint)
        except Exception:
            pass
        return hints
    except Exception:
        return []


# --------------------------------------------------------------------------- #
# main                                                                         #
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Phase-2 two-gate claim search")
    ap.add_argument("--steps", type=int, default=5,
                    help="LLM-proposed candidates to try (needs token)")
    ap.add_argument("--seed-only", action="store_true",
                    help="just run the deterministic seed through both gates and exit")
    ap.add_argument("--no-gate2", action="store_true",
                    help="run Gate 1 only (skip network/novelty)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    logger.info("[claim_search] === seed claim through both gates (sanity) ===")
    verdict = two_gate_eval(NAIVE_CLAIM_SEED, run_gate2=not args.no_gate2)
    _log_verdict(verdict)
    # The seed is a KNOWN effect: expect gate1 pass + gate2 'known' (no emit).
    if verdict["both_pass"]:
        logger.warning("[claim_search] seed unexpectedly passed both gates — "
                       "novelty gate may be too permissive")

    if args.seed_only or not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        if not args.seed_only:
            logger.info("[claim_search] no LLM token — seed-only run done")
        return

    logger.info("[claim_search] === evolving %d LLM-proposed claim(s) ===",
                args.steps)
    try:
        proposer = LLMProposer(task_system=data_profile.build_task_system(),
                               entry_point=ENTRY_POINT)
    except Exception as e:
        logger.warning("[claim_search] LLM proposer unavailable: %s", e)
        return
    parent = NAIVE_CLAIM_SEED
    parent_metrics = verdict["gate1"]["metrics"]
    base_hints = _verdict_feedback_hints()   # Phases 3+4: feed recent failures back
    tracker = diversity.FamilyTracker()       # Tier 3: per-family diversity pressure
    for i in range(args.steps):
        hints = list(base_hints)
        dhint = tracker.hint()
        if dhint:
            hints.append(dhint)
        child, _spec, info = proposer.propose(
            parent, parent_metrics, None, inspirations.pick(i),
            context_level="rich", hints=hints)
        if not child:
            logger.info("[claim_search] step %d: proposer returned nothing (%s)",
                        i, info.get("error", "?"))
            continue
        v = two_gate_eval(child, run_gate2=not args.no_gate2)
        logger.info("[claim_search] step %d claim: %s", i, (v["claim"] or "")[:70])
        _log_verdict(v, prefix=f"  step {i}: ")
        _emit(v)
        tracker.note(v.get("claim") or parse_claim(child) or "")  # Tier 3
        # adopt as parent if it passed gate 1 (a real effect to build on)
        if v["gate1"]["pass"]:
            parent, parent_metrics = child, v["gate1"]["metrics"]


def _log_verdict(v: dict, prefix: str = ""):
    logger.info("%sgate1: %s", prefix, v["gate1"]["reason"])
    g2 = v["gate2"]
    if g2:
        logger.info("%sgate2: %s (%s) n=%s", prefix, g2.get("status"),
                    (g2.get("reasoning") or "")[:90], g2.get("n_retrieved"))
    logger.info("%s=> both_pass=%s", prefix, v["both_pass"])


if __name__ == "__main__":
    main()
