#!/usr/bin/env python3
"""fetch_pbdb_data.py — fetch paleontological data from the Paleobiology Database
(PBDB) for the discovery pipeline's paleontology / fossil-record / early-Earth
atmosphere focus.

Fetches fossil COLLECTIONS (localities) with age, environment, lithology, and
taxonomic diversity from the PBDB v1.2 API (https://paleobiodb.org/data1.2/).
Each collection becomes a ROW in the output CSV — a real paleontological substrate
the pipeline can mine for life–environment coupling, preservation dynamics, and
diversity patterns through time.

The PBDB API is clean, reliable, and open (no key needed). This fetcher focuses on
the Proterozoic + early Paleozoic (the mission window: 2500–400 Ma) but can fetch
any age range.

Output: a CSV at $GEODISC_REAL_DATA (or default
~/.geodisc_persistent/pbdb_paleo.csv) with columns the pipeline contracts on.
Use with GEODISC_DATA_PROFILE=paleo.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://paleobiodb.org/data1.2"
DEFAULT_OUT = Path.home() / ".geodisc_persistent" / "pbdb_paleo.csv"

# PBDB interval IDs for Proterozoic + early Paleozoic (the mission window).
# interval_id=1 is "Proterozoic"; we also include early Paleozoic eras.
# The PBDB uses numeric interval IDs; we query by age range instead for flexibility.


def _api(endpoint: str, params: dict, timeout: float = 60) -> list:
    """Call a PBDB v1.2 JSON endpoint. Returns the 'records' list."""
    url = f"{API_BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "GEODISC-PBDB-fetcher/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    return data.get("records", data.get("data", []))


def fetch_collections(age_min: float, age_max: float, limit: int = 50000) -> list:
    """Fetch PBDB collections in an age range. Each collection is a fossil locality
    with age, environment, lithology, and occurrence data."""
    all_recs = []
    offset = 0
    page = 5000
    while offset < limit:
        params = {
            "limit": min(page, limit - offset),
            "offset": offset,
            "show": "strat,geo,age,ref",  # stratigraphy + geography + age + ref
            "min_ma": age_min,
            "max_ma": age_max,
        }
        try:
            recs = _api("colls/list.json", params)
        except Exception as e:
            print(f"  PBDB fetch failed at offset {offset}: {e}")
            break
        if not recs:
            break
        all_recs.extend(recs)
        print(f"  fetched {len(recs)} collections (total {len(all_recs)}) at offset {offset}")
        if len(recs) < page:
            break
        offset += page
        time.sleep(1)  # politeness
    return all_recs


def tabulate(records: list) -> list:
    """Convert PBDB collection records to flat rows for the pipeline CSV."""
    rows = []
    for r in records:
        row = {
            "collection_id": str(r.get("oid", "").replace("col:", "")),
            "late_age_ma": _num(r.get("lag")),
            "early_age_ma": _num(r.get("eag")),
            "mid_age_ma": _mid(r.get("lag"), r.get("eag")),
            "n_occurrences": _num(r.get("noc")),
            "n_references": _num(r.get("nref")),
            "paleolatitude": _num(r.get("plg") or r.get("lat")),
            "paleolongitude": _num(r.get("pln") or r.get("lng")),
            "latitude": _num(r.get("lat")),
            "longitude": _num(r.get("lng")),
            "environment": str(r.get("env", "") or r.get("envb", "") or "")[:120],
            "lithology": str(r.get("lith", "") or r.get("lith1", "") or "")[:120],
            "epoch": str(r.get("oei", "") or r.get("ei", "") or "")[:80],
            "formation": str(r.get("sfm", "") or "")[:120],
            "country": str(r.get("cc2", "") or r.get("cny", "") or "")[:60],
        }
        rows.append(row)
    return rows


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return ""


def _mid(lo, hi):
    try:
        return (float(lo) + float(hi)) / 2.0
    except (TypeError, ValueError):
        return ""


def main():
    ap = argparse.ArgumentParser(description="Fetch PBDB paleontological data.")
    ap.add_argument("--out", default=os.environ.get("GEODISC_REAL_DATA", str(DEFAULT_OUT)))
    ap.add_argument("--age-min", type=float, default=400.0, help="youngest age (Ma)")
    ap.add_argument("--age-max", type=float, default=2500.0, help="oldest age (Ma)")
    ap.add_argument("--limit", type=int, default=50000)
    args = ap.parse_args()

    print(f"[pbdb-fetch] fetching collections {args.age_min}-{args.age_max} Ma ...")
    records = fetch_collections(args.age_min, args.age_max, args.limit)
    rows = tabulate(records)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys()) if rows else []
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"[pbdb-fetch] wrote {len(rows)} fossil collections to {out}")
    print(f"[pbdb-fetch] columns: {cols}")
    print(f"[pbdb-fetch] to use: GEODISC_DATA_PROFILE=paleo GEODISC_REAL_DATA={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
