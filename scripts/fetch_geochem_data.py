#!/usr/bin/env python3
"""fetch_geochem_data.py — populate $GEODISC_REAL_DATA with REAL geochemistry data.

GEODISC's prime directive is NO FICTIONAL / SYNTHETIC DATA. This script fetches
REAL whole-rock geochemistry from a public, peer-reviewed, citable source and
writes a cleaned subset to the path the two-gate engine reads
(``$GEODISC_REAL_DATA`` or ``~/.geodisc_persistent/geochem_real.csv``).

Source: Gard, M., Hasterok, D., Halpin, J.A. et al. (2019), "A global
geochemical database for chemical and sedimentary rock analyses", Earth System
Science Data 11, 1553-1566 — the *Global whole-rock geochemical database
compilation*, Zenodo record 3359791. Real major-oxide AND trace-element whole-
rock analyses from governmental and academic studies.

NICHE-WIDENING (2026-07-15): major oxides alone are textbook-saturated (most
significant oxide relations are already known -> Gate 2 rejects them). Trace
elements (V, Cr, Ni, Rb, Sr, Y, Zr, Nb, Ba, REE, ...) have thinner textbook
coverage, so widening to them gives the search genuine novelty headroom (the
sec-7.6 lesson: mine the productive niche, skip the saturated one). This script
merges major.csv (oxides) + trace.csv (trace elements) on the shared sample id
(an inner join -- only samples with BOTH), then cleans + samples.

This script only SELECTS and CLEANS real records; it never synthesises rows.

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

ZEN = "https://zenodo.org/api/records/3359791/files"
MAJOR_CSV = f"{ZEN}/major.csv/content"
TRACE_CSV = f"{ZEN}/trace.csv/content"

# Major oxides (wt%) -- the textbook-saturated niche.
OXIDES = ["sio2", "tio2", "al2o3", "feo_tot", "mgo", "cao", "mno", "na2o", "k2o", "p2o5"]
# Trace elements (ppm) -- the thinner-textbook-coverage niche (transition metals,
# LILE, HFSE, REE). These are the productive search space for genuine novelty.
TRACES = ["v_ppm", "cr_ppm", "co_ppm", "ni_ppm", "cu_ppm", "zn_ppm", "rb_ppm",
          "sr_ppm", "y_ppm", "zr_ppm", "nb_ppm", "ba_ppm", "la_ppm", "ce_ppm", "nd_ppm"]
ALL_COLS = OXIDES + TRACES

DEFAULT_OUT = Path.home() / ".geodisc_persistent" / "geochem_real.csv"


def _fetch(url: str, tmp: Path) -> None:
    urllib.request.urlretrieve(url, tmp)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rows", type=int, default=5000)
    ap.add_argument("--out", default=os.environ.get("GEODISC_REAL_DATA", str(DEFAULT_OUT)))
    args = ap.parse_args()
    out = Path(args.out)

    import pandas as pd

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        major_tmp, trace_tmp = Path(tf.name), None
    trace_tmp = Path(str(major_tmp) + ".t")

    print("fetching REAL geochemistry (major.csv ~50MB + trace.csv ~118MB)...")
    try:
        _fetch(MAJOR_CSV, major_tmp)
        _fetch(TRACE_CSV, trace_tmp)
        major = pd.read_csv(major_tmp, usecols=lambda c: c in ("major_id",) or c in OXIDES,
                            low_memory=False).rename(columns={"major_id": "sample_id"})
        trace = pd.read_csv(trace_tmp, usecols=lambda c: c in ("trace_id",) or c in TRACES,
                            low_memory=False).rename(columns={"trace_id": "sample_id"})
    finally:
        for t in (major_tmp, trace_tmp):
            try:
                t.unlink()
            except OSError:
                pass

    n_major, n_trace = len(major), len(trace)
    # Inner join on the shared sample id -> samples with BOTH major + trace.
    df = major.merge(trace, on="sample_id", how="inner")
    n_joined = len(df)

    # CLEAN real data only: numeric, finite, plausible ranges. NO rows invented.
    for c in ALL_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=ALL_COLS)
    for c in OXIDES:
        df = df[(df[c] >= 0) & (df[c] <= 100)]
    for c in TRACES:
        df = df[(df[c] >= 0) & (df[c] < 50000)]   # ppm plausible upper bound
    n_valid = len(df)
    if n_valid == 0:
        print("ERROR: no valid rows after the major+trace merge+clean "
              "(join schema may differ).", file=sys.stderr)
        return 1

    df = df.sample(n=min(args.max_rows, n_valid), random_state=42)[ALL_COLS].reset_index(drop=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\nwrote {len(df)} REAL samples (major+trace merged) to\n  {out}")
    print(f"  major={n_major}, trace={n_trace}, joined(both)={n_joined}, valid={n_valid}")
    print("  oxides :", OXIDES)
    print("  traces :", TRACES)
    # sanity: a trace relation (Zr vs Nb -- HFSE pair) should be real + positive
    r = df[["zr_ppm", "nb_ppm"]].corr().iloc[0, 1]
    print(f"  real r(Zr, Nb) = {r:.3f}  (HFSE pair; expect positive)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
