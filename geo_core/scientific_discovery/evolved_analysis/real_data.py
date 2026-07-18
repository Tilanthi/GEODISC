"""real_data.py — REAL geochemistry data loader for the two-gate engine.

Provides ``load_split(seed) -> {"train": df, "eval": df}`` for the sandboxed
Gate-1 workers (``claim_eval_worker``, ``eval_worker``). The DataFrames carry
the geochemistry columns the engine contracts on:

    sio2, tio2, al2o3, feo_tot, mgo, cao, mno, na2o, k2o, p2o5
        — whole-rock major oxides (wt %) from the real Gard et al. (2019)
          global whole-rock compilation

GEODISC's prime directive is **NO FICTIONAL / SYNTHETIC DATA**. This loader
therefore reads REAL data only — from a CSV/Parquet at ``$GEODISC_REAL_DATA``
(or the default path below), populated by ``scripts/fetch_geochem_data.py`` from
the real Gard et al. (2019) global whole-rock compilation (Zenodo 3359791). If
no real-data file is present it
raises a clear error rather than synthesising rows, so the engine fails loudly
instead of grading fiction. (The two-gate EVALUATE is meaningless on made-up
data — that is the whole point of Gate 1.)

To enable Gate 1: run ``python scripts/fetch_geochem_data.py`` (fetches + cleans
the real compilation to the default path), or point ``GEODISC_REAL_DATA`` at your
own real geochemistry table with the columns above.
"""
from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DATA_PATH = Path.home() / ".geodisc_persistent" / "geochem_real.csv"

# Real whole-rock columns the engine contracts on: major oxides (wt %) PLUS key
# trace elements (ppm). The seed uses sio2/mgo (oxides); the proposer should
# explore the TRACE elements too -- they have thinner textbook coverage than the
# saturated major oxides, so that is where genuine novelty lives (sec 7.6).
_REQUIRED_COLUMNS = (
    # major oxides (wt %)
    "sio2", "tio2", "al2o3", "feo_tot", "mgo", "cao", "mno", "na2o", "k2o", "p2o5",
    # trace elements (ppm) -- transition metals, LILE, HFSE, REE
    "v_ppm", "cr_ppm", "co_ppm", "ni_ppm", "cu_ppm", "zn_ppm", "rb_ppm",
    "sr_ppm", "y_ppm", "zr_ppm", "nb_ppm", "ba_ppm", "la_ppm", "ce_ppm", "nd_ppm",
)


def _data_path() -> Path:
    return Path(os.environ.get("GEODISC_REAL_DATA", DEFAULT_DATA_PATH))


try:
    from . import data_profile  # Tier 3: data-driven column contract
except ImportError:
    import data_profile          # standalone


def required_columns() -> tuple:
    """Required columns for the ACTIVE data profile (default gard = _REQUIRED_COLUMNS)."""
    return data_profile.required_cols()


def load_split(seed: int = 42) -> dict:
    """Load REAL geochemistry data and return deterministic train/eval splits.

    Returns ``{"train": DataFrame, "eval": DataFrame}``. Raises RuntimeError
    if no real-data file is available or required columns are missing — it
    NEVER fabricates data. Required columns are those of the active data profile
    (``$GEODISC_DATA_PROFILE``, default ``gard`` -> ``_REQUIRED_COLUMNS``).
    """
    path = _data_path()
    if not path.is_file():
        raise RuntimeError(
            f"real_data: no real geochemistry data found at {path}. GEODISC does "
            f"not synthesise data (prime directive: no fictional/synthetic data). "
            f"Populate this file from a real database (e.g. EarthChem / GEOROC / "
            f"PBDB) as CSV with columns {list(required_columns())} (one sample per "
            f"row), or set GEODISC_REAL_DATA to point at it."
        )
    import pandas as pd
    if path.suffix in (".parquet", ".pq"):
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)
    required = required_columns()
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(
            f"real_data: {path} is missing required columns {missing} for the "
            f"'{data_profile.active_name()}' profile; expected {list(required)}."
        )
    if len(df) < 10:
        raise RuntimeError(
            f"real_data: {path} has only {len(df)} rows; need a real sample with "
            f"enough records for a held-out split."
        )
    # Deterministic shuffle + 80/20 split, reproducible from `seed`.
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    n_eval = max(1, int(0.2 * len(df)))
    return {
        "train": df.iloc[n_eval:].reset_index(drop=True),
        "eval": df.iloc[:n_eval].reset_index(drop=True),
    }


if __name__ == "__main__":
    # Self-check: report whether real data is wired (does NOT create any).
    p = _data_path()
    if p.is_file():
        print(f"real data present at {p}")
    else:
        print(f"no real data at {p} — populate it from EarthChem/GEOROC/PBDB "
              f"(columns {list(_REQUIRED_COLUMNS)}) to enable Gate 1.")
