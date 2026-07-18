"""surprise.py — Tier 2 Part A: a surprise / anomaly objective for the pipeline.

WHY THIS EXISTS
---------------
Tier 1 stops the pipeline re-evaluating relations it already knows are known, but
it does not change WHAT the proposer aims for. The proposer's only concrete
success signal is significance (Gate-1 effect / p-value), and the strongest
correlations in a global compilation (r ~= 0.8 between two incompatible elements)
are the MOST textbook — so the pipeline is structurally tuned to re-derive known
things.

This module gives a cheap, deterministic *surprise score*: for a candidate whose
confirmed sign CONTRADICTS the textbook-expected sign for that element pair
(reward -> 1.0), vs. a confirmation (0.0), vs. an unstudied pair (0.5 neutral).
The proposer is nudged toward the 1.0 tail (a contradiction the data actually
supports — the rare paradigm-shift-shaped candidate); survivors are annotated
with the score for ranking/triage.

CONSERVATIVE: pure annotation + proposer guidance. It NEVER rejects a candidate.
Reuses ``canonical_signature.components`` for element extraction so it composes
with Tier 1.
"""
from __future__ import annotations

import os
from typing import List, Optional, Tuple

try:
    from . import canonical_signature as cs
except ImportError:
    import canonical_signature as cs


# --------------------------------------------------------------------------- #
# Expectations table — textbook correlation signs for the saturated pairs the  #
# proposer keeps re-deriving (drawn from the verdict-log gate2-known families). #
# Key: sorted canonical element pair -> (expected_sign, one-line reason).        #
# Extensible; this is a starting set covering the dominant textbook families.   #
# --------------------------------------------------------------------------- #
_EXPECTATIONS = {
    # incompatible-element coherence (the Ce-Nb / Nd-Nb / etc. family)
    ("ce", "nb"):  ("+", "LREE-HFSE incompatible coherence"),
    ("nd", "nb"):  ("+", "incompatible coherence"),
    ("la", "nb"):  ("+", "LREE-HFSE incompatible coherence"),
    ("ce", "nd"):  ("+", "LREE coherence"),
    ("la", "ce"):  ("+", "LREE coherence"),
    ("zr", "nb"):  ("+", "HFSE coherence"),
    ("y", "zr"):   ("+", "HFSE coherence"),
    ("rb", "sr"):  ("+", "LILE incompatible coherence"),
    ("ba", "sr"):  ("+", "LILE coherence"),
    ("rb", "ba"):  ("+", "LILE coherence"),
    ("cr", "ni"):  ("+", "compatibility-driven coherence (spinel/olivine)"),
    # major-oxide fractionation trends
    ("mgo", "sio2"): ("-", "Harker fractionation"),
    ("feo", "mgo"):  ("+", "Fe-Mg covariation"),
    ("k2o", "na2o"): ("+", "total-alkali covariation (TAS)"),
    ("al2o3", "mgo"): ("-", "fractionation (Al rises as MgO falls)"),
    ("cao", "mgo"):   ("+", "fractionation coherence"),
}


def enabled() -> bool:
    """Surprise guidance on by default; set GEODISC_SURPRISE_GUIDANCE=0 to disable."""
    return os.environ.get("GEODISC_SURPRISE_GUIDANCE", "1") not in ("0", "false", "False")


def _pair_key(primary: Tuple[str, ...]) -> Optional[Tuple[str, str]]:
    """Sorted 2-element key for the expectations table lookup."""
    if len(primary) == 2:
        a, b = primary
        return (a, b) if a <= b else (b, a)
    return None


def expected_sign(claim: str) -> Optional[Tuple[str, str]]:
    """Return (expected_sign, reason) if the claim's primary pair is in the table."""
    comp = cs.components(claim)
    if comp is None:
        return None
    k = _pair_key(comp["primary"])
    if k is None:
        return None
    return _EXPECTATIONS.get(k)


def sign_of(effect) -> Optional[str]:
    """Derive '+'/'-' from a numeric effect, or None."""
    try:
        return "+" if float(effect) >= 0 else "-"
    except (TypeError, ValueError):
        return None


def _sign_char(s: Optional[str]) -> Optional[str]:
    """Normalize a sign expressed as '+'/'-' or 'positive'/'negative' to '+'/'-'."""
    if s in ("+", "positive"):
        return "+"
    if s in ("-", "negative"):
        return "-"
    return None


def surprise_score(claim: str, effect_sign: Optional[str]) -> float:
    """Surprise score in [0, 1].

    - 1.0 : the claim's primary pair is in the expectations table AND the
            confirmed sign CONTRADICTS the expected sign (a real anomaly).
    - 0.0 : pair in the table AND the confirmed sign matches (a confirmation).
    - 0.5 : pair not in the table, or sign unknown -> unstaged / neutral.
    """
    exp = expected_sign(claim)
    if exp is None:
        return 0.5
    ec = _sign_char(effect_sign)
    if ec is None:
        return 0.5
    return 1.0 if ec != exp[0] else 0.0


def surprise_hint(recent: List[Tuple[str, Optional[float]]]) -> Optional[str]:
    """If recent survivors are mostly confirmations of a known pair, nudge the
    proposer toward the opposite sign (or an unstudied pair).

    ``recent`` is a list of (claim, surprise_score) for recent both-pass survivors.
    Returns a guidance string, or None if there's nothing actionable.
    """
    confs = [(c, s) for c, s in recent if s is not None and s < 0.5]
    if len(confs) < 2:
        return None
    tally = {}
    for claim, _ in confs:
        exp = expected_sign(claim)
        if exp:
            tally[exp] = tally.get(exp, 0) + 1
    if not tally:
        return None
    (sign, reason), n = max(tally.items(), key=lambda kv: kv[1])
    return (
        f"SURPRISE NUDGE: the last {n} survivor(s) were confirmations of the "
        f"{reason} (expected sign {sign}). A paradigm-shift candidate asserts the "
        f"OPPOSITE sign for that pair and survives Gate 1, or explores an "
        f"unstudied pair (isotopes, age-conditional, ratio systematics). Pure "
        f"confirmations are rarely novel even if highly significant.")
