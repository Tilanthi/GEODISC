"""verdict_log.py — structured per-candidate verdict logging (§7.2).

The supervisor runs the open-ended claim search as a SUBPROCESS with stdout
captured (and, in always-on mode, frequently discarded). Without an explicit
file write, every Gate-1/Gate-2 verdict is silently lost and the search funnel
(§4: where do candidates actually die?) is undiagnosable.

This module appends ONE JSONL line per evaluated candidate to
``~/.geodisc_persistent/evolved_programs/claim_verdicts.jsonl``, written
INSIDE the search process — independent of stdout capture. Each line carries
the outcome bucket needed for funnel analysis so the next iteration can be
chosen from data, not assumption (§4/§5).

Public API:
    outcome(verdict)  -> str        # bucket the verdict for the funnel
    log_verdict(verdict, dataset="default", path=None) -> None
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

VERDICT_LOG = (Path.home() / ".geodisc_persistent" / "evolved_programs"
               / "claim_verdicts.jsonl")


def outcome(verdict: dict) -> str:
    """Bucket a two-gate verdict into a single funnel label.

    Ordered so the most actionable diagnosis wins: a leakage block and a
    Gate-1 failure are distinct bottlenecks (§4), so they must not collapse.
    """
    g1 = verdict.get("gate1") or {}
    g2 = verdict.get("gate2")
    g1_reason = (g1.get("reason") or "") if isinstance(g1, dict) else ""

    # Tier 1: canonical-signature pre-filter short-circuit (sandbox skipped for
    # a relation Gate 2 already ruled known). gate1.pass is None (not run), so
    # bucket it distinctly from a real gate1-failed or gate2-known verdict.
    if isinstance(g1, dict) and g1.get("pass") is None and "canonical" in g1_reason:
        return "canonical-known"
    if isinstance(g1, dict) and not g1.get("pass"):
        if g1_reason.startswith("leakage"):
            return "leakage-blocked"
        return "gate1-failed"
    if g2 is None:
        return "gate2-skipped"
    status = g2.get("status") or ""
    if g2.get("pass") is True and verdict.get("both_pass"):
        return "both-pass"
    if status == "retrieval-failed" or "retrieval-failed" in status:
        return "gate2-retrieval-failed"
    if "error" in status:
        return "gate2-error"
    if g2.get("pass") is False:
        return "gate2-known"  # entailed / textbook / not novel
    return status or "other"


def log_verdict(verdict: dict, dataset: str = "default", path=None) -> None:
    """Append one JSONL verdict line. Best-effort: never breaks the search."""
    try:
        out = Path(path) if path else VERDICT_LOG
        out.parent.mkdir(parents=True, exist_ok=True)
        g1 = verdict.get("gate1") or {}
        g2 = verdict.get("gate2")
        line = {
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "dataset": dataset,
            "claim": verdict.get("claim"),
            "program_hash": verdict.get("program_hash"),
            "outcome": outcome(verdict),
            "both_pass": bool(verdict.get("both_pass")),
            "surprise": verdict.get("surprise"),           # Tier 2
            "novelty_tier": verdict.get("novelty_tier"),   # Tier 2
            "gate1": {
                "pass": g1.get("pass") if isinstance(g1, dict) else None,
                "reason": (g1.get("reason") if isinstance(g1, dict) else None),
                "effect": (g1.get("metrics", {}) or {}).get("effect"),
                "pvalue": (g1.get("metrics", {}) or {}).get("pvalue"),
            },
            "gate2": None if g2 is None else {
                "pass": g2.get("pass"),
                "status": g2.get("status"),
                "n_retrieved": g2.get("n_retrieved"),
            },
        }
        with out.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line) + "\n")
    except Exception:
        # Logging must never derail the search loop.
        pass


if __name__ == "__main__":
    # Self-demo: a gate1-fail verdict is bucketed and written.
    demo = {"claim": "demo", "program_hash": "demo0",
            "gate1": {"pass": False, "reason": "gate1-failed: weak",
                      "metrics": {"effect": 0.1, "pvalue": 0.4}},
            "gate2": None, "both_pass": False}
    print("outcome:", outcome(demo))
    log_verdict(demo, dataset="self-test")
    print("appended to", VERDICT_LOG)
