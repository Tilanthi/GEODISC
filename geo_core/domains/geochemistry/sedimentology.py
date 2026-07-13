"""Level 3 - Sedimentology (GEODISC geochemistry scaffold).

Preservation begins during deposition; distinguishing biological from
sedimentological effects requires sedimentological expertise.
"""
from .base import GeochemistryDomainBase


class SedimentologyDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "sedimentology"
    DESCRIPTION = "Sediment transport, deposition, burial, diagenesis and porosity evolution."
    CAPABILITIES = [
        "sediment transport", "facies", "depositional environments", "burial",
        "diagenesis", "compaction", "porosity evolution",
    ]
    KEYWORDS = ["facies", "depositional environment", "diagenesis", "burial", "compaction"]
    DEPENDENCIES = ["earth_system_science"]


__all__ = ["SedimentologyDomain"]
