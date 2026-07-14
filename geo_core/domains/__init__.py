"""
Base domain module interface for GEODISC

Provides abstract base class and configuration for all domain modules.
Enables plug-and-play domain expansion with hot-swapping capabilities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


@dataclass
class DomainConfig:
    """
    Configuration for domain modules

    Attributes:
        domain_name: Unique identifier for the domain
        version: Domain module version
        dependencies: List of other domains this domain depends on
        keywords: Keywords for automatic domain detection
        task_types: Task types this domain can handle
        enabled: Whether the domain is enabled
        description: Human-readable description
        capabilities: List of specific capabilities provided
    """
    domain_name: str
    version: str
    dependencies: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    task_types: List[str] = field(default_factory=list)
    enabled: bool = True
    description: str = ""
    capabilities: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration"""
        if not self.domain_name:
            raise ValueError("domain_name cannot be empty")
        if not self.version:
            raise ValueError("version cannot be empty")


@dataclass
class DomainQueryResult:
    """
    Result from domain query processing

    Attributes:
        domain_name: Name of domain that processed the query
        answer: Generated answer
        confidence: Confidence in the answer (0-1)
        reasoning_trace: List of reasoning steps
        capabilities_used: Capabilities used in processing
        metadata: Additional metadata
    """
    domain_name: str
    answer: str
    confidence: float
    reasoning_trace: List[str] = field(default_factory=list)
    capabilities_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate result"""
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

    def __getitem__(self, key: str) -> Any:
        """Support dict-style access for backward compatibility"""
        return getattr(self, key, self.metadata.get(key))

    def get(self, key: str, default: Any = None) -> Any:
        """Get method for dict-like compatibility"""
        return getattr(self, key, self.metadata.get(key, default))


@dataclass
class CrossDomainConnection:
    """
    Represents a connection between two domains

    Attributes:
        source_domain: Source domain name
        target_domain: Target domain name
        connection_type: Type of connection (analogy, shared_concept, etc.)
        strength: Strength of connection (0-1)
        description: Description of the connection
        transferable_knowledge: Knowledge that can be transferred
    """
    source_domain: str
    target_domain: str
    connection_type: str
    strength: float
    description: str = ""
    transferable_knowledge: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate connection"""
        if not 0 <= self.strength <= 1:
            raise ValueError("strength must be between 0 and 1")


