"""Level 2 - Earth System Science (GEODISC geochemistry scaffold).

Earth as one coupled dynamical system: atmosphere, oceans, crust, mantle,
biosphere, sedimentary cycles as one interacting network.
"""
from .base import GeochemistryDomainBase


class EarthSystemScienceDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "earth_system_science"
    DESCRIPTION = "Coupled Earth-system dynamics across atmosphere, ocean, crust, mantle, biosphere."
    CAPABILITIES = [
        "biogeochemical cycles", "Earth system feedbacks", "weathering",
        "volcanism", "hydrothermal systems", "nutrient cycling", "tectonics",
        "carbon cycle", "sulphur cycle", "phosphorus cycle", "iron cycle",
    ]
    KEYWORDS = ["earth system", "biogeochemistry", "feedback", "weathering", "volcanism"]
    DEPENDENCIES = []


__all__ = ["EarthSystemScienceDomain"]
