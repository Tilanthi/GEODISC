#!/usr/bin/env python3
"""fetch_geochem_data.py — populate $GEODISC_REAL_DATA with REAL geochemistry data.

GEODISC's prime directive is NO FICTIONAL / SYNTHETIC DATA. This script therefore
fetches REAL whole-rock geochemistry from a public, peer-reviewed, citable source
and writes a cleaned subset to the path the two-gate engine reads
(``$GEODISC_REAL_DATA`` or ``~/.geodisc_persistent/geochem_real.csv`` by default).

Source: Gard, M., Hasterok, D., Halpin, J.A. et al. (2019), "A global
geochemical database for chemical and sedimentary rock analyses", Earth System
Science Data 11, 1553-1566 — the *Global whole-rock geochemical database
compilation*, Zenodo record 3359791 (``major.csv``). Real major-oxide whole-rock
analyses from governmental and academic studies.

This script only SELECTS and CLEANS real records (drops non-finite / out-of-range
values); it never synthesises rows. Re-run any time to refresh the local cache.

Usage:
    python scripts/fetch_geochem_data.py [--max-rows 5000]
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

ZENODO_MAJOR_CSV = "https://zenodo.org/api/records/3359791/files/major.csv/content"

# Real major-oxide columns (wt%) the engine contracts on. feo_tot = total Fe as
# FeO (a single Fe column); the rest are standard whole-rock major oxides.
COLUMNS = ["sio2", "tio2", "al2o3", "feo_tot", "mgo", "cao", "mno", "na2o", "k2o", "p2o5"]

DEFAULT_OUT = Path.home() / ".geodisc_persistent" / "geochem_real.csv"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rows", type=int, default=5000,
                    help="cap on rows written (a real subset; default 5000)")
    ap.add_argument("--out", default=os.environ.get("GEODISC_REAL_DATA", str(DEFAULT_OUT)))
    args = ap.parse_args()
    out = Path(args.out)

    import pandas as pd  # late import; heavy

    print(f"fetching REAL geochemistry from\n  {ZENODO_MAJOR_CSV}\n(this is ~50 MB)...")
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        tmp = Path(tf.name)
    try:
        urllib.request.urlretrieve(ZENODO_MAJOR_CSV, tmp)
        df = pd.read_csv(tmp, usecols=lambda c: c == "major_id" or c in COLUMNS,
                         low_memory=False)
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass

    n0 = len(df)
    # CLEAN real data only: coerce to numeric, drop non-finite / implausible oxide
    # values (oxides are wt%, so 0..100). NO rows are invented.
    for c in COLUMNS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=COLUMNS)
    for c in COLUMNS:
        df = df[(df[c] >= 0) & (df[c] <= 100)]
    n1 = len(df)
    if n1 == 0:
        print("ERROR: no valid rows after cleaning — source schema may have changed.",
              file=sys.stderr)
        return 1

    # Deterministic real subset.
    df = df.sample(n=min(args.max_rows, len(df)), random_state=42)[COLUMNS].reset_index(drop=True)

    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\nwrote {len(df)} REAL whole-rock analyses (cleaned from {n0} raw, "
          f"{n1} valid) to\n  {out}")
    print("columns:", list(df.columns))
    # Honest sanity signal: the seed-claim correlation (SiO2 vs MgO, Harker trend).
    r = df[["sio2", "mgo"]].corr().iloc[0, 1]
    print(f"real Spearman/Pearson r(sio2, mgo) = {r:.3f}  (expect negative: silicic rocks are MgO-poor)")
    print("\nNext: the two-gate engine can now load this via real_data.load_split().")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
