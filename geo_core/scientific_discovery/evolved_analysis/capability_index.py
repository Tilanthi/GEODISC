"""capability_index.py — GEODISC's measurement stack + closed RSI loop.

Adapted from the "Unleashing the Beast" measurement discipline (a measured,
gated, failure-ledger -> fix -> re-measure loop) to GEODISC's discovery engine.
The Beast builds a software company; GEODISC does science — so the *goal* differs
(revenue vs genuine, honestly-verified discovery), but the *engineering lesson*
transfers: stop running the improvement loop by hand, and instead make it
structural, measured, and trend-tracked over the engine's own failure ledger.

THE LOOP (over ``claim_verdicts.jsonl``):

    mine failures  -> identify the dominant recurring failure class (the bottleneck)
    propose fix    -> a concrete, human-readable proposal for that class
    [human applies] -> the human/curator applies the fix and registers it
                      (register_applied_fix) — the approval gate, never automatic
    measure        -> did the targeted failure class actually drop after the fix?
    fold into CI   -> measured effectiveness feeds the capability index's "learning"
                      sub-score; watch the TREND, not the level

THE CAPABILITY INDEX (CI-score) is a self-reported operational heuristic — NOT an
external benchmark. It composes the *engineering* health of the funnel
(Gate-1 proposer effectiveness, Gate-2 literature coverage, the RSI learning
rate). The *yield* (novel_rate) is reported separately and is bounded by the
domain's textbook ceiling. novelty_quality (genuine vs gate-passing-but-textbook)
requires expert human judgment and is NOT auto-computed.

Boundary claims are attached to every CI (see ``BOUNDARY_NOTES``): the value is
the trend and the honesty of the instruments, not the absolute number.

Public API:
    load_verdicts(), load_applied_fixes(), register_applied_fix(...)
    compute_ci(verdicts, applied_fixes=None, since=None) -> dict
    mine_dominant_failure(verdicts) -> dict | None
    propose_fix(outcome) -> str
    measure_fix_effectiveness(verdicts, applied_fixes) -> list[dict]
    report(verdicts, applied_fixes) -> None     (prints the honest dashboard)

CLI:  python -m evolved_analysis.capability_index
"""
from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

VERDICT_LOG = (Path.home() / ".geodisc_persistent" / "evolved_programs"
               / "claim_verdicts.jsonl")
APPLIED_FIXES = (Path.home() / ".geodisc_persistent" / "evolved_programs"
                 / "applied_fixes.json")

# Outcome buckets in the verdict log (the failure ledger).
GATE1_BLOCKED = {"gate1-failed", "leakage-blocked"}     # never reached Gate 2
GATE2_REAL = {"gate2-known", "both-pass"}               # got a real novelty verdict
GATE2_FAILED = {"gate2-retrieval-failed", "gate2-error"}  # Gate 2 couldn't evaluate

# CI composite weights (visible + adjustable — Beast discipline).
W_GATE1, W_COVERAGE, W_LEARNING = 0.30, 0.40, 0.30

# Minimum verdicts in EACH window (before AND after) to trust a fix-effectiveness
# measurement. Below this the measurement is too noisy and is reported as
# "insufficient sample" rather than a misleading number.
MIN_EFFECTIVENESS_SAMPLE = 20

BOUNDARY_NOTES = [
    "Self-reported operational heuristic over the verdict log; NOT an external "
    "benchmark.",
    "Watch the TREND over time, not the snapshot level.",
    "novel_rate is bounded by the domain's textbook ceiling (most real geochem "
    "relations are already known); a low novel_rate is correct, not a fault.",
    "novelty_quality (genuine vs gate-passing-but-textbook) requires expert human "
    "judgment; not auto-computed.",
    "ci_score=100 would mean saturation of THIS formula (every candidate "
    "significant + full retrieval + every applied fix effective), NOT a "
    "scientific breakthrough.",
]

