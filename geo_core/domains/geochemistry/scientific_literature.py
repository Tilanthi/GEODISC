"""Level 17 - Scientific Literature (GEODISC geochemistry scaffold).

Not merely papers but a knowledge graph of scientific debate: who disagrees
with whom, which hypotheses compete, where datasets conflict.
"""
from .base import GeochemistryDomainBase


class ScientificLiteratureDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "scientific_literature"
    DESCRIPTION = "Knowledge graph of competing hypotheses, evidence and dataset conflicts."
    CAPABILITIES = [
        "competing hypotheses", "evidence mapping", "uncertainty location",
        "dataset conflicts", "debate knowledge graph", "citation / influence mapping",
    ]
    KEYWORDS = ["hypothesis competition", "evidence map", "debate graph", "conflict"]
    DEPENDENCIES = []


__all__ = ["ScientificLiteratureDomain"]
