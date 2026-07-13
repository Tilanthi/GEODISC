"""Level 6 - Mineralogy (GEODISC geochemistry scaffold).

Minerals preserve or destroy biology; surface chemistry controls adsorption
and templating of organic matter.
"""
from .base import GeochemistryDomainBase


class MineralogyDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "mineralogy"
    DESCRIPTION = "Minerals and surface chemistry that preserve or destroy biosignatures."
    CAPABILITIES = [
        "clays", "silica", "carbonates", "phosphates", "iron oxides",
        "iron silicates", "sulphides", "surface chemistry", "adsorption",
        "crystal growth",
    ]
    KEYWORDS = ["clay", "silica", "carbonate", "phosphate", "sulphide", "adsorption"]
    DEPENDENCIES = []


__all__ = ["MineralogyDomain"]
