"""Level 12 - Thermodynamics (GEODISC geochemistry scaffold)."""
from .base import GeochemistryDomainBase


class ThermodynamicsDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "thermodynamics"
    DESCRIPTION = "Chemical thermodynamics and kinetics governing diagenesis and maturation."
    CAPABILITIES = [
        "chemical potentials", "entropy", "phase diagrams", "kinetics",
        "diffusion", "reaction networks", "equilibrium", "irreversibility",
    ]
    KEYWORDS = ["chemical potential", "entropy", "phase diagram", "kinetics", "equilibrium"]
    DEPENDENCIES = []


__all__ = ["ThermodynamicsDomain"]
