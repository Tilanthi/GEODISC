#!/usr/bin/env python3
"""fetch_proterozoic_data.py — autonomous fetcher for the Proterozoic Fe-speciation
+ TOC substrate (Tier 3, Part 3.2).

Source: SGP Phase 2 (Farrell et al. 2026, Chemical Geology) — CC BY 4.0.
API: POST https://sgp-search.io/api/v1/post  body {type, filters, show}
(see https://sgp-search.io/documentation/api-description).

The SGP gateway intermittently 504s / times out on geochem queries, so this
fetcher is built to be AUTONOMOUS AND RESILIENT, not interactive:
  - one attribute per small call (unambiguous column mapping + minimal backend load),
  - paginated by age window (Paleoproterozoic-Mesoproterozoic, 1000-2500 Ma),
  - exponential backoff + many retries on 504/timeout (transient overload),
  - politeness delay between calls,
  - resumable: each age window is checkpointed, so re-running continues where it
    left off (and the supervisor can re-trigger it across cycles until complete),
  - client-side validation: refuses to write if a REQUIRED column is all-empty
    (a wrong/renamed attribute is detected, never silently producing fiction).

Output: a CSV with columns fe_hr, fe_t, fe_py, toc, age (+ sample_id) written to
GEODISC_REAL_DATA (or ~/.geodisc_persistent/geochem_proterozoic.csv), consumable
by the `proterozoic_redox` data profile ($GEODISC_DATA_PROFILE=proterozoic_redox).

No fictional/synthetic data: every value comes from the real SGP API; rows missing
the required on-mission columns (fe_hr, fe_py, age) are dropped client-side.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://sgp-search.io/api/v1/post"
DEFAULT_OUT = Path.home() / ".geodisc_persistent" / "geochem_proterozoic.csv"
CHECKPOINT_DIR = Path.home() / ".geodisc_persistent" / "proterozoic_fetch"

# SGP API attribute -> (canonical column, fallback API names, display-name token).
# fe_t is TOTAL Fe; SGP exposes it as `fe` (Fe wt%). TOC + age use the standard
# SGP names; fallbacks cover possible renames (validated client-side).
ATTRIBUTES = [
    ("fe",        "fe_t",  ["fe"],                 "total Fe"),
    ("fe_hr",     "fe_hr", ["fe_hr"],              "FeHR"),
    ("fe_py",     "fe_py", ["fe_py"],              "Fe-py"),
    ("total_org_c", "toc", ["total_org_c", "toc", "c_org"], "organic carbon"),
    ("max_age_ma",  "age", ["max_age_ma", "age"],  "age"),
]
REQUIRED = ("fe_hr", "fe_py", "age")  # must be non-empty in the final dataset

USER_AGENT = "GEODISC-autonomous-fetcher/1.0 (research; contact via repo)"


def _post(body: dict, timeout: float) -> list:
    req = urllib.request.Request(
        API_URL, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def api_call(body: dict, retries: int, base_timeout: float) -> list:
    """POST one query with exponential backoff on 504/timeout/connection errors."""
    delay = 3.0
    last = None
    for attempt in range(retries):
        try:
            return _post(body, base_timeout + 10 * attempt)  # lengthen timeout too
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            code = getattr(e, "code", None)
            # 4xx (bad request) is not transient — bail with a marker.
            if isinstance(e, urllib.error.HTTPError) and 400 <= code < 500 and code != 429:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 60.0)
    raise RuntimeError(f"api_call failed after {retries} retries: {last}")


def fetch_attr_window(candidates: list, lo: float, hi: float, retries: int, timeout: float) -> dict:
    """Return {sample_id: value} for one attribute over one age window.

    Tries each candidate API name in turn until one yields values (handles
    renamed attributes; validated client-side later so a wrong name is detected,
    never producing fiction).
    """
    for attr in candidates:
        body = {"type": "samples",
                "filters": {"max_age_ma": [lo, hi]},
                "show": ["sample identifier", attr]}
        try:
            rows = api_call(body, retries=retries, base_timeout=timeout)
        except Exception:
            rows = []
        out = {}
        for r in rows:
            sid = r.get("sample identifier")
            if sid is None:
                continue
            val = next((v for k, v in r.items() if k != "sample identifier"), None)
            if val not in (None, "", []):
                out[sid] = val
        if out:
            return out, attr  # (values, the name that worked)
    return {}, None


def fetch_window(lo: float, hi: float, retries: int, timeout: float, politeness: float) -> dict:
    """Fetch all attributes for one age window; return {sample_id: {col: val}}."""
    stitched: dict = {}
    for api_name, canon, fallbacks, _disp in ATTRIBUTES:
        candidates = [api_name] + [f for f in fallbacks if f != api_name]
        got, worked = fetch_attr_window(candidates, lo, hi, retries, timeout)
        for sid, val in got.items():
            stitched.setdefault(sid, {})[canon] = val
        tag = f"{api_name}" + (f" (via {worked})" if worked and worked != api_name else "")
        print(f"    [{lo}-{hi} Ma] {tag}: {len(got)} values" if got else
              f"    [{lo}-{hi} Ma] {api_name}: 0 values (all candidates empty/failed)")
        time.sleep(politeness)
    return stitched


def _resolve(name: str) -> str:
    """Allow GEODISC_SGP_<ATTR> env overrides for attribute names (paranoid)."""
    return os.environ.get(f"GEODISC_SGP_{name.upper()}", name)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.environ.get("GEODISC_REAL_DATA", str(DEFAULT_OUT)))
    ap.add_argument("--age-min", type=float, default=1000.0, help="youngest age (Ma)")
    ap.add_argument("--age-max", type=float, default=2500.0, help="oldest age (Ma)")
    ap.add_argument("--window", type=float, default=100.0, help="age-window width (Ma)")
    ap.add_argument("--retries", type=int, default=6)
    ap.add_argument("--timeout", type=float, default=25.0)
    ap.add_argument("--politeness", type=float, default=2.0, help="seconds between calls")
    ap.add_argument("--max-rows", type=int, default=0, help="0 = no cap")
    ap.add_argument("--max-runtime-sec", type=float, default=900.0,
                    help="per-run wall-clock budget; stops fetching NEW windows after "
                         "this (cached windows still load) so periodic auto-retries "
                         "accumulate progress without overlapping")
    ap.add_argument("--max-rows", type=int, default=0, help="0 = no cap")
    ap.add_argument("--max-runtime-sec", type=float, default=900.0,
                    help="per-run wall-clock budget; stops fetching NEW windows after "
                         "this (cached windows still load) so periodic auto-retries "
                         "accumulate progress without overlapping")
    ap.add_argument("--max-failed-runs", type=int, default=10,
                    help="after this many consecutive runs that fetch ZERO new "
                         "samples, self-park: subsequent runs do only a cheap 1-window "
                         "recovery probe until the source responds (finite retry, no "
                         "infinite loop on a permanently stalled source)")
    args = ap.parse_args()

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fail_state_path = CHECKPOINT_DIR / "fail_state.json"

    def _load_fail_state():
        try:
            return json.loads(fail_state_path.read_text())
        except Exception:
            return {"consecutive_empty": 0, "parked": False}

    def _save_fail_state(s):
        try:
            fail_state_path.write_text(json.dumps(s))
        except Exception:
            pass

    fail_state = _load_fail_state()
    parked = bool(fail_state.get("parked"))

    cols = ["sample_id", "fe_t", "fe_hr", "fe_py", "toc", "age"]
    windows = []
    lo = args.age_min
    while lo < args.age_max:
        windows.append((lo, min(lo + args.window, args.age_max)))
        lo += args.window

    # Self-park: if the source has stalled for many runs, do only a cheap 1-window
    # recovery probe instead of the full sweep (bounded retries; revisit later).
    if parked:
        windows = windows[:1]
        print(f"[prot-fetch] PARKED (source stalled {fail_state.get('consecutive_empty')} "
              f"runs) — running a cheap 1-window recovery probe only.")
    print(f"[prot-fetch] {len(windows)} age window(s) ({args.age_min}-{args.age_max} Ma, "
          f"width {args.window}); retries={args.retries} timeout={args.timeout}s "
          f"budget={args.max_runtime_sec}s")

    t_start = time.time()
    all_rows = {}
    new_this_run = 0  # samples from NON-cached windows (drives the park/probe logic)
    for lo, hi in windows:
        ck = CHECKPOINT_DIR / f"window_{int(lo)}_{int(hi)}.json"
        if ck.exists():
            try:
                stitched = json.loads(ck.read_text())
                print(f"[prot-fetch] window {lo}-{hi} Ma: cached ({len(stitched)} samples)")
                all_rows.update(stitched)
                continue
            except Exception:
                pass
        if time.time() - t_start > args.max_runtime_sec:
            print(f"[prot-fetch] per-run budget reached at window {lo}-{hi} Ma; "
                  f"will resume here next run (checkpoint/resumable).")
            break
        print(f"[prot-fetch] window {lo}-{hi} Ma ...")
        stitched = fetch_window(lo, hi, args.retries, args.timeout, args.politeness)
        all_rows.update(stitched)
        new_this_run += len(stitched)
        try:
            ck.write_text(json.dumps(stitched))
        except Exception as e:
            print(f"    checkpoint write failed: {e}")

    # Park/probe bookkeeping: a run that fetched NEW samples resets the stall
    # counter (and unparks); an empty run increments it, parking after the cap.
    if new_this_run > 0:
        fail_state = {"consecutive_empty": 0, "parked": False}
    else:
        c = int(fail_state.get("consecutive_empty", 0)) + 1
        fail_state = {"consecutive_empty": c,
                      "parked": c >= args.max_failed_runs}
    _save_fail_state(fail_state)
    if fail_state["parked"] and new_this_run == 0:
        print(f"[prot-fetch] no new samples; parking after {fail_state['consecutive_empty']} "
              f"empty run(s) — will cheap-probe on subsequent ticks until the source "
              f"responds.")

    # keep only rows with the required on-mission columns
    clean = []
    for sid, vals in all_rows.items():
        if all(k in vals for k in REQUIRED):
            clean.append({"sample_id": sid,
                          "fe_t": vals.get("fe_t"), "fe_hr": vals.get("fe_hr"),
                          "fe_py": vals.get("fe_py"), "toc": vals.get("toc"),
                          "age": vals.get("age")})
    if args.max_rows and len(clean) > args.max_rows:
        clean = clean[:args.max_rows]

    # VALIDATION: refuse to write an empty / all-null required column (no fiction).
    if not clean:
        print(f"[prot-fetch] no samples had all required cols {REQUIRED} — the API "
              f"may be unresponsive or an attribute name needs correcting; nothing "
              f"written. Re-run later (checkpoints are kept).")
        return 1
    for col in REQUIRED:
        n = sum(1 for r in clean if r.get(col) not in (None, ""))
        if n == 0:
            print(f"[prot-fetch] required column '{col}' is all-empty — likely a wrong "
                  f"SGP attribute name (set GEODISC_SGP_<NAME>). Nothing written.")
            return 1

    with out_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in clean:
            w.writerow(r)
    print(f"[prot-fetch] wrote {len(clean)} real Proterozoic samples to {out_path}")
    print(f"[prot-fetch] set: GEODISC_DATA_PROFILE=proterozoic_redox  "
          f"GEODISC_REAL_DATA={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
