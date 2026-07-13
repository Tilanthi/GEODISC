"""
V6.0 Theoretical Discovery System

This module provides comprehensive theoretical discovery capabilities for GEODISC,
enabling the system to move beyond empirical data analysis to genuine theoretical
insight and hypothesis generation.

Components:
- SymbolicTheoreticEngine: Analytical derivation from first principles
- TheorySpaceMapper: Navigation and mapping of theoretical frameworks
- TheoryRefutationEngine: Systematic testing of theories against constraints
- LiteratureTheorySynthesizer: Mining literature for theoretical insights
- ComputationalTheoreticalBridge: Connecting computation and theory
- V6TheoreticalDiscovery: Main integrator and orchestrator

Author: GEODISC Project
Version: 6.0
"""

from .symbolic_theoretic_engine import (
    SymbolicTheoreticEngine,
    PhysicsDomain,
    PhysicalConstraint,
    ScalingRelation
)
from .theory_space_mapper import (
    TheorySpaceMapper,
    TheoryFramework,
    TheoryConnection,
    TheoryType,
    TheoryRelation
)
from .theory_refutation_engine import (
    TheoryRefutationEngine,
    TheoryTestResult,
    ConstraintViolation,
    Severity
)
from .literature_theory_synthesizer import (
    LiteratureTheorySynthesizer,
    TheoreticalInsight,
    InsightType,
    Equation
)
from .computational_theoretical_bridge import (
    ComputationalTheoreticalBridge,
    SimulationDesign,
    SimulationResult,
    SimulationInsight,
    InsightCategory
)
from .v6_theoretical_discovery import (
    V6TheoreticalDiscovery,
    create_v6_theoretical_system,
    DiscoveryMode,
    DiscoveryResult,
    TheoreticalProblem
)

__all__ = [
    # Main components
    'SymbolicTheoreticEngine',
    'TheorySpaceMapper',
    'TheoryRefutationEngine',
    'LiteratureTheorySynthesizer',
    'ComputationalTheoreticalBridge',
    'V6TheoreticalDiscovery',
    'create_v6_theoretical_system',
    'DiscoveryMode',
    'DiscoveryResult',
    'TheoreticalProblem',
    # Supporting classes
    'PhysicsDomain',
    'PhysicalConstraint',
    'ScalingRelation',
    'TheoryFramework',
    'TheoryConnection',
    'TheoryType',
    'TheoryRelation',
    'TheoryTestResult',
    'ConstraintViolation',
    'Severity',
    'TheoreticalInsight',
    'InsightType',
    'Equation',
    'SimulationDesign',
    'SimulationResult',
    'SimulationInsight',
    'InsightCategory',
]
