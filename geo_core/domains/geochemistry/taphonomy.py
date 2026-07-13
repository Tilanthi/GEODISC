"""Level 4 - Taphonomy (GEODISC geochemistry scaffold).

Central discipline for GEODISC: decay, degradation, and the fossilisation
pathways that preserve (or destroy) biology. This is where the oxygenic-
revolution / preservation hypothesis lives.
"""
from .base import GeochemistryDomainBase


class TaphonomyDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "taphonomy"
    DESCRIPTION = "Decay, microbial degradation, and fossilisation / preservation pathways."
    CAPABILITIES = [
        "decay processes", "microbial degradation", "exceptional preservation",
        "fossilisation pathways", "silicification", "pyritisation",
        "phosphatisation", "kerogen formation",
    ]
    KEYWORDS = ["taphonomy", "decay", "fossilisation", "silicification", "pyritisation", "phosphatisation"]
    DEPENDENCIES = ["organic_geochemistry", "mineralogy", "microbial_ecology"]


__all__ = ["TaphonomyDomain"]
