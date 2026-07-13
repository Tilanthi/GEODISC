"""
V106 Explainable Causal Reasoning - Natural Language Explanations from Causal Graphs
===================================================================================

PROBLEM: Causal graphs (PAGs from V98) are not interpretable by astronomers.
Need to translate:
- X --> Y (directed edge)
- X <-> Y (bidirected - latent confounder)
- X o-o Y (uncertain)

into natural language explanations with physical meaning.

SOLUTION: Explainable Causal Reasoning with:
1. Causal Story Generator - Convert PAGs to narratives
2. Question Answering - "Why does X cause Y?"
3. Visualization Engine - Interactive causal graph exploration
4. Physical Interpretation - Map causal relations to astrophysics

INTEGRATION:
- Uses V98 FCI output (PAGs) as input
- Integrates with V103 (multi-modal evidence for explanations)
- Works with V4.0 MCE (contextualizes explanations)
- Produces output for V107 (triage and prioritization)

USE CASES:
- Explain Jeans mass --> SFR causal relationship
- Why N(H2) threshold is a proxy, not direct cause
- Explain feedback loops in AGN variability

Date: 2026-04-14
Version: 1.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
import json


class CausalRelationshipType(Enum):
    """Types of causal relationships"""
    DIRECT_CAUSATION = "direct_causation"
    CORRELATION_WITHOUT_CAUSATION = "correlation_without_causation"
    PROXY_RELATIONSHIP = "proxy_relationship"
    CONFOUNDED_RELATIONSHIP = "confounded_relationship"
    FEEDBACK_LOOP = "feedback_loop"
    UNCERTAIN_RELATIONSHIP = "uncertain_relationship"


class CausalExplanation:
    """Natural language explanation of a causal relationship"""

    def __init__(
        self,
        source: str,
        target: str,
        relationship_type: CausalRelationshipType,
        strength: float,
        confidence: float,
        mechanism: str = "",
        evidence: List[str] = None
    ):
        self.source = source
        self.target = target
        self.relationship_type = relationship_type
        self.strength = strength
        self.confidence = confidence
        self.mechanism = mechanism
        self.evidence = evidence or []

    def to_natural_language(self) -> str:
        """Convert to natural language explanation"""
        if self.relationship_type == CausalRelationshipType.DIRECT_CAUSATION:
            return self._explain_direct_causation()
        elif self.relationship_type == CausalRelationshipType.PROXY_RELATIONSHIP:
            return self._explain_proxy_relationship()
        elif self.relationship_type == CausalRelationshipType.CONFOUNDED_RELATIONSHIP:
            return self._explain_confounded_relationship()
        elif self.relationship_type == CausalRelationshipType.FEEDBACK_LOOP:
            return self._explain_feedback_loop()
        else:
            return self._explain_uncertain_relationship()

    def _explain_direct_causation(self) -> str:
        """Explain direct causation"""
        strength_desc = self._describe_strength(self.strength)
        conf_desc = self._describe_confidence(self.confidence)

        explanation = (
            f"{self.source} causes {self.target} {strength_desc}. "
            f"This is a direct causal relationship {conf_desc}. "
        )

        if self.mechanism:
            explanation += f"The mechanism: {self.mechanism}."

        return explanation

    def _explain_proxy_relationship(self) -> str:
        """Explain proxy relationship"""
        return (
            f"{self.source} correlates with {self.target} but is not directly causal. "
            f"The correlation exists because both are causally related to a third variable. "
            f"Treat {self.source} as a proxy indicator for {self.target}, not a cause."
        )

    def _explain_confounded_relationship(self) -> str:
        """Explain confounded relationship"""
        return (
            f"The relationship between {self.source} and {self.target} is confounded. "
            f"This means that the observed correlation may be due to hidden (latent) variables "
            f"that affect both {self.source} and {self.target}. "
            f"Additional data is needed to identify these confounders."
        )

    def _explain_feedback_loop(self) -> str:
        """Explain feedback loop"""
        return (
            f"{self.source} and {self.target} are engaged in a feedback loop. "
            f"{self.source} affects {self.target}, which in turn affects {self.source} "
            f"creating a cycle. This indicates the system self-regulates through these interactions."
        )

    def _explain_uncertain_relationship(self) -> str:
        """Explain uncertain relationship"""
        return (
            f"The causal direction between {self.source} and {self.target} is uncertain "
            f"given current data. The observed correlation could mean {self.source} → {self.target}, "
            f"{self.target} → {self.source}, or both are caused by hidden variables."
        )

    def _describe_strength(self, strength: float) -> str:
        """Describe causal strength"""
        if abs(strength) > 0.8:
            return "(very strong relationship)"
        elif abs(strength) > 0.5:
            return "(strong relationship)"
        elif abs(strength) > 0.3:
            return "(moderate relationship)"
        elif abs(strength) > 0.1:
            return "(weak relationship)"
        else:
            return "(very weak relationship)"

    def _describe_confidence(self, confidence: float) -> str:
        """Describe confidence level"""
        if confidence > 0.9:
            return "with very high confidence"
        elif confidence > 0.7:
            return "with high confidence"
        elif confidence > 0.5:
            return "with moderate confidence"
        elif confidence > 0.3:
            return "with low confidence"
        else:
            return "with very low confidence"


class CausalStoryGenerator:
    """
    Converts PAGs into narrative explanations.

    Generates coherent stories about causal mechanisms.
    """

    def __init__(self):
        """Initialize causal story generator"""

    def generate_story(
        self,
        pag_edges: List,
        variable_descriptions: Dict[str, str],
        domain_context: str = ""
    ) -> str:
        """
        Generate causal story from PAG edges.

        Args:
            pag_edges: List of PAGEdge or TimeLaggedPAGEdge
            variable_descriptions: Dict mapping variable names to descriptions
            domain_context: Domain-specific context

        Returns:
            Narrative story explaining causal relationships
        """
        story_lines = []
        story_lines.append(f"=== CAUSAL ANALYSIS: {domain_context} ===\n")

        # Group by relationship type
        direct_edges = []
        proxy_edges = []
        confounded_edges = []
        feedback_edges = []
        uncertain_edges = []

        for edge in pag_edges:
            # Determine relationship type
            is_bidirected = hasattr(edge, 'is_bidirected') and edge.is_bidirected()
            has_latent = hasattr(edge, 'has_latent_confounding') and edge.has_latent_confounding()

            if is_bidirected:
                feedback_edges.append(edge)
            elif has_latent:
                confounded_edges.append(edge)
            elif hasattr(edge, 'source_end') and edge.source_end.value == 'tail' and edge.target_end.value == 'arrow':
                direct_edges.append(edge)
            else:
                uncertain_edges.append(edge)

        # Direct causal relationships
        if direct_edges:
            story_lines.append("\nDIRECT CAUSAL RELATIONSHIPS:\n")
            for edge in direct_edges[:5]:  # Limit to first 5
                story_lines.append(self._explain_single_edge(edge, variable_descriptions))

        # Proxy relationships
        if proxy_edges:
            story_lines.append("\nPROXY RELATIONSHIPS (Correlation ≠ Causation):\n")
            for edge in proxy_edges[:5]:
                story_lines.append(self._explain_single_edge(edge, variable_descriptions))

        # Confounded relationships
        if confounded_edges:
            story_lines.append("\nCONFOUNDED RELATIONSHIPS (Unclear Causality):\n")
            for edge in confounded_edges[:5]:
                story_lines.append(self._explain_single_edge(edge, variable_descriptions))

        # Feedback loops
        if feedback_edges:
            story_lines.append("\nFEEDBACK LOOPS:\n")
            for edge in feedback_edges[:5]:
                story_lines.append(self._explain_single_edge(edge, variable_descriptions))

        # Uncertain relationships
        if uncertain_edges:
            story_lines.append("\nUNCERTAIN RELATIONSHIPS:\n")
            for edge in uncertain_edges[:5]:
                story_lines.append(self._explain_single_edge(edge, variable_descriptions))

        return "\n".join(story_lines)

    def _describe_confidence(self, confidence: float) -> str:
        """Describe confidence level"""
        if confidence > 0.9:
            return "(very high confidence)"
        elif confidence > 0.7:
            return "(high confidence)"
        elif confidence > 0.5:
            return "(moderate confidence)"
        elif confidence > 0.3:
            return "(low confidence)"
        else:
            return "(very low confidence)"

    def _explain_single_edge(
        self,
        edge: Any,
        variable_descriptions: Dict[str, str]
    ) -> str:
        """Generate explanation for a single edge"""
        source_desc = variable_descriptions.get(edge.source, edge.source)
        target_desc = variable_descriptions.get(edge.target, edge.target)

        if hasattr(edge, 'lag'):
            lag_info = f" with {edge.lag} time-step lag"
        else:
            lag_info = ""

        # Get confidence
        confidence = getattr(edge, 'confidence', 1.0)
        conf_desc = self._describe_confidence(confidence)

        return f"  • {source_desc} → {target_desc}{lag_info} {conf_desc}"


class ExplainableCausalReasoner:
    """
    Main orchestrator for explainable causal reasoning.

    Takes PAGs as input and generates:
    - Natural language explanations
    - Q&A interface
    - Visualization preparation
    """

    def __init__(self):
        """Initialize explainable causal reasoner"""
        self.story_gen = CausalStoryGenerator()

    def explain_pag(
        self,
        pag: Any,
        variable_descriptions: Optional[Dict[str, str]] = None,
        domain_context: str = ""
    ) -> Dict[str, Any]:
        """
        Generate comprehensive explanation of a PAG.

        Args:
            pag: Partial Ancestral Graph (from V98 FCI)
            variable_descriptions: Optional variable name → description mapping
            domain_context: Domain context for explanation

        Returns:
            Dictionary with explanation components
        """
        # Default variable descriptions
        if variable_descriptions is None:
            variable_descriptions = {}

        # Extract edges from PAG
        if hasattr(pag, 'edges'):
            edges = pag.edges
        else:
            edges = []

        # Generate story
        story_gen = CausalStoryGenerator()
        story = story_gen.generate_story(edges, variable_descriptions, domain_context)

        # Generate explanations for each edge
        explanations = []
        for edge in edges[:10]:  # Limit to first 10
            explanation = CausalExplanation(
                source=edge.source,
                target=edge.target,
                relationship_type=CausalRelationshipType.DIRECT_CAUSATION,
                strength=0.5,
                confidence=edge.confidence if hasattr(edge, 'confidence') else 0.5
            )

            # Determine relationship type from edge structure
            if hasattr(edge, 'has_latent_confounding'):
                if edge.has_latent_confounding():
                    explanation.relationship_type = CausalRelationshipType.CONFOUNDED_RELATIONSHIP
                elif hasattr(edge, 'is_bidirected') and edge.is_bidirected():
                    explanation.relationship_type = CausalRelationshipType.FEEDBACK_LOOP
                else:
                    explanation.relationship_type = CausalRelationshipType.UNCERTAIN_RELATIONSHIP

            explanations.append(explanation)

        return {
            'story': story,
            'explanations': [exp.to_natural_language() for exp in explanations],
            'variable_descriptions': variable_descriptions,
            'n_edges': len(edges),
            'n_explanations': len(explanations)
        }

    def answer_question(
        self,
        question: str,
        pag: Any,
        variable_descriptions: Dict[str, str]
    ) -> str:
        """
        Answer a question about the PAG.

        Args:
            question: User question
            pag: PAG to explain
            variable_descriptions: Variable descriptions

        Returns:
            Natural language answer
        """
        question_lower = question.lower()

        # Parse question to extract relevant variables
        mentioned_vars = []
        for var in variable_descriptions.keys():
            if var.lower() in question_lower:
                mentioned_vars.append(var)

        if not mentioned_vars:
            return "I cannot answer that question directly. Please specify which variables you're asking about."

        # Check for different question types

        # Type 1: "Why does X cause Y?"
        if 'why' in question_lower and len(mentioned_vars) >= 2:
            source = mentioned_vars[0]
            target = mentioned_vars[1]

            # Find edge between them
            for edge in pag.edges:
                if edge.source == source and edge.target == target:
                    explanation = CausalExplanation(
                        source=source,
                        target=target,
                        relationship_type=CausalRelationshipType.DIRECT_CAUSATION,
                        strength=0.5,
                        confidence=edge.confidence if hasattr(edge, 'confidence') else 0.5
                    )
                    return explanation.to_natural_language()

        # Type 2: "Is there a feedback loop?"
        if 'feedback' in question_lower:
            feedback_loops = [
                (e.source, e.target)
                for e in pag.edges
                if hasattr(e, 'is_bidirected') and e.is_bidirected()
            ]

            if feedback_loops:
                return f"Yes, feedback loops detected: {', '.join([f'{s}↔{t}' for s, t in feedback_loops])}"

        # Type 3: "Is X a proxy?"
        if 'proxy' in question_lower:
            for edge in pag.edges:
                if edge.source in mentioned_vars or edge.target in mentioned_vars:
                    if hasattr(edge, 'has_latent_confounding') and edge.has_latent_confounding():
                        return f"Yes, {edge.source} may be a proxy. The relationship is confounded by latent variables."

        # Default: generic answer
        return f"The analysis shows {len(pag.edges)} causal relationships. " + \
               f"For specific questions about {', '.join(mentioned_vars[:3])}, please provide more context."

    def generate_visualization_data(
        self,
        pag: Any,
        layout: str = "circular"
    ) -> Dict[str, Any]:
        """
        Generate data for causal graph visualization.

        Args:
            pag: PAG to visualize
            layout: Layout algorithm ("circular", "hierarchical", "force_directed")

        Returns:
            Visualization data structure
        """
        nodes = pag.nodes if hasattr(pag, 'nodes') else set()
        edges = pag.edges if hasattr(pag, 'edges') else []

        # Node positions for different layouts
        positions = self._compute_layout(nodes, layout)

        return {
            'nodes': list(nodes),
            'edges': [
                {
                    'source': e.source,
                    'target': e.target,
                    'type': self._edge_type_to_viz_type(e),
                    'lag': getattr(e, 'lag', 0)
                }
                for e in edges
            ],
            'positions': positions,
            'layout': layout
        }

    def _edge_type_to_viz_type(self, edge: Any) -> str:
        """Convert edge type to visualization type"""
        if hasattr(edge, 'is_bidirected') and edge.is_bidirected():
            return "bidirectional"
        elif hasattr(edge, 'has_latent_confounding') and edge.has_latent_confounding():
            return "confounded"
        elif hasattr(edge, 'source_end') and edge.source_end.value == 'tail':
            return "directed"
        else:
            return "uncertain"

    def _compute_layout(
        self,
        nodes: set,
        layout: str
    ) -> Dict[str, Tuple[float, float]]:
        """Compute node positions for visualization"""
        positions = {}

        if layout == "circular" and len(nodes) > 1:
            # Circular layout
            angle_step = 2 * np.pi / len(nodes)
            for i, node in enumerate(nodes):
                x = np.cos(i * angle_step)
                y = np.sin(i * angle_step)
                positions[node] = (x, y)

        elif layout == "hierarchical":
            # Hierarchical layout (group by prefix)
            groups = {}
            for node in nodes:
                prefix = node.split('_')[0] if '_' in node else node[0]
                if prefix not in groups:
                    groups[prefix] = []
                groups[prefix].append(node)

            # Position by group
            y_offset = 0
            for i, (group_name, group_nodes) in enumerate(groups.items()):
                x_offset = i * 2.0
                for j, node in enumerate(group_nodes):
                    x = x_offset + j * 0.5
                    y = y_offset
                    positions[node] = (x, y)

        else:  # Force-directed
            # Simple left-to-right layout
            for i, node in enumerate(nodes):
                positions[node] = (i * 1.0, 0.0)

        return positions


# Factory function

def create_explainable_causal_reasoner() -> ExplainableCausalReasoner:
    """Factory function to create ExplainableCausalReasoner"""
    return ExplainableCausalReasoner()


# Convenience function

def explain_causal_discovery_to_astronomer(
    pag: Any,
    question: Optional[str] = None,
    variable_descriptions: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate astronomer-friendly explanation of causal discovery results.

    Args:
        pag: PAG from V98 FCI
        question: Optional specific question
        variable_descriptions: Optional variable descriptions

    Returns:
        Natural language explanation
    """
    reasoner = create_explainable_causal_reasoner()

    if question:
        return reasoner.answer_question(question, pag, variable_descriptions or {})
    else:
        result = reasoner.explain_pag(pag, variable_descriptions)
        return result['story']


