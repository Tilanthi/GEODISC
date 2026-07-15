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
ISO_CSV = f"{ZEN}/isotope.csv/content"
AGE_CSV = f"{ZEN}/age.csv/content"

# Major oxides (wt%) -- the textbook-saturated niche.
OXIDES = ["sio2", "tio2", "al2o3", "feo_tot", "mgo", "cao", "mno", "na2o", "k2o", "p2o5"]
# Trace elements (ppm) -- thinner textbook coverage.
TRACES = ["v_ppm", "cr_ppm", "co_ppm", "ni_ppm", "cu_ppm", "zn_ppm", "rb_ppm",
          "sr_ppm", "y_ppm", "zr_ppm", "nb_ppm", "ba_ppm", "la_ppm", "ce_ppm", "nd_ppm"]
# Radiogenic isotopes -- the THINNEST textbook-coverage niche (source/process
# tracers: Sr-Nd-Pb-Hf). Their cross-relations with elements + age are far less
# canonical than oxide trends -> the most productive novelty space.
ISOTOPES = ["sr87_sr86", "nd143_nd144", "epsilon_nd", "epsilon_sr",
            "pb206_pb204", "pb207_pb204", "pb208_pb204", "hf176_hf177", "epsilon_hf"]
AGE = "age"   # central age estimate (Ga) -> enables secular / temporal relations
ALL_COLS = OXIDES + TRACES + ISOTOPES + [AGE]

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

    tmps = []
    try:
        print("fetching REAL geochemistry (major+trace+isotope+age)...")
        major_tmp = Path(tempfile.mkstemp(suffix=".csv")[1]); tmps.append(major_tmp)
        trace_tmp = Path(tempfile.mkstemp(suffix=".csv")[1]); tmps.append(trace_tmp)
        iso_tmp = Path(tempfile.mkstemp(suffix=".csv")[1]); tmps.append(iso_tmp)
        age_tmp = Path(tempfile.mkstemp(suffix=".csv")[1]); tmps.append(age_tmp)
        _fetch(MAJOR_CSV, major_tmp)
        _fetch(TRACE_CSV, trace_tmp)
        _fetch(ISO_CSV, iso_tmp)
        _fetch(AGE_CSV, age_tmp)
        major = pd.read_csv(major_tmp, usecols=lambda c: c == "major_id" or c in OXIDES,
                            low_memory=False).rename(columns={"major_id": "sample_id"})
        trace = pd.read_csv(trace_tmp, usecols=lambda c: c == "trace_id" or c in TRACES,
                            low_memory=False).rename(columns={"trace_id": "sample_id"})
        iso = pd.read_csv(iso_tmp, usecols=lambda c: c == "iso_id" or c in ISOTOPES,
                          low_memory=False).rename(columns={"iso_id": "sample_id"})
        age = pd.read_csv(age_tmp, usecols=lambda c: c == "age_id" or c == "age",
                          low_memory=False).rename(columns={"age_id": "sample_id"})
    finally:
        for t in tmps:
            try:
                t.unlink()
            except OSError:
                pass

    # Inner-join major+trace (the DENSE base). LEFT-join isotope+age -- they are
    # sparse (isotopes measured on only ~13% of samples, age on ~2%), so
    # requiring them would collapse the dataset to ~0. They are kept as OPTIONAL
    # columns (NaN where absent) so the proposer can search the thin-textbook
    # isotope niche on the subset that has it.
    df = (major.merge(trace, on="sample_id", how="inner")
              .merge(iso, on="sample_id", how="left")
              .merge(age, on="sample_id", how="left"))

    # CLEAN real data only (NO rows invented). oxides+trace are REQUIRED (finite +
    # plausible -> drop bad rows). isotopes+age are coerced; out-of-range values
    # are masked to NaN (the row is kept for its oxide+trace data).
    for c in ALL_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=OXIDES + TRACES)
    for c in OXIDES:
        df = df[(df[c] >= 0) & (df[c] <= 100)]
    for c in TRACES:
        df = df[(df[c] >= 0) & (df[c] < 50000)]        # ppm
    df.loc[~df[AGE].between(0, 4.6), AGE] = pd.NA      # Ga
    for c in ("sr87_sr86", "nd143_nd144", "hf176_hf177"):
        df.loc[~df[c].between(0, 2), c] = pd.NA
    for c in ("epsilon_nd", "epsilon_sr", "epsilon_hf"):
        df.loc[~df[c].between(-50, 50), c] = pd.NA
    for c in ("pb206_pb204", "pb207_pb204", "pb208_pb204"):
        df.loc[~df[c].between(0, 60), c] = pd.NA
    n_valid = len(df)
    n_with_iso = int(df[ISOTOPES].notna().any(axis=1).sum())
    if n_valid == 0:
        print("ERROR: no valid rows after merge+clean.", file=sys.stderr)
        return 1

    df = df.sample(n=min(args.max_rows, n_valid), random_state=42)[ALL_COLS].reset_index(drop=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\nwrote {len(df)} REAL samples to\n  {out}")
    print(f"  base(oxides+trace)={n_valid}, of which {n_with_iso} have isotope data; "
          f"columns={len(ALL_COLS)} (oxides+trace required; isotopes+age optional)")
    print(f"  oxides:{len(OXIDES)} traces:{len(TRACES)} isotopes:{len(ISOTOPES)} +age")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


