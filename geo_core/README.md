# geo_core - GEODISC core package

The core package of **GEODISC** (Geological Discovery): a domain-independent
scientific-discovery engine plus a geochemistry domain layer and a mechanistic
process-graph capability.

## Layout
- `core/` - `EnhancedUnifiedSTANSystem` unified orchestration
- `reasoning/`, `causal/`, `swarm/`, `memory/`, `symbolic/`, `intelligence/`,
  `metacognitive/`, `theoretical_discovery/`, `self_teaching/`, `knowledge/`,
  `physics/`, `mathematical/`, `neural/`, `retrieval/`, `simulation/`,
  `autonomy/`, `utils/` - domain-independent subsystems
- `domains/` - `BaseDomainModule` framework + domain-neutral modules +
  `geochemistry/` (Levels 2-17)
- `mechanistic_process_graphs/` - edge-weighted causal-mechanistic graphs
- `scientific_discovery/` - fiction-free discovery chokepoint (`discovery_store`),
  the `autonomous_discovery_supervisor`, and the `evolved_analysis` engine
- `tests/` - regression tests (incl. `test_discovery_chokepoint.py`)

## Entry points
```python
from geo_core import create_geo_stan_system        # construct the system
python -m geo_core.autonomous_discovery_supervisor  # run the supervisor
```

See `../CLAUDE.md` and `../CLAUDE_GEO_ARCHITECTURE.md` for the full guide.
