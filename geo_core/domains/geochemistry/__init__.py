"""GEODISC geochemistry domain registry (Levels 2-17).

Level 1 (general scientific reasoning) lives in ``geo_core.reasoning`` and
``geo_core.causal`` -- it is the existing domain-independent core, not a domain
module here. The 16 modules below are SCAFFOLDS: import-clean, registered and
queryable now, with each module's ``CAPABILITIES`` checklist acting as the
training roadmap for separate geochemistry training.

Register them all with a DomainRegistry via :func:`register_all`, or import
:data:`ALL_GEODISC_DOMAINS` to use the classes directly.
"""
from .earth_system_science import EarthSystemScienceDomain
from .sedimentology import SedimentologyDomain
from .taphonomy import TaphonomyDomain
from .organic_geochemistry import OrganicGeochemistryDomain
from .mineralogy import MineralogyDomain
from .general_geochemistry import GeneralGeochemistryDomain
from .precambrian_geology import PrecambrianGeologyDomain
from .microbial_ecology import MicrobialEcologyDomain
from .evolution import EvolutionDomain
from .spectroscopy import SpectroscopyDomain
from .thermodynamics import ThermodynamicsDomain
from .statistical_physics import StatisticalPhysicsDomain
from .imaging import ImagingDomain
from .bayesian_data_fusion import BayesianDataFusionDomain
from .philosophy_of_science import PhilosophyOfScienceDomain
from .scientific_literature import ScientificLiteratureDomain

ALL_GEODISC_DOMAINS = [
    EarthSystemScienceDomain,
    SedimentologyDomain,
    TaphonomyDomain,
    OrganicGeochemistryDomain,
    MineralogyDomain,
    GeneralGeochemistryDomain,
    PrecambrianGeologyDomain,
    MicrobialEcologyDomain,
    EvolutionDomain,
    SpectroscopyDomain,
    ThermodynamicsDomain,
    StatisticalPhysicsDomain,
    ImagingDomain,
    BayesianDataFusionDomain,
    PhilosophyOfScienceDomain,
    ScientificLiteratureDomain,
]


def register_all(registry) -> None:
    """Instantiate and register every GEODISC geochemistry domain (Levels 2-17)."""
    import logging
    log = logging.getLogger(__name__)
    for domain_cls in ALL_GEODISC_DOMAINS:
        try:
            registry.register_domain(domain_cls())
        except Exception as e:  # never let one domain break registration
            log.warning(f"Could not register {domain_cls.__name__}: {e}")


__all__ = ["ALL_GEODISC_DOMAINS", "register_all"] + [
    c.__name__ for c in ALL_GEODISC_DOMAINS
]
