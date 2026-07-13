"""
Causal Capabilities

This module contains causal inference and causal discovery capabilities.
"""

# Re-export for backward compatibility
import warnings

# Import from new locations
try:
    from .causal_engine import *
    from .fci_discovery import *
    from .explainable_causal import *
    from .temporal_causal import *
    from .universal_causal import *
except ImportError as e:
    warnings.warn(f"Some causal capabilities could not be imported: {e}")

__all__ = [
    # Causal inference
    'CausalEngine',
    'FCIDiscovery',
    'ExplainableCausal',
    'TemporalCausal',
    'UniversalCausal',
]
