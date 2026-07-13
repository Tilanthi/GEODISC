"""Mechanistic process-graph data model for GEODISC.

Nodes are mechanistic steps / state variables. Edges carry probability,
uncertainty, supporting evidence, and a mechanistic type -- so the graph
represents MECHANISM (not mere statistical correlation). Designed to compose
with ``geo_core.causal`` (structural causal models + do-calculus).

This is the headline novel capability: instead of treating scientific statements
as isolated facts, represent them as components of a causal-mechanistic network
where every edge carries probability, uncertainty, and supporting evidence.
New data strengthens, weakens, or splits causal links, letting the system
compare competing MECHANISTIC explanations rather than fit statistical
correlations.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Evidence:
    """A single piece of evidence supporting (or weakening) an edge."""
    source: str                       # e.g. "Raman D-band", "Fe-speciation", "literature:Smith2010"
    weight: float = 1.0               # relative evidential weight
    note: str = ""


@dataclass
class MechanisticEdge:
    """A directed mechanistic causal link between two process nodes."""
    source: str
    target: str
    probability: float = 0.5         # P(target active | source active)
    uncertainty: float = 0.5         # 0 = certain, 1 = complete ignorance
    mechanistic_type: str = "unknown"  # e.g. "catalytic", "inhibitory", "rate-limiting"
    evidence: List[Evidence] = field(default_factory=list)

    def posterior(self) -> Dict[str, float]:
        return {"probability": self.probability, "uncertainty": self.uncertainty}


@dataclass
class MechanisticProcessGraph:
    """A directed graph of mechanistic process steps."""
    name: str
    nodes: Dict[str, dict] = field(default_factory=dict)                # node_id -> attributes
    edges: Dict[Tuple[str, str], MechanisticEdge] = field(default_factory=dict)

    def add_node(self, node_id: str, **attrs) -> None:
        self.nodes[node_id] = attrs

    def add_edge(self, src: str, dst: str, **edge_attrs) -> MechanisticEdge:
        e = MechanisticEdge(source=src, target=dst, **edge_attrs)
        self.edges[(src, dst)] = e
        return e

    def predecessors(self, node_id: str) -> List[str]:
        return [s for (s, d) in self.edges if d == node_id]

    def chain_to(self, target: str) -> List[List[str]]:
        """Return all simple causal chains ending at ``target`` (ancestral paths).

        Each chain is a list of node ids from an upstream root down to ``target``.
        """
        preds = self.predecessors(target)
        if not preds:
            return [[target]]
        chains: List[List[str]] = []
        for p in preds:
            for upstream in self.chain_to(p):
                chains.append(upstream + [target])
        return chains
