"""Tests for Tier 2: surprise/anomaly objective + mechanistic-contrast novelty tier.

Covers: the expectations-table lookup, the surprise score (contradiction vs
confirmation vs neutral), the surprise feedback hint, the novelty_tier
classifier, and the augmented Gate-2 judge parsing 'requires_unstated_process'
via a mocked LLM gateway.

Run: python3 geo_core/tests/test_surprise_and_contrast.py   (pytest-discoverable)
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from geo_core.scientific_discovery.evolved_analysis import (  # noqa: E402
    surprise as sur, novelty_gate as ng)

CE_NB_POS = ("In global igneous rocks, after regressing out MgO, residual Ce and "
             "residual Nb are positively correlated.")
CE_NB_NEG = ("In global igneous rocks, after regressing out MgO, residual Ce and "
             "residual Nb are NEGATIVELY correlated.")
MGO_SIO2_NEG = "In basalts, SiO2 is negatively correlated with MgO."
UNSTAGED = "residual vanadium and chromium positively correlate after regressing out MgO."


# --- surprise score ---------------------------------------------------------- #
def test_expected_sign_lookup():
    assert sur.expected_sign(CE_NB_POS) == ("+", "LREE-HFSE incompatible coherence")
    assert sur.expected_sign(UNSTAGED) is None  # V-Cr not in the table


def test_surprise_confirmation_is_zero():
    assert sur.surprise_score(CE_NB_POS, "+") == 0.0   # data confirms textbook +
    assert sur.surprise_score(MGO_SIO2_NEG, "-") == 0.0  # Harker confirmation


def test_surprise_contradiction_is_one():
    assert sur.surprise_score(CE_NB_NEG, "-") == 1.0   # anomaly: Ce-Nb negative


def test_surprise_neutral_for_unstaged_or_unknown_sign():
    assert sur.surprise_score(UNSTAGED, "+") == 0.5    # unstudied pair
    assert sur.surprise_score(CE_NB_POS, None) == 0.5  # sign unknown


def test_sign_of_numeric():
    assert sur.sign_of(0.81) == "+"
    assert sur.sign_of(-0.4) == "-"
    assert sur.sign_of("not a number") is None


def test_surprise_hint_fires_on_confirmations():
    hint = sur.surprise_hint([(CE_NB_POS, 0.0), (CE_NB_POS, 0.0)])
    assert hint is not None and "OPPOSITE sign" in hint


def test_surprise_hint_quiet_without_enough_confirmations():
    assert sur.surprise_hint([(CE_NB_POS, 0.0)]) is None
    assert sur.surprise_hint([(CE_NB_NEG, 1.0), (CE_NB_NEG, 1.0)]) is None  # anomalies, not confirmations


# --- novelty tier ------------------------------------------------------------ #
def test_novelty_tier_classification():
    assert ng.novelty_tier(ng.NoveltyResult(False, "known", "c")) == "known"
    assert ng.novelty_tier(ng.NoveltyResult(True, "novel", "c",
                                            mechanistic_contrast=True)) == "strong-novel"
    assert ng.novelty_tier(ng.NoveltyResult(True, "novel", "c",
                                            mechanistic_contrast=False)) == "weak-novel"
    assert ng.novelty_tier(ng.NoveltyResult(True, "novel", "c")) == "weak-novel"  # None
    assert ng.novelty_tier(ng.NoveltyResult(False, "retrieval-failed", "c")) == "unverified"


# --- augmented judge (mocked gateway) ---------------------------------------- #
class _FakeGW:
    def __init__(self, json_text):
        self.json = json_text
        self.asked_for_mc = False

    def complete(self, system, messages, max_tokens=None):
        if "requires_unstated_process" in system:
            self.asked_for_mc = True
        return self.json, {"input_tokens": 0, "output_tokens": 0}


def _paper():
    return ng.Paper("openalex", "A geochem paper", "abstract text", "id1", "2020")


def test_judge_parses_mechanistic_contrast(monkeypatch):
    gw = _FakeGW('{"known": false, "reason": "novel", "by_abstract": null, '
                 '"reasoning": "unstated", "requires_unstated_process": true}')
    monkeypatch.setattr(ng, "_get_gateway", lambda: gw)
    monkeypatch.delenv("GEODISC_MECHANISTIC_CONTRAST", raising=False)
    known, ent, label, reasoning, mc = ng._judge_known(CE_NB_POS, [_paper()])
    assert known is False
    assert mc is True
    assert gw.asked_for_mc is True  # the prompt actually asked the new question


def test_judge_mechanistic_contrast_disabled(monkeypatch):
    gw = _FakeGW('{"known": false, "reason": "novel", "reasoning": "x", '
                 '"requires_unstated_process": true}')
    monkeypatch.setattr(ng, "_get_gateway", lambda: gw)
    monkeypatch.setenv("GEODISC_MECHANISTIC_CONTRAST", "0")
    known, ent, label, reasoning, mc = ng._judge_known(CE_NB_POS, [_paper()])
    assert mc is None                       # flag off -> not asked / not parsed
    assert gw.asked_for_mc is False


def test_judge_malformed_mc_defaults_null(monkeypatch):
    gw = _FakeGW('{"known": false, "reason": "novel", "reasoning": "x"}')  # no mc field
    monkeypatch.setattr(ng, "_get_gateway", lambda: gw)
    monkeypatch.delenv("GEODISC_MECHANISTIC_CONTRAST", raising=False)
    known, ent, label, reasoning, mc = ng._judge_known(CE_NB_POS, [_paper()])
    assert mc is None  # missing field -> defensive null


# --- end-to-end annotation in two_gate_eval ---------------------------------- #
def test_two_gate_eval_annotates_surprise(monkeypatch):
    """A gate1-passing Ce-Nb-positive candidate is annotated surprise=0.0."""
    from geo_core.scientific_discovery.evolved_analysis import run_claim_search as rcs
    src = ('CLAIM = "In global igneous rocks, after regressing out MgO, residual Ce '
           'and residual Nb are positively correlated."\n'
           'def run_claim(df_train, df_eval):\n'
           '    x = df_eval["ce_ppm"].to_numpy(float)\n'
           '    return {"effect": 0.8, "pvalue": 1e-9, "effect_type": "x", "summary": "s"}\n')
    monkeypatch.setattr(rcs, "gate1_run",
                        lambda src, seed=42, timeout=90.0:
                        {"effect": 0.8, "pvalue": 1e-9, "effect_type": "x", "summary": "s"})
    monkeypatch.setattr(rcs, "_canonical_prefilter_enabled", lambda: False)
    monkeypatch.setattr(rcs.question_prescreen, "enabled", lambda: False)
    v = rcs.two_gate_eval(src, run_gate2=False)
    assert v["gate1"]["pass"] is True
    assert v.get("surprise") == 0.0  # Ce-Nb positive is a textbook confirmation


if __name__ == "__main__":
    import inspect
    failed = 0
    for name, fn in sorted(inspect.getmembers(sys.modules[__name__], inspect.isfunction)):
        if not name.startswith("test_"):
            continue
        class _MP:
            def __init__(self): import os; self._e = os.environ
            def setattr(self, *a, **k): setattr(*a)
            def setenv(self, k, v): import os; os.environ[k] = v
            def delenv(self, k, raising=True): import os; os.environ.pop(k, None)
            def __getattr__(self, n): return lambda *a, **k: None
        try:
            sig = inspect.signature(fn)
            fn(_MP()) if sig.parameters else fn()
            print(f"  PASS  {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{'FAILURES' if failed else 'ALL PASS'}: {failed}")
    sys.exit(1 if failed else 0)