# Failure-class -> human-gated proposal (the identify+propose half of the loop).
FIX_PROPOSALS = {
    "gate2-known":
        "Textbook ceiling: most candidates are already-known relations. Prime the "
        "proposer toward NON-OBVIOUS relations -- residuals after removing the "
        "dominant trend, PARTIAL correlations (controlling for a confounder), "
        "conditional/subset relations, and 3+-variable interactions (sec 7.5). "
        "That is where genuine novelty lives, not in pairwise Harker/Fenner/TAS.",
    "gate1-failed":
        "Candidates not statistically significant on the real held-out data. Prime "
        "the proposer toward stronger-effect geochemical relationships, or review "
        "whether EFFECT_MIN / PMAX thresholds match the dataset's signal-to-noise.",
    "gate2-retrieval-failed":
        "Literature retrieval not surfacing relevant geochemistry. Expand the "
        "corpus (more OpenAlex concept filters, or additional geochem abstract "
        "sources) so Gate 2 can confirm novelty instead of failing.",
    "leakage-blocked":
        "Candidates ignore the held-out (df_eval) split. Reinforce the df_eval "
        "contract in the proposer prompt so the headline statistic comes from "
        "held-out data.",
    "gate2-error":
        "Gate-2 judge/retrieval errored. Check the LLM-gateway availability and "
        "the OpenAlex/arXiv/S2 endpoints.",
}
DEFAULT_PROPOSAL = ("No specific proposal mapped for this outcome; review the "
                    "verdict log manually.")


# --------------------------------------------------------------------------- #
# I/O                                                                         #
# --------------------------------------------------------------------------- #
def load_verdicts(path: Path = VERDICT_LOG) -> List[dict]:
    """Read the verdict log (one JSON object per line). Empty list if absent."""
    if not path.is_file():
        return []
    try:
        return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    except Exception as e:
        logger.warning("[ci] could not read verdict log: %s", e)
        return []


def load_applied_fixes(path: Path = APPLIED_FIXES) -> List[dict]:
    if not path.is_file():
        return []
    try:
        d = json.loads(path.read_text())
        return d if isinstance(d, list) else []
    except Exception:
        return []


def register_applied_fix(fix_id: str, applied_at: str, kind: str,
                         targeted_outcome: Optional[str], description: str,
                         path: Path = APPLIED_FIXES) -> dict:
    """Record a fix a human APPLIED (the approval gate). ``kind`` in
    {'reduce','guard','add-source','instrument'}; only 'reduce' fixes are later
    measured for failure-class reduction. Idempotent on fix_id."""
    fixes = load_applied_fixes(path)
    if any(f.get("fix_id") == fix_id for f in fixes):
        return {"fix_id": fix_id, "registered": False, "reason": "already present"}
    rec = {"fix_id": fix_id, "applied_at": applied_at, "kind": kind,
           "targeted_outcome": targeted_outcome, "description": description}
    fixes.append(rec)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(fixes, indent=2))
    except Exception as e:
        logger.warning("[ci] could not write applied_fixes: %s", e)
    return {"fix_id": fix_id, "registered": True, "record": rec}


# --------------------------------------------------------------------------- #
# the capability index                                                        #
# --------------------------------------------------------------------------- #
def _outcome(v: dict) -> str:
    return str(v.get("outcome") or "")


def _ts(v: dict) -> str:
    return str(v.get("timestamp") or "")


