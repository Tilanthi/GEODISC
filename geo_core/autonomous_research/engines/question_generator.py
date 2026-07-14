"""
Question Generator Engine

Identifies important unanswered scientific questions by analyzing
knowledge gaps, tensions, and opportunities.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re

# Import shared types to avoid duplicate definitions
from ..types import ResearchQuestion, QuestionType, QuestionImportance


class QuestionGenerator:
    """
    Generates important research questions by identifying gaps and tensions.

    Uses multiple strategies:
    1. Literature gap detection
    2. Tension identification
    3. Parameter space gaps
    4. Theory boundary exploration
    5. Cross-domain analogy
    """

    def __init__(self):
        """Initialize the question generator"""
        self.gap_database = {}
        self.tension_database = {}
        self.question_history = []

        # Known gaps by domain (expanded database)
        self.domain_gaps = self._initialize_gap_database()

        # Known tensions by domain
        self.domain_tensions = self._initialize_tension_database()

    def _initialize_gap_database(self) -> Dict[str, List[Dict]]:
        """Initialize known knowledge gaps by domain"""
        gaps = {
            'redox_geochemistry': [
                {
                    'gap': 'Timing and structure of the Great Oxidation Event',
                    'type': 'incomplete',
                    'importance': 5,
                    'references': ['Holland 2006', 'Lyons et al. 2014']
                },
                {
                    'gap': 'Extent of Proterozoic ocean euxinia',
                    'type': 'incomplete',
                    'importance': 5,
                    'references': ['Canfield 1998', 'Poulton & Canfield 2011']
                },
                {
                    'gap': 'Redox sensitivity of rare earth element proxies',
                    'type': 'untested',
                    'importance': 4,
                    'references': ['Planavsky et al. 2010']
                }
            ],
            'organic_geochemistry': [
                {
                    'gap': 'Controls on organic carbon burial across the Proterozoic',
                    'type': 'incomplete',
                    'importance': 5,
                    'references': ['Berner 2004', 'Des Marais et al. 1992']
                },
                {
                    'gap': 'Biomarker preservation in Archean rocks',
                    'type': 'tension',
                    'importance': 5,
                    'references': ['Brocks et al. 2003', 'French et al. 2015']
                },
                {
                    'gap': 'Origin of kerogen molecular structure',
                    'type': 'unknown',
                    'importance': 4,
                    'references': ['Vandenbroucke & Largeau 2007']
                }
            ],
            'taphonomy': [
                {
                    'gap': 'Role of silicification in Proterozoic fossil preservation',
                    'type': 'incomplete',
                    'importance': 5,
                    'references': ['Knoll 1985', 'Wacey et al. 2011']
                },
                {
                    'gap': 'Redox controls on soft-tissue preservation',
                    'type': 'incomplete',
                    'importance': 4,
                    'references': ['Canfield et al. 2010']
                },
                {
                    'gap': 'Decay rate versus mineral encapsulation timing',
                    'type': 'unknown',
                    'importance': 4,
                    'references': ['Briggs & McMahon 2016']
                }
            ],
            'isotope_geochemistry': [
                {
                    'gap': 'Carbon isotope chemostratigraphy across the GOE',
                    'type': 'incomplete',
                    'importance': 5,
                    'references': ['Schidlowski 2001', 'Karhu & Holland 1996']
                },
                {
                    'gap': 'Multiple sulfur isotope mass-independent fractionation demise',
                    'type': 'incomplete',
                    'importance': 5,
                    'references': ['Farquhar et al. 2000', 'Farquhar & Wing 2003']
                },
                {
                    'gap': 'Iron isotope fractionation as a redox proxy',
                    'type': 'untested',
                    'importance': 4,
                    'references': ['Johnson et al. 2008']
                }
            ],
            'sedimentology': [
                {
                    'gap': 'Origin of Proterozoic banded iron formations',
                    'type': 'incomplete',
                    'importance': 5,
                    'references': ['Bekker et al. 2010', 'Klein 2005']
                },
                {
                    'gap': 'Microbialite decline through the Proterozoic',
                    'type': 'incomplete',
                    'importance': 4,
                    'references': ['Grotzinger & Knoll 1999']
                },
                {
                    'gap': 'Diagenetic controls on chert nodule formation',
                    'type': 'unknown',
                    'importance': 3,
                    'references': ['Maliva et al. 2005']
                }
            ]
        }

        return gaps

    def _initialize_tension_database(self) -> Dict[str, List[Dict]]:
        """Initialize known tensions by domain"""
        tensions = {
            'redox_geochemistry': [
                {
                    'tension': 'Lomagundi carbon isotope excursion vs atmospheric O2 models',
                    'type': 'contradiction',
                    'evidence': ['Karhu & Holland 1996', 'Bekker & Holland 2012'],
                    'importance': 5,
                    'resolutions': ['Carbon burial flux revision', 'Weathering feedback']
                },
                {
                    'tension': 'MIF sulfur isotope record vs late Archean oxygen whiffs',
                    'type': 'contradiction',
                    'evidence': ['Farquhar et al. 2000', 'Anbar et al. 2007'],
                    'importance': 4,
                    'resolutions': ['Localised oxygen oases', 'Photochemical modelling']
                }
            ],
            'organic_geochemistry': [
                {
                    'tension': 'Archean biomarker syngeneity vs contamination',
                    'type': 'contradiction',
                    'evidence': ['Brocks et al. 2003', 'Rasmussen et al. 2008'],
                    'importance': 5,
                    'resolutions': ['Improved extraction protocols', 'In-situ analysis']
                }
            ],
            'taphonomy': [
                {
                    'tension': 'Silicification vs redox as the dominant preservation control',
                    'type': 'inconsistency',
                    'evidence': ['Wacey et al. 2011', 'Canfield et al. 2010'],
                    'importance': 4,
                    'resolutions': ['Dual-control model', 'Environmental context']
                }
            ]
        }

        return tensions

    def identify_gaps(
        self,
        domain: str,
        context: Dict[str, Any]
    ) -> List[ResearchQuestion]:
        """
        Identify knowledge gaps and generate research questions.

        Args:
            domain: Scientific domain
            context: Additional context

        Returns:
            List of research questions
        """
        print(f"[Question Generator] Identifying gaps in {domain}")

        questions = []

        # Get known gaps for domain
        domain_lower = domain.lower().replace(' ', '_')

        # Match to domain categories
        matched_domains = self._match_domain(domain_lower)

        for matched_domain in matched_domains:
            # Process gaps
            if matched_domain in self.domain_gaps:
                for gap_info in self.domain_gaps[matched_domain]:
                    question = self._gap_to_question(gap_info, matched_domain)
                    questions.append(question)

            # Process tensions
            if matched_domain in self.domain_tensions:
                for tension_info in self.domain_tensions[matched_domain]:
                    question = self._tension_to_question(tension_info, matched_domain)
                    questions.append(question)

        # Generate additional questions from context
        context_questions = self._generate_contextual_questions(domain, context)
        questions.extend(context_questions)

        # Generate cross-domain questions
        cross_questions = self._generate_cross_domain_questions(domain)
        questions.extend(cross_questions)

        # Remove duplicates
        questions = self._deduplicate_questions(questions)

        print(f"[Question Generator] Found {len(questions)} potential questions")

        return questions

    def _match_domain(self, domain: str) -> List[str]:
        """Match domain to known domain categories"""
        domain_map = {
            'redox_geochemistry': ['redox_geochemistry', 'redox', 'oxygen', 'goe', 'euxinic'],
            'organic_geochemistry': ['organic_geochemistry', 'organic', 'kerogen', 'biomarker', 'toc'],
            'taphonomy': ['taphonomy', 'preservation', 'fossil', 'silicification'],
            'isotope_geochemistry': ['isotope_geochemistry', 'isotope', 'chemostratigraphy', 'fractionation'],
            'sedimentology': ['sedimentology', 'bif', 'chert', 'microbialite', 'diagenesis']
        }

        matched = []
        for key, variants in domain_map.items():
            if any(variant in domain for variant in variants):
                matched.append(key)

        return matched if matched else ['sedimentology']  # Default

    def _gap_to_question(self, gap_info: Dict, domain: str) -> ResearchQuestion:
        """Convert a gap to a research question"""
        gap = gap_info['gap']
        gap_type = gap_info['type']
        importance = gap_info['importance']

        # Determine question type
        if gap_type == 'unknown':
            question_type = QuestionType.OBSERVATIONAL
            question = f"What is {gap.lower()}?"
        elif gap_type == 'incomplete':
            question_type = QuestionType.THEORETICAL
            question = f"How does {gap.lower()} work?"
        elif gap_type == 'tension':
            question_type = QuestionType.INTERDISCIPLINARY
            question = f"How can we resolve {gap.lower()}?"
        else:  # untested
            question_type = QuestionType.EXPERIMENTAL
            question = f"Can we test {gap.lower()}?"

        # Determine importance level
        if importance >= 5:
            importance_level = QuestionImportance.TRANSFORMATIVE
        elif importance >= 4:
            importance_level = QuestionImportance.MAJOR
        elif importance >= 3:
            importance_level = QuestionImportance.MODERATE
        else:
            importance_level = QuestionImportance.MINOR

        return ResearchQuestion(
            question=question,
            question_type=question_type,
            importance=importance_level,
            domain=domain,
            context={'gap_info': gap_info},
            motivation=f"This addresses a critical gap: {gap}",
            feasibility=0.7,
            expected_impact=importance * 0.2,
            references=gap_info.get('references', [])
        )

    def _tension_to_question(self, tension_info: Dict, domain: str) -> ResearchQuestion:
        """Convert a tension to a research question"""
        tension = tension_info['tension']
        tension_type = tension_info['type']
        importance = tension_info['importance']

        question = f"How do we resolve {tension.lower()}?"

        # Determine question type
        if tension_type == 'contradiction':
            question_type = QuestionType.INTERDISCIPLINARY
        else:
            question_type = QuestionType.THEORETICAL

        # Determine importance level
        if importance >= 5:
            importance_level = QuestionImportance.TRANSFORMATIVE
        elif importance >= 4:
            importance_level = QuestionImportance.MAJOR
        else:
            importance_level = QuestionImportance.MODERATE

        return ResearchQuestion(
            question=question,
            question_type=question_type,
            importance=importance_level,
            domain=domain,
            context={'tension_info': tension_info},
            motivation=f"This addresses a critical tension: {tension}",
            feasibility=0.6,
            expected_impact=importance * 0.25,
            references=tension_info.get('evidence', [])
        )

    def _generate_contextual_questions(
        self,
        domain: str,
        context: Dict[str, Any]
    ) -> List[ResearchQuestion]:
        """Generate questions based on specific context"""
        questions = []

        # Check for parameter gaps
        if 'parameters' in context:
            param_questions = self._generate_parameter_questions(
                domain,
                context['parameters']
            )
            questions.extend(param_questions)

        # Check for observational constraints
        if 'observations' in context:
            obs_questions = self._generate_observation_questions(
                domain,
                context['observations']
            )
            questions.extend(obs_questions)

        # Check for theoretical frameworks
        if 'theories' in context:
            theory_questions = self._generate_theory_questions(
                domain,
                context['theories']
            )
            questions.extend(theory_questions)

        return questions

    def _generate_parameter_questions(
        self,
        domain: str,
        parameters: List[str]
    ) -> List[ResearchQuestion]:
        """Generate questions about unexplored parameter space"""
        questions = []

        # Look for parameter combinations that haven't been tested
        for i, param1 in enumerate(parameters):
            for param2 in parameters[i+1:]:
                question = ResearchQuestion(
                    question=f"How does {param1} interact with {param2} in {domain}?",
                    question_type=QuestionType.COMPUTATIONAL,
                    importance=QuestionImportance.MODERATE,
                    domain=domain,
                    context={'parameters': [param1, param2]},
                    motivation=f"Untested parameter space: {param1} × {param2}",
                    feasibility=0.8,
                    expected_impact=0.6
                )
                questions.append(question)

        return questions

    def _generate_observation_questions(
        self,
        domain: str,
        observations: List[str]
    ) -> List[ResearchQuestion]:
        """Generate questions requiring new observations"""
        questions = []

        # Look for unobserved phenomena
        for obs in observations:
            question = ResearchQuestion(
                question=f"What would we discover by observing {obs} in {domain}?",
                question_type=QuestionType.OBSERVATIONAL,
                importance=QuestionImportance.MAJOR,
                domain=domain,
                context={'observation': obs},
                motivation=f"Critical observation missing: {obs}",
                feasibility=0.7,
                expected_impact=0.8
            )
            questions.append(question)

        return questions

    def _generate_theory_questions(
        self,
        domain: str,
        theories: List[str]
    ) -> List[ResearchQuestion]:
        """Generate questions about theoretical frameworks"""
        questions = []

        # Look for theoretical gaps
        for i, theory1 in enumerate(theories):
            for theory2 in theories[i+1:]:
                question = ResearchQuestion(
                    question=f"Can {theory1} and {theory2} be unified in {domain}?",
                    question_type=QuestionType.THEORETICAL,
                    importance=QuestionImportance.MODERATE,
                    domain=domain,
                    context={'theories': [theory1, theory2]},
                    motivation=f"Potential theoretical synthesis",
                    feasibility=0.5,
                    expected_impact=0.7
                )
                questions.append(question)

        return questions

    def _generate_cross_domain_questions(
        self,
        domain: str
    ) -> List[ResearchQuestion]:
        """Generate questions that span multiple domains"""
        questions = []

        # Define cross-domain connections
        cross_connections = {
            'redox_geochemistry': ['organic_geochemistry', 'taphonomy'],
            'organic_geochemistry': ['redox_geochemistry', 'sedimentology', 'taphonomy'],
            'taphonomy': ['redox_geochemistry', 'organic_geochemistry', 'sedimentology'],
            'sedimentology': ['taphonomy', 'isotope_geochemistry'],
            'isotope_geochemistry': ['redox_geochemistry', 'sedimentology']
        }

        if domain in cross_connections:
            for connected_domain in cross_connections[domain]:
                question = ResearchQuestion(
                    question=f"How does {domain} affect {connected_domain} across the sedimentary record?",
                    question_type=QuestionType.INTERDISCIPLINARY,
                    importance=QuestionImportance.MAJOR,
                    domain=f"{domain}_{connected_domain}",
                    context={'primary': domain, 'secondary': connected_domain},
                    motivation=f"Cross-domain connection: {domain} → {connected_domain}",
                    feasibility=0.6,
                    expected_impact=0.75
                )
                questions.append(question)

        return questions

    def _deduplicate_questions(
        self,
        questions: List[ResearchQuestion]
    ) -> List[ResearchQuestion]:
        """Remove duplicate questions"""
        seen = set()
        unique_questions = []

        for question in questions:
            # Create a signature based on question text
            signature = question.question.lower().strip()
            if signature not in seen:
                seen.add(signature)
                unique_questions.append(question)

        return unique_questions

    def assess_feasibility(self, question: ResearchQuestion) -> float:
        """
        Assess feasibility of addressing a research question.

        Args:
            question: Research question

        Returns:
            Feasibility score (0-1)
        """
        # Base feasibility on question type
        type_feasibility = {
            QuestionType.OBSERVATIONAL: 0.7,
            QuestionType.THEORETICAL: 0.8,
            QuestionType.EXPERIMENTAL: 0.5,
            QuestionType.COMPUTATIONAL: 0.9,
            QuestionType.INTERDISCIPLINARY: 0.6,
            QuestionType.METHODOLOGICAL: 0.7
        }

        base_score = type_feasibility.get(question.question_type, 0.7)

        # Adjust based on domain
        domain_difficulty = {
            'taphonomy': 0.6,  # Hard due to sparse preservation record
            'isotope_geochemistry': 0.5,  # Hard due to analytical precision needs
            'organic_geochemistry': 0.8,  # Easier - mature toolkit
            'redox_geochemistry': 0.7,
            'sedimentology': 0.7
        }

        domain_factor = 1.0
        for domain, difficulty in domain_difficulty.items():
            if domain in question.domain.lower():
                domain_factor = difficulty
                break

        # Adjust based on importance (more important = harder)
        importance_factor = {
            QuestionImportance.TRANSFORMATIVE: 0.7,
            QuestionImportance.MAJOR: 0.8,
            QuestionImportance.MODERATE: 0.9,
            QuestionImportance.MINOR: 0.95,
            QuestionImportance.TECHNICAL: 1.0
        }

        importance_factor_val = importance_factor.get(question.importance, 0.8)

        feasibility = base_score * domain_factor * importance_factor_val

        return min(1.0, max(0.0, feasibility))

    def rank_by_importance(
        self,
        questions: List[ResearchQuestion]
    ) -> List[ResearchQuestion]:
        """
        Rank questions by importance.

        Args:
            questions: List of questions

        Returns:
            Sorted list of questions
        """
        # Sort by expected impact
        return sorted(
            questions,
            key=lambda q: q.expected_impact,
            reverse=True
        )
