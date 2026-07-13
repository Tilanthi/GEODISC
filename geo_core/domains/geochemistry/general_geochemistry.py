"""Level 7 - Geochemistry (GEODISC geochemistry scaffold).

Note: module is 'general_geochemistry' to avoid clashing with this package name.
"""
from .base import GeochemistryDomainBase


class GeneralGeochemistryDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "geochemistry"
    DESCRIPTION = "Redox, Eh-pH, trace-metal and isotope geochemistry with kinetics."
    CAPABILITIES = [
        "redox chemistry", "Eh-pH systems", "iron chemistry", "sulphur chemistry",
        "oxygen chemistry", "trace metals", "equilibrium thermodynamics",
        "reaction kinetics", "stable isotopes",
    ]
    KEYWORDS = ["redox", "Eh-pH", "trace metal", "stable isotope", "kinetics"]
    DEPENDENCIES = []


__all__ = ["GeneralGeochemistryDomain"]
