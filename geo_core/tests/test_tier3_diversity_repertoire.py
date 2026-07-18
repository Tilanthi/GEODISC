"""Tests for Tier 3: per-family diversity cap, repertoire inspirations, and the
data-driven column contract (data profiles).

Run: python3 geo_core/tests/test_tier3_diversity_repertoire.py   (pytest-discoverable)
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from geo_core.scientific_discovery.evolved_analysis import (  # noqa: E402
    diversity, inspirations, data_profile, claim_task, real_data)

CE_NB = ("In global igneous rocks, after regressing out MgO, residual Ce and "
         "residual Nb are positively correlated.")


# --- Part 1: diversity ------------------------------------------------------- #
def test_diversity_fires_on_family_dominance():
    t = diversity.FamilyTracker()
    for _ in range(4):
        t.note(CE_NB)
    hint = t.hint()
    assert hint is not None and "DIVERSITY" in hint and "ce-nb" in hint


def test_diversity_silent_when_families_vary():
    t = diversity.FamilyTracker()
    for claim in [
        "residual Ce and Nb correlate after regressing out MgO",
        "residual Rb and Sr correlate after regressing out MgO",
        "SiO2 is negatively correlated with MgO",
    ]:
        t.note(claim)
    assert t.hint() is None


def test_diversity_disabled_via_env(monkeypatch):
    monkeypatch.setenv("GEODISC_DIVERSITY_CAP", "0")
    t = diversity.FamilyTracker()
    for _ in range(5):
        t.note(CE_NB)
    assert t.hint() is None


# --- Part 2: inspirations + repertoire --------------------------------------- #
def test_inspirations_bank_is_diverse_and_parseable():
    assert len(inspirations.BANK) >= 4
    for _name, src in inspirations.BANK:
        assert "def run_claim" in src and "CLAIM" in src
    picks = inspirations.pick(0, k=2)
    assert len(picks) == 2
    # rotation: step 0 vs step 1 differ
    assert inspirations.pick(0, k=1) != inspirations.pick(1, k=1)


def test_task_system_names_all_repertoire_forms():
    ts = claim_task.TASK_SYSTEM
    for marker in ("PARTIAL", "CONDITIONAL", "INTERACTION",
                   "THRESHOLD", "ANOMALY", "PREDICTIVE", "LOG-RATIO"):
        assert marker in ts, f"repertoire form {marker} missing from TASK_SYSTEM"


# --- Part 3: data profiles --------------------------------------------------- #
def test_gard_is_default_and_byte_identical():
    assert data_profile.active_name() == "gard"
    assert data_profile.build_task_system("gard") is claim_task.TASK_SYSTEM
    assert set(data_profile.required_cols()) == set(real_data._REQUIRED_COLUMNS)


def test_proterozoic_profile_contract():
    p = data_profile._PROFILES["proterozoic_redox"]
    assert set(["fe_hr", "fe_t", "fe_py", "age"]).issubset(set(p["required_cols"]))
    ts = data_profile.build_task_system("proterozoic_redox")
    assert "FeHR/FeT" in ts and "FePy/FeHR" in ts and "TOC" in ts.upper() or "toc" in ts


def test_load_split_validates_active_profile(monkeypatch, tmp_path):
    """A synthetic proterozoic CSV validates under the proterozoic profile."""
    import csv as _csv
    csv_path = tmp_path / "prot.csv"
    with csv_path.open("w", newline="") as fh:
        w = _csv.writer(fh)
        w.writerow(["fe_hr", "fe_t", "fe_py", "age", "toc"])
        import random
        rnd = random.Random(1)
        for _ in range(40):
            fe_t = rnd.uniform(2, 8)
            fe_hr = rnd.uniform(0.0, 0.9) * fe_t
            fe_py = rnd.uniform(0.0, 0.95) * fe_hr
            w.writerow([round(fe_hr, 3), round(fe_t, 3), round(fe_py, 3),
                        round(rnd.uniform(0.5, 2.0), 3), round(rnd.uniform(0, 2), 3)])
    monkeypatch.setenv("GEODISC_REAL_DATA", str(csv_path))
    monkeypatch.setenv("GEODISC_DATA_PROFILE", "proterozoic_redox")
    splits = real_data.load_split(seed=42)
    assert set(["train", "eval"]).issubset(splits.keys())
    assert len(splits["train"]) + len(splits["eval"]) == 40
    assert "fe_py" in splits["train"].columns


def test_load_split_rejects_missing_required_cols(monkeypatch, tmp_path):
    """A CSV missing the active profile's required cols raises (no fiction)."""
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("fe_hr,age\n0.5,1.0\n0.4,1.1\n")  # missing fe_t, fe_py
    monkeypatch.setenv("GEODISC_REAL_DATA", str(csv_path))
    monkeypatch.setenv("GEODISC_DATA_PROFILE", "proterozoic_redox")
    try:
        real_data.load_split(seed=42)
        assert False, "expected RuntimeError for missing required columns"
    except RuntimeError as e:
        assert "required columns" in str(e)


if __name__ == "__main__":
    import inspect
    failed = 0
    for name, fn in sorted(inspect.getmembers(sys.modules[__name__], inspect.isfunction)):
        if not name.startswith("test_"):
            continue
        class _MP:
            def setattr(self, *a, **k): setattr(*a)
            def setenv(self, k, v): import os; os.environ[k] = v
            def __getattr__(self, n): return lambda *a, **k: None
        try:
            sig = inspect.signature(fn)
            params = list(sig.parameters)
            args = []
            if params: args.append(_MP())          # monkeypatch
            if len(params) >= 2: args.append(tmp_path := Path("/tmp/geodisc_t3"))
            if len(params) >= 2:
                tmp_path.mkdir(exist_ok=True)
            fn(*args)
            print(f"  PASS  {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{'FAILURES' if failed else 'ALL PASS'}: {failed}")
    sys.exit(1 if failed else 0)
