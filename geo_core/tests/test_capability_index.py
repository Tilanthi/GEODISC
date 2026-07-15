"""Tests for the GEODISC capability index + closed RSI loop (the Beast-style
measurement stack, adapted to discovery).

The capability index is a self-reported operational heuristic over the verdict
log (claim_verdicts.jsonl) — NOT an external benchmark. These tests pin its
mechanics: sub-score computation, dominant-failure mining, fix proposals, and
before/after effectiveness measurement.

Run: python3 geo_core/tests/test_capability_index.py   (also pytest-discoverable)
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from geo_core.scientific_discovery.evolved_analysis.capability_index import (  # noqa: E402
    compute_ci, mine_dominant_failure, propose_fix, measure_fix_effectiveness)


def _v(outcome, ts, both_pass=None):
    bp = both_pass if both_pass is not None else (outcome == "both-pass")
    return {"outcome": outcome, "both_pass": bp, "timestamp": ts}


def test_compute_ci_subscores_and_composite():
    # 10 verdicts: 3 gate1-failed, 1 leakage-blocked, 3 gate2-known,
    # 1 gate2-retrieval-failed, 2 both-pass
    vs = (
        [_v("gate1-failed", "2026-07-15T10:00:00") for _ in range(3)] +
        [_v("leakage-blocked", "2026-07-15T10:00:00")] +
        [_v("gate2-known", "2026-07-15T10:00:00") for _ in range(3)] +
        [_v("gate2-retrieval-failed", "2026-07-15T10:00:00")] +
        [_v("both-pass", "2026-07-15T10:00:00") for _ in range(2)]
    )
    ci = compute_ci(vs)
    assert ci["n"] == 10
    assert abs(ci["gate1_pass_rate"] - 0.6) < 1e-9      # 6/10 reached gate2
    assert abs(ci["gate2_coverage"] - 5 / 6) < 1e-9      # 5 real verdicts / 6 reached
    assert abs(ci["novel_rate"] - 0.2) < 1e-9            # 2/10 emitted
    assert ci["novelty_quality"] is None                 # not auto-computed (human)
    # STABLE weighting: always 0.3/0.4/0.3; learning term = 0 when unmeasured.
    # ci = (0.3*0.6 + 0.4*(5/6) + 0.3*0) * 100
    assert abs(ci["ci_score"] - (0.3 * 0.6 + 0.4 * (5 / 6)) * 100) < 1e-6
    # honesty: boundary notes always present (case-insensitive concept check)
    assert ci["notes"] and any("not an external benchmark" in n.lower() for n in ci["notes"])
    assert any("textbook ceiling" in n.lower() for n in ci["notes"])


def test_mine_dominant_failure():
    # gate2-known dominates -> the textbook ceiling (the realistic bottleneck)
    vs = (
        [_v("gate2-known", "2026-07-15T10:00:00") for _ in range(7)] +
        [_v("gate1-failed", "2026-07-15T10:00:00") for _ in range(2)] +
        [_v("both-pass", "2026-07-15T10:00:00")]
    )
    dom = mine_dominant_failure(vs)
    assert dom is not None
    assert dom["outcome"] == "gate2-known"
    assert dom["count"] == 7
    assert abs(dom["share"] - 7 / 9) < 1e-9   # share over failures (9), both-pass excluded


def test_propose_fix_maps_failure_to_actionable_proposal():
    p = propose_fix("gate2-known")
    assert isinstance(p, str) and len(p) > 10
    # the textbook-ceiling fix is to prime for non-obvious residual relations
    assert any(k in p.lower() for k in ("residual", "partial", "conditional"))
    # unknown failure class -> still returns a sensible proposal, never raises
    assert isinstance(propose_fix("something-new"), str)


def test_measure_fix_effectiveness_before_after():
    # a 'reduce' fix targeting gate2-retrieval-failed; >= MIN_EFFECTIVENESS_SAMPLE
    # verdicts in each window so it is actually measured.
    before = ([_v("gate2-retrieval-failed", "2026-07-14T10:00:00") for _ in range(20)] +
              [_v("gate2-known", "2026-07-14T10:00:00") for _ in range(5)])   # 25, 20 fail -> 0.8
    after = ([_v("gate2-retrieval-failed", "2026-07-15T12:00:00") for _ in range(5)] +
             [_v("gate2-known", "2026-07-15T12:00:00") for _ in range(20)])    # 25, 5 fail -> 0.2
    fixes = [{"fix_id": "openalex", "applied_at": "2026-07-15",
              "kind": "reduce", "targeted_outcome": "gate2-retrieval-failed",
              "description": "added OpenAlex geochem source"}]
    e = measure_fix_effectiveness(before + after, fixes)[0]
    assert e["fix_id"] == "openalex"
    assert abs(e["before_rate"] - 0.8) < 1e-9
    assert abs(e["after_rate"] - 0.2) < 1e-9
    assert abs(e["effectiveness"] - 0.75) < 1e-9   # (0.8-0.2)/0.8


def test_measure_min_sample_guard():
    # too few verdicts in a window -> NOT measured (no noisy number emitted)
    before = [_v("gate2-retrieval-failed", "2026-07-14T10:00:00") for _ in range(5)]
    after = [_v("gate2-known", "2026-07-15T12:00:00") for _ in range(5)]
    fixes = [{"fix_id": "small", "applied_at": "2026-07-15", "kind": "reduce",
              "targeted_outcome": "gate2-retrieval-failed", "description": "x"}]
    e = measure_fix_effectiveness(before + after, fixes)[0]
    assert e["effectiveness"] is None
    assert "insufficient sample" in e["note"]


def test_measure_increase_novel_rate():
    # a priming fix targets the YIELD (novel_rate), measured as a RISE -- the
    # correct target for a priming fix (gate2-known is ceiling-bounded).
    before = ([_v("both-pass", "2026-07-14T10:00:00") for _ in range(2)] +
              [_v("gate2-known", "2026-07-14T10:00:00") for _ in range(23)])   # 25, 2 -> 0.08
    after = ([_v("both-pass", "2026-07-15T12:00:00") for _ in range(5)] +
             [_v("gate2-known", "2026-07-15T12:00:00") for _ in range(20)])    # 25, 5 -> 0.20
    fixes = [{"fix_id": "priming", "applied_at": "2026-07-15", "kind": "increase",
              "targeted_outcome": "novel_rate", "description": "residual priming"}]
    e = measure_fix_effectiveness(before + after, fixes)[0]
    assert e["fix_id"] == "priming"
    assert abs(e["before_rate"] - 0.08) < 1e-9
    assert abs(e["after_rate"] - 0.20) < 1e-9
    assert abs(e["effectiveness"] - 1.5) < 1e-9   # (0.20-0.08)/0.08


def test_measure_skips_non_reduction_fixes_honestly():
    # a 'guard' fix (adds a block) is not a reduction fix -> reported, not measured
    vs = [_v("leakage-blocked", "2026-07-15T10:00:00") for _ in range(3)]
    fixes = [{"fix_id": "leakage-guard", "applied_at": "2026-07-14",
              "kind": "guard", "targeted_outcome": None,
              "description": "held-out leakage guard"}]
    eff = measure_fix_effectiveness(vs, fixes)
    assert eff[0]["effectiveness"] is None          # not a reduction fix
    assert "guard" in (eff[0]["note"] or "").lower() or eff[0]["note"]


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(_run())
