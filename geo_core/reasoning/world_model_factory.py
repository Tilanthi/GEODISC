"""
World Model Factory for STAN

Provides singleton instances of world models for counterfactual reasoning.
This is the missing piece that breaks counterfactual reasoning.

Date: 2025-12-11
Version: 1.0
"""

from typing import Optional, Dict, Any
from geo_core.reasoning.unified_world_model import UnifiedWorldModel, CausalGraph, CausalEdge, Belief, BeliefType, Hypothesis


# Singleton instances
_world_model: Optional[UnifiedWorldModel] = None
_integration_bus = None


def get_world_model(config: Optional[Dict[str, Any]] = None) -> UnifiedWorldModel:
    """
    Get or create the singleton world model instance.

    This is the factory function that counterfactual reasoning expects.
    """
    global _world_model

    if _world_model is None:
        _world_model = UnifiedWorldModel()

        # Initialize with basic geochemistry knowledge
        _initialize_geochemistry_knowledge(_world_model)

    return _world_model


def _initialize_geochemistry_knowledge(world_model: UnifiedWorldModel):
    """Initialize world model with geochemistry / taphonomy knowledge"""

    # Add causal knowledge about organic-carbon preservation
    causal_knowledge = [
        # Oxygen levels -> preservation
        CausalEdge(
            edge_id="oxygen_to_preservation",
            cause="dissolved_oxygen_level",
            effect="organic_carbon_preservation",
            strength=0.85,
            mechanism="microbial_respiration",
            confidence=0.9
        ),
        CausalEdge(
            edge_id="sedimentation_to_preservation",
            cause="sedimentation_rate",
            effect="organic_carbon_preservation",
            strength=0.7,
            mechanism="rapid_burial",
            confidence=0.85
        ),
        CausalEdge(
            edge_id="porewater_to_preservation",
            cause="porewater_chemistry",
            effect="organic_carbon_preservation",
            strength=0.6,
            mechanism="diagenetic_alteration",
            confidence=0.8
        ),
        # Organic-matter flux -> preservation efficiency
        CausalEdge(
            edge_id="om_flux_to_efficiency",
            cause="organic_matter_flux",
            effect="preservation_efficiency",
            strength=0.9,
            mechanism="burial_flux_balance",
            confidence=0.88
        ),
        CausalEdge(
            edge_id="efficiency_to_preservation",
            cause="preservation_efficiency",
            effect="organic_carbon_preservation",
            strength=0.92,
            mechanism="preservation_threshold",
            confidence=0.9
        ),
    ]

    for edge in causal_knowledge:
        world_model.causal_graph.add_edge(edge)

    # Add key hypothesis about Proterozoic organic-carbon preservation
    hypothesis = Hypothesis(
        hypothesis_id="proterozoic_low_o2_preservation",
        statement="Low dissolved O2 in Proterozoic oceans enhances organic-carbon preservation by suppressing oxidative decay prior to burial",
        confidence=0.9,
        status="active",
        evidence_for=[],  # Changed from 'evidence' to 'evidence_for'
        predictions=["Higher TOC preservation efficiency in low-O2 Proterozoic basins"],
        tests_performed=["Redox proxy analysis", "TOC measurements across GOE intervals"]
    )

    world_model.add_hypothesis(hypothesis, notify=False)

    # Add physical constraints
    constraints = {
        "redox_threshold": {
            "formula": "preservation_rate ~ k * [O2]^(-alpha)",
            "parameters": {"k": "decay_constant", "O2": "dissolved_oxygen", "alpha": "oxidation_order"},
            "typical_value": "anoxic_favorable",
            "confidence": 0.9
        },
        "burial_rate_threshold": {
            "formula": "F_burial = F_OM * (1 - f_decay)",
            "parameters": {"F_burial": "burial_flux", "F_OM": "organic_matter_flux", "f_decay": "decay_fraction"},
            "typical_value": "high_sedimentation_favorable",
            "confidence": 0.85
        },
        "silicification_rate": {
            "formula": "d[SiO2]/dt = k_sil * [Si] * f(pH, T)",
            "parameters": {"k_sil": "silicification_rate_constant", "Si": "dissolved_silica", "pH": "acidity", "T": "temperature"},
            "typical_value": "variable",
            "confidence": 0.8
        }
    }

    for name, constraint_data in constraints.items():
        world_model.constraints[name] = constraint_data


def reset_world_model():
    """Reset the world model (useful for testing)"""
    global _world_model
    _world_model = None
