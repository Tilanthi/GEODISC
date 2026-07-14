# GEODISC Project Guide

**GEODISC — Geological Discovery.** An autonomous scientific-discovery system for
geochemistry, focused on Proterozoic geochemistry, early-Earth atmospheric
evolution, biological evolution, and the role of the oxygenic revolution in
biological preservation. Built on a domain-independent reasoning core
(Bayesian inference, causal graphical models, swarm intelligence, stigmergic
memory) repurposed from astrophysics to geochemistry.

---

## 🚫 CRITICAL INVARIANTS (read first)

1. **NEVER read or modify any file in `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main`.**
   That folder is the unrelated predecessor system (ASTRA, astrophysics). GEODISC
   and ASTRA-dev-main are **entirely unrelated** — no imports, paths, symlinks, or
   references between them. Do not even inspect ASTRA-dev-main. If a command would
   target that path, do not run it.

2. **Never refer to "ASTRA" / "Astra" within GEODISC.** This system is GEODISC.
   All code, docs, services, and identifiers use the GEODISC / `geo_core` naming.
   (The only legitimate mentions are in the migration spec, which records the
   one-time repurposing from the astrophysics system.)

3. **No fictional / synthetic / mock discoveries.** Only genuine, machine-verified
   results may be written. The single write chokepoint
   `geo_core/scientific_discovery/discovery_store.py` rejects any record lacking
   a machine `verification` block. If an unverified record appears, it is a bug.

---

## Project Overview

- **GEODISC**: Autonomous Scientific Discovery in Geochemistry
- **Purpose**: Proterozoic geochemistry; atmospheric evolution of the early Earth;
  biological evolution; the oxygenic revolution/evolution and its role in
  biological preservation (taphonomy).
- **Core package**: `geo_core/` (one-time repurposing from the predecessor
  astrophysics `astra_core`; see the migration spec)
- **Status (2026-07-14)**: Astrophysics fully purged. All astronomy domain
  modules, the FPUS "Universe Simulator", the 4 astro domain packages
  (`general_relativity` / `plasma_physics` / `radiative_processes` /
  `radiative_transfer_theory`), astro physics models
  (`schwarzschild_metric` / `orbital_velocity` / `virial_theorem`), the GR
  `relativistic_physics` module, and all `STAN-XI-ASTRO` branding have been
  removed. `geo_core` imports clean and constructs; 16 geochemistry domain
  scaffolds (Levels 2-17) registered; mechanistic process-graph capability
  present. Domain *content* is skeletal — awaiting separate geochemistry
  training. Gates green: `import geo_core` + `create_geo_stan_system()`;
  `geo_core/tests/test_discovery_chokepoint.py` (11) +
  `geo_core/tests/test_claim_gates.py` (8); `mpg.explain_preservation()`;
  16 domains.
- **Pipeline discipline added (2026-07-14):** the two-gate engine now runs a
  static **leakage guard** (`claim_uses_heldout_split` in `claim_task.py`) that
  rejects any candidate whose Gate-1 headline ignores the held-out `df_eval`
  split — the §7.3 in-sample trap, run *before* the sandbox eval. It also logs
  one structured JSONL verdict per candidate (pass or fail) to
  `~/.geodisc_persistent/evolved_programs/claim_verdicts.jsonl` (§7.2) so the
  search funnel (where candidates die) is diagnosable. **Known gap:** the
  sandbox worker still cannot load real data — `real_data.load_split` was purged
  with the astrophysics data, so Gate 1 currently always fails; re-grounding it
  in geochemistry data (EarthChem / PBDB) is the remaining domain task.
- **Full astrophysics-content purge (2026-07-14):** all residual ASTROPHYSICS
  *content* removed or re-grounded to geochemistry. Identifier renames
  (`astra`→`geo`/`geodisc`, ~14 files). Deleted dead astro modules
  (`advanced_analysis` [GalaxyClassifier/photo-z], `theoretical_physics`
  [MHD/plasma stubs], `genuine_discovery_validator`, `data_repositories`
  [ALMA/NASA/ESO], the `autotunnel_viz` orphan, 3 `.backup`/`.broken` files,
  `test_phase_2_4` [exoplanet test]). Removed astrophysics-only domain packages
  (`atomic_physics`, `quantum_applications`) + 5 dead astro-domain imports
  (exoplanets/gravitational_waves/cosmology/solar_system/time_domain). The
  Phase-1 photo-z evolutionary engine was re-grounded to a **geochemistry
  TOC-prediction** task (`estimate_toc`, rmse/r² metrics); the MORK concept
  graph de-astro'd (Schwarzschild/Black-Hole/Cosmology/stellar-Fusion removed);
  the `astronomy` operating mode and astro examples (stellar/halo causal,
  planetary-nebulae demos, molecular-cloud prior knowledge) replaced with
  geochemistry (TOC / δ¹³C / redox / pyrite-framboid / taphonomy) across
  reasoning / capabilities / theoretical_discovery / autonomy / self_teaching /
  autonomous_research / retrieval. **Retained intentionally (not astrophysics
  domain content):** NASA ADS + arXiv `astro-ph` literature-retrieval
  infrastructure (also indexes geochemistry papers), the migration-spec path
  reference, the `STAN` identifier, and domain-neutral foundational-physics
  taxonomy (e.g. the cosmological length-scale tier, gravitational-physics task
  type). The unrelated `arc_agi/` / `arc_reasoning/` subsystem has pre-existing
  syntax errors, untouched and out of scope. Gates green throughout: 19 tests,
  smoke, capability, 16 domains; `python -m compileall geo_core` clean except
  the pre-existing arc_* errors.
