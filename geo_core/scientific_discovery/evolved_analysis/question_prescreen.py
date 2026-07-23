"""question_prescreen.py — Gate 0: LLM-powered question novelty prescreen.

WHY THIS EXISTS
---------------
The pipeline's persistent failure: most generated claims are statistically
significant but SCIENTIFICALLY WELL-KNOWN (textbook taphonomic bias, standard
diversity curves, established preservation patterns). These waste expensive
sandbox + retrieval cycles before Gate 2 rejects them — or worse, Gate 2's
not-found-verbatim logic lets them through as "novel."

Gate 0 is a CHEAP LLM agent (one call, no network/retrieval) that judges whether
a CLAIM is textbook/already-published BEFORE the sandbox runs. Textbook claims
are rejected early; genuinely under-studied questions proceed to Gate 1 + 2.

The agent uses the LLM's own paleontology / Earth-history domain knowledge —
NOT retrieval (that's Gate 2's job). It's a fast knowledge-based filter.

CONSERVATIVE: if the gateway is unavailable or the judge fails, the claim
PROCEEDS (Gate 0 should never block a potentially-novel claim on infrastructure
failure). If the judge is uncertain, it leans textbook (reject).
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Tuple

logger = logging.getLogger(__name__)

try:
    from ._llm import gateway_module
except ImportError:
    gateway_module = None


def _get_gateway():
    if gateway_module is None:
        try:
            from ..intelligence.llm_gateway import get_gateway
            return get_gateway()
        except Exception:
            return None
    try:
        LLMGateway = gateway_module().LLMGateway
        return LLMGateway(model=os.environ.get("GEODISC_PROPOSER_MODEL", "claude-sonnet-5-20250929"),
                          max_tokens=400, timeout=30.0)
    except Exception:
        return None


_SYSTEM = (
    "You are an expert PALEONTOLOGIST, taphonomist, and Earth-history scientist "
    "evaluating a candidate scientific CLAIM for GENUINE NOVELTY before any "
    "computation is done.\n\n"
    "Classify the claim as ONE of:\n"
    "  'textbook' — a well-established pattern from taphonomy, paleoecology, "
    "sedimentary geology, or Earth-history textbooks. Examples: 'deep-water "
    "environments preserve more fossils than peritidal' (taphonomic bias); "
    "'diversity increases through the Phanerozoic' (documented); 'carbonate vs "
    "clastic preservation differs' (known); 'more fossils in younger rocks' "
    "(the Pull of the Recent — sampling bias).\n"
    "  'published' — not textbook-fundamental, but already addressed in specific "
    "published research (a known result within the specialist literature).\n"
    "  'novel' — genuinely under-studied: a coupling not previously tested at "
    "this scale, a pattern in an under-sampled interval/organism group, a "
    "counterintuitive relationship, or a new combination of variables that goes "
    "BEYOND standard taphonomic or diversity-pattern knowledge.\n\n"
    "Be STRICT. When uncertain, lean toward 'textbook' or 'published' (we prefer "
    "to drop a marginal result than waste cycles on a known one). A claim that "
    "simply confirms an expected pattern (e.g. 'environment X has more fossils') "
    "is textbook, NOT novel, even if the specific pair hasn't been phrased this way."
)


def prescreen(claim: str) -> Tuple[bool, str]:
    """Gate 0: judge whether ``claim`` is textbook/known or potentially novel.

    Returns (proceed, reason). proceed=True if the claim should continue to
    Gate 1 (sandbox). proceed=False if it's textbook/published (skip sandbox).
    Conservative: proceeds on any infrastructure failure."""
    if not claim or not claim.strip():
        return True, "empty-claim"

    gw = _get_gateway()
    if gw is None:
        return True, "no-gateway"  # never block on infra failure

    user = (
        f"CANDIDATE CLAIM:\n{claim}\n\n"
        "Respond with ONLY JSON: "
        '{"verdict": "textbook"|"published"|"novel", '
        '"reasoning": "<one sentence explaining WHY>"}'
    )
    try:
        text, _ = gw.complete(
            system=_SYSTEM,
            messages=[{"role": "user", "content": user}],
            max_tokens=200)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return True, "judge-unparseable"  # proceed on parse failure
        result = json.loads(m.group(0))
        verdict = str(result.get("verdict", "")).strip().lower()
        reasoning = str(result.get("reasoning", ""))[:200]
        if verdict in ("textbook", "published"):
            return False, f"gate0-{verdict}: {reasoning}"
        if verdict == "novel":
            return True, f"gate0-novel: {reasoning}"
        return True, f"gate0-unclear: {reasoning}"  # proceed on unclear
    except Exception as e:
        logger.debug("[prescreen] judge failed: %s", e)
        return True, f"judge-error: {type(e).__name__}"


def enabled() -> bool:
    """Gate 0 on by default; set GEODISC_QUESTION_PRESCREEN=0 to disable."""
    return os.environ.get("GEODISC_QUESTION_PRESCREEN", "1") not in ("0", "false", "False")