def create_visualization_for_paper(
    pag: Any,
    variable_descriptions: Dict[str, str],
    title: str = "Causal Structure Discovery"
) -> str:
    """
    Generate LaTeX/visualization code for causal graph for paper inclusion.

    Args:
        pag: PAG from V98 FCI
        variable_descriptions: Variable name → description mapping
        title: Figure title

    Returns:
        LaTeX/TikZ code for causal graph
    """
    nodes = pag.nodes if hasattr(pag, 'nodes') else set()
    edges = pag.edges if hasattr(pag, 'edges') else []

    # Generate TikZ code
    tikz_code = f"""
\\begin{{figure*}}[h]
\\centering
\\begin{{tikzpicture}}[
  node_distance=2.5cm,
  edge_distance=2cm,
  ->{{short}}]}}
"""

    # Add nodes
    for i, node in enumerate(sorted(nodes)):
        tikz_code += f"  \\node ({i}) [circle, draw, fill=blue!20, minimum size=1.5cm] {{{node}}}]\n"

    # Add edges
    for edge in edges:
        source = edge.source
        target = edge.target
        edge_style = "->"

        if hasattr(edge, 'is_bidirected') and edge.is_bidirected():
            edge_style = "<->"
        elif hasattr(edge, 'has_latent_confounding') and edge.has_latent_confounding():
            edge_style = "-, dashed"

        tikz_code += f"  \\draw [{edge_style}] ({source}) to ({target})\n"

    tikz_code += f"""
]
\\end{{tikzpicture}}
\\caption{{{title}}}
\\label{{fig:causal_graph}}
\\end{{figure*}}
"""

    return tikz_code


# Astrophysical domain knowledge for explanations

ASTROPHYSICAL_MECHANISMS = {
    "jeans_mass_sfr": "Gravitational instability: When Jeans mass falls below cloud mass, regions become gravitationally unstable and can collapse to form stars",
    "magnetic_field_sfr": "Magnetic suppression: Strong magnetic fields provide additional pressure support against gravity, inhibiting gravitational collapse",
    "turbulence_sfr": "Turbulent support: High turbulence (virial parameter > 1) provides kinetic pressure support against collapse",
    "column_density_sfr": "Column density is correlated with SFR but is a proxy: it correlates with Jeans mass (both depend on density) but is not causally responsible",
    "stellar_mass_sfr": "Stellar mass determines gravitational potential; more mass → deeper potential wells → more material for star formation",
    "metallicity_sfr": "Metallicity affects cooling efficiency; higher metallicity enables more efficient cooling and fragmentation"
}