class BaseDomainModule(ABC):
    """
    Abstract base class for all domain modules

    All domain modules must inherit from this class and implement
    the required methods. This enables plug-and-play domain expansion.
    """

    def __init__(self, config: Optional[DomainConfig] = None):
        """
        Initialize domain module

        Args:
            config: Domain configuration. If None, uses get_default_config()
        """
        self.config = config or self.get_default_config()
        self._initialized = False

    @abstractmethod
    def get_default_config(self) -> DomainConfig:
        """
        Return default configuration for this domain

        Returns:
            DomainConfig with default values
        """
        pass

    def get_config(self) -> DomainConfig:
        """Return domain configuration"""
        return self.config

    @abstractmethod
    def initialize(self, global_config: Dict[str, Any]) -> None:
        """
        Initialize domain with global configuration

        Args:
            global_config: Global STAN configuration
        """
        self._initialized = True
        logger.info(f"Domain {self.config.domain_name} initialized")

    @abstractmethod
    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        """
        Process domain-specific query

        Args:
            query: User query
            context: Additional context (parameters, metadata, etc.)

        Returns:
            DomainQueryResult with answer and metadata
        """
        if not self._initialized:
            raise RuntimeError(f"Domain {self.config.domain_name} not initialized")

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of domain capabilities

        Returns:
            List of capability names
        """
        pass

    def discover_cross_domain_connections(
        self,
        other_domains: List['BaseDomainModule']
    ) -> List[CrossDomainConnection]:
        """
        Discover connections to other domains

        Args:
            other_domains: List of other domain modules

        Returns:
            List of discovered connections
        """
        connections = []

        for other_domain in other_domains:
            if other_domain.config.domain_name == self.config.domain_name:
                continue

            # Look for shared keywords
            shared_keywords = set(self.config.keywords) & set(other_domain.config.keywords)

            # Look for shared capabilities
            shared_capabilities = set(self.config.capabilities) & set(other_domain.config.capabilities)

            # Create connection if significant overlap
            overlap_score = (len(shared_keywords) + len(shared_capabilities)) / max(
                len(self.config.keywords) + len(self.config.capabilities),
                len(other_domain.config.keywords) + len(other_domain.config.capabilities),
                1
            )

            if overlap_score > 0.1:  # 10% overlap threshold
                connection = CrossDomainConnection(
                    source_domain=self.config.domain_name,
                    target_domain=other_domain.config.domain_name,
                    connection_type="shared_concepts",
                    strength=overlap_score,
                    description=f"Shared {len(shared_keywords)} keywords and {len(shared_capabilities)} capabilities",
                    transferable_knowledge=list(shared_keywords | shared_capabilities)
                )
                connections.append(connection)

        return connections

    def can_handle_query(self, query: str) -> float:
        """
        Determine if this domain can handle a query

        Args:
            query: User query

        Returns:
            Confidence score (0-1) indicating how well this domain can handle the query
        """
        query_lower = query.lower()
        keyword_matches = sum(1 for kw in self.config.keywords if kw in query_lower)

        if not self.config.keywords:
            return 0.0

        return keyword_matches / len(self.config.keywords)

    def get_status(self) -> Dict[str, Any]:
        """
        Get domain status information

        Returns:
            Dictionary with status information
        """
        return {
            'domain_name': self.config.domain_name,
            'version': self.config.version,
            'initialized': self._initialized,
            'enabled': self.config.enabled,
            'capabilities': self.get_capabilities(),
            'dependencies': self.config.dependencies
        }

    def __repr__(self) -> str:
        return f"DomainModule({self.config.domain_name}, v{self.config.version})"


class DomainModuleRegistry:
    """
    Registry for domain module classes

    Enables automatic discovery and loading of domain modules.
    """
    _domain_classes: Dict[str, type] = {}

    @classmethod
    def register(cls, domain_class: type) -> None:
        """Register a domain module class"""
        domain_name = domain_class.__name__
        cls._domain_classes[domain_name] = domain_class
        logger.info(f"Registered domain class: {domain_name}")

    @classmethod
    def unregister(cls, domain_class: type) -> None:
        """Unregister a domain module class"""
        domain_name = domain_class.__name__
        if domain_name in cls._domain_classes:
            del cls._domain_classes[domain_name]

    @classmethod
    def get(cls, domain_name: str) -> Optional[type]:
        """Get registered domain class by name"""
        return cls._domain_classes.get(domain_name)

    @classmethod
    def list_domains(cls) -> List[str]:
        """List all registered domain class names"""
        return list(cls._domain_classes.keys())

    @classmethod
    def create(cls, domain_name: str, **kwargs) -> Optional['BaseDomainModule']:
        """Create instance of registered domain class"""
        domain_class = cls.get(domain_name)
        if domain_class:
            return domain_class(**kwargs)
        return None


def register_domain(cls: type) -> type:
    """
    Decorator to register a domain module class

    Usage:
        @register_domain
        class MyDomain(BaseDomainModule):
            pass
    """
    DomainModuleRegistry.register(cls)
    return cls


# Import DomainRegistry from registry module
from .registry import DomainRegistry


# ----------------------------------------------------------------------------
# Domain-neutral modules (kept from the original set; usable by any science).
# Each import is guarded so a missing optional dependency degrades gracefully.
# ----------------------------------------------------------------------------
NEUTRAL_DOMAIN_IMPORTS = {
    "molecular_spectroscopy": ("MolecularSpectroscopyDomain", "create_molecular_spectroscopy_domain"),
    "fluid_dynamics": ("FluidDynamicsDomain", "create_fluid_dynamics_domain"),
    "dynamical_systems": ("DynamicalSystemsDomain", "create_dynamical_systems_domain"),
    "numerical_methods": ("NumericalMethodsDomain", "create_numerical_methods_domain"),
    "signal_processing": ("SignalProcessingDomain", "create_signal_processing_domain"),
    "inverse_problems": ("InverseProblemsDomain", "create_inverse_problems_domain"),
    "hpc": ("HPCDomain", "create_hpc_domain"),
    "statistical_mechanics": ("StatisticalMechanicsDomain", "create_statistical_mechanics_domain"),
    "prebiotic_chemistry": ("PrebioticChemistryDomain", "create_prebiotic_chemistry_domain"),
}

import importlib as _importlib

# Resolve neutral domains and expose their symbols at package level.
_loaded_neutral = []
for _mod_name, (_cls, _factory) in NEUTRAL_DOMAIN_IMPORTS.items():
    try:
        _mod = _importlib.import_module(f".{_mod_name}", package=__name__)
        globals()[_cls] = getattr(_mod, _cls)
        globals()[_factory] = getattr(_mod, _factory)
        _loaded_neutral.append(_cls)
    except Exception:
        globals()[_cls] = None
        globals()[_factory] = None

# ----------------------------------------------------------------------------
# Geochemistry domains (GEODISC Levels 2-17). Populated in
# geo_core/domains/geochemistry/. Scaffolds only at this stage.
# ----------------------------------------------------------------------------
try:
    from .geochemistry import ALL_GEODISC_DOMAINS, register_all as register_geo_domains
    GEODISC_DOMAINS_AVAILABLE = True
except Exception:
    ALL_GEODISC_DOMAINS = []
    register_geo_domains = None
    GEODISC_DOMAINS_AVAILABLE = False


# Public API
__all__ = [
    # Framework
    "DomainConfig",
    "DomainQueryResult",
    "CrossDomainConnection",
    "BaseDomainModule",
    "DomainModuleRegistry",
    "DomainRegistry",
    "register_domain",
    # Neutral domains
    *_loaded_neutral,
    # Geochemistry
    "ALL_GEODISC_DOMAINS",
    "register_geo_domains",
    "GEODISC_DOMAINS_AVAILABLE",
]
