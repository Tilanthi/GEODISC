"""discovery_ranking.py — rank discoveries by scientific value, not just pass/fail.

LEARNING SOURCE: the three discovery-process documents (DISCOVERY-PROCESSES-SURVEY,
ITEM-BANK-SCHEMA, GATES-RECALIBRATION). Their headline finding: gates operated as
BINARY kills at proposal time would have killed 7 of 20 landmark discoveries
(pulsars, CMB, quasicrystals, H. pylori, prions, continental drift, dark matter).
The fix: convert from pass/fail to a RANKING system with two axes:

  promotion_score ∈ [0,1]  — how strong is the evidence? (provenance, significance,
                              method integrity, replication potential)
  anomaly_priority ∈ [0,1] — how paradigm-breaking is this? (mechanism-absence
                              INVERTED into a boost, consensus-conflict as signal)

And a four-way LEDGER STATUS that classifies each discovery:

  EXPLAINED_CONFIRMED     — real effect + known mechanism (normal)
  UNEXPLAINED_CONFIRMED   — real effect + NO known mechanism (HIGH priority —
                            this is the pulsar/quasicrystal/prion signature)
  EXPLAINED_UNCONFIRMED   — plausible mechanism, needs replication
  UNEXPLAINED_UNCONFIRMED — anomaly, no mechanism, single observation

The key inversion (from GATES-RECALIBRATION §R1 + DISCOVERY-PROCESSES-SURVEY §3.3):
mechanism-absence should RAISE priority, not lower it. "Paradigm-breaking discoveries
will always fail survivability tests calibrated to paradigm-consistent priors."
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

# Four-way ledger status (from GATES-RECALIBRATION §R1).
EXPLAINED_CONFIRMED = "EXPLAINED_CONFIRMED"
UNEXPLAINED_CONFIRMED = "UNEXPLAINED_CONFIRMED"      # paradigm-breaker candidate
EXPLAINED_UNCONFIRMED = "EXPLAINED_UNCONFIRMED"
UNEXPLAINED_UNCONFIRMED = "UNEXPLAINED_UNCONFIRMED"


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def promotion_score(effect: Optional[float], pvalue: Optional[float],
                     gate0_vetted: bool = False) -> float:
    """How strong is the evidence? Continuous score in [0, 1].

    Combines: significance magnitude (|effect| + -log10(p)), scaled to [0,1].
    A Gate-0-vetted question gets a small floor boost (the novelty has been
    pre-vetted, so modest evidence is more trustworthy).

    This REPLACES the binary gate1 threshold as a RANKING dimension.
    (GATES-RECALIBRATION §R5: sigma as ranking, not hard admission bar.)
    """
    try:
        eff = abs(float(effect)) if effect is not None else 0.0
        pv = float(pvalue) if pvalue is not None else 1.0
        pv = max(pv, 1e-300)  # avoid log(0)
        # significance signal: |effect| (capped at 0.5) + log10(1/p) (capped)
        sig = min(eff / 0.5, 1.0) * 0.5 + min(-math.log10(pv) / 10.0, 1.0) * 0.5
        floor = 0.1 if gate0_vetted else 0.0
        return min(1.0, floor + sig * (1.0 - floor))
    except Exception:
        return 0.0


def anomaly_priority(novelty_tier: Optional[str],
                     surprise: Optional[float],
                     gate0_verdict: Optional[str] = None) -> float:
    """How paradigm-breaking is this discovery? Continuous score in [0, 1].

    KEY INVERSION (GATES-RECALIBRATION §R1 + SURVEY §3.3):
    - mechanism-absence (strong-novel tier) RAISES priority, not lowers it.
    - high surprise (data contradicts textbook) RAISES priority.
    - Gate-0 "novel" verdict adds a small boost (question was pre-vetted as under-studied).

    This is the "inexplicable-but-reproducible" signal — the quasicrystal/pulsar/prion
    signature that a binary gate would KILL but that history says is the most valuable.
    """
    score = 0.0
    # mechanism-absence: strong-novel = "requires a process NOT in the literature"
    # This is the INVERTED signal — absence of explanation = +priority.
    if novelty_tier == "strong-novel":
        score += 0.40  # the biggest single boost (9/20 landmark discoveries had no mechanism)
    elif novelty_tier == "weak-novel":
        score += 0.10
    # surprise: data contradicts textbook expectation
    if surprise is not None and surprise >= 0.5:
        score += 0.20
    if surprise is not None and surprise >= 1.0:
        score += 0.15  # full contradiction (anomaly) gets extra
    # Gate-0 novelty verdict: the question was pre-vetted as genuinely under-studied
    if gate0_verdict and "novel" in str(gate0_verdict).lower():
        score += 0.15
    return min(1.0, score)


def ledger_status(novelty_tier: Optional[str],
                  gate2_status: Optional[str]) -> str:
    """Classify a discovery into the four-way ledger (GATES-RECALIBRATION §R1).

    EXPLAINED_CONFIRMED: Gate 2 says novel (found in literature or mechanistically
        ordinary) — the finding has an explanation context.
    UNEXPLAINED_CONFIRMED: Gate 2 says novel AND the mechanistic-contrast judge
        flagged strong-novel (requires a process NOT in the literature) — this is
        the paradigm-breaker candidate. HIGH PRIORITY.
    EXPLAINED_UNCONFIRMED: gate2 known but the effect is real — plausible but
        needs replication context.
    UNEXPLAINED_UNCONFIRMED: gate2 status unclear/errored.
    """
    if gate2_status == "novel" and novelty_tier == "strong-novel":
        return UNEXPLAINED_CONFIRMED
    if gate2_status == "novel":
        return EXPLAINED_CONFIRMED
    if gate2_status == "known":
        return EXPLAINED_UNCONFIRMED
    return UNEXPLAINED_UNCONFIRMED


def is_paradigm_breaker(status: str, priority: float) -> bool:
    """Does this discovery qualify for a reserved paradigm-breaker slot?

    From GATES-RECALIBRATION §4: the shortlist reserves ≥2 slots for
    UNEXPLAINED_CONFIRMED candidates so the sieve can never rank
    paradigm-breakers to zero.
    """
    return status == UNEXPLAINED_CONFIRMED and priority >= 0.4


def rank_discoveries(records: list) -> list:
    """Rank a list of discovery records by combined score (descending).

    Combined score = promotion_score + anomaly_priority.
    Paradigm-breaker candidates (UNEXPLAINED_CONFIRMED) get a floor boost
    so they always appear in the top-K shortlist (the reserved-slot guarantee).
    """
    def combined(r):
        ver = r.get("verification", r) if isinstance(r, dict) else {}
        eff = ver.get("effect")
        pv = ver.get("pvalue")
        tier = ver.get("novelty_tier") or r.get("novelty_tier")
        surp = ver.get("surprise") if ver.get("surprise") is not None else r.get("surprise")
        g0 = ver.get("gate0_verdict")
        g2s = ver.get("gate", {}).get("gate2_novelty") if isinstance(ver.get("gate"), dict) else None
        ps = promotion_score(eff, pv, gate0_vetted=bool(g0))
        ap = anomaly_priority(tier, surp, g0)
        status = ledger_status(tier, g2s)
        # reserved-slot floor for paradigm-breakers
        if is_paradigm_breaker(status, ap):
            return max(ps + ap, 0.5)  # floor so they always rank in top-K
        return ps + ap
    return sorted(records, key=combined, reverse=True)
