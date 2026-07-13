"""GEODISC geochemistry domain scaffold base (Levels 2-17).

Each geochemistry domain subclasses ``GeochemistryDomainBase``, declaring a
``DOMAIN_NAME``, ``DESCRIPTION``, a ``CAPABILITIES`` checklist (drawn from the
GEODISC domain brief), ``KEYWORDS``, and ``DEPENDENCIES`` on other geo domains.

Subclasses are SKELETONS: :meth:`process_query` is a stub to be populated by
separate geochemistry training. The scaffold exists so the domain layer is
import-clean, registered, and queryable now, with the subtopic checklist acting
as the training roadmap.
"""
from typing import Dict, Any, List

from .. import BaseDomainModule, DomainConfig, DomainQueryResult


class GeochemistryDomainBase(BaseDomainModule):
    """Shared skeleton for all GEODISC geochemistry domains."""

    # --- Declared per concrete domain -------------------------------------
    DOMAIN_NAME: str = "geo_base"
    DESCRIPTION: str = ""
    CAPABILITIES: List[str] = []
    KEYWORDS: List[str] = []
    DEPENDENCIES: List[str] = []      # other geo domain_names this builds on
    TASK_TYPES: List[str] = ["scientific"]
    VERSION: str = "0.1.0"

    # --- BaseDomainModule interface ---------------------------------------
    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name=self.DOMAIN_NAME,
            version=self.VERSION,
            dependencies=list(self.DEPENDENCIES),
            keywords=list(self.KEYWORDS),
            task_types=list(self.TASK_TYPES),
            capabilities=list(self.CAPABILITIES),
            description=self.DESCRIPTION,
            enabled=True,
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """No-op init; geochemistry training populates knowledge later."""
        return None

    def get_capabilities(self) -> List[str]:
        return list(self.CAPABILITIES)

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        caps = list(self.CAPABILITIES)
        shown = ", ".join(caps[:8]) + ("…" if len(caps) > 8 else "")
        return DomainQueryResult(
            domain_name=self.DOMAIN_NAME,
            answer=(
                f"[{self.DOMAIN_NAME}] scaffold only — awaiting geochemistry training. "
                f"Declared capabilities: {shown}"
            ),
            confidence=0.0,
            reasoning_trace=[],
            capabilities_used=[],
            metadata={"trained": False, "capabilities": caps},
        )
