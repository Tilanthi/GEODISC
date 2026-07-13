# GEODISC User Manual
## Autonomous Scientific Discovery in Geochemistry

**Version**: 1.0 (GEODISC migration)
**Date**: July 2026
**Focus**: Proterozoic geochemistry, early-Earth atmospheric evolution, biological
evolution, and the oxygenic revolution's role in biological preservation.

---

## 1. Introduction

GEODISC (Geological Discovery) is an AGI-inspired framework for autonomous
hypothesis generation, mechanism discovery, and validation in geochemistry. It
combines a domain-independent scientific-reasoning core with a geochemistry
domain layer and a mechanistic process-graph capability.

Its central scientific question: *which combination of processes — oxygen
availability, iron chemistry, mineral adsorption, microbial decay, burial rate,
thermal maturation — best explains the observed preservation of both organic
carbon and recognizable morphology?* GEODISC shifts the focus from pattern
recognition to **mechanism discovery**.

## 2. System Architecture

- **Domain-independent core**: causal inference, Bayesian reasoning, swarm
  intelligence, stigmergic memory, symbolic reasoning, an LLM gateway,
  metacognitive monitoring. (See `CLAUDE_GEO_ARCHITECTURE.md`.)
- **Discovery pipeline**: a fiction-free single write chokepoint
  (`discovery_store`) plus an always-on supervisor and an AlphaEvolve-style
  two-gate evolutionary engine.
- **Geochemistry domain layer**: 16 `BaseDomainModule` scaffolds (Levels 2-17).
- **Mechanistic process-graph capability**: edge-weighted causal-mechanistic
  networks with per-edge probability, uncertainty, and evidence.

## 3. Installation and Setup

```bash
cd /Users/gjw255/astrodata/SWARM/GEODISC
python -c "import geo_core; from geo_core import create_geo_stan_system; create_geo_stan_system()"
```

The autonomous service (`com.geodisc.discovery`) runs the supervisor directly.

## 4. Basic Usage

```python
from geo_core import create_geo_stan_system
system = create_geo_stan_system()

# Mechanistic process graph
from geo_core import mechanistic_process_graphs as mpg
graph = mpg.explain_preservation()
print([n for n in graph.nodes])

# Domains
from geo_core.domains import geochemistry
print(len(geochemistry.ALL_GEODISC_DOMAINS), "geochemistry domains")
```

## 5. The 17 Domain Levels

Physics -> Chemistry -> Thermodynamics -> Earth System Science -> Geochemistry ->
Mineralogy -> Sedimentology -> Organic Geochemistry -> Microbiology ->
Taphonomy -> Precambrian Geology -> Analytical Instrumentation -> Scientific
Literature. (Full table in `CLAUDE.md`.)

## 6. Autonomous Discovery

The supervisor runs ingest-only by default. To enable evolutionary search, place
`ANTHROPIC_AUTH_TOKEN` and `GEODISC_EVOLUTION_MODULE` in
`~/.geodisc_persistent/llm_env` (chmod 600). It never falls back to fiction.

## 7. Testing

```bash
python -m pytest geo_core/tests/test_discovery_chokepoint.py -q
```

## Guardrails
- Never modify `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main` (unrelated predecessor).
- No fictional/synthetic discoveries.
