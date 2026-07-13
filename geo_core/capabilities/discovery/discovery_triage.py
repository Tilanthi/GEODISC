"""
V107 Discovery Triage and Prioritization - Impact-Based Discovery Ranking
=========================================================================

PROBLEM: Scientific discovery systems can generate hundreds of potential
discoveries. Without triage, researchers waste time on low-impact findings
while high-impact discoveries are overlooked.

SOLUTION: Discovery Triage and Prioritization with:
1. Impact Scoring - Multi-dimensional impact assessment
2. Novelty-Adjusted Confidence - Balance novelty with reliability
3. Scientific Value Scoring - Field-transformative potential
4. Actionability Scoring - Can this be validated?
5. Triage Queue - Priority-ranked discovery queue

INTEGRATION:
- Uses V97 novelty scores as input
- Integrates with V98 causal discovery for causal impact
- Uses V103 multi-modal evidence for confidence
- Works with V104 adversarial results for robustness
- Integrates with V106 explainable reasoning for communication

USE CASES:
- Prioritize which discoveries to investigate first
- Rank discoveries by paper-worthiness
- Identify "low-hanging fruit" vs "major breakthroughs"
- Triage between "publish now" vs "gather more evidence"

Date: 2026-04-14
Version: 1.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
import numpy as np
from scipy import stats
import json
from collections import defaultdict
from datetime import datetime, timedelta


class ImpactDimension(Enum):
    """Dimensions of discovery impact"""
    NOVELTY = "novelty"                  # How new is this? (from V97)
    CONFIDENCE = "confidence"            # How reliable? (from V103)
    CAUSAL_IMPORTANCE = "causal"         # Causal significance (from V98)
    SCIENTIFIC_VALUE = "scientific"      # Field-transformative potential
    ACTIONABILITY = "actionability"      # Can we validate this?
    INTERDISCIPLINARY = "interdisciplinary"  # Cross-domain impact
    REPRODUCIBILITY = "reproducibility"  # How reproducible?


class TriageCategory(Enum):
    """Triage categories for discoveries"""
    CRITICAL_BREAKTHROUGH = "critical_breakthrough"  # Immediate attention
    HIGH_PRIORITY = "high_priority"                  # Investigate soon
    MEDIUM_PRIORITY = "medium_priority"              # Worth exploring
    LOW_PRIORITY = "low_priority"                    # Backlog
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"  # Need more data
    REPRODUCIBILITY_NEEDED = "reproducibility_needed"  # Cannot assess


class ValidationStrategy(Enum):
    """Validation strategies for discoveries"""
    IMMEDIATE_PUBLICATION = "immediate_publication"
    TARGETED_OBSERVATION = "targeted_observation"
    CROSS_VALIDATION = "cross_validation"
    REPRODUCTION_REQUIRED = "reproduction_required"
    LITERATURE_REVIEW = "literature_review"
    EXPERT_CONSULTATION = "expert_consultation"
    SIMULATION_TEST = "simulation_test"


@dataclass
class ImpactScore:
    """Multi-dimensional impact score"""
    dimension: ImpactDimension
    score: float  # 0-1
    confidence: float  # 0-1
    reasoning: str
    evidence_sources: List[str] = field(default_factory=list)


@dataclass
class DiscoveryTriageResult:
    """Result of triage assessment for a single discovery"""
    discovery_id: str
    claim: str
    overall_impact_score: float  # Weighted combination
    triage_category: TriageCategory
    dimension_scores: Dict[ImpactDimension, ImpactScore]
    recommended_action: str
    validation_strategy: ValidationStrategy
    estimated_investigation_time: str  # e.g., "1 week", "1 month"
    publication_readiness: float  # 0-1
    requires_additional_evidence: List[str]
    potential_collaborators: List[str]  # Suggested collaborators


@dataclass
class TriageQueue:
    """Priority queue of discoveries"""
    queue: List[DiscoveryTriageResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ImpactScoringEngine:
    """
    Calculate multi-dimensional impact scores for discoveries.

    Dimensions:
    - Novelty: From V97 Knowledge Isolation
    - Confidence: From V103 Multi-Modal Evidence
    - Causal Importance: From V98 FCI
    - Scientific Value: Field-transformative potential
    - Actionability: Can this be validated?
    - Interdisciplinary: Cross-domain impact
    - Reproducibility: From V103 code evidence
    """

    def __init__(self):
        """Initialize impact scoring engine"""
        # Default weights for each dimension
        self.default_weights = {
            ImpactDimension.NOVELTY: 0.25,
            ImpactDimension.CONFIDENCE: 0.20,
            ImpactDimension.CAUSAL_IMPORTANCE: 0.15,
            ImpactDimension.SCIENTIFIC_VALUE: 0.20,
            ImpactDimension.ACTIONABILITY: 0.10,
            ImpactDimension.INTERDISCIPLINARY: 0.05,
            ImpactDimension.REPRODUCIBILITY: 0.05
        }

        # Domain-specific value multipliers
        self.domain_value_multipliers = {
            "star_formation": 1.2,      # High impact field
            "exoplanets": 1.3,          # Very high impact
            "high_energy": 1.1,
            "cosmology": 1.2,
            "ism_structure": 1.0,
            "time_domain": 1.15,        # Growing field
            "galactic_archaeology": 1.0
        }

    def calculate_impact_scores(
        self,
        discovery: Dict[str, Any],
        domain: str = ""
    ) -> Dict[ImpactDimension, ImpactScore]:
        """
        Calculate impact scores across all dimensions.

        Args:
            discovery: Discovery dict with claim, evidence, etc.
            domain: Domain context

        Returns:
            Dict mapping dimension to ImpactScore
        """
        scores = {}

        # Novelty score (from V97)
        scores[ImpactDimension.NOVELTY] = self._score_novelty(discovery)

        # Confidence score (from V103 multi-modal evidence)
        scores[ImpactDimension.CONFIDENCE] = self._score_confidence(discovery)

        # Causal importance (from V98)
        scores[ImpactDimension.CAUSAL_IMPORTANCE] = self._score_causal_importance(discovery)

        # Scientific value
        scores[ImpactDimension.SCIENTIFIC_VALUE] = self._score_scientific_value(
            discovery, domain
        )

        # Actionability
        scores[ImpactDimension.ACTIONABILITY] = self._score_actionability(discovery)

        # Interdisciplinary impact
        scores[ImpactDimension.INTERDISCIPLINARY] = self._score_interdisciplinary(discovery)

        # Reproducibility
        scores[ImpactDimension.REPRODUCIBILITY] = self._score_reproducibility(discovery)

        return scores

    def _score_novelty(self, discovery: Dict[str, Any]) -> ImpactScore:
        """Score novelty based on V97 novelty detection"""
        novelty_score = discovery.get('novelty_score', 0.5)

        # Check if knowledge was isolated (V97)
        was_isolated = discovery.get('knowledge_isolated', False)
        isolation_bonus = 0.2 if was_isolated else 0.0

        final_score = min(1.0, novelty_score + isolation_bonus)

        return ImpactScore(
            dimension=ImpactDimension.NOVELTY,
            score=final_score,
            confidence=0.8,
            reasoning=f"Novelty score: {novelty_score:.2f}" +
                     (f" + isolation bonus: {isolation_bonus:.2f}" if isolation_bonus > 0 else ""),
            evidence_sources=["V97_Knowledge_Isolation"]
        )

    def _score_confidence(self, discovery: Dict[str, Any]) -> ImpactScore:
        """Score confidence based on multi-modal evidence"""
        # Get multi-modal evidence confidence if available
        fusion_result = discovery.get('multimodal_fusion')
        if fusion_result:
            # Handle both dict and EvidenceFusionResult objects
            if isinstance(fusion_result, dict):
                conf = fusion_result.get('aggregate_confidence', 0.5)
                triangulation = fusion_result.get('triangulation_strength', 'none')
            else:
                conf = fusion_result.aggregate_confidence
                triangulation = fusion_result.triangulation_strength

            # Bonus for strong triangulation
            if triangulation == "strong":
                conf = min(1.0, conf + 0.15)
            elif triangulation == "moderate":
                conf = min(1.0, conf + 0.05)

            return ImpactScore(
                dimension=ImpactDimension.CONFIDENCE,
                score=conf,
                confidence=0.9,
                reasoning=f"Multi-modal confidence: {conf:.2f}, triangulation: {triangulation}",
                evidence_sources=["V103_Multi_Modal_Evidence"]
            )

        # Fallback: statistical significance
        p_value = discovery.get('p_value', 1.0)
        sample_size = discovery.get('sample_size', 0)

        if sample_size > 0:
            # Statistical power consideration
            power = min(1.0, sample_size / 1000)  # Simplified
            score = (1 - p_value) * 0.7 + power * 0.3
        else:
            score = 1 - p_value

        return ImpactScore(
            dimension=ImpactDimension.CONFIDENCE,
            score=score,
            confidence=0.6,
            reasoning=f"Statistical significance only (p={p_value:.3f})",
            evidence_sources=["statistical_tests"]
        )

    def _score_causal_importance(self, discovery: Dict[str, Any]) -> ImpactScore:
        """Score causal importance"""
        pag = discovery.get('causal_graph')
        if not pag:
            return ImpactScore(
                dimension=ImpactDimension.CAUSAL_IMPORTANCE,
                score=0.3,  # Low score if no causal info
                confidence=0.5,
                reasoning="No causal graph available",
                evidence_sources=[]
            )

        # Count direct causal edges
        n_direct_edges = 0
        n_edges = 0

        if hasattr(pag, 'edges'):
            for edge in pag.edges:
                n_edges += 1
                if hasattr(edge, 'source_end') and edge.source_end.value == 'tail':
                    n_direct_edges += 1

        # Score based on ratio of direct causal edges
        if n_edges > 0:
            causal_ratio = n_direct_edges / n_edges
        else:
            causal_ratio = 0

        # Bonus for number of causal relationships
        edge_bonus = min(0.2, n_direct_edges * 0.02)

        score = causal_ratio + edge_bonus

        return ImpactScore(
            dimension=ImpactDimension.CAUSAL_IMPORTANCE,
            score=min(1.0, score),
            confidence=0.8,
            reasoning=f"{n_direct_edges} direct causal edges out of {n_edges} total",
            evidence_sources=["V98_FCI_Causal_Discovery"]
        )

    def _score_scientific_value(
        self,
        discovery: Dict[str, Any],
        domain: str
    ) -> ImpactScore:
        """Score scientific value (field-transformative potential)"""
        base_score = 0.5

        # Domain-specific multiplier
        domain_multiplier = self.domain_value_multipliers.get(domain, 1.0)

        # Check for keywords indicating high impact
        claim = discovery.get('claim', '').lower()
        value_keywords = {
            'first': 0.15,
            'new mechanism': 0.2,
            'breakthrough': 0.25,
            'paradigm shift': 0.3,
            'unexpected': 0.1,
            'challenges': 0.15,
            'revises': 0.15,
            'contradicts': 0.2
        }

        keyword_bonus = 0.0
        for keyword, bonus in value_keywords.items():
            if keyword in claim:
                keyword_bonus += bonus

        # Check for effect size
        effect_size = discovery.get('effect_size', 0)
        if effect_size > 0.8:
            effect_bonus = 0.15
        elif effect_size > 0.5:
            effect_bonus = 0.10
        elif effect_size > 0.3:
            effect_bonus = 0.05
        else:
            effect_bonus = 0.0

        score = (base_score + keyword_bonus + effect_bonus) * domain_multiplier

        return ImpactScore(
            dimension=ImpactDimension.SCIENTIFIC_VALUE,
            score=min(1.0, score),
            confidence=0.7,
            reasoning=f"Base: {base_score:.2f}, domain multiplier: {domain_multiplier:.2f}, " +
                     f"keyword bonus: {keyword_bonus:.2f}, effect bonus: {effect_bonus:.2f}",
            evidence_sources=["domain_knowledge"]
        )

    def _score_actionability(self, discovery: Dict[str, Any]) -> ImpactScore:
        """Score actionability (can this be validated?)"""
        score = 0.5

        # Check for available follow-up observations
        claim = discovery.get('claim', '').lower()

        # High actionability indicators
        if 'testable' in claim or 'predict' in claim:
            score += 0.2

        # Check if data is available
        if discovery.get('data_available', False):
            score += 0.15

        # Check if reproducible code exists
        if discovery.get('reproducible_code', False):
            score += 0.15

        # Check for specific predictions
        if discovery.get('predictions'):
            score += 0.1

        return ImpactScore(
            dimension=ImpactDimension.ACTIONABILITY,
            score=min(1.0, score),
            confidence=0.7,
            reasoning="Actionability based on testability and data availability",
            evidence_sources=["V103_Code_Evidence"]
        )

    def _score_interdisciplinary(self, discovery: Dict[str, Any]) -> ImpactScore:
        """Score interdisciplinary impact"""
        # Count domains involved
        domains = discovery.get('domains', [])
        n_domains = len(domains)

        if n_domains >= 3:
            score = 1.0
            reasoning = f"High interdisciplinary impact ({n_domains} domains)"
        elif n_domains == 2:
            score = 0.7
            reasoning = f"Moderate interdisciplinary impact (2 domains)"
        else:
            score = 0.3
            reasoning = "Single-domain focus"

        return ImpactScore(
            dimension=ImpactDimension.INTERDISCIPLINARY,
            score=score,
            confidence=0.8,
            reasoning=reasoning,
            evidence_sources=["domain_analysis"]
        )

    def _score_reproducibility(self, discovery: Dict[str, Any]) -> ImpactScore:
        """Score reproducibility"""
        score = 0.3  # Base score

        # Check for code evidence
        if discovery.get('reproducible_code', False):
            score += 0.3

        # Check for open data
        if discovery.get('open_data', False):
            score += 0.2

        # Check for documented methodology
        if discovery.get('methodology_documented', False):
            score += 0.1

        # Check for reproducibility score from V103
        fusion_result = discovery.get('multimodal_fusion')
        if fusion_result:
            # Handle both dict and EvidenceFusionResult objects
            if isinstance(fusion_result, dict):
                supporting = fusion_result.get('supporting_evidence', [])
            else:
                supporting = fusion_result.supporting_evidence if hasattr(fusion_result, 'supporting_evidence') else []

            code_evidence = [e for e in supporting if 'code' in str(e).lower()]
            if code_evidence:
                score += 0.1

        return ImpactScore(
            dimension=ImpactDimension.REPRODUCIBILITY,
            score=min(1.0, score),
            confidence=0.8,
            reasoning=f"Reproducibility based on code and data availability",
            evidence_sources=["V103_Code_Evidence"]
        )

    def compute_overall_impact(
        self,
        dimension_scores: Dict[ImpactDimension, ImpactScore],
        custom_weights: Optional[Dict[ImpactDimension, float]] = None
    ) -> float:
        """
        Compute overall impact score from dimension scores.

        Args:
            dimension_scores: Dict of dimension scores
            custom_weights: Optional custom weights

        Returns:
            Overall impact score (0-1)
        """
        weights = custom_weights or self.default_weights

        weighted_sum = 0.0
        weight_sum = 0.0

        for dimension, score_obj in dimension_scores.items():
            weight = weights.get(dimension, 0.1)
            weighted_sum += score_obj.score * weight
            weight_sum += weight

        return weighted_sum / weight_sum if weight_sum > 0 else 0.0


class DiscoveryTriageSystem:
    """
    Main system for discovery triage and prioritization.

    Orchestrates impact scoring, categorization, and queue management.
    """

    def __init__(self):
        """Initialize discovery triage system"""
        self.impact_engine = ImpactScoringEngine()
        self.queue: TriageQueue = TriageQueue()
        self.processed_discoveries: Dict[str, DiscoveryTriageResult] = {}

    def triage_discovery(
        self,
        discovery: Dict[str, Any],
        domain: str = ""
    ) -> DiscoveryTriageResult:
        """
        Triage a single discovery.

        Args:
            discovery: Discovery dict
            domain: Domain context

        Returns:
            DiscoveryTriageResult
        """
        discovery_id = discovery.get('discovery_id',
                                     f"discovery_{len(self.processed_discoveries)}")

        # Calculate impact scores
        dimension_scores = self.impact_engine.calculate_impact_scores(
            discovery, domain
        )

        # Compute overall impact
        overall_impact = self.impact_engine.compute_overall_impact(dimension_scores)

        # Determine triage category
        category = self._categorize_discovery(overall_impact, dimension_scores)

        # Determine validation strategy
        validation_strategy = self._determine_validation_strategy(
            discovery, dimension_scores
        )

        # Generate recommended action
        action = self._generate_recommended_action(category, dimension_scores)

        # Estimate investigation time
        time_estimate = self._estimate_investigation_time(discovery, category)

        # Calculate publication readiness
        pub_readiness = self._calculate_publication_readiness(dimension_scores)

        # Identify additional evidence needed
        additional_evidence = self._identify_additional_evidence_needed(
            discovery, dimension_scores
        )

        # Suggest collaborators
        collaborators = self._suggest_collaborators(discovery, domain)

        result = DiscoveryTriageResult(
            discovery_id=discovery_id,
            claim=discovery.get('claim', ''),
            overall_impact_score=overall_impact,
            triage_category=category,
            dimension_scores=dimension_scores,
            recommended_action=action,
            validation_strategy=validation_strategy,
            estimated_investigation_time=time_estimate,
            publication_readiness=pub_readiness,
            requires_additional_evidence=additional_evidence,
            potential_collaborators=collaborators
        )

        # Store result
        self.processed_discoveries[discovery_id] = result

        return result

    def _categorize_discovery(
        self,
        overall_impact: float,
        dimension_scores: Dict[ImpactDimension, ImpactScore]
    ) -> TriageCategory:
        """Categorize discovery into triage category"""
        # Check for insufficient evidence
        conf_score = dimension_scores.get(ImpactDimension.CONFIDENCE)
        if conf_score and conf_score.score < 0.3:
            return TriageCategory.INSUFFICIENT_EVIDENCE

        # Check for reproducibility issues
        repro_score = dimension_scores.get(ImpactDimension.REPRODUCIBILITY)
        if repro_score and repro_score.score < 0.4:
            return TriageCategory.REPRODUCIBILITY_NEEDED

        # Categorize by impact
        if overall_impact > 0.85:
            return TriageCategory.CRITICAL_BREAKTHROUGH
        elif overall_impact > 0.70:
            return TriageCategory.HIGH_PRIORITY
        elif overall_impact > 0.50:
            return TriageCategory.MEDIUM_PRIORITY
        else:
            return TriageCategory.LOW_PRIORITY

    def _determine_validation_strategy(
        self,
        discovery: Dict[str, Any],
        dimension_scores: Dict[ImpactDimension, ImpactScore]
    ) -> ValidationStrategy:
        """Determine best validation strategy"""
        # If high confidence and reproducibility
        repro_score = dimension_scores.get(ImpactDimension.REPRODUCIBILITY)
        conf_score = dimension_scores.get(ImpactDimension.CONFIDENCE)

        if repro_score and repro_score.score > 0.8 and conf_score and conf_score.score > 0.8:
            return ValidationStrategy.IMMEDIATE_PUBLICATION

        # If needs more data
        if discovery.get('needs_follow_up_observation', False):
            return ValidationStrategy.TARGETED_OBSERVATION

        # If low confidence but high novelty
        if conf_score and conf_score.score < 0.5:
            return ValidationStrategy.CROSS_VALIDATION

        # Default
        return ValidationStrategy.REPRODUCTION_REQUIRED

    def _generate_recommended_action(
        self,
        category: TriageCategory,
        dimension_scores: Dict[ImpactDimension, ImpactScore]
    ) -> str:
        """Generate recommended action"""
        actions = {
            TriageCategory.CRITICAL_BREAKTHROUGH:
                "IMMEDIATE ACTION: Draft paper for rapid publication, "
                "assemble collaboration, prepare press release",
            TriageCategory.HIGH_PRIORITY:
                "Investigate within 1-2 weeks: gather additional evidence, "
                "contact domain experts, begin drafting paper",
            TriageCategory.MEDIUM_PRIORITY:
                "Add to research queue: interesting finding worth exploring "
                "when resources permit",
            TriageCategory.LOW_PRIORITY:
                "Log for future reference: may become relevant with additional context",
            TriageCategory.INSUFFICIENT_EVIDENCE:
                "GATHER MORE DATA: Current evidence insufficient for publication",
            TriageCategory.REPRODUCIBILITY_NEEDED:
                "IMPROVE REPRODUCIBILITY: Document methodology, share code and data"
        }
        return actions.get(category, "Review and assess")

    def _estimate_investigation_time(
        self,
        discovery: Dict[str, Any],
        category: TriageCategory
    ) -> str:
        """Estimate time needed for investigation"""
        time_estimates = {
            TriageCategory.CRITICAL_BREAKTHROUGH: "2-4 weeks (rapid publication)",
            TriageCategory.HIGH_PRIORITY: "1-2 months",
            TriageCategory.MEDIUM_PRIORITY: "3-6 months",
            TriageCategory.LOW_PRIORITY: "6+ months",
            TriageCategory.INSUFFICIENT_EVIDENCE: "Until sufficient data gathered",
            TriageCategory.REPRODUCIBILITY_NEEDED: "2-4 weeks (documentation)"
        }
        return time_estimates.get(category, "TBD")

    def _calculate_publication_readiness(
        self,
        dimension_scores: Dict[ImpactDimension, ImpactScore]
    ) -> float:
        """Calculate publication readiness score (0-1)"""
        # Key dimensions for publication
        conf_score = dimension_scores.get(ImpactDimension.CONFIDENCE)
        repro_score = dimension_scores.get(ImpactDimension.REPRODUCIBILITY)
        novel_score = dimension_scores.get(ImpactDimension.NOVELTY)
        sci_val_score = dimension_scores.get(ImpactDimension.SCIENTIFIC_VALUE)

        scores = []
        if conf_score:
            scores.append(conf_score.score)
        if repro_score:
            scores.append(repro_score.score)
        if novel_score:
            scores.append(novel_score.score)
        if sci_val_score:
            scores.append(sci_val_score.score)

        return np.mean(scores) if scores else 0.0

    def _identify_additional_evidence_needed(
        self,
        discovery: Dict[str, Any],
        dimension_scores: Dict[ImpactDimension, ImpactScore]
    ) -> List[str]:
        """Identify additional evidence needed"""
        needed = []

        # Check confidence
        conf_score = dimension_scores.get(ImpactDimension.CONFIDENCE)
        if conf_score and conf_score.score < 0.7:
            needed.append("Additional statistical validation needed")

        # Check reproducibility
        repro_score = dimension_scores.get(ImpactDimension.REPRODUCIBILITY)
        if repro_score and repro_score.score < 0.7:
            needed.append("Share reproducible code and data")

        # Check causal understanding
        causal_score = dimension_scores.get(ImpactDimension.CAUSAL_IMPORTANCE)
        if causal_score and causal_score.score < 0.5:
            needed.append("Causal mechanism investigation needed")

        # Check adversarial validation
        if not discovery.get('adversarial_validation'):
            needed.append("Adversarial validation recommended")

        return needed

    def _suggest_collaborators(
        self,
        discovery: Dict[str, Any],
        domain: str
    ) -> List[str]:
        """Suggest potential collaborators"""
        collaborators = []

        # Domain experts
        if domain:
            collaborators.append(f"{domain.replace('_', ' ').title()} expert")

        # Specialists based on discovery type
        claim = discovery.get('claim', '').lower()

        if 'causal' in claim:
            collaborators.append("Causal inference specialist")

        if 'statistic' in claim or 'correlation' in claim:
            collaborators.append("Statistician")

        if discovery.get('simulations'):
            collaborators.append("Computational astrophysicist")

        if discovery.get('observations'):
            collaborators.append("Observational astronomer")

        return collaborators[:5]  # Limit to 5

    def triage_batch(
        self,
        discoveries: List[Dict[str, Any]],
        domain: str = ""
    ) -> List[DiscoveryTriageResult]:
        """
        Triage multiple discoveries.

        Args:
            discoveries: List of discovery dicts
            domain: Domain context

        Returns:
            List of triage results
        """
        results = []
        for discovery in discoveries:
            result = self.triage_discovery(discovery, domain)
            results.append(result)

        # Update queue (sorted by impact)
        self.queue.queue = sorted(results, key=lambda r: r.overall_impact_score, reverse=True)

        return results

    def get_priority_queue(self) -> List[DiscoveryTriageResult]:
        """Get discoveries sorted by priority"""
        return sorted(self.queue.queue, key=lambda r: r.overall_impact_score, reverse=True)

    def generate_triage_report(self) -> str:
        """Generate summary report of triage results"""
        lines = []
        lines.append("=== DISCOVERY TRIAGE REPORT ===\n")

        # Summary statistics
        n_total = len(self.queue.queue)
        n_critical = sum(1 for r in self.queue.queue
                        if r.triage_category == TriageCategory.CRITICAL_BREAKTHROUGH)
        n_high = sum(1 for r in self.queue.queue
                    if r.triage_category == TriageCategory.HIGH_PRIORITY)
        n_medium = sum(1 for r in self.queue.queue
                      if r.triage_category == TriageCategory.MEDIUM_PRIORITY)
        n_low = sum(1 for r in self.queue.queue
                   if r.triage_category == TriageCategory.LOW_PRIORITY)

        lines.append(f"Total Discoveries: {n_total}")
        lines.append(f"Critical Breakthroughs: {n_critical}")
        lines.append(f"High Priority: {n_high}")
        lines.append(f"Medium Priority: {n_medium}")
        lines.append(f"Low Priority: {n_low}\n")

        # Top discoveries
        lines.append("TOP 5 DISCOVERIES:\n")
        for i, result in enumerate(self.get_priority_queue()[:5], 1):
            lines.append(f"{i}. [{result.triage_category.value.upper()}] "
                        f"(Impact: {result.overall_impact_score:.2f})")
            lines.append(f"   Claim: {result.claim[:80]}...")
            lines.append(f"   Action: {result.recommended_action}\n")

        return "\n".join(lines)


# Factory functions

def create_discovery_triage_system() -> DiscoveryTriageSystem:
    """Factory function to create DiscoveryTriageSystem"""
    return DiscoveryTriageSystem()


def create_impact_scoring_engine() -> ImpactScoringEngine:
    """Factory function to create ImpactScoringEngine"""
    return ImpactScoringEngine()


# Convenience function

def triage_discoveries(
    discoveries: List[Dict[str, Any]],
    domain: str = ""
) -> Dict[str, Any]:
    """
    Triage a list of discoveries and return prioritized results.

    Args:
        discoveries: List of discovery dicts
        domain: Domain context

    Returns:
        Complete triage results with report
    """
    system = create_discovery_triage_system()
    results = system.triage_batch(discoveries, domain)
    report = system.generate_triage_report()

    return {
        'triage_results': results,
        'priority_queue': system.get_priority_queue(),
        'report': report,
        'statistics': {
            'total': len(results),
            'critical': sum(1 for r in results if r.triage_category == TriageCategory.CRITICAL_BREAKTHROUGH),
            'high_priority': sum(1 for r in results if r.triage_category == TriageCategory.HIGH_PRIORITY),
            'medium_priority': sum(1 for r in results if r.triage_category == TriageCategory.MEDIUM_PRIORITY),
            'low_priority': sum(1 for r in results if r.triage_category == TriageCategory.LOW_PRIORITY)
        }
    }