def compute_ci(verdicts: List[dict], applied_fixes: Optional[List[dict]] = None,
               since: Optional[str] = None) -> dict:
    """Compute the capability index over a verdict list.

    Returns a dict with engineering sub-scores, the composite ``ci_score`` (0-100),
    the reported (domain-bounded) yield, and the boundary notes. Never raises.
    """
    if since:
        verdicts = [v for v in verdicts if _ts(v) >= since]
    n = len(verdicts)
    if n == 0:
        return {"n": 0, "ci_score": 0.0, "notes": BOUNDARY_NOTES,
                "window": "no verdicts", "computed_at": _now()}

    outs = [_outcome(v) for v in verdicts]
    gate1_pass = sum(1 for o in outs if o not in GATE1_BLOCKED)
    gate1_pass_rate = gate1_pass / n

    real = sum(1 for o in outs if o in GATE2_REAL)
    failed = sum(1 for o in outs if o in GATE2_FAILED)
    denom = real + failed
    gate2_coverage = (real / denom) if denom else 0.0

    novel_rate = sum(1 for o in outs if o == "both-pass") / n

    # learning = mean measured effectiveness of 'reduce'-type applied fixes
    learning = None
    if applied_fixes:
        eff = measure_fix_effectiveness(verdicts, applied_fixes)
        measured = [e["effectiveness"] for e in eff
                    if e.get("effectiveness") is not None]
        if measured:
            learning = sum(measured) / len(measured)

    # STABLE WEIGHTING (the CI must be comparable over time): always use the same
    # weights; an unmeasured learning term contributes 0 (neutral) rather than
    # re-weighting the other sub-scores. (An earlier version switched between
    # 0.5/0.5 and 0.3/0.4/0.3 when learning became available, which made the CI
    # non-comparable across that transition -- a misleading instrument.)
    learning_term = learning if learning is not None else 0.0
    ci = (W_GATE1 * gate1_pass_rate + W_COVERAGE * gate2_coverage
          + W_LEARNING * learning_term) * 100

    ts = sorted(_ts(v) for v in verdicts if _ts(v))
    window = (f"{ts[0][:19]} -> {ts[-1][:19]}") if ts else "undated"
    return {
        "n": n,
        "gate1_pass_rate": gate1_pass_rate,
        "gate2_coverage": gate2_coverage,
        "novel_rate": novel_rate,
        "novelty_quality": None,   # human-judged; deliberately not auto-computed
        "learning": learning,
        "ci_score": ci,
        "window": window,
        "computed_at": _now(),
        "notes": BOUNDARY_NOTES,
    }


def mine_dominant_failure(verdicts: List[dict]) -> Optional[dict]:
    """Identify the largest FAILURE bucket (the bottleneck). both-pass (success)
    is excluded. Returns {outcome, count, share} or None if there are no
    failures."""
    from collections import Counter
    failures = [_outcome(v) for v in verdicts
                if _outcome(v) and _outcome(v) != "both-pass"]
    if not failures:
        return None
    c = Counter(failures)
    outcome, count = c.most_common(1)[0]
    return {"outcome": outcome, "count": count, "share": count / len(failures)}


def propose_fix(outcome: str) -> str:
    """Human-gated proposal for a failure class. Never raises."""
    return FIX_PROPOSALS.get(outcome, DEFAULT_PROPOSAL)


