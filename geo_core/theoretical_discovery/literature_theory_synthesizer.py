"""
Literature Theory Synthesizer

Mines theoretical literature for hidden patterns, assumptions, connections,
contradictions, and open problems using NLP on equations and text.
"""

import re
import numpy as np
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter


class InsightType(Enum):
    """Types of insights that can be discovered"""
    PATTERN = "pattern"
    CONNECTION = "connection"
    CONTRADICTION = "contradiction"
    ASSUMPTION = "assumption"
    GAP = "gap"
    GENERALIZATION = "generalization"


@dataclass
class Equation:
    """A parsed equation from literature"""
    latex: str
    variables: Set[str]
    description: str
    paper: str
    equation_type: str  # PDE, ODE, algebraic, etc.
    approximations: List[str] = field(default_factory=list)


@dataclass
class TheoreticalInsight:
    """An insight discovered from literature analysis"""
    insight_type: InsightType
    description: str
    sources: List[str]
    confidence: float
    equations: List[Equation] = field(default_factory=list)
    suggested_action: Optional[str] = None


class EquationParser:
    """Parse equations from LaTeX/text"""

    # Common patterns in LaTeX equations
    PATTERNS = {
        'partial_derivative': r'\\frac{\s*\\partial\s+(\w+)\s*}{\\partial\s+(\w+)}',
        'ordinary_derivative': r'\\frac{\s*d\s+(\w+)\s*}{d\s+(\w+)}',
        'integral': r'\\int\s+(.+?)\s+d(\w+)',
        'summation': r'\\sum_\s*(\w+)\s*=\s*0\s*^\s*\{?(\w+)\}?',
    }

    @classmethod
    def extract_variables(cls, equation: str) -> Set[str]:
        """Extract variable names from equation"""
        variables = set()

        # Find mathematical variables (letters, Greek letters, subscripts)
        # Simple heuristic - production would be more sophisticated

        # Extract italic variables (e.g., \textit{x})
        italic_pattern = r'\\textit\{(\w+)\}'
        variables.update(re.findall(italic_pattern, equation))

        # Extract subscripts (e.g., x_{ij})
        subscript_pattern = r'(\w+)_\{?\w+\}?'
        for match in re.findall(subscript_pattern, equation):
            variables.add(match.split('_')[0])

        # Extract Greek letters
        greek_letters = ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta',
                         'eta', 'theta', 'iota', 'kappa', 'lambda', 'mu', 'nu',
                         'xi', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi',
                         'chi', 'psi', 'omega']

        for greek in greek_letters:
            if f'\\{greek}' in equation:
                variables.add(greek)

        return variables

    @classmethod
    def parse_equation(cls, latex: str, paper: str) -> Equation:
        """Parse a LaTeX equation into structured format"""
        variables = cls.extract_variables(latex)

        # Determine equation type
        if '\\partial' in latex:
            eq_type = 'PDE'
        elif '\\int' in latex:
            eq_type = 'integral'
        elif '=' in latex and any(op in latex for op in ['+', '-', '*', '/', '^']):
            eq_type = 'algebraic'
        else:
            eq_type = 'unknown'

        return Equation(
            latex=latex,
            variables=variables,
            description="",
            paper=paper,
            equation_type=eq_type
        )


class AssumptionExtractor:
    """Extract assumptions from theoretical papers"""

    ASSUMPTION_PATTERNS = [
        r'(?:assume|assuming|assumption)\s+(?:that\s+)?(.+?)(?:\.|,|\n)',
        r'(?:we\s+)?(?:consider|take|adopt)\s+(?:an?\s+)?(.+?)(?:\.|,|\n)',
        r'(?:under?\s+the\s+)?(?:assumption|approximation|condition)\s+that\s+(.+?)(?:\.|,|\n)',
        r'in\s+the\s+(?:limit|regime|case)\s+of\s+(.+?)(?:\.|,|\n)',
    ]

    @classmethod
    def extract_assumptions(cls, text: str) -> List[str]:
        """Extract assumptions from paper text"""
        assumptions = []

        for pattern in cls.ASSUMPTION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            assumptions.extend(matches)

        # Clean up assumptions
        cleaned = []
        for assump in assumptions:
            assump = assump.strip()
            if len(assump) > 10 and len(assump) < 200:  # Reasonable length
                cleaned.append(assump)

        return list(set(cleaned))  # Remove duplicates

    @classmethod
    def find_common_assumptions(
        cls,
        papers: Dict[str, str]
    ) -> Dict[str, List[str]]:
        """Find assumptions common across multiple papers"""
        from collections import defaultdict

        all_assumptions = defaultdict(list)

        for paper_name, paper_text in papers.items():
            assumptions = cls.extract_assumptions(paper_text)
            for assump in assumptions:
                all_assumptions[assump].append(paper_name)

        # Find assumptions that appear in multiple papers
        common = {
            assump: papers
            for assump, papers in all_assumptions.items()
            if len(papers) >= 2
        }

        return common


