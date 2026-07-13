"""Level 5 - Organic Geochemistry (GEODISC geochemistry scaffold)."""
from .base import GeochemistryDomainBase


class OrganicGeochemistryDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "organic_geochemistry"
    DESCRIPTION = "Kerogen, bitumen, biomarkers, maturation and organic reaction pathways."
    CAPABILITIES = [
        "kerogen", "bitumen", "organic maturation", "aromaticity", "pyrolysis",
        "Raman spectroscopy", "FTIR", "carbon isotopes", "molecular fossils",
        "lipid biomarkers", "hydrocarbons", "thermal maturation", "reaction pathways",
    ]
    KEYWORDS = ["kerogen", "biomarker", "maturation", "isotope", "pyrolysis"]
    DEPENDENCIES = ["general_geochemistry", "mineralogy"]


__all__ = ["OrganicGeochemistryDomain"]
