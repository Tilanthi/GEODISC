"""real_data.py — REAL geochemistry data loader for the two-gate engine.

Provides ``load_split(seed) -> {"train": df, "eval": df}`` for the sandboxed
Gate-1 workers (``claim_eval_worker``, ``eval_worker``). The DataFrames carry
the geochemistry columns the engine contracts on:

    toc    — total organic carbon (wt %)
    d13c   — organic-matter δ¹³C (per mil VPDB)
    Fe_Al  — Fe/Al ratio (redox / detrital proxy)
    S_TOC  — S/TOC ratio
    depth  — burial depth (km)
    Ro     — vitrinite reflectance (thermal maturity)
    HI     — hydrogen index

GEODISC's prime directive is **NO FICTIONAL / SYNTHETIC DATA**. This loader
therefore reads REAL data only — from a CSV/Parquet at ``$GEODISC_REAL_DATA``
(or the default path below), which the user populates from a real geochemical
database (e.g. EarthChem, GEOROC, PBDB). If no real-data file is present it
raises a clear error rather than synthesising rows, so the engine fails loudly
instead of grading fiction. (The two-gate EVALUATE is meaningless on made-up
data — that is the whole point of Gate 1.)

To enable Gate 1: export a real geochemistry table (columns above, one sample
per row) to the path below — or set ``GEODISC_REAL_DATA`` — then run the search.
"""
from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DATA_PATH = Path.home() / ".geodisc_persistent" / "geochem_real.csv"

# Columns the geochem engine (claim_task seed + Phase-1 estimate_toc) reads.
# At minimum the headline target `toc` and one feature must be present; the
# others let the proposer explore richer relationships.
_REQUIRED_COLUMNS = ("toc", "d13c", "Fe_Al", "S_TOC", "depth", "Ro", "HI")


def _data_path() -> Path:
    return Path(os.environ.get("GEODISC_REAL_DATA", DEFAULT_DATA_PATH))


def load_split(seed: int = 42) -> dict:
    """Load REAL geochemistry data and return deterministic train/eval splits.

    Returns ``{"train": DataFrame, "eval": DataFrame}``. Raises RuntimeError
    if no real-data file is available or required columns are missing — it
    NEVER fabricates data.
    """
    path = _data_path()
    if not path.is_file():
        raise RuntimeError(
            f"real_data: no real geochemistry data found at {path}. GEODISC does "
            f"not synthesise data (prime directive: no fictional/synthetic data). "
            f"Populate this file from a real database (e.g. EarthChem / GEOROC / "
            f"PBDB) as CSV with columns {list(_REQUIRED_COLUMNS)} (one sample per "
            f"row), or set GEODISC_REAL_DATA to point at it."
        )
    import pandas as pd
    if path.suffix in (".parquet", ".pq"):
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)
    missing = [c for c in _REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise RuntimeError(
            f"real_data: {path} is missing required columns {missing}; expected "
            f"at least the geochemistry columns {list(_REQUIRED_COLUMNS)}."
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
