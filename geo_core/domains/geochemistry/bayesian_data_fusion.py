"""Level 15 - Bayesian Data Fusion (GEODISC geochemistry scaffold).

The most valuable capability: infer which hidden processes best explain a
multi-modal observation set (Raman, SEM, TOC, isotopes, Fe-speciation,
mineralogy, stratigraphy, microfossil quality). Essentially Bayesian inversion.
"""
from .base import GeochemistryDomainBase


class BayesianDataFusionDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "bayesian_data_fusion"
    DESCRIPTION = "Multi-modal Bayesian inversion over hidden preservation processes."
    CAPABILITIES = [
        "multi-modal evidence fusion",
        "observation modalities: Raman, SEM, TOC, carbon isotopes, Fe-speciation, "
        "mineralogy, stratigraphy, microfossil quality",
        "Bayesian inversion over hidden processes", "posterior process inference",
        "uncertainty propagation", "model comparison",
    ]
    KEYWORDS = ["Bayesian fusion", "inversion", "multi-modal", "posterior", "uncertainty"]
    DEPENDENCIES = ["spectroscopy", "mineralogy"]


__all__ = ["BayesianDataFusionDomain"]
