"""Level 14 - Imaging (GEODISC geochemistry scaffold).

Fossils become image problems: segmentation, morphometrics, 3D reconstruction.
"""
from .base import GeochemistryDomainBase


class ImagingDomain(GeochemistryDomainBase):
    DOMAIN_NAME = "imaging"
    DESCRIPTION = "Computer vision, segmentation, morphometrics and 3D reconstruction of fossils."
    CAPABILITIES = [
        "computer vision", "segmentation", "morphometrics", "graph extraction",
        "3D reconstruction", "texture analysis",
    ]
    KEYWORDS = ["segmentation", "morphometrics", "3D reconstruction", "computer vision"]
    DEPENDENCIES = []


__all__ = ["ImagingDomain"]