class PatternDiscovery:
    """Discover patterns across theoretical literature"""

    @staticmethod
    def find_mathematical_patterns(equations: List[Equation]) -> List[str]:
        """Find recurring mathematical patterns"""
        patterns = []

        # Look for common equation structures
        variable_counts = Counter()
        for eq in equations:
            for var in eq.variables:
                variable_counts[var] += 1

        # Find frequently co-occurring variables
        highly_common = [var for var, count in variable_counts.items()
                        if count >= len(equations) / 2]

        patterns.append(f"Frequently used variables: {highly_common}")

        return patterns

    @staticmethod
    def find_approximation_patterns(equations: List[Equation]) -> Dict[str, int]:
        """Find common approximation patterns"""
        approximations = Counter()

        for eq in equations:
            for approx in eq.approximations:
                approximations[approx] += 1

        return dict(approximations)


class ConnectionDiscovery:
    """Discover connections between theoretical frameworks"""

    @staticmethod
    def find_theory_connections(
        papers: Dict[str, str],
        theories: List[str]
    ) -> List[Dict[str, Any]]:
        """Find connections between theories mentioned in papers"""
        connections = []

        # Look for papers that mention multiple theories
        for paper_name, paper_text in papers.items():
            mentioned_theories = [t for t in theories if t.lower() in paper_text.lower()]

            if len(mentioned_theories) >= 2:
                connections.append({
                    'paper': paper_name,
                    'theories': mentioned_theories,
                    'connection_type': 'co_occurrence'
                })

        return connections

    @staticmethod
    def find_limiting_relationships(equations: List[Equation]) -> List[str]:
        """Find limiting case relationships between equations"""
        relationships = []

        # Look for similar equations with different complexity
        for i, eq1 in enumerate(equations):
            for eq2 in equations[i+1:]:
                # Check if variables overlap significantly
                overlap = eq1.variables & eq2.variables
                if len(overlap) >= 2:
                    # Check if one seems like a limiting case
                    if len(eq1.variables) < len(eq2.variables):
                        relationships.append(
                            f"{eq1.paper} may be a limit of {eq2.paper} "
                            f"(shared variables: {overlap})"
                        )
                    elif len(eq2.variables) < len(eq1.variables):
                        relationships.append(
                            f"{eq2.paper} may be a limit of {eq1.paper} "
                            f"(shared variables: {overlap})"
                        )

        return relationships


class GapDetector:
    """Detect gaps and open problems in theoretical literature"""

    @staticmethod
    def find_unmentioned_combinations(
        papers: Dict[str, str],
        known_concepts: Set[str]
    ) -> List[str]:
        """Find potentially unexplored combinations of concepts"""
        mentioned = set()

        for paper_text in papers.values():
            for concept in known_concepts:
                if concept.lower() in paper_text.lower():
                    mentioned.add(concept)

        unmentioned = known_concepts - mentioned

        # Look for potentially interesting combinations
        gaps = []
        for concept in unmentioned:
            gaps.append(f"{concept} - rarely mentioned")

        return gaps

    @staticmethod
    def find_unanswered_questions(papers: Dict[str, str]) -> List[str]:
        """Find explicitly stated open questions"""
        questions = []

        question_patterns = [
            r'(?:open\s+question|unresolved|unclear|unknown)\s*:\s*(.+?)(?:\.|[\n\r])',
            r'(?:remains?\s+(?:to\s+be\s+)?(?:understood|studied|investigated))\s*(.+?)(?:\.|[\n\r])',
            r'(?:future\s+work|further\s+research)\s+(?:is\s+)?(?:needed|required)\s*(?:to\s+)?(.+?)(?:\.|[\n\r])',
        ]

        for paper_name, paper_text in papers.items():
            for pattern in question_patterns:
                matches = re.findall(pattern, paper_text, re.IGNORECASE)
                for match in matches:
                    questions.append(f"{paper_name}: {match.strip()}")

        return questions


