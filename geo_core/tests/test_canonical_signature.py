"""Tests for the Tier-1 canonical-signature pre-filter (discovery pipeline).

Covers: phrasing-invariant signatures, the learned known-registry, the
two_gate_eval pre-filter short-circuit (sandbox skipped for known signatures),
the env disable switch, the new 'canonical-known' outcome bucket, and the
phrasing-invariant novelty cache key.

This is the fix for the production phrasing-escape where the SAME Ce-Nb
residual relation was gate2=known under one wording and gate2=novel (and
stored as a "discovery") under another.

Run: python3 geo_core/tests/test_canonical_signature.py   (pytest-discoverable)
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from geo_core.scientific_discovery.evolved_analysis import (  # noqa: E402
    canonical_signature as cs, run_claim_search as rcs, verdict_log)

# Two phrasings of the SAME relation (Ce-Nb residual after MgO); one was judged
# gate2=known, the other gate2=novel in production.
CE_NB_A = ("In global igneous rocks, the residual enrichment of Cerium (Ce) relative "
           "to the dominant fractionation trend (regressing out MgO) exhibits a strong "
           "positive correlation with the residual enrichment of Niobium (Nb).")
CE_NB_B = ("In global igneous rocks, after correcting for magmatic fractionation "
           "(regressing out MgO), residual Ce and residual Nb are positively correlated.")
ND_NB = ("In global igneous rocks, after regressing out MgO, residual Neodymium (Nd) "
         "and Niobium (Nb) are positively correlated.")

# Compliant (uses df_eval, so passes the §7.3 leakage guard) candidate carrying
# a Ce-Nb claim.
CE_NB_SRC = '''CLAIM = "In global igneous rocks, after regressing out MgO, residual Ce and residual Nb are positively correlated."
def run_claim(df_train, df_eval):
    import numpy as np
    x = df_eval["ce_ppm"].to_numpy(float)
    return {"effect": 0.5, "pvalue": 1e-9, "effect_type": "x", "summary": "s"}
'''


# --- signature --------------------------------------------------------------- #
def test_signature_phrasing_invariant():
    assert cs.signature(CE_NB_A) is not None
    assert cs.signature(CE_NB_A) == cs.signature(CE_NB_B), \
        "re-phrasings of the same relation must share a signature"


def test_signature_distinct_relations():
    assert cs.signature(CE_NB_A) != cs.signature(ND_NB), \
        "different element pairs must have different signatures"


def test_signature_unparseable_returns_none():
    assert cs.signature("the meaning of life is forty-two") is None


# --- learned known-signature registry ---------------------------------------- #
def test_registry_roundtrip(monkeypatch, tmp_path):
    reg = tmp_path / "known.json"
    monkeypatch.setattr(cs, "KNOWN_REGISTRY_PATH", reg)
    assert cs.is_known(CE_NB_A) is False
    assert cs.register_known(CE_NB_A) is True
    assert cs.is_known(CE_NB_A) is True
    assert cs.register_known(CE_NB_A) is False      # idempotent
    assert cs.is_known(CE_NB_B) is True             # phrasing B is also known now
    assert cs.is_known(ND_NB) is False              # distinct relation not blocked


# --- phrasing-invariant novelty cache key ------------------------------------ #
def test_cache_key_phrasing_invariant():
    from geo_core.scientific_discovery.evolved_analysis.novelty_gate import _cache_key
    kA, kB = _cache_key(CE_NB_A), _cache_key(CE_NB_B)
    assert kA == kB, "novelty cache key must be phrasing-invariant"
    assert kA.startswith("canon:")
    assert kA != _cache_key(ND_NB)


def test_cache_key_text_fallback():
    from geo_core.scientific_discovery.evolved_analysis.novelty_gate import _cache_key
    assert _cache_key("the meaning of life is forty-two").startswith("text:"), \
        "unparseable claim must fall back to a text key"


# --- two_gate_eval pre-filter short-circuit ---------------------------------- #
def _run_with_gate1_spy(src, is_known_value):
    """Run two_gate_eval with gate1_run spied + canonical.is_known forced."""
    spawned = {"yes": False}

    def spy(*a, **k):
        spawned["yes"] = True
        return {"effect": 0.5, "pvalue": 1e-9, "effect_type": "x", "summary": "s"}

    orig_gate1 = rcs.gate1_run
    orig_isknown = rcs.canonical.is_known
    rcs.gate1_run = spy
    rcs.canonical.is_known = lambda claim: is_known_value
    try:
        verdict = rcs.two_gate_eval(src, run_gate2=False)
    finally:
        rcs.gate1_run = orig_gate1
        rcs.canonical.is_known = orig_isknown
    return verdict, spawned["yes"]


def test_prefilter_skips_gate1_for_known_signature():
    verdict, spawned = _run_with_gate1_spy(CE_NB_SRC, is_known_value=True)
    assert spawned is False, "sandbox must NOT run for a known-signature claim"
    assert verdict["gate1"]["pass"] is None
    assert "canonical" in verdict["gate1"]["reason"]
    assert verdict_log.outcome(verdict) == "canonical-known"


def test_prefilter_runs_gate1_when_unknown():
    verdict, spawned = _run_with_gate1_spy(CE_NB_SRC, is_known_value=False)
    assert spawned is True, "sandbox MUST run for an unknown-signature claim"
    assert verdict_log.outcome(verdict) != "canonical-known"


def test_prefilter_disabled_via_env(monkeypatch):
    monkeypatch.setenv("GEODISC_CANONICAL_PREFILTER", "0")
    verdict, spawned = _run_with_gate1_spy(CE_NB_SRC, is_known_value=True)
    assert spawned is True, "with the pre-filter disabled the sandbox runs even for known signatures"
    assert verdict_log.outcome(verdict) != "canonical-known"


if __name__ == "__main__":
    # Self-run: execute every test_* function.
    import inspect
    failed = 0
    class _MP:  # tiny monkeypatch stand-in for self-run
        def setattr(self, *a, **k): setattr(*a)
        def setenv(self, k, v): import os; os.environ[k] = v
        def __getattr__(self, n): return lambda *a, **k: None
    for name, fn in sorted(inspect.getmembers(sys.modules[__name__], inspect.isfunction)):
        if not name.startswith("test_"):
            continue
        try:
            sig = inspect.signature(fn)
            if sig.parameters:
                fn(_MP(), tmp_path=Path("/tmp/geodisc_canon_test"))
            else:
                fn()
            print(f"  PASS  {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{'FAILURES' if failed else 'ALL PASS'}: {failed}")
    sys.exit(1 if failed else 0)
