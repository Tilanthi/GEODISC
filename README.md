# GEODISC: Autonomous Scientific Discovery in Geochemistry

GEODISC (Geological Discovery) is an AGI-inspired framework for autonomous
hypothesis generation, mechanism discovery, and validation in geochemistry —
with a focus on Proterozoic geochemistry, the atmospheric evolution of the early
Earth, biological evolution, and the role of the oxygenic revolution in
biological preservation.

It is built on a domain-independent reasoning core (causal inference, Bayesian
reasoning, swarm intelligence, stigmergic memory) and adds a geochemistry domain
layer plus a novel **mechanistic process-graph** capability.

## Overview

GEODISC integrates:
- **Causal inference & discovery** — structural causal models, PC/GES/FCI, do-calculus, counterfactuals
- **Bayesian data fusion** — multi-modal inversion over hidden preservation processes
- **Mechanistic process graphs** — competing mechanistic explanations as comparable, edge-weighted causal networks
- **Swarm intelligence** — multi-agent reasoning, stigmergic coordination
- **Geochemistry domain layer** — 16 domain modules (Earth system science, sedimentology, taphonomy, organic geochemistry, mineralogy, geochemistry, Precambrian geology, microbial ecology, evolution, spectroscopy, thermodynamics, statistical physics, imaging, Bayesian data fusion, philosophy of science, scientific literature)
- **Fiction-free discovery** — a single machine-verified write chokepoint; no synthetic discoveries

## Quick start

```python
from geo_core import create_geo_stan_system
system = create_geo_stan_system()
```

Autonomous discovery (standalone supervisor, launched by the
`com.geodisc.discovery` service):

```bash
python -m geo_core.autonomous_discovery_supervisor
```

## Mechanistic process graphs (headline capability)

Instead of treating scientific statements as isolated facts, GEODISC represents
them as components of a causal-mechanistic network where every edge carries
probability, uncertainty, and supporting evidence. New data strengthens,
weakens, or splits causal links.

```python
from geo_core import mechanistic_process_graphs as mpg
g = mpg.explain_preservation()                         # canonical GOE preservation chain
mpg.refine_with_evidence(g, ("silica_nucleation","mineral_encapsulation"),
                         mpg.Evidence(source="SEM imaging"),
                         new_probability=0.82, new_uncertainty=0.15)
```

## Repository layout
- `geo_core/` — the system (domain-independent core + `domains/geochemistry/` + `mechanistic_process_graphs/`)
- `docs/superpowers/specs/` — design spec
- `User_Manual/` — user manual
- `CLAUDE.md`, `CLAUDE_GEO_ARCHITECTURE.md` — project guide and architecture

## Status
Migration complete (2026-07-11). Domain *content* is scaffolded and awaiting
separate geochemistry training; the architecture is import-clean, the
fiction-free chokepoint is enforced (11 regression tests pass), and the 16
geochemistry domains + process-graph capability are wired in.

## Guardrails
- Never modify the unrelated predecessor folder `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main`.
- No fictional/synthetic/mock discoveries — only machine-verified results.
