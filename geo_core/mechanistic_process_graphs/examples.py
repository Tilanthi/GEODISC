"""Canonical GOE preservation mechanistic graph (the GEODISC headline example).

    Low O2 -> Microbial respiration -> Decay rate -> Cell wall integrity
           -> Silica nucleation -> Mineral encapsulation -> Morphological preservation

Each edge carries a placeholder probability / uncertainty to be refined by
geochemistry training and Bayesian data fusion.
"""
from .graph import MechanisticProcessGraph


def goe_preservation_graph() -> MechanisticProcessGraph:
    """The canonical Great Oxidation / preservation mechanistic chain."""
    g = MechanisticProcessGraph(name="goe_preservation")
    chain = [
        "low_O2",
        "microbial_respiration",
        "decay_rate",
        "cell_wall_integrity",
        "silica_nucleation",
        "mineral_encapsulation",
        "morphological_preservation",
    ]
    for n in chain:
        g.add_node(n)
    for src, dst in zip(chain, chain[1:]):
        g.add_edge(src, dst, probability=0.5, uncertainty=0.5, mechanistic_type="rate-limiting")
    return g


def _doctest():
    r"""Doctests for the GOE example graph.

    >>> g = goe_preservation_graph()
    >>> [n for n in g.nodes]
    ['low_O2', 'microbial_respiration', 'decay_rate', 'cell_wall_integrity', 'silica_nucleation', 'mineral_encapsulation', 'morphological_preservation']
    >>> len(g.edges)
    6
    >>> g.chain_to('morphological_preservation')[-1][-1]
    'morphological_preservation'
    >>> g.chain_to('morphological_preservation')[0][0]
    'low_O2'
    """
    import doctest
    doctest.testmod()


if __name__ == "__main__":
    _doctest()
