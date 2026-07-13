# GEODISC Architecture

GEODISC (Geological Discovery) = a **domain-independent scientific-discovery
core** + a **geochemistry domain layer** + a **mechanistic process-graph
capability**. This document maps the subsystems in `geo_core/`.

## Design principles
- **Fiction is impossible by construction.** One write chokepoint
  (`scientific_discovery/discovery_store.py`) rejects records without a machine
  `verification` block.
- **Domain knowledge is hot-swappable.** `BaseDomainModule` + `DomainRegistry`
  let domains register and route queries without touching core reasoning code.
- **Mechanism over correlation.** The process-graph capability makes
  competing mechanistic explanations first-class, comparable objects.

## Domain-independent core
| Subsystem | Role |
|-----------|------|
| `core/` | `EnhancedUnifiedSTANSystem` — unified orchestration (`unified_enhanced.py`, `unified.py`) |
| `reasoning/` | 70+ engines: Bayesian, abductive, analogical, counterfactual, MCTS, neural-symbolic |
| `causal/` | SCMs, PC/GES/FCI, do-calculus, counterfactual queries, simulation-based inference |
| `swarm/` | Swarm intelligence, pheromone dynamics, memory graph, multi-agent coordination |
| `memory/` | Hierarchical multi-scale memory (episodic, semantic, vector, working, persistent) |
| `symbolic/` | Symbolic reasoning, ontology, self-consistency |
| `intelligence/` | Multi-mind orchestration + `llm_gateway.py` (canonical LLM access) |
| `metacognitive/` | Data-sufficiency evaluation, meta-context |
| `scientific_discovery/` | Discovery pipeline, `discovery_store` chokepoint, `evolved_analysis` engine |
| `theoretical_discovery/` | Symbolic theoretic engine, theory refutation/synthesis |
| `self_teaching/` | Self-improvement, curriculum generation |
| `knowledge/` | Ontology, hierarchical knowledge compression |
| `physics/`, `mathematical/`, `neural/` | General physics, maths, NN infrastructure |
| `retrieval/`, `simulation/`, `autonomy/`, `utils/` | RAG, simulators, autonomy, helpers |

## Domain-neutral domain modules (kept under `domains/`)
`atomic_physics`, `molecular_spectroscopy`, `fluid_dynamics`, `dynamical_systems`,
`numerical_methods`, `signal_processing`, `inverse_problems`, `hpc`,
`plasma_physics`, `quantum_applications`, `statistical_mechanics`,
`prebiotic_chemistry`, `radiative_transfer_theory`, `radiative_processes`,
`general_relativity`.

## Geochemistry domain layer — `domains/geochemistry/`
- `base.py` — `GeochemistryDomainBase(BaseDomainModule)`: shared skeleton
  (`get_default_config`, `initialize`, `get_capabilities`, `process_query`).
- 16 domain modules (Levels 2-17), each a subclass declaring `DOMAIN_NAME`,
  `DESCRIPTION`, `CAPABILITIES` (training checklist), `KEYWORDS`,
  `DEPENDENCIES` (cross-domain edges).
- `__init__.py` — `ALL_GEODISC_DOMAINS` list + `register_all(registry)`.
- Registered into the live system during `EnhancedUnifiedSTANSystem` construction
  via `register_geo_domains` (see `core/unified_enhanced.py::_initialize_domains`).

## Mechanistic process-graph capability — `mechanistic_process_graphs/`
- `graph.py` — `MechanisticProcessGraph`, `MechanisticEdge` (probability,
  uncertainty, mechanistic_type, evidence[]), `Evidence`, `chain_to()`.
- `engine.py` — `build_from_observations`, `refine_with_evidence`,
  `compare_mechanisms`, `explain_preservation` (GOE use-case).
- `examples.py` — canonical GOE preservation graph + doctests.
- Designed to compose with `causal/` (SCM + do-calculus); a refined graph can
  count as a discovery whose verification block is the edge evidence.

## Discovery flow
1. `create_geo_stan_system()` constructs `EnhancedUnifiedSTANSystem`, which loads
   neutral domains + registers the 16 geochemistry domains.
2. `AutonomousDiscoverySupervisor.run_forever()` (run by the
   `com.geodisc.discovery` service) ingests machine-verified records and, when
   idle + LLM credentials available, runs the `evolved_analysis` engine.
3. Every candidate passes Gate 1 (real-data significance) + Gate 2 (literature
   novelty); both-gate survivors are written via `discovery_store.append_verified`.

## Open work
- Populate geochemistry domain *content* via separate training (scaffolds are
  import-clean and queryable now).
- Wire the process-graph engine to `causal/` structure learning + the
  discovery store verification block.
