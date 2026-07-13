"""Level 9 - Microbial Ecology (GEODISC geochemistry scaffold).

Before animals, life is microbes; microbial metabolism drives decay and
mineral precipitation.
"""
from .base import GeochemistryDomainBase


class MicrobialEcologyDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "microbial_ecology"
    DESCRIPTION = "Microbial metabolisms, mats, biofilms and EPS that mediate preservation."
    CAPABILITIES = [
        "cyanobacteria", "methanogens", "iron reducers", "iron oxidisers",
        "sulphur bacteria", "biofilms", "EPS", "microbial mats", "microbial metabolism",
    ]
    KEYWORDS = ["cyanobacteria", "methanogen", "biofilm", "EPS", "microbial mat"]
    DEPENDENCIES = []


__all__ = ["MicrobialEcologyDomain"]