- **Public repo**: https://github.com/Tilanthi/GEODISC (`main` branch; git
  remotes `origin` and `geodisc` both point here). Published as a clean
  geochemistry-only history. The precursor astrophysics history is preserved
  only on local branch `archive/astra-precursor` and on the unrelated ASTRA-dev
  repository — never push it to GEODISC.
- **Operating mode: interactive-only.** GEODISC services **user-requested
  tasks** via `create_geo_stan_system()`. The autonomous discovery supervisor
  (`com.geodisc.discovery`) is **intentionally disabled** — it is NOT installed
  in `~/Library/LaunchAgents` and does not run. The supervisor code and the
  `com.geodisc.discovery.plist` are retained in-repo so autonomous mode can be
  re-enabled later if needed (see "Commands"). This is the desired state, not a
  fault.
- **Spec**: `docs/superpowers/specs/2026-07-11-geodisc-migration-design.md`
- **Plan**: `docs/superpowers/plans/2026-07-11-geodisc-migration.md`

---

## Quick Start

GEODISC is used **interactively for user-requested tasks**:

```python
from geo_core import create_geo_stan_system
system = create_geo_stan_system()   # constructs the EnhancedUnifiedSTANSystem
```

Autonomous discovery is **off by default** (interactive-only mode). The
supervisor can be run manually if ever needed, but is not auto-started:

```bash
python -m geo_core.autonomous_discovery_supervisor   # optional, not auto-run
```

---

## Architecture

GEODISC keeps a **domain-independent core** and adds a **geochemistry domain
layer** plus a **mechanistic process-graph capability**.

### Domain-independent core (carries over to any science)
`core/` (unified system), `reasoning/`, `causal/`, `swarm/`, `memory/`,
`symbolic/`, `intelligence/` (LLM gateway), `metacognitive/`,
`theoretical_discovery/`, `self_teaching/`, `knowledge/`, `mathematical/`,
`neural/`, `retrieval/`, `simulation/`, `autonomy/`, `utils/`, `physics/`.

### Discovery pipeline (fiction-free)
`scientific_discovery/discovery_store.py` — single machine-verified write
chokepoint. `autonomous_discovery_supervisor.py` — always-on, user-yielding
supervisor that ingests verified records and (when idle + an LLM token is
available) runs the evolutionary engine. `scientific_discovery/evolved_analysis/`
— the generic AlphaEvolve two-gate engine (Gate 1: real-data significance,
sandboxed; Gate 2: literature novelty). Within it, `two_gate_eval` (in
`run_claim_search.py`) runs a static **leakage guard** (`claim_uses_heldout_split`)
before the sandbox — rejecting candidates whose headline ignores the held-out
`df_eval` split — and appends one structured JSONL verdict per candidate via
`verdict_log.py`.

### Geochemistry domain layer — `geo_core/domains/geochemistry/`
16 `BaseDomainModule` scaffolds (Levels 2-17), each declaring its capability
checklist as the training roadmap. Registered via `register_all(registry)`.

### Mechanistic process-graph capability — `geo_core/mechanistic_process_graphs/`
The headline novel feature. Represents scientific statements as a causal-
mechanistic network where every edge carries `{probability, uncertainty,
supporting_evidence, mechanistic_type}`. New data strengthens, weakens, or
splits edges, so the system compares competing **mechanistic** explanations
rather than fitting statistical correlations.

```
Low O2 -> Microbial respiration -> Decay rate -> Cell wall integrity
       -> Silica nucleation -> Mineral encapsulation -> Morphological preservation
```

See `CLAUDE_GEO_ARCHITECTURE.md` for the full subsystem map.

---

## The 17 Geochemistry Domain Levels

