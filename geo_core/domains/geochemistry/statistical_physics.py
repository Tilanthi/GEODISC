"""Level 13 - Statistical Physics (GEODISC geochemistry scaffold).

Preservation is an emergent process; reaction-diffusion and network theory
apply to mineral encapsulation and decay fronts.
"""
from .base import GeochemistryDomainBase


class StatisticalPhysicsDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "statistical_physics"
    DESCRIPTION = "Emergent / non-equilibrium statistical physics of preservation processes."
    CAPABILITIES = [
        "percolation", "network theory", "reaction-diffusion", "cellular automata",
        "non-equilibrium systems", "complex systems",
    ]
    KEYWORDS = ["percolation", "reaction-diffusion", "non-equilibrium", "complex systems"]
    DEPENDENCIES = []


__all__ = ["StatisticalPhysicsDomain"]
