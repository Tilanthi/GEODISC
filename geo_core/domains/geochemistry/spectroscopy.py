"""Level 11 - Spectroscopy & Analytical Instrumentation (GEODISC geochemistry scaffold)."""
from .base import GeochemistryDomainBase


class SpectroscopyDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "spectroscopy"
    DESCRIPTION = "Analytical instrumentation: Raman, FTIR, XRD, SEM, TEM, NanoSIMS, XANES, STXM."
    CAPABILITIES = [
        "Raman", "FTIR", "XRD", "SEM", "TEM", "NanoSIMS", "XANES", "STXM",
        "spectral inversion", "signal processing", "peak fitting", "ML on spectra",
    ]
    KEYWORDS = ["Raman", "FTIR", "XANES", "STXM", "NanoSIMS", "spectral inversion"]
    DEPENDENCIES = []


__all__ = ["SpectroscopyDomain"]