| # | Level | Module (`domains/geochemistry/`) |
|---|-------|----------------------------------|
| 1 | General scientific reasoning | *(core: `reasoning/` + `causal/`)* |
| 2 | Earth System Science | `earth_system_science` |
| 3 | Sedimentology | `sedimentology` |
| 4 | Taphonomy *(central)* | `taphonomy` |
| 5 | Organic Geochemistry | `organic_geochemistry` |
| 6 | Mineralogy | `mineralogy` |
| 7 | Geochemistry | `general_geochemistry` |
| 8 | Precambrian Geology | `precambrian_geology` |
| 9 | Microbial Ecology | `microbial_ecology` |
| 10 | Evolution | `evolution` |
| 11 | Spectroscopy & Instrumentation | `spectroscopy` |
| 12 | Thermodynamics | `thermodynamics` |
| 13 | Statistical Physics | `statistical_physics` |
| 14 | Imaging | `imaging` |
| 15 | Bayesian Data Fusion | `bayesian_data_fusion` |
| 16 | Philosophy of Science | `philosophy_of_science` |
| 17 | Scientific Literature | `scientific_literature` |

Recommended build/training order: Physics -> Chemistry -> Thermodynamics -> Earth
System Science -> Geochemistry -> Mineralogy -> Sedimentology -> Organic
Geochemistry -> Microbiology -> Taphonomy -> Precambrian Geology -> Analytical
Instrumentation -> Scientific Literature.

---

## Commands

**Service management** (`com.geodisc.discovery`) — **currently disabled by design
(interactive-only mode)**. The service is not installed and not running. To
re-enable autonomous discovery later, if ever required:
```bash
cp com.geodisc.discovery.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.geodisc.discovery.plist
launchctl list com.geodisc.discovery
tail -f .geodisc_service.log
```
To disable again:
```bash
launchctl unload ~/Library/LaunchAgents/com.geodisc.discovery.plist
rm ~/Library/LaunchAgents/com.geodisc.discovery.plist
```
> Do **not** touch `com.astra.discovery` — that agent belongs to the unrelated
> ASTRA-dev-main system.

**System status:**
```python
status = system.get_discovery_status()
```

**Enabling autonomous evolution:** the supervisor runs ingest-only until
`~/.geodisc_persistent/llm_env` (chmod 600) contains `ANTHROPIC_AUTH_TOKEN`
(+ optional base URL) and `GEODISC_EVOLUTION_MODULE` (e.g.
`evolved_analysis.run_claim_search` for Phase-2 open-ended search). It never
falls back to fiction.

---

## Persistent Memory & Key Files
- `~/.geodisc_persistent/` — GEODISC persistent state, conversation context, LLM env
- `~/.geodisc_persistent/discovery_memory.json` — verified discoveries
- `~/.geodisc_persistent/evolved_programs/claim_verdicts.jsonl` — per-candidate
  two-gate verdict log (one JSONL line each, with `outcome` funnel bucket) for
  the evolutionary search
- `.geodisc_state.json`, `.geodisc_service.log` — runtime state/logs (gitignored)

---

## Testing
```bash
python -m pytest geo_core/tests/test_discovery_chokepoint.py geo_core/tests/test_claim_gates.py -q  # fiction-free gate (11) + gate discipline (8)
python -c "import geo_core; from geo_core import create_geo_stan_system; create_geo_stan_system()"  # smoke
python -c "from geo_core import mechanistic_process_graphs as mpg; mpg.explain_preservation()"     # capability
python -c "from geo_core.domains import geochemistry; print(len(geochemistry.ALL_GEODISC_DOMAINS))" # 16
```

**Note:** `geo_core/arc_reasoning/improved_solver.py` has a pre-existing syntax
error (a `[...]` list literal never closed) inherited from the astrophysics
codebase; it is not on any live import path and is out of scope for the
geochemistry migration.

---

## GitHub
This repository is GEODISC only. When pushing, target only the GEODISC remote and
ensure all content is geochemistry-related. (ASTRA-dev-main is a separate,
unrelated repository and must never be touched.)

**Push target (Glenn's GEODISC repo):** When asked to push to Glenn's GEODISC
GitHub repository — e.g. "push to Glenn's GitHub repo", "push GEODISC to GitHub",
or any push of this repo — **always push to the `main` branch of
https://github.com/Tilanthi/GEODISC** (configured as the `geodisc` git remote).
Never push GEODISC content to the `origin` remote (which points at the unrelated
ASTRA-dev astrophysics repository) or to any ASTRA remote. If a push would also
publish astrophysics code/data/history, do not proceed — the public GEODISC repo
is geochemistry-only.
