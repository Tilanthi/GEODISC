"""canonical_signature.py — phrasing-invariant claim signature + known-signature
registry (discovery-pipeline Tier 1).

WHY THIS EXISTS
---------------
Gate 2's novelty cache (``novelty_gate._cache_key``) and the textbook blocklist
both key on the *literal* claim string. So the SAME geochemical relation can be
judged ``known`` under one phrasing and ``novel`` under another — a *phrasing
escape*. Observed in production: a Ce-Nb residual correlation was
``gate2=known (n_retrieved=7)`` under one wording and ``gate2=novel`` under
another, and the latter was stored as a "discovery".

This module does two things:

1. **Canonical signature** — reduce a natural-language claim to a meaning-based
   signature hash invariant to wording:
   ``(relation_type, sorted(primary_vars), sorted(conditioning_vars), sign,
      population_bucket)``. Returns ``None`` when the claim cannot be parsed
   with confidence (so the caller falls through to the normal gate path).

2. **Known-signature registry** — a persistent set of signatures already judged
   ``known`` by the FULL Gate 2 (OpenAlex retrieval + LLM judge).
   ``run_claim_search.two_gate_eval`` consults the registry BEFORE the expensive
   90-second Gate 1 sandbox, so any re-phrasing of an already-rejected relation
   is skipped at near-zero CPU cost.

CONSERVATIVE BY CONSTRUCTION
----------------------------
A signature only enters the registry AFTER Gate 2 ruled some phrasing of it
``known``. The pre-filter never rejects a claim on its own authority — it only
short-circuits relations Gate 2 itself already rejected. Unparseable claims
return ``None`` and fall through, so genuine novelty is never blocked here.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)

KNOWN_REGISTRY_PATH = (Path.home() / ".geodisc_persistent" / "evolved_programs"
                       / "known_signatures.json")
VERDICT_LOG_PATH = (Path.home() / ".geodisc_persistent" / "evolved_programs"
                    / "claim_verdicts.jsonl")


# --------------------------------------------------------------------------- #
# Element / variable vocabulary                                                #
# --------------------------------------------------------------------------- #
# canonical_token -> tuple of regex forms (lower-cased match). Full names are
# listed alongside the symbol/_ppm forms; word boundaries on bare symbols avoid
# substring matches. Built from the real_data column set (claim_task.TASK_SYSTEM).
_ELEMENTS: Dict[str, Tuple[str, ...]] = {
    # major oxides
    "sio2":  (r"sio2", r"\bsilicon\b"),
    "tio2":  (r"tio2", r"\btitanium\b"),
    "al2o3": (r"al2o3", r"\balumina\b", r"\baluminium\b", r"\baluminum\b"),
    "feo":   (r"feo[_ ]?tot", r"\bfeot\b", r"fe2o3", r"\biron\b"),
    "mgo":   (r"mgo", r"mg#", r"mg-number", r"\bmagnesium\b"),
    "cao":   (r"cao", r"\bcalcium\b"),
    "mno":   (r"mno", r"\bmanganese\b"),
    "na2o":  (r"na2o", r"\bsodium\b"),
    "k2o":   (r"k2o", r"\bpotassium\b"),
    "p2o5":  (r"p2o5", r"\bphosphorus\b", r"\bphosphate\b"),
    # trace elements (ppm) — the widened, thinner-textbook niche
    "v":  (r"v_ppm", r"\bvanadium\b"),
    "cr": (r"cr_ppm", r"\bchromium\b"),
    "co": (r"co_ppm", r"\bcobalt\b"),
    "ni": (r"ni_ppm", r"\bnickel\b"),
    "cu": (r"cu_ppm", r"\bcopper\b"),
    "zn": (r"zn_ppm", r"\bzinc\b"),
    "rb": (r"rb_ppm", r"\brubidium\b", r"\brb\b"),
    "sr": (r"sr_ppm", r"\bstrontium\b", r"\bsr\b"),
    "y":  (r"y_ppm", r"\byttrium\b"),
    "zr": (r"zr_ppm", r"\bzirconium\b", r"\bzr\b"),
    "nb": (r"nb_ppm", r"\bniobium\b", r"\bnb\b"),
    "ba": (r"ba_ppm", r"\bbarium\b", r"\bba\b"),
    "la": (r"la_ppm", r"\blanthanum\b", r"\bla\b"),
    "ce": (r"ce_ppm", r"\bcerium\b", r"\bce\b"),
    "nd": (r"nd_ppm", r"\bneodymium\b", r"\bnd\b"),
    # isotopes (sparse, on-mission-relevant) — order matters: longer tokens first
    "sr87_sr86":   (r"sr87[_/]sr86", r"87sr/?86sr"),
    "nd143_nd144": (r"nd143[_/]nd144", r"143nd/?144nd"),
    "hf176_hf177": (r"hf176[_/]hf177", r"176hf/?177hf"),
    "pb206_pb204": (r"pb206[_/]pb204", r"206pb/?204pb"),
    "pb207_pb204": (r"pb207[_/]pb204", r"207pb/?204pb"),
    "pb208_pb204": (r"pb208[_/]pb204", r"208pb/?204pb"),
    "epsilon_nd":  (r"epsilon[_ ]?nd", r"εnd"),
    "epsilon_sr":  (r"epsilon[_ ]?sr", r"εsr"),
    "epsilon_hf":  (r"epsilon[_ ]?hf", r"εhf"),
    # age
    "age": (r"\bage\b",),
}

# Conditioning markers: the variable(s) regressed out / controlled for.
_COND_MARKERS = (
    "regress out", "regressing out", "regressed out",
    "controlling for", "control for", "controlled for",
    "after removing", "removing the", "after correcting",
    "correcting for", "correct for", "corrected for",
    "adjusting for", "adjust for",
    "conditioning on", "condition on", "partiall",
)
# Relation-type markers.
_RELATION_RESIDUAL = ("residual", "resid", "partial correlation",
                      "regress out", "regressing", "removing the dominant",
                      "correcting for", "correct for", "controlling for",
                      "control for", "after removing", "after correcting",
                      "adjusting for", "adjust for")
_RELATION_CONDITIONAL = ("among", "within", "subset", "in basalts",
                         "in arc", "conditional on", "restricted to",
                         "for samples", "where ")
_RELATION_RATIO = ("/", " ratio", "interaction", "*")

# Population buckets.
_POP_RULES = (
    ("basalt", ("basalt",)),
    ("arc", ("arc", "subduction")),
    ("sediment", ("sediment", "shale", "carbonate", "chert")),
    ("ultramafic", ("peridotite", "komatiite", "ultramafic")),
)

# Clause terminators that bound a conditioning clause (so the window after
# "regressing out MgO" captures MgO but NOT the later primary variables).
_COND_BOUNDARY = r"[);,\n.]|\b(?:is|are|was|were|exhibits?|correlat\w*|shows?|positive|negative|enrichment|residual)\b"


def _find_elements(low: str) -> Set[str]:
    """Return the set of canonical element tokens mentioned in lower-cased text."""
    found: Set[str] = set()
    for canon, forms in _ELEMENTS.items():
        for pat in forms:
            try:
                if re.search(pat, low):
                    found.add(canon)
                    break
            except re.error:
                continue
    return found


def _conditioning_elements(low: str, all_elements: Set[str]) -> Set[str]:
    """Elements mentioned inside a conditioning clause ('regressing out MgO', ...).

    The clause is the token run from a conditioning marker up to the first
    clause boundary, so the primary variables that come later in the sentence
    are NOT absorbed into the conditioning set.
    """
    cond: Set[str] = set()
    for marker in _COND_MARKERS:
        idx = low.find(marker)
        if idx < 0:
            continue
        tail = low[idx + len(marker): idx + len(marker) + 40]
        tail = re.split(_COND_BOUNDARY, tail, maxsplit=1)[0]
        for el in all_elements:
            for pat in _ELEMENTS[el]:
                try:
                    if re.search(pat, tail):
                        cond.add(el)
                except re.error:
                    continue
    return cond


def _relation_type(low: str) -> str:
    if any(k in low for k in _RELATION_RESIDUAL):
        return "residual"
    if any(k in low for k in _RELATION_CONDITIONAL):
        return "conditional"
    if any(k in low for k in _RELATION_RATIO):
        return "ratio"
    return "pairwise"


def _population(low: str) -> str:
    for bucket, kws in _POP_RULES:
        if any(k in low for k in kws):
            return bucket
    return "general"


def _sign(low: str) -> str:
    pos = any(k in low for k in ("positive", "positively", "enrich", "increase",
                                 "correlate", "coupl"))
    neg = any(k in low for k in ("negative", "negatively", "deplet", "decrease",
                                 "anti-correl", "anticorrel", "inverse"))
    if pos and not neg:
        return "positive"
    if neg and not pos:
        return "negative"
    return "unstated"


def components(claim: str) -> Optional[dict]:
    """Parse a claim into its canonical components, or ``None`` if not confident.

    Confidence rule: at least one primary variable (an element mentioned outside
    the conditioning clause) must be identifiable. Otherwise the claim is too
    ambiguous to signature safely -> return None so the caller falls through.
    """
    if not claim or not claim.strip():
        return None
    try:
        low = claim.lower()
        all_el = _find_elements(low)
        cond = _conditioning_elements(low, all_el)
        primary = all_el - cond
        if not primary:
            return None
        return {
            "relation_type": _relation_type(low),
            "primary": tuple(sorted(primary)),
            "conditioning": tuple(sorted(cond)),
            "sign": _sign(low),
            "population": _population(low),
        }
    except Exception:
        return None


def signature(claim: str) -> Optional[str]:
    """Return a short hex hash of the claim's canonical signature, or None."""
    c = components(claim)
    if c is None:
        return None
    canon = "|".join((
        c["relation_type"],
        ",".join(c["primary"]),
        ",".join(c["conditioning"]),
        c["sign"],
        c["population"],
    ))
    return hashlib.sha1(canon.encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Known-signature registry (learned from Gate-2 'known' verdicts)              #
# --------------------------------------------------------------------------- #
def load_known() -> Set[str]:
    """Load the set of signature hashes Gate 2 has ruled 'known'."""
    try:
        if KNOWN_REGISTRY_PATH.exists():
            data = json.loads(KNOWN_REGISTRY_PATH.read_text())
            if isinstance(data, dict):
                return {str(k) for k in data.get("signatures", [])}
            if isinstance(data, list):
                return {str(k) for k in data}
    except Exception as e:
        logger.debug("[canonical] known-registry load failed: %s", e)
    return set()


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    tmp.replace(path)


def register_known(claim: str) -> bool:
    """Record a claim's signature as known. Idempotent. Returns True if new."""
    sig = signature(claim)
    if sig is None:
        return False
    known = load_known()
    if sig in known:
        return False
    known.add(sig)
    try:
        KNOWN_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {"signatures": sorted(known), "count": len(known)}
        _atomic_write(KNOWN_REGISTRY_PATH, json.dumps(payload, indent=2))
    except Exception as e:
        logger.debug("[canonical] known-registry save failed: %s", e)
    return True


def is_known(claim: str) -> bool:
    """True iff the claim's canonical signature is in the known-registry."""
    sig = signature(claim)
    if sig is None:
        return False
    return sig in load_known()


def seed_from_verdict_log(path: Path = VERDICT_LOG_PATH) -> int:
    """Populate the registry from every prior ``gate2-known`` verdict.

    Returns the number of new signatures added. This makes the pre-filter
    immediately useful on first deploy: the textbook families the proposer has
    already been rejected for are recognized from cycle 1.
    """
    added = 0
    if not path.exists():
        return 0
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("outcome") != "gate2-known":
                    continue
                claim = rec.get("claim") or ""
                if register_known(claim):
                    added += 1
    except Exception as e:
        logger.warning("[canonical] verdict-log seed failed: %s", e)
    return added


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Canonical signature / known-registry tool")
    ap.add_argument("--seed", action="store_true",
                    help="seed the known-registry from the verdict log")
    ap.add_argument("--show", action="store_true",
                    help="print the registry size")
    ap.add_argument("--claim", default=None, help="print the signature of this claim")
    args = ap.parse_args()
    if args.seed:
        n = seed_from_verdict_log()
        print(f"seeded {n} new known signatures (registry total: {len(load_known())})")
    if args.claim:
        print("components:", components(args.claim))
        print("signature :", signature(args.claim))
        print("is_known  :", is_known(args.claim))
    if args.show:
        print(f"registry size: {len(load_known())} at {KNOWN_REGISTRY_PATH}")
