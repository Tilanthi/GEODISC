"""diversity.py — Tier 3 Part 1: per-family diversity pressure (guidance only).

WHY THIS EXISTS
---------------
Without diversity pressure the proposer re-mines one element-pair family
indefinitely (the production store is dominated by the Ce-Nb / Nd-Nb / Ba-Nb
incompatible-pair vein). This module tracks the family of each candidate the
search generates (reusing ``canonical_signature.components`` — the primary
element tuple is the family key) and emits a guidance hint when one family
dominates the recent window, nudging the proposer toward a different family or
repertoire form.

CONSERVATIVE: guidance only. It never rejects or skips a candidate, so a
genuinely-novel re-phrasing is never lost. Env-gated via GEODISC_DIVERSITY_CAP
(set 0 to disable; the numeric value is the dominance threshold).
"""
from __future__ import annotations

import os
from collections import Counter, deque
from typing import Optional

try:
    from . import canonical_signature as cs
except ImportError:
    import canonical_signature as cs

_DEFAULT_CAP = 3
_DEFAULT_WINDOW = 8


def enabled() -> bool:
    return os.environ.get("GEODISC_DIVERSITY_CAP", str(_DEFAULT_CAP)) not in ("0", "false", "False")


def _cap() -> int:
    try:
        return int(os.environ.get("GEODISC_DIVERSITY_CAP", _DEFAULT_CAP))
    except ValueError:
        return _DEFAULT_CAP


class FamilyTracker:
    """Tracks the families of recently-generated candidates in a sliding window."""

    def __init__(self, window: int = _DEFAULT_WINDOW):
        self._recent: deque = deque(maxlen=window)

    @staticmethod
    def _family(claim: str) -> Optional[str]:
        try:
            comp = cs.components(claim)
        except Exception:
            comp = None
        if comp and comp["primary"]:
            return "-".join(comp["primary"])
        return None

    def note(self, claim: str) -> None:
        """Record a candidate's family (no-op if the claim can't be parsed)."""
        self._recent.append(self._family(claim))

    def hint(self) -> Optional[str]:
        """A diversification nudge if one family dominates the recent window."""
        if not enabled():
            return None
        present = [f for f in self._recent if f]
        if not present:
            return None
        top_fam, top_n = Counter(present).most_common(1)[0]
        if top_n >= _cap():
            return (
                f"DIVERSITY: {top_n} of the last {len(present)} candidate(s) were the "
                f"{top_fam} element-pair family. That vein is likely exhausted -- switch "
                f"to a DIFFERENT element-pair family or a different repertoire form "
                f"(threshold/non-monotonic, anomaly subpopulation, ratio systematics, "
                f"predictive validity). Pure re-phrasings of the same family are rarely "
                f"novel.")
        return None
