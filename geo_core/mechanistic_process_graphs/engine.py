"""Mechanistic process-graph inference engine (SCAFFOLD).

``build_from_observations`` / ``refine_with_evidence`` / ``compare_mechanisms``
/ ``explain_preservation`` delegate to ``geo_core.causal`` for structure
learning once populated by training. For now they return scaffold graphs so the
plumbing is wired, import-clean and testable. Geochemistry training fills in
the inference.
"""
from typing import Dict, List, Tuple

from .graph import MechanisticProcessGraph, Evidence


def build_from_observations(observations: Dict[str, float],
                            name: str = "inferred") -> MechanisticProcessGraph:
    """Propose a mechanistic graph from observations.

    SCAFFOLD: registers observations as nodes; structure learning (which
    edges, with which probabilities) is populated by geochemistry training via
    ``geo_core.causal``.
    """
    g = MechanisticProcessGraph(name=name)
    for obs, val in observations.items():
        g.add_node(obs, observed=True, value=val)
    return g


def refine_with_evidence(graph: MechanisticProcessGraph,
                         edge_key: Tuple[str, str],
                         evidence: Evidence,
                         new_probability: float,
                         new_uncertainty: float) -> MechanisticProcessGraph:
    """Bayesian update of one edge: strengthen / weaken / split the link.

    SCAFFOLD: sets the edge posterior directly and appends the evidence. A
    trained implementation will compute the posterior from prior + evidence
    likelihood.
    """
    if edge_key in graph.edges:
        e = graph.edges[edge_key]
        e.probability = new_probability
        e.uncertainty = new_uncertainty
        e.evidence.append(evidence)
    return graph


def compare_mechanisms(a: MechanisticProcessGraph,
                       b: MechanisticProcessGraph) -> Dict[str, float]:
    """Model comparison of two competing mechanistic explanations.

    SCAFFOLD: reports structural summary statistics. A trained implementation
    will return marginal-likelihood / posterior-ratio style scores.
    """
    return {
        "graph_a_nodes": len(a.nodes),
        "graph_b_nodes": len(b.nodes),
        "graph_a_edges": len(a.edges),
        "graph_b_edges": len(b.edges),
    }


def explain_preservation(observations: Dict[str, float] = None) -> MechanisticProcessGraph:
    """GOE use-case: infer which mix of O2 / iron chemistry / mineral adsorption /
    microbial decay / burial rate / thermal maturation best explains the
    observed preservation of both organic carbon and recognizable morphology.

    SCAFFOLD: returns the canonical GOE example chain to keep the plumbing
    testable. A trained implementation performs Bayesian inversion over the
    candidate process set conditioned on ``observations``.
    """
    from .examples import goe_preservation_graph
    g = goe_preservation_graph()
    if observations:
        for obs, val in observations.items():
            if obs in g.nodes:
                g.nodes[obs]["observed"] = True
                g.nodes[obs]["value"] = val
    return g
