"""
Theory-Space Mapper

Maps and navigates the space of theoretical frameworks, treating theories
as points in a mathematical space and discovering connections between them.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx


class TheoryType(Enum):
    """Types of theoretical frameworks"""
    ANALYTICAL = "analytical"
    NUMERICAL = "numerical"
    PHENOMENOLOGICAL = "phenomenological"
    FUNDAMENTAL = "fundamental"
    EFFECTIVE = "effective"
    APPROXIMATION = "approximation"


class TheoryRelation(Enum):
    """Types of relationships between theories"""
    LIMITING_CASE = "limiting_case"  # Theory A reduces to Theory B in some limit
    DUALITY = "duality"  # Mathematical equivalence between descriptions
    GENERALIZATION = "generalization"  # Theory A contains Theory B
    APPROXIMATION = "approximation"  # Theory B approximates Theory A
    UNIFICATION = "unification"  # Theory C unifies A and B
    CONTRADICTION = "contradiction"  # Theories make incompatible predictions
    COMPLEMENTARY = "complementary"  # Theories describe different aspects


@dataclass
class TheoryFramework:
    """A theoretical framework"""
    name: str
    description: str
    theory_type: TheoryType
    domains: List[str]
    key_equations: List[str]
    assumptions: List[str]
    predictions: List[str]
    limitations: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)

    def get_signature(self) -> str:
        """Get a unique signature for this theory"""
        key_elements = sorted(self.assumptions + self.key_equations)
        return f"{self.name}:" + ":".join(key_elements[:3])


@dataclass
class TheoryConnection:
    """A relationship between two theories"""
    theory_a: str
    theory_b: str
    relation_type: TheoryRelation
    strength: float  # 0-1, how strong is the connection
    description: str
    mathematical_form: Optional[str] = None
    conditions: List[str] = field(default_factory=list)


class TheorySpaceMapper:
    """
    Maps and navigates the space of theoretical frameworks.

    This enables GEODISC to:
    - Discover connections between theories
    - Find unifying frameworks
    - Identify limiting cases
    - Generate novel theoretical combinations
    """

    def __init__(self):
        self.theories = {}  # name -> TheoryFramework
        self.connections = []  # List of TheoryConnection
        self.theory_graph = nx.DiGraph()

        # Initialize with known astrophysical theories
        self._initialize_known_theories()

    def _initialize_known_theories(self):
        """Initialize with well-known astrophysical theories"""

        # Fluid dynamics theories
        self.add_theory(TheoryFramework(
            name="Euler_Equations",
            description="Inviscid fluid equations",
            theory_type=TheoryType.FUNDAMENTAL,
            domains=["fluid_dynamics", "astrophysics"],
            key_equations=[
                "∂ρ/∂t + ∇·(ρv) = 0",
                "ρ(∂v/∂t + v·∇v) = -∇P"
            ],
            assumptions=["Inviscid flow", "No heat conduction"],
            predictions=["Conservation of mass and momentum"],
            limitations=["Cannot describe viscous effects"]
        ))

        self.add_theory(TheoryFramework(
            name="Navier_Stokes",
            description="Viscous fluid equations",
            theory_type=TheoryType.FUNDAMENTAL,
            domains=["fluid_dynamics"],
            key_equations=[
                "∂ρ/∂t + ∇·(ρv) = 0",
                "ρ(∂v/∂t + v·∇v) = -∇P + μ∇²v"
            ],
            assumptions=["Newtonian viscosity", "Incompressible or compressible"],
            predictions=["Viscous dissipation", "Boundary layers"],
            limitations=["Turbulence requires closure models"]
        ))

        # Stellar structure
        self.add_theory(TheoryFramework(
            name="Polytropic_Model",
            description="Polytropic equation of state for stars",
            theory_type=TheoryType.ANALYTICAL,
            domains=["stellar_structure", "astrophysics"],
            key_equations=["P = Kρ^(1+1/n)"],
            assumptions=["Polytropic relation", "Hydrostatic equilibrium"],
            predictions=["Lane-Emden equation solutions"],
            limitations=["Simplified EOS"]
        ))

        # Black hole physics
        self.add_theory(TheoryFramework(
            name="Schwarzschild_Metric",
            description="Non-rotating black hole solution",
            theory_type=TheoryType.FUNDAMENTAL,
            domains=["general_relativity", "black_holes"],
            key_equations=[
                "ds² = -(1-2GM/rc²)dt² + (1-2GM/rc²)⁻¹dr² + r²dΩ²"
            ],
            assumptions=["Spherical symmetry", "No rotation", "Vacuum"],
            predictions=["Event horizon at r=2GM/c²"],
            limitations=["No spin, no charge"]
        ))

        self.add_theory(TheoryFramework(
            name="Kerr_Metric",
            description="Rotating black hole solution",
            theory_type=TheoryType.FUNDAMENTAL,
            domains=["general_relativity", "black_holes"],
            key_equations=["Kerr line element with parameters a, M"],
            assumptions=["Axisymmetry", "Stationary", "Vacuum"],
            predictions=["Frame dragging", "Ergosphere"],
            limitations=["No magnetic fields"]
        ))

        # Establish known connections
        self.add_connection(TheoryConnection(
            theory_a="Euler_Equations",
            theory_b="Navier_Stokes",
            relation_type=TheoryRelation.LIMITING_CASE,
            strength=0.95,
            description="Navier-Stokes reduces to Euler when μ → 0"
        ))

        self.add_connection(TheoryConnection(
            theory_a="Schwarzschild_Metric",
            theory_b="Kerr_Metric",
            relation_type=TheoryRelation.LIMITING_CASE,
            strength=0.9,
            description="Schwarzschild is limit of Kerr as a → 0"
        ))

    def add_theory(self, theory: TheoryFramework):
        """Add a theory framework to the space"""
        self.theories[theory.name] = theory
        self.theory_graph.add_node(theory.name, theory=theory)

    def add_connection(self, connection: TheoryConnection):
        """Add a connection between theories"""
        self.connections.append(connection)
        self.theory_graph.add_edge(
            connection.theory_a,
            connection.theory_b,
            relation=connection
        )

    def construct_theory_space(self, domains: List[str]) -> nx.DiGraph:
        """
        Build network of theories in specified domains.

        Args:
            domains: Physics domains of interest

        Returns:
            NetworkX graph of theory space
        """
        # Filter theories by domain
        relevant_theories = {}
        for name, theory in self.theories.items():
            if any(domain in theory.domains for domain in domains):
                relevant_theories[name] = theory

        # Build subgraph
        subgraph = self.theory_graph.subgraph(relevant_theories.keys())

        return subgraph

    def discover_connections(
        self,
        theory_a: str,
        theory_b: str
    ) -> List[TheoryConnection]:
        """
        Find mathematical bridges between two theories.

        Args:
            theory_a: First theory name
            theory_b: Second theory name

        Returns:
            List of discovered connections
        """
        connections = []

        # Check if direct connection exists
        if self.theory_graph.has_edge(theory_a, theory_b):
            connections.append(self.theory_graph[theory_a][theory_b]['relation'])

        # Look for intermediate theories
        try:
            shortest_path = nx.shortest_path(
                self.theory_graph,
                theory_a,
                theory_b
            )

            if len(shortest_path) > 2:
                # Create connection through intermediate theory
                intermediate = shortest_path[1]
                connections.append(TheoryConnection(
                    theory_a=theory_a,
                    theory_b=theory_b,
                    relation_type=TheoryRelation.COMPLEMENTARY,
                    strength=0.5,
                    description=f"Connected through {intermediate}",
                    conditions=[f"Via {intermediate}"]
                ))
        except nx.NetworkXNoPath:
            pass

        # Look for mathematical similarities
        theory_a_obj = self.theories.get(theory_a)
        theory_b_obj = self.theories.get(theory_b)

        if theory_a_obj and theory_b_obj:
            # Check for shared assumptions
            shared_assumptions = set(theory_a_obj.assumptions) & \
                                set(theory_b_obj.assumptions)

            if shared_assumptions:
                connections.append(TheoryConnection(
                    theory_a=theory_a,
                    theory_b=theory_b,
                    relation_type=TheoryRelation.COMPLEMENTARY,
                    strength=len(shared_assumptions) / max(
                        len(theory_a_obj.assumptions),
                        len(theory_b_obj.assumptions)
                    ),
                    description=f"Shared assumptions: {shared_assumptions}"
                ))

        return connections

    def generate_theory_hypotheses(
        self,
        problem_domain: Dict[str, Any]
    ) -> List[TheoryFramework]:
        """
        Propose novel theoretical frameworks by combining
        elements from existing theories.

        Args:
            problem_domain: Description of the problem domain

        Returns:
            List of novel theory proposals
        """
        hypotheses = []

        # Get relevant existing theories
        domain_names = problem_domain.get('domains', [])
        relevant_theories = [
            t for t in self.theories.values()
            if any(d in t.domains for d in domain_names)
        ]

        if len(relevant_theories) < 2:
            return hypotheses

        # Generate combinations
        for i, theory_a in enumerate(relevant_theories):
            for theory_b in relevant_theories[i+1:]:
                # Look for complementary strengths
                novel_theory = self._combine_theories(theory_a, theory_b, problem_domain)
                if novel_theory:
                    hypotheses.append(novel_theory)

        return hypotheses

    def _combine_theories(
        self,
        theory_a: TheoryFramework,
        theory_b: TheoryFramework,
        context: Dict[str, Any]
    ) -> Optional[TheoryFramework]:
        """Combine two theories to create a novel framework"""

        # Check if theories are compatible
        a_assumptions = set(theory_a.assumptions)
        b_assumptions = set(theory_b.assumptions)

        # Check for contradictions
        contradictions = self._find_contradictions(theory_a, theory_b)
        if contradictions:
            # Theories might not be directly compatible
            # Try to find a subset that works
            pass

        # Create combined theory
        combined_name = f"{theory_a.name}_x_{theory_b.name}"
        combined_equations = theory_a.key_equations + theory_b.key_equations

        # Remove duplicate equations
        combined_equations = list(set(combined_equations))

        novel_theory = TheoryFramework(
            name=combined_name,
            description=f"Combined framework integrating {theory_a.name} and {theory_b.name}",
            theory_type=TheoryType.EFFECTIVE,
            domains=list(set(theory_a.domains + theory_b.domains)),
            key_equations=combined_equations,
            assumptions=list(a_assumptions | b_assumptions),
            predictions=theory_a.predictions + theory_b.predictions,
            limitations=theory_a.limitations + theory_b.limitations + ["Combined theory needs validation"]
        )

        return novel_theory

    def _find_contradictions(
        self,
        theory_a: TheoryFramework,
        theory_b: TheoryFramework
    ) -> List[str]:
        """Find contradictions between two theories"""
        contradictions = []

        # Check for mutually exclusive assumptions
        incompatible_pairs = [
            ("inviscid", "viscous"),
            ("incompressible", "compressible"),
            ("spherical", "axisymmetric"),
            ("static", "time-dependent"),
            ("quantum", "classical"),
        ]

        a_assumptions_lower = [a.lower() for a in theory_a.assumptions]
        b_assumptions_lower = [a.lower() for a in theory_b.assumptions]

        for pair in incompatible_pairs:
            if pair[0] in a_assumptions_lower and pair[1] in b_assumptions_lower:
                contradictions.append(f"Incompatible: {pair[0]} vs {pair[1]}")
            elif pair[1] in a_assumptions_lower and pair[0] in b_assumptions_lower:
                contradictions.append(f"Incompatible: {pair[1]} vs {pair[0]}")

        return contradictions

    def find_limiting_cases(
        self,
        theory_name: str
    ) -> List[Dict[str, Any]]:
        """
        Find limiting cases where a theory reduces to simpler forms.

        Args:
            theory_name: Theory to analyze

        Returns:
            List of limiting cases with conditions
        """
        limiting_cases = []

        theory = self.theories.get(theory_name)
        if not theory:
            return limiting_cases

        # Check connections for LIMITING_CASE relations
        for conn in self.connections:
            if conn.theory_a == theory_name and \
               conn.relation_type == TheoryRelation.LIMITING_CASE:
                limiting_cases.append({
                    'limit': conn.theory_b,
                    'conditions': conn.conditions,
                    'description': conn.description
                })
            elif conn.theory_b == theory_name and \
                 conn.relation_type == TheoryRelation.LIMITING_CASE:
                limiting_cases.append({
                    'limit': conn.theory_a,
                    'conditions': conn.conditions,
                    'description': conn.description
                })

        return limiting_cases

    def find_unifying_frameworks(
        self,
        theories: List[str]
    ) -> List[TheoryFramework]:
        """
        Find frameworks that unify multiple theories.

        Args:
            theories: List of theory names to unify

        Returns:
            List of unifying frameworks
        """
        unifiers = []

        # Look for existing theories that are generalizations
        for theory_name, theory in self.theories.items():
            if theory.theory_type == TheoryType.FUNDAMENTAL:
                # Check if this could unify the given theories
                could_unify = True
                for t in theories:
                    if t not in [c.theory_b for c in self.connections
                                if c.theory_a == theory_name and
                                c.relation_type == TheoryRelation.GENERALIZATION]:
                        could_unify = False
                        break

                if could_unify:
                    unifiers.append(theory)

        return unifiers

    def map_theory_space(
        self,
        query: str,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Map relevant theory space for a given query.

        Args:
            query: Scientific query or problem
            max_depth: Maximum depth of theory exploration

        Returns:
            Mapped theory space with relevant theories and connections
        """
        # Parse query to identify relevant physics
        relevant_domains = self._identify_domains_from_query(query)
        relevant_theories = self._identify_theories_from_query(query)

        # Construct theory space
        theory_graph = self.construct_theory_space(relevant_domains)

        # Find connections between relevant theories
        connections = []
        for i, theory_a in enumerate(relevant_theories):
            for theory_b in relevant_theories[i+1:]:
                conns = self.discover_connections(theory_a, theory_b)
                connections.extend(conns)

        return {
            'query': query,
            'relevant_domains': relevant_domains,
            'relevant_theories': relevant_theories,
            'theory_graph': theory_graph,
            'connections': connections,
            'suggested_combinations': self._suggest_theory_combinations(
                relevant_theories, relevant_domains
            )
        }

    def _identify_domains_from_query(self, query: str) -> List[str]:
        """Identify physics domains from query text"""
        query_lower = query.lower()

        domain_keywords = {
            'fluid_dynamics': ['fluid', 'flow', 'turbulence', 'viscous', 'shock', 'accretion'],
            'stellar_structure': ['star', 'stellar', 'main sequence', 'giant', 'dwarf'],
            'black_holes': ['black hole', 'schwarzschild', 'kerr', 'event horizon'],
            'general_relativity': ['gravitational', 'metric', 'curvature', 'relativ'],
            'thermodynamics': ['temperature', 'heat', 'entropy', 'pressure'],
            'electromagnetism': ['magnetic', 'electric', 'radiation', 'field'],
            'quantum_mechanics': ['quantum', 'wave function', 'uncertainty'],
        }

        domains = []
        for domain, keywords in domain_keywords.items():
            if any(kw in query_lower for kw in keywords):
                domains.append(domain)

        return domains if domains else ['astrophysics']

    def _identify_theories_from_query(self, query: str) -> List[str]:
        """Identify relevant theories from query"""
        query_lower = query.lower()
        relevant = []

        theory_keywords = {
            'Euler_Equations': ['euler', 'inviscid', 'ideal fluid'],
            'Navier_Stokes': ['navier', 'stokes', 'viscous', 'viscosity'],
            'Polytropic_Model': ['polytrope', 'lane-emden'],
            'Schwarzschild_Metric': ['schwarzschild', 'non-rotating', 'static black hole'],
            'Kerr_Metric': ['kerr', 'rotating black hole', 'spin'],
        }

        for theory, keywords in theory_keywords.items():
            if any(kw in query_lower for kw in keywords):
                relevant.append(theory)

        return relevant

    def _suggest_theory_combinations(
        self,
        theories: List[str],
        domains: List[str]
    ) -> List[str]:
        """Suggest potentially useful theory combinations"""
        combinations = []

        if len(theories) >= 2:
            for i, theory_a in enumerate(theories):
                for theory_b in theories[i+1:]:
                    combinations.append(f"{theory_a} + {theory_b}")

        return combinations


# Factory function
def create_theory_space_mapper() -> TheorySpaceMapper:
    """Factory function to create theory space mapper"""
    return TheorySpaceMapper()
