"""
Autonomous Research System

This module contains the V7.0 autonomous research scientist system.
"""

# Import main system
from .v7_autonomous_scientist import (
    V7AutonomousScientist,
    create_v7_scientist,
    ResearchCycle,
    ResearchQuestion,
    Hypothesis,
    Experiment,
    ResearchResult,
    Publication
)

__all__ = [
    # Main system
    'V7AutonomousScientist',
    'create_v7_scientist',
    'ResearchCycle',
    'ResearchQuestion',
    'Hypothesis',
    'Experiment',
    'ResearchResult',
    'Publication',
]