def measure_fix_effectiveness(verdicts: List[dict],
                              applied_fixes: List[dict]) -> List[dict]:
    """For each applied fix, measure whether its target moved in the intended
    direction after the fix date.

    kind='reduce'   -> targeted_outcome is a failure bucket; effectiveness =
                       (before_rate - after_rate)/before_rate  (did it DROP?).
    kind='increase' -> targeted_outcome is a yield metric ('novel_rate' counts
                       'both-pass'); effectiveness = (after_rate -
                       before_rate)/before_rate  (did it RISE?). Priming fixes
                       should target novel_rate (a yield), NOT a failure class --
                       gate2-known is bounded by the textbook ceiling.
    other kinds     -> not measured (reported as n/a).

    A min-sample guard (MIN_EFFECTIVENESS_SAMPLE in each window) stops a tiny
    after-window from emitting a confident, noisy number. effectiveness is None
    when the fix is not directional, the sample is too small, or there is no
    prior baseline to compare against.
    """
    out = []
    for f in applied_fixes:
        fix_id = f.get("fix_id")
        kind = f.get("kind")
        target = f.get("targeted_outcome")
        applied_at = f.get("applied_at", "")
        if kind not in ("reduce", "increase") or not target:
            out.append({"fix_id": fix_id, "kind": kind, "effectiveness": None,
                        "note": f"{kind} fix -- not a directional fix; not measured"})
            continue
        outcome_to_count = "both-pass" if target == "novel_rate" else target
        before = [v for v in verdicts if _ts(v) and _ts(v) < applied_at]
        after = [v for v in verdicts if _ts(v) and _ts(v) >= applied_at]
        if (len(before) < MIN_EFFECTIVENESS_SAMPLE
                or len(after) < MIN_EFFECTIVENESS_SAMPLE):
            out.append({"fix_id": fix_id, "kind": kind, "target": target,
                        "effectiveness": None, "before_n": len(before),
                        "after_n": len(after),
                        "note": (f"insufficient sample (before={len(before)}, "
                                 f"after={len(after)}); need >="
                                 f" {MIN_EFFECTIVENESS_SAMPLE} in each window")})
            continue
        before_rate = sum(1 for v in before if _outcome(v) == outcome_to_count) / len(before)
        after_rate = sum(1 for v in after if _outcome(v) == outcome_to_count) / len(after)
        if before_rate <= 0:
            eff, note = None, f"no prior occurrences of {target} (before_rate=0)"
        elif kind == "reduce":
            eff = (before_rate - after_rate) / before_rate
            note = (f"{target}: {before_rate:.3f} -> {after_rate:.3f} "
                    f"({'reduced' if eff > 0 else 'rose' if eff < 0 else 'flat'})")
        else:  # increase
            eff = (after_rate - before_rate) / before_rate
            note = (f"{target}: {before_rate:.3f} -> {after_rate:.3f} "
                    f"({'rose' if eff > 0 else 'fell' if eff < 0 else 'flat'})")
        out.append({"fix_id": fix_id, "kind": kind, "target": target,
                    "before_rate": before_rate, "after_rate": after_rate,
                    "effectiveness": eff, "note": note})
    return out


def report(verdicts: List[dict], applied_fixes: List[dict]) -> None:
    """Print the honest capability dashboard."""
    ci = compute_ci(verdicts, applied_fixes)
    print("=" * 72)
    print("GEODISC DISCOVERY CAPABILITY INDEX")
    print("=" * 72)
    if ci["n"] == 0:
        print("(no verdicts yet -- the engine has not evaluated any candidates)")
        return
    print(f"CI-score          : {ci['ci_score']:.1f} / 100   "
          f"[engineering health; trend over level]")
    print(f"  gate1_pass_rate : {ci['gate1_pass_rate']:.3f}  "
          f"(candidates significant on real data)")
    print(f"  gate2_coverage  : {ci['gate2_coverage']:.3f}  "
          f"(retrieval surfaces relevant geochem literature)")
    print(f"  learning        : "
          f"{('%.3f' % ci['learning']) if ci['learning'] is not None else 'n/a'}  "
          f"(measured RSI effectiveness of applied fixes)")
    print(f"novel_rate (yield): {ci['novel_rate']:.3f}   "
          f"[domain-bounded by the textbook ceiling]")
    print(f"novelty_quality   : n/a   [requires expert human judgment]")
    print(f"verdicts (n)      : {ci['n']}   window: {ci['window']}")
    print()
    dom = mine_dominant_failure(verdicts)
    if dom:
        print(f"Dominant failure  : {dom['outcome']} "
              f"({dom['count']}, {dom['share']*100:.0f}% of failures)")
        print(f"Proposed fix (HUMAN-GATED, not auto-applied):")
        print(f"  -> {propose_fix(dom['outcome'])}")
    eff = measure_fix_effectiveness(verdicts, applied_fixes)
    if eff:
        print()
        print("Applied-fix effectiveness (measured):")
        for e in eff:
            ev = ("%.1f%%" % (e["effectiveness"] * 100)) if e.get("effectiveness") is not None else "n/a"
            print(f"  {e['fix_id']:<28} effectiveness={ev:<8} {e.get('note','')}")
    print()
    print("Boundary claims (load-bearing -- do not soften):")
    for note in ci["notes"]:
        print(f"  - {note}")
    print("=" * 72)


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    report(load_verdicts(), load_applied_fixes())
