"""GEODISC mechanistic process-graph capability.

Represents scientific statements as components of a causal-mechanistic network
in which every edge carries probability, uncertainty, and supporting evidence.
New data strengthens, weakens, or splits causal links, enabling comparison of
competing MECHANISTIC explanations rather than the fitting of statistical
correlations.

This is where GEODISC's central scientific advantage lives: shifting focus from
pattern recognition to mechanism discovery (e.g. inferring which combination of
oxygen availability, iron chemistry, mineral adsorption, microbial decay,
burial rate, and thermal maturation best explains observed fossil preservation).
"""
from .graph import MechanisticProcessGraph, MechanisticEdge, Evidence
from .engine import (
    build_from_observations,
    refine_with_evidence,
    compare_mechanisms,
    explain_preservation,
)
from .examples import goe_preservation_graph

__all__ = [
    "MechanisticProcessGraph",
    "MechanisticEdge",
    "Evidence",
    "build_from_observations",
    "refine_with_evidence",
    "compare_mechanisms",
    "explain_preservation",
    "goe_preservation_graph",
]