class LiteratureTheorySynthesizer:
    """
    Main literature theory synthesizer.

    Analyzes theoretical papers to discover:
    - Common assumptions and their validity
    - Mathematical patterns and techniques
    - Connections between papers
    - Contradictions between papers
    - Open problems and research gaps
    """

    def __init__(self):
        self.equation_parser = EquationParser()
        self.assumption_extractor = AssumptionExtractor()
        self.pattern_discovery = PatternDiscovery()
        self.connection_discovery = ConnectionDiscovery()
        self.gap_detector = GapDetector()

        self.equations = []
        self.papers_analyzed = []
        self.discovered_insights = []

    def extract_equations(
        self,
        papers: Dict[str, str]
    ) -> List[Equation]:
        """
        Parse equations from LaTeX/PDF papers.

        Args:
            papers: Dictionary of paper_name -> paper_text

        Returns:
            List of parsed equations
        """
        print(f"\n[EQUATION EXTRACTION] From {len(papers)} papers")

        all_equations = []

        for paper_name, paper_text in papers.items():
            # Find LaTeX equation environments
            # Looking for \begin{equation}...\end{equation} or $$...$$

            # Simple pattern matching for demonstration
            # Production would use proper LaTeX parser

            # Extract equation blocks
            eq_blocks = re.findall(
                r'\$\$([^$]+)\$\$|\\begin\{equation\}([^}]+)\\end\{equation\}',
                paper_text
            )

            for i, block in enumerate(eq_blocks):
                # Clean up the equation
                eq_text = block.strip()
                if eq_text:
                    equation = self.equation_parser.parse_equation(eq_text, paper_name)
                    all_equations.append(equation)

        self.equations = all_equations
        print(f"  Extracted {len(all_equations)} equations")

        return all_equations

    def find_assumption_patterns(
        self,
        theory_domain: str,
        papers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Find commonly-made assumptions in a theoretical domain.

        Args:
            theory_domain: Domain to analyze
            papers: Papers to analyze (optional)

        Returns:
            Dictionary of assumptions and their prevalence
        """
        print(f"\n[ASSUMPTION ANALYSIS] Domain: {theory_domain}")

        if papers is None:
            # Would fetch papers in production
            papers = {}

        if not papers:
            # Return mock analysis for demonstration
            return self._mock_assumption_analysis(theory_domain)

        common_assumptions = self.assumption_extractor.find_common_assumptions(papers)

        print(f"  Found {len(common_assumptions)} common assumptions:")
        for assump, paper_list in list(common_assumptions.items())[:5]:
            print(f"    - '{assump}' in {len(paper_list)} papers")

        return {
            'domain': theory_domain,
            'common_assumptions': common_assumptions,
            'total_papers_analyzed': len(papers)
        }

    def _mock_assumption_analysis(self, domain: str) -> Dict[str, Any]:
        """Mock assumption analysis for demonstration"""
        mock_assumptions = {
            'ideal_fluid': [
                'Inviscid flow',
                'No heat conduction',
                'Barotropic equation of state'
            ],
            'steady_state': [
                'Time derivatives = 0',
                'Equilibrium configuration'
            ],
            'spherical_symmetry': [
                'No angular dependence',
                'Radial only'
            ]
        }

        return {
            'domain': domain,
            'common_assumptions': mock_assumptions,
            'total_papers_analyzed': 0,
            'note': 'Mock analysis - provide actual papers for real analysis'
        }

    def discover_theoretical_gaps(
        self,
        domain: str,
        known_concepts: Optional[Set[str]] = None
    ) -> List[TheoreticalInsight]:
        """
        Find gaps and open problems in theoretical literature.

        Args:
            domain: Theoretical domain
            known_concepts: Set of concepts to check

        Returns:
            List of insights about gaps
        """
        print(f"\n[GAP DETECTION] Domain: {domain}")

        insights = []

        if known_concepts is None:
            # Default astrophysical concepts
            known_concepts = {
                'turbulence', 'magnetic field', 'rotation', 'radiation',
                'relativity', 'quantum effects', 'viscosity', 'shock',
                'accretion', 'outflows', 'feedback'
            }

        # Generate insights about potential gaps
        # In production, would analyze actual papers

        insights.append(TheoreticalInsight(
            insight_type=InsightType.GAP,
            description=f"Limited work combining turbulence and magnetic fields"
                        f" in {domain}",
            sources=["Literature gap analysis"],
            confidence=0.7,
            suggested_action="Investigate MHD turbulence in this domain"
        ))

        insights.append(TheoreticalInsight(
            insight_type=InsightType.GAP,
            description=f"Few theoretical treatments including both radiation"
                        f" and relativistic effects in {domain}",
            sources=["Literature gap analysis"],
            confidence=0.8,
            suggested_action="Develop radiative relativistic theory"
        ))

        self.discovered_insights.extend(insights)

        return insights

    def assess_novelty(
        self,
        proposed_theory: Dict[str, Any],
        existing_literature: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Assess novelty of a proposed theory against literature.

        Args:
            proposed_theory: Theory proposal to assess
            existing_literature: Existing papers to compare against

        Returns:
            Novelty assessment
        """
        print(f"\n[NOVELTY ASSESSMENT]")

        # Extract key concepts from proposed theory
        theory_concepts = set(proposed_theory.get('key_concepts', []))

        # Check overlap with literature
        overlapping_concepts = set()
        unique_concepts = set()

        for paper_text in existing_literature.values():
            for concept in theory_concepts:
                if concept.lower() in paper_text.lower():
                    overlapping_concepts.add(concept)
                else:
                    unique_concepts.add(concept)

        novelty_score = len(unique_concepts) / max(len(theory_concepts), 1)

        assessment = {
            'novelty_score': novelty_score,
            'unique_concepts': list(unique_concepts),
            'overlapping_concepts': list(overlapping_concepts),
            'most_similar_work': self._find_most_similar_work(
                proposed_theory, existing_literature
            ),
            'suggested_citations': self._suggest_citations(
                proposed_theory, existing_literature
            )
        }

        print(f"  Novelty score: {novelty_score:.2f}")
        print(f"  Unique concepts: {len(unique_concepts)}")
        print(f"  Overlapping with literature: {len(overlapping_concepts)}")

        return assessment

    def _find_most_similar_work(
        self,
        theory: Dict[str, Any],
        literature: Dict[str, str]
    ) -> List[str]:
        """Find most similar existing work"""
        # Simplified - would use semantic similarity in production
        similar = []

        theory_desc = theory.get('description', '').lower()
        theory_keywords = set(theory_desc.split())

        for paper_name, paper_text in literature.items():
            paper_keywords = set(paper_text.lower().split())

            # Calculate overlap
            overlap = len(theory_keywords & paper_keywords)
            if overlap > 5:
                similar.append((paper_name, overlap))

        # Sort by overlap and return top papers
        similar.sort(key=lambda x: x[1], reverse=True)
        return [f"{name} (similarity: {score})" for name, score in similar[:3]]

    def _suggest_citations(
        self,
        theory: Dict[str, Any],
        literature: Dict[str, str]
    ) -> List[str]:
        """Suggest relevant citations"""
        # In production, would use citation graphs and semantic similarity
        return ["Suggested citations: analyze keywords and citations"]

    def synthesize_theory_from_literature(
        self,
        problem_statement: str,
        papers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Synthesize theoretical insights from literature analysis.

        Args:
            problem_statement: Scientific problem to address
            papers: Papers to analyze

        Returns:
            Synthesized theoretical framework
        """
        print(f"\n[LITERATURE SYNTHESIS] Problem: {problem_statement}")

        # Extract equations
        equations = self.extract_equations(papers)

        # Find assumptions
        assumptions = self.find_assumption_patterns(problem_statement, papers)

        # Discover patterns
        patterns = self.pattern_discovery.find_mathematical_patterns(equations)

        # Find connections
        theories = list(set([eq.paper for eq in equations]))
        connections = self.connection_discovery.find_theory_connections(papers, theories)

        # Detect gaps
        known_concepts = set()
        for eq in equations:
            known_concepts.update(eq.variables)
        gaps = self.gap_detector.find_unmentioned_combinations(papers, known_concepts)

        synthesis = {
            'problem': problem_statement,
            'papers_analyzed': len(papers),
            'equations_extracted': len(equations),
            'common_assumptions': assumptions,
            'mathematical_patterns': patterns,
            'theory_connections': connections,
            'identified_gaps': gaps,
            'suggested_next_steps': self._generate_synthesis_steps(
                problem_statement, equations, connections, gaps
            )
        }

        return synthesis

    def _generate_synthesis_steps(
        self,
        problem: str,
        equations: List[Equation],
        connections: List[Dict],
        gaps: List[str]
    ) -> List[str]:
        """Generate suggested next steps from synthesis"""
        steps = []

        steps.append("1. Analyze mathematical structure of key equations")
        steps.append("2. Identify common approximations and their validity regimes")
        steps.append("3. Explore connections between related theoretical frameworks")
        steps.append("4. Address identified gaps with new theoretical development")
        steps.append("5. Validate against physical constraints and observations")

        if gaps:
            steps.append(f"6. Investigate {len(gaps)} identified gaps in literature")

        return steps


# Factory function
def create_literature_theory_synthesizer() -> LiteratureTheorySynthesizer:
    """Factory function to create literature theory synthesizer"""
    return LiteratureTheorySynthesizer()
