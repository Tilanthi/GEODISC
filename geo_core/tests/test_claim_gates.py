"""Tests for the Gate-1 leakage guard (§7.3) and structured verdict logging (§7.2).

The two-gate engine inherits a held-out contract: Gate 1 must report
significance computed on the held-out (eval) split, not the train split.
A candidate that ignores df_eval makes in-sample == out-of-sample, so the
gate's "significant on real held-out data" promise is silently a lie. This
is the §7.3 trap. The guard below is a cheap AST check run BEFORE we spend
a sandbox eval, and the verdict log is a per-candidate JSONL line written
INSIDE the search process (independent of stdout capture) so the §4 funnel
can be diagnosed.

Run: python3 geo_core/tests/test_claim_gates.py   (also pytest-discoverable)
"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from geo_core.scientific_discovery.evolved_analysis.claim_task import (  # noqa: E402
    claim_uses_heldout_split, NAIVE_CLAIM_SEED)
from geo_core.scientific_discovery.evolved_analysis import verdict_log  # noqa: E402

# --- candidate programs for the static guard --------------------------------- #
# Train-only: the bug. Computes the headline on df_train; never touches df_eval.
LEAKY_SRC = '''CLAIM = "A relationship computed on the training split only."
def run_claim(df_train, df_eval):
    import numpy as np
    df = df_train
    x = df["a"].to_numpy(float)
    return {"effect": 0.5, "pvalue": 1e-9, "effect_type": "x", "summary": "s"}
'''

# Eval via subscript: compliant.
EVAL_SUBSCRIPT_SRC = '''CLAIM = "Uses the held-out eval split via subscript."
def run_claim(df_train, df_eval):
    import numpy as np
    x = df_eval["a"].to_numpy(float)
    return {"effect": 0.5, "pvalue": 1e-9, "effect_type": "x", "summary": "s"}
'''

# Legitimate ML pattern: fit on train, predict/score on eval. Must NOT be
# rejected as a false positive.
EVAL_PREDICT_SRC = '''CLAIM = "Fit on train, score predictions on the held-out eval frame."
def run_claim(df_train, df_eval):
    import numpy as np
    from sklearn.linear_model import LinearRegression
    m = LinearRegression().fit(df_train[["a"]], df_train["y"])
    pred = m.predict(df_eval[["a"]])
    return {"effect": 0.5, "pvalue": 1e-9, "effect_type": "x", "summary": "s"}
'''


# --- §7.3 leakage guard ------------------------------------------------------ #
def test_guard_rejects_train_only():
    """The dominant failure mode (copying the seed's df = df_train) is rejected."""
    ok, reason = claim_uses_heldout_split(LEAKY_SRC)
    assert ok is False, "train-only candidate must be rejected"
    assert "leakage" in reason, f"reason should name the leakage trap: {reason}"


def test_guard_accepts_eval_subscript():
    ok, reason = claim_uses_heldout_split(EVAL_SUBSCRIPT_SRC)
    assert ok is True, f"eval-subscript candidate wrongly rejected: {reason}"


def test_guard_accepts_eval_predict_no_false_positive():
    """Fit-on-train / predict-on-eval is the correct held-out pattern; the guard
    must not flag it as leakage."""
    ok, reason = claim_uses_heldout_split(EVAL_PREDICT_SRC)
    assert ok is True, f"legitimate predict(df_eval) wrongly rejected: {reason}"


def test_guard_rejects_signature_only_mention():
    """df_eval appearing ONLY in the parameter list (never used in the body) is
    not a real held-out use — a substring check would wrongly pass this."""
    src = ('CLAIM = "Mentions df_eval only in the signature."\n'
           'def run_claim(df_train, df_eval):\n'
           '    df = df_train\n'
           '    x = df["a"].to_numpy(float)\n'
           '    return {"effect": 0.5, "pvalue": 1e-9}\n')
    ok, _ = claim_uses_heldout_split(src)
    assert ok is False


def test_seed_is_compliant():
    """The deterministic seed is run through both gates on every sanity pass; it
    must itself pass the leakage guard (and therefore compute its headline on the
    held-out frame). If this fails, the floor example is the bug."""
    ok, reason = claim_uses_heldout_split(NAIVE_CLAIM_SEED)
    assert ok is True, f"seed is leaky: {reason}"


# --- §7.2 verdict logging ---------------------------------------------------- #
def test_log_verdict_writes_one_line_per_call():
    fd, p = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    Path(p).unlink()  # start empty
    v = {
        "claim": "c", "program_hash": "h",
        "gate1": {"pass": False, "reason": "gate1-failed: weak",
                  "metrics": {"effect": 0.1, "pvalue": 0.4}},
        "gate2": None, "both_pass": False,
    }
    verdict_log.log_verdict(v, dataset="ds1", path=p)
    verdict_log.log_verdict(v, dataset="ds1", path=p)
    lines = Path(p).read_text().strip().splitlines()
    assert len(lines) == 2, f"expected 2 lines, got {len(lines)}"
    rec = json.loads(lines[0])
    assert rec["program_hash"] == "h"
    assert rec["dataset"] == "ds1"
    assert rec["outcome"] == "gate1-failed"
    assert "timestamp" in rec
    os.unlink(p)


def test_outcome_bucketing():
    o = verdict_log.outcome
    assert o({"gate1": {"pass": False, "reason": "leakage: held-out unused"}}) \
        == "leakage-blocked"
    assert o({"gate1": {"pass": False, "reason": "gate1-failed: weak"}}) \
        == "gate1-failed"
    assert o({"gate1": {"pass": True}, "gate2": {"pass": False, "status": "known"},
              "both_pass": False}) == "gate2-known"
    assert o({"gate1": {"pass": True},
              "gate2": {"pass": False, "status": "retrieval-failed"},
              "both_pass": False}) == "gate2-retrieval-failed"
    assert o({"gate1": {"pass": True}, "gate2": {"pass": False, "status": "gate2-error"},
              "both_pass": False}) == "gate2-error"
    assert o({"gate1": {"pass": True}, "gate2": {"pass": True, "status": "novel"},
              "both_pass": True}) == "both-pass"


# --- integration: the guard short-circuits before the sandbox ---------------- #
def test_two_gate_short_circuits_on_leaky_candidate():
    """The §7.3 value: a leaky candidate is rejected WITHOUT spawning the
    sandboxed Gate-1 subprocess (no point spending the eval)."""
    from geo_core.scientific_discovery.evolved_analysis import run_claim_search as rcs

    spawned = {"yes": False}

    def _spy_gate1(src, seed=42, timeout=90.0):
        spawned["yes"] = True
        return {"effect": 0.0, "pvalue": 1.0}

    orig = rcs.gate1_run
    rcs.gate1_run = _spy_gate1
    try:
        verdict = rcs.two_gate_eval(LEAKY_SRC, run_gate2=False)
        assert verdict["gate1"]["pass"] is False
        assert "leakage" in verdict["gate1"]["reason"]
        assert spawned["yes"] is False, "sandbox was spawned for a leaky candidate"
    finally:
        rcs.gate1_run = orig


# --- Phases 3+4: verdict-feedback to the proposer (closed loop) ------------- #
def test_verdict_feedback_hints_reads_failures():
    """The proposer should be fed its recent gate2-known (avoid these textbook
    families) and gate1-failed (generate stronger-effect relations) claims."""
    import json as _json, os as _os, tempfile as _tf
    from geo_core.scientific_discovery.evolved_analysis.run_claim_search import (
        _verdict_feedback_hints)
    fd, p = _tf.mkstemp(suffix=".jsonl"); _os.close(fd)
    rows = [
        {"outcome": "gate2-known", "claim": "SiO2-MgO Harker trend"},
        {"outcome": "gate1-failed", "claim": "weak relation A"},
        {"outcome": "both-pass", "claim": "a genuine novel find"},
        {"outcome": "gate2-known", "claim": "Fenner Fe-enrichment"},
        {"outcome": "gate1-failed", "claim": "weak relation B"},
    ]
    with open(p, "w") as f:
        for r in rows:
            f.write(_json.dumps(r) + "\n")
    try:
        hints = _verdict_feedback_hints(path=p, n_known=5, n_failed=5)
        text = "\n".join(hints)
        assert any(("already-known" in h.lower() or "textbook" in h.lower()) for h in hints)
        assert "Harker" in text and "Fenner" in text   # gate2-known claims surfaced
        assert "weak relation" in text                  # gate1-failed claims surfaced
        assert "genuine novel find" not in text         # both-pass NOT fed back
    finally:
        _os.unlink(p)


# --- sign-consistency guard (claim direction vs effect sign) ---------------- #
def test_claim_stated_direction():
    from geo_core.scientific_discovery.evolved_analysis.claim_task import (
        _claim_stated_direction as d)
    assert d("A is positively correlated with B") == "positive"
    assert d("A is negatively correlated with B") == "negative"
    assert d("a robust negative partial correlation between A and B") == "negative"
    # Broadened (2026-07-19): bare direction adjectives are now recognized so the
    # proposer cannot evade the sign-consistency guard with "significantly negative".
    assert d("A positively correlates with B") == "positive"
    assert d("the residual covariation ... is significantly negative") == "negative"
    assert d("the covariance is significantly NEGATIVE.") == "negative"
    assert d("a robust positive residual after removing MgO") == "positive"
    assert d("A and B show a relationship") is None             # genuinely unstated


def test_guard_rejects_direction_misstatement():
    """Regression: a claim whose stated sign contradicts its computed effect is
    rejected (the surprise-objective evasion that let 'significantly negative'
    claims with positive data into the store)."""
    from geo_core.scientific_discovery.evolved_analysis.claim_task import (
        _direction_consistent as g)
    # claim says negative, effect is positive -> REJECT
    ok, reason = g("residual Nd-Ce covariation is significantly negative", 0.939)
    assert ok is False and "sign-mismatch" in reason
    # honest in both directions -> pass
    assert g("X is negatively correlated with Y", -0.4)[0] is True
    assert g("X is positively correlated with Y", 0.4)[0] is True


def test_gate1_pvalue_consistent():
    """Regression: Gate 1 independently verifies a candidate's self-reported
    p-value against its reported |r|. Recycled/hardcoded p (the same p for
    different correlations) is rejected; legitimate strong-correlation underflow
    (p=0.0) is NOT."""
    from geo_core.scientific_discovery.evolved_analysis.claim_task import (
        gate1_pvalue_consistent as c)
    # legit: strong correlation, p=0.0 is genuine underflow -> PASS
    assert c(0.94, 0.0, 1000)[0] is True
    # legit: p consistent with r -> PASS
    assert c(0.555, 5.976e-82, 1000)[0] is True
    # FAKE: r=-0.426 cannot yield p=5.98e-82 (that's the r=+0.555 p) -> REJECT
    ok, reason = c(-0.426, 5.976e-82, 1000)
    assert ok is False and "pvalue-implausible" in reason
    # FAKE: weak correlation claiming p=0.0 -> REJECT
    assert c(0.30, 0.0, 1000)[0] is False
    # conservative: missing/uncomputable -> PASS (never block on check failure)
    assert c(None, 0.01, 1000)[0] is True
    assert c(0.5, 0.01, None)[0] is True


def test_direction_consistent():
    from geo_core.scientific_discovery.evolved_analysis.claim_task import (
        _direction_consistent as c)
    assert c("A positively correlated with B", 0.5)[0] is True
    assert c("A negatively correlated with B", -0.5)[0] is True
    assert c("A positively correlated with B", -0.5)[0] is False   # MISMATCH
    assert c("A negatively correlated with B", 0.5)[0] is False    # MISMATCH
    assert c("A correlates with B", 0.5)[0] is True                # unstated -> ok
    assert c("A correlates with B", -0.5)[0] is True


def test_two_gate_rejects_sign_mismatched_claim():
    """A candidate whose CLAIM asserts positive but whose computed effect is
    negative must FAIL Gate 1 (sign-consistency guard), not pass through."""
    from geo_core.scientific_discovery.evolved_analysis import run_claim_search as rcs
    # run_claim references df_eval (passes the leakage guard) but returns a
    # NEGATIVE significant effect while the CLAIM asserts POSITIVE.
    src = ('CLAIM = "A is positively correlated with B"\n\n\n'
           'def run_claim(df_train, df_eval):\n'
           '    _ = df_eval\n'
           '    return {"effect": -0.55, "pvalue": 1e-12}\n')
    orig = rcs.gate1_run
    rcs.gate1_run = lambda s, seed=42, timeout=90.0: {"effect": -0.55, "pvalue": 1e-12}
    try:
        v = rcs.two_gate_eval(src, run_gate2=False)
        assert v["gate1"]["pass"] is False
        assert "mismatch" in v["gate1"]["reason"].lower()
    finally:
        rcs.gate1_run = orig


def test_verdict_feedback_detects_column_name_failures():
    """When recent candidates fail with KeyError on bare element names, the
    feedback must tell the proposer the EXACT column names (the _ppm suffix)."""
    import json as _json, os as _os, tempfile as _tf
    from geo_core.scientific_discovery.evolved_analysis.run_claim_search import (
        _verdict_feedback_hints)
    fd, p = _tf.mkstemp(suffix=".jsonl"); _os.close(fd)
    rows = [
        {"outcome": "gate1-failed", "claim": "X vs nb",
         "gate1": {"reason": "gate1-failed: no valid metric (KeyError: ['nb'])",
                   "metrics": {"error": "KeyError: ['nb']", "effect": 0.0}}},
        {"outcome": "gate1-failed", "claim": "Y vs nd",
         "gate1": {"reason": "gate1-failed: no valid metric (KeyError: ['nd'])",
                   "metrics": {"error": "KeyError: ['nd']", "effect": 0.0}}},
    ]
    with open(p, "w") as f:
        for r in rows:
            f.write(_json.dumps(r) + "\n")
    try:
        hints = _verdict_feedback_hints(path=p)
        text = "\n".join(hints)
        assert "_ppm" in text, f"feedback should name the _ppm columns: {text[:200]}"
    finally:
        _os.unlink(p)


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
