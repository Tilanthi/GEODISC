"""Level 8 - Precambrian Geology (GEODISC geochemistry scaffold)."""
from .base import GeochemistryDomainBase


class PrecambrianGeologyDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "precambrian_geology"
    DESCRIPTION = "Archean-Proterozoic geology, GOE, Snowball Earth, BIFs, stromatolites."
    CAPABILITIES = [
        "Archean", "Paleoproterozoic", "GOE", "Snowball Earth",
        "banded iron formations", "greenstone belts", "shales", "stromatolites",
        "major formations", "geological timescales",
    ]
    KEYWORDS = ["archean", "proterozoic", "GOE", "BIF", "stromatolite", "snowball"]
    DEPENDENCIES = ["earth_system_science"]


__all__ = ["PrecambrianGeologyDomain"]
