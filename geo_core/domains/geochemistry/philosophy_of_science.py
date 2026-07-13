"""Level 16 - Philosophy of Science (GEODISC geochemistry scaffold).

Guards against spurious correlations: preservation bias, confounding, and the
necessary-vs-sufficient distinction that is central to the GOE hypothesis.
"""
from .base import GeochemistryDomainBase


class PhilosophyOfScienceDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "philosophy_of_science"
    DESCRIPTION = "Hypothesis testing, causality, confounding and preservation bias."
    CAPABILITIES = [
        "hypothesis testing", "confirmation", "model comparison", "causality",
        "necessary vs sufficient causes", "confounding", "measurement bias",
        "selection bias", "preservation bias",
    ]
    KEYWORDS = ["causality", "confounding", "preservation bias", "necessary vs sufficient"]
    DEPENDENCIES = []


__all__ = ["PhilosophyOfScienceDomain"]
