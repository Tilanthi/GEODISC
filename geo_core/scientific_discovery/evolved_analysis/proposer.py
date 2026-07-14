"""proposer.py — AlphaEvolve-style "creative generation".

Given a parent program (source + metrics) and inspirations (other good
programs), a Proposer produces a CHILD program source.

  * LLMProposer — asks Claude (via the configured gateway) for an improvement,
                  as either a search/replace DIFF or a full rewrite. This is the
                  real AlphaEvolve path, used by the Phase-2 claim search.

apply_diff() parses the <<<SEARCH ... >>> <<<REPLACE ... >>> block format and
falls back to a fenced full-rewrite, then to the parent unchanged.
"""
from __future__ import annotations

import os
import re
from typing import List, Optional, Tuple


# --------------------------------------------------------------------------- #
# diff parsing / application                                                   #
# --------------------------------------------------------------------------- #
_SEARCH_RE = re.compile(
    r"<<<\s*SEARCH\s*>>>(.*?)<<<\s*REPLACE\s*>>>(.*?)<<<\s*END\s*>>>",
    re.DOTALL)


def _has_entry_point(src: str, entry_point: str) -> bool:
    """Cheap static check that the source defines the required entry point."""
    return f"def {entry_point}" in src


def extract_python_block(text: str) -> Optional[str]:
    m = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def apply_diff(parent_src: str, response: str, entry_point: str = "run_claim") -> Tuple[str, str]:
    """Return (child_source, mode) where mode in
    {'diff','rewrite','unchanged'}. Never raises."""
    # 1) try SEARCH/REPLACE blocks
    blocks = _SEARCH_RE.findall(response)
    if blocks:
        out = parent_src
        for old, new in blocks:
            old_s, new_s = old.strip("\n"), new.strip("\n")
            if old_s and old_s in out:
                out = out.replace(old_s, new_s, 1)
            else:
                return parent_src, "unchanged"   # a block failed to match -> bail
        if _has_entry_point(out, entry_point):
            return out, "diff"
    # 2) try a fenced full rewrite
    py = extract_python_block(response)
    if py and _has_entry_point(py, entry_point):
        return py, "rewrite"
    # 3) last resort: maybe the whole response IS the function
    if _has_entry_point(response, entry_point):
        return response.strip(), "rewrite"
    return parent_src, "unchanged"


# --------------------------------------------------------------------------- #
# proposer interface + LLM backend                                             #
# --------------------------------------------------------------------------- #
class Proposer:
    name = "base"

    def propose(self, parent_source: str, parent_metrics: dict,
                parent_spec: Optional[dict], inspirations: List[str]
                ) -> Tuple[Optional[str], Optional[dict], dict]:
        """Return (child_source, child_spec, info).
        child_source None means 'could not propose'."""
        raise NotImplementedError


class LLMProposer(Proposer):
    name = "llm"

    def __init__(self, model: Optional[str] = None,
                 max_tokens: int = 1600, timeout: float = 90.0,
                 context_level: str = "rich",
                 task_system: Optional[str] = None,
                 entry_point: str = "run_claim"):
        # Load the canonical gateway decoupled from geo_core/__init__ (evolved_analysis
        # runs with PYTHONPATH=geo_core/scientific_discovery). See _llm.py.
        from ._llm import gateway_module
        LLMGateway = gateway_module().LLMGateway
        self._gw = LLMGateway(
            model=(model or os.environ.get("GEODISC_PROPOSER_MODEL",
                                           "claude-sonnet-5-20250929")),
            max_tokens=max_tokens, timeout=timeout)
        self.client = self._gw.client
        self.model = self._gw.model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.context_level = context_level   # "minimal" | "rich"
        # Task generality (WP5): an alternative task system prompt + entry point.
        # The Phase-2 claim search supplies a geochemistry task_system; the
        # BASE_SYSTEM below is a domain-neutral fallback.
        self.task_system = task_system
        self.entry_point = entry_point
        self.n_calls = 0
        self.n_errors = 0

    # Generic fallback system prompt (domain-neutral scientist/ML improver). The
    # Phase-2 claim search overrides this with a geochemistry TASK_SYSTEM.
    BASE_SYSTEM = (
        "You are an expert scientist and ML engineer. You improve a Python "
        "function that is graded on REAL held-out data by the metrics shown. "
        "Lower-is-better metrics should decrease; higher-is-better should "
        "increase.\n"
        "HARD RULES:\n"
        "- Keep the EXACT function signature.\n"
        "- You may import ONLY: numpy, scipy, sklearn, pandas (already available).\n"
        "- No file I/O, no network, no plotting, no global side effects.\n"
        "- Be correct and self-contained.\n"
        "RESPOND WITH EITHER:\n"
        "  (a) one or more diff blocks (use this exact format):\n"
        "<<<SEARCH>>>\nexact existing code to replace\n<<<REPLACE>>>\nnew code\n<<<END>>>\n"
        "  (b) a single complete rewritten function in one ```python``` block.\n"
        "Prefer small targeted diffs. Output ONLY the diff or code, no explanation."
    )

    # keep SYSTEM alias so any external refs still work
    SYSTEM = BASE_SYSTEM

    def _render_diagnostics(self, m: dict) -> str:
        """Render a metrics dict generically — works for the Phase-2 claim
        metrics ({effect, pvalue}) and for regression metrics (rmse, r2, ...)."""
        if not m:
            return "(no diagnostics available)"
        parts = []
        for k in ("effect", "pvalue", "rmse", "r2", "balanced_accuracy"):
            if k in m:
                try:
                    parts.append(f"{k}={float(m[k]):.4f}")
                except (TypeError, ValueError):
                    parts.append(f"{k}={m[k]}")
        return "  ".join(parts) if parts else "(no diagnostics available)"

    def propose(self, parent_source, parent_metrics, parent_spec, inspirations,
                hints=None, context_level=None):
        """context_level: 'minimal' (parent source only) or 'rich' (source +
        rendered diagnostics + inspirations). hints: extra strategy lines
        appended to the system prompt (meta-prompt co-evolution)."""
        level = context_level or self.context_level
        system = self.task_system if self.task_system else self.BASE_SYSTEM
        if hints:
            system += "\n\nAdditional strategy hints to follow:\n- " + \
                      "\n- ".join(hints)
        msg = []
        if level == "minimal":
            msg.append(f"Current program:\n```python\n{parent_source}\n```")
        else:
            msg.append("Current program and its diagnostics on real held-out "
                       f"data:\n{self._render_diagnostics(parent_metrics)}\n"
                       f"```python\n{parent_source}\n```")
            if inspirations:
                joined = "\n\n---\n\n".join(inspirations)
                msg.append("Inspirations (other, diverse approaches — borrow ideas):\n"
                           f"```python\n{joined}\n```")
        msg.append("Propose an improvement that improves the metric on real "
                   "held-out data. Keep it correct.")
        try:
            self.n_calls += 1
            r = self.client.messages.create(
                model=self.model, max_tokens=self.max_tokens,
                system=system, messages=[{"role": "user",
                                          "content": "\n\n".join(msg)}])
            text = "".join(b.text for b in r.content if hasattr(b, "text"))
            child, mode = apply_diff(parent_source, text, self.entry_point)
            return child, None, {"mode": mode, "raw_len": len(text),
                                 "model": self.model,
                                 "in": getattr(r.usage, "input_tokens", 0),
                                 "out": getattr(r.usage, "output_tokens", 0)}
        except Exception as e:
            self.n_errors += 1
            return None, None, {"error": f"{type(e).__name__}: {str(e)[:120]}",
                                "model": self.model}
