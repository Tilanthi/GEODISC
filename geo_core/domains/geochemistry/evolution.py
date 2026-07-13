"""Level 10 - Evolution (GEODISC geochemistry scaffold).

Not only Darwinian evolution: the origin of oxygenic photosynthesis and the
metabolic / ecosystem revolutions that frame the preservation question.
"""
from .base import GeochemistryDomainBase


class EvolutionDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "evolution"
    DESCRIPTION = "Origin of oxygenic photosynthesis and molecular/metabolic/ecosystem evolution."
    CAPABILITIES = [
        "origin of oxygenic photosynthesis", "molecular evolution",
        "genome evolution", "metabolic evolution", "ecosystem evolution",
    ]
    KEYWORDS = ["oxygenic photosynthesis", "molecular evolution", "metabolic evolution"]
    DEPENDENCIES = ["microbial_ecology"]


__all__ = ["EvolutionDomain"]
