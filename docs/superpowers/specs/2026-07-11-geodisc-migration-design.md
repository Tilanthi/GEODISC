# GEODISC Migration — Design Specification

**Date:** 2026-07-11
**Status:** Approved (user granted full autonomous implementation permission)
**Scope:** Transform a copy of the ASTRA astrophysics discovery system into **GEODISC — Geological Discovery**, a geochemistry-focused scientific discovery system, by pruning astronomy content, rebranding, and scaffolding a geochemistry domain layer plus a novel mechanistic process-graph capability.

---

## 0. Guardrails (non-negotiable invariants)

1. **Never read or modify** `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main`. GEODISC and ASTRA-dev-main are unrelated — no imports, paths, symlinks, or references between them.
2. **No "ASTRA"/"Astra" branding** anywhere in GEODISC henceforth. The system is **GEODISC — Geological Discovery**, geochemistry-focused. Recorded as a top-level invariant in `CLAUDE.md`.
3. **Fiction-free principle preserved.** The `discovery_store` machine-verification chokepoint is retained unchanged in spirit; no mock/placeholder/synthetic discoveries under any circumstance.

---

## 1. Decisions (locked via user Q&A)

| Decision | Choice |
|---|---|
| Build scope | **Scaffold now, train later** — import-clean `geo_core` with geochemistry domain structure + process-graph capability + rebranded docs. Domain *content* skeletal. |
| Live service | **Stop, rebrand as GEODISC at end** — unload ASTRA LaunchAgent + stop process before changes; install `com.geodisc.discovery` at the end. |
| Purge depth | **Surgical** — remove astronomy modules/domains/engines; cut wired-in imports (stub the hooks); mechanically rename `astra→geo`; leave domain-neutral code untouched even if comments mention stars. |

---

## 2. Safe-cutover phase order

1. **Halt the live service.**
2. **Prune** everything outside the keep-set.
3. **Rename** `astra_core → geo_core` + rebrand `astra→geo`.
4. **Surgery** — cut the `astro_physics` wiring in `core/`.
5. **Scaffold** geochemistry domains + mechanistic process-graph capability.
6. **Docs** — rewrite CLAUDE.md + dependents.
7. **Verify** — import smoke test + chokepoint test.
8. **Reinstall** service as `com.geodisc.discovery`.

---

## 3. Prune map

### Delete (top-level, outside the keep-set)
- **Astronomy campaign/work folders & tarballs:** `ASTRA-dev/`, `RASTI_AI/`, `RASTI_paper/`, `W3_HGBS_filaments/`, `ISM_filaments/`, `filaments/`, `simulations/`, `injection_recovery_campaign/`, `DTC_APR2026/`, `FIELD_GEOMETRY_APR2026/`, `FILAMENT_SPACING_CAMPAIGN_APR2026/`, `MODE_IDENTITY_CAMPAIGN/`, `PEER_REVIEW_VALIDATION_TESTS/`, `SUBISOTHERMAL_PERPENDICULAR_CAMPAIGN/`, `targeted_supercritical_f15/`, `targeted_supercritical_f15_may2026/`, `THEORETICIAN_CAMPAIGN_2026/`, `theoretician_campaign_analysis/`, `BRIDGE_GRID_PACKAGE_200VCPU/`, `campaigns/`, `astra_live_backend/`, `data/`, `logs/`, `paper/`, all `*.tar.gz`.
- **Astronomy `.md/.pdf` docs:** `ASTRA_*.md/.pdf`, `ALPHAEVOLVE_*`, `AUTONOMOUS_*`, `PHOTON*`, `COMPREHENSIVE_REFEREE_*`, `ENHANCED_CAUSAL_*`, `REFEREE_*`, `ASTRA_discovery_rate_analysis.md`, etc.
- **ASTRA scripts:** `start_*.sh/.py`, `run_24_7_*`, `check_*_status.sh`, `view_*_discoveries.sh`, `monitor_discovery_fix.sh`, `stop_continuous_discovery.sh`, `start_continuous_discovery.sh`, `astra_context_restorer.py`, `auto_restore_context.py`, `extract_p1_rtc_subspace.py`.
- **Astronomy test scripts:** `test_astronomical_discovery.py`, `test_autonomous_*.py`, `test_transformational_*.py`, `test_validation_pipeline_integration.py`.
- **Runtime state/logs:** `.astra_*` (incl. the 334 MB log), `.evolution_checkpoint_*.json`, `astra_discoveries.db`.
- **Astronomy specs:** `docs/mnras_paper_outline.md`, `docs/superpowers/plans/*`, `.superpowers/sdd/*` (stellar-evolution content).

### Keep (infrastructure)
`.git/`, `.gitignore` (rewritten), `.superpowers/` (directory retained, astronomy content cleared), `docs/superpowers/specs/` (spec home).

### Keep + rewrite (docs)
`CLAUDE.md`; a lean set of **5** dependent docs rewritten as `CLAUDE_GEO_{FULL,ARCHITECTURE,QUICKSTART,TESTING,SYSTEM_STATUS}.md` (the two VALIDATION docs and all ASTRA reports deleted); `README.md`; `User_Manual/`.

---

## 4. geo_core internal surgery

### Delete entirely
`astro_physics/`, `trading/`, `legacy/`, the photo-z/SDSS `evolved_analysis` files (keep generic two-gate scaffolding), `astro_databases.py`, `astronomical_data_integration.py`, `safe_fits_reader.py`, the `autonomous_startup_discovery_v2*` fiction-emitter files, `genuine_discovery_pipeline.py`, `computational_analysis_engine.py`, `physics/nuclear_astro.py`.

### Domains
Delete ~60 astronomy modules. **Keep the framework** (`BaseDomainModule` + `DomainRegistry`) + ~15 domain-neutral modules: `atomic_physics`, `molecular_spectroscopy`, `fluid_dynamics`, `dynamical_systems`, `numerical_methods`, `signal_processing`, `inverse_problems`, `hpc`, `plasma_physics`, `quantum_applications`, `statistical_mechanics`, `prebiotic_chemistry`, `radiative_transfer_theory`, `mathematical`.

### Critical wiring cut
`core/unified.py`, `core/__init__.py`, `scientific_discovery/discovery_orchestrator.py`, `physics/__init__.py` import from `astro_physics` → remove those imports, stub the handful of astro capability hooks so `EnhancedUnifiedSTANSystem` still constructs. Keep `autonomous_discovery_supervisor.py` + `discovery_store.py` (the v14.0 truth).

### Rename
- Dir `astra_core → geo_core`.
- Imports `astra_core. → geo_core.`, `import astra_core → import geo_core`.
- Symbols `create_enhanced_stan_system` / `create_stan_system → create_geo_stan_system`.
- Paths `~/.astra_persistent → ~/.geodisc_persistent`, `.astra_* → .geodisc_*`.
- LaunchAgent `com.astra.discovery → com.geodisc.discovery`.
- Env `ASTRA_EVOLUTION_MODULE → GEODISC_EVOLUTION_MODULE` (`ANTHROPIC_AUTH_TOKEN` unchanged).
- The internal "STAN" symbolic-engine name is retained (it is not "ASTRA"); user-facing names are rebranded.

---

## 5. Geochemistry domain scaffold (17 levels)

Under `geo_core/domains/`, one `BaseDomainModule` subclass per level, organized by the build order Physics → Chemistry → … → Scientific Literature.

- Level 1 (general scientific reasoning) is the existing `reasoning/` + `causal/` core — **not** a new domain.
- New domain modules (Levels 2–17): `earth_system_science`, `sedimentology`, `taphonomy`, `organic_geochemistry`, `mineralogy`, `geochemistry`, `precambrian_geology`, `microbial_ecology`, `evolution`, `spectroscopy`, `thermodynamics`, `statistical_physics`, `imaging`, `bayesian_data_fusion`, `philosophy_of_science`, `scientific_literature`.
- Each is a **skeleton**: class shell + the subtopic checklist from the user's brief as a docstring + stub `process_query()` / `get_capabilities()` — ready for separate training.
- `domains/geochemistry/__init__.py` registers them with `DomainRegistry` and wires cross-domain connections (e.g. taphonomy ↔ organic_geochemistry ↔ mineralogy).

---

## 6. Mechanistic process-graph capability (novel feature)

New top-level module `geo_core/mechanistic_process_graphs/` (peer to `causal/`, `swarm/`).

- **Graph model:** nodes = mechanistic steps / state variables; edges carry `{probability, uncertainty, supporting_evidence[], mechanistic_type}`.
- Built on the existing `causal/` SCM + do-calculus, specialized for *mechanistic* (not merely statistical) causal chains.
- **Interface:**
  - `build_from_observations(observations)` — propose a graph (Bayesian structure learning).
  - `refine_with_evidence(graph, new_data)` — Bayesian edge updates; strengthens / weakens / splits links.
  - `compare_mechanisms(graph_a, graph_b)` — model comparison for competing explanations.
  - `explain_preservation(observations)` — the GOE use-case: infer which mix of O₂ / iron chemistry / mineral adsorption / decay / burial / thermal maturation best explains preserved organic carbon + recognizable morphology.
- **Wiring:** into `causal/` (SCM + do-calculus), `scientific_discovery/` (a refined graph counts as a discovery), and the `discovery_store` verification block (edge evidence = machine verification).
- **Scaffold + the GOE example graph** as a doctest; inference trained later.

Example mechanistic chain (each edge carries probability/uncertainty/evidence):
```
Low O₂ → Microbial respiration → Decay rate → Cell wall integrity
       → Silica nucleation → Mineral encapsulation → Morphological preservation
```

---

## 7. CLAUDE.md + docs rewrite

- `CLAUDE.md`: GEODISC identity; the ASTRA-dev-main prohibition (prominent); geochemistry focus; 17-level domain map; process-graph capability; fiction-free rules; no-ASTRA-reference invariant; renamed commands (`geo_core`, `com.geodisc.discovery`, `~/.geodisc_persistent`); system status reflecting the migration.
- Dependent docs: rewrite the kept 5 (`CLAUDE_GEO_*`).
- `README.md`: rewrite.

---

## 8. Verification gates

1. `python -c "import geo_core"` imports clean (no `ModuleNotFoundError`).
2. `python -c "from geo_core import create_geo_stan_system; create_geo_stan_system()"` constructs.
3. `discovery_store` chokepoint regression passes (adapted).
4. No stray `astra`/`ASTRA` strings in `geo_core/**/*.py` (except the prohibition note).
5. `com.geodisc.discovery` installed and idle; ASTRA service fully removed.

---

## 9. Open items to confirm during implementation

- Exact split of `evolved_analysis`: keep the generic AlphaEvolve two-gate loop, delete only photo-z/SDSS-specific files (`evolve_photoz.py`, `real_data.py`, README, SDSS refs in `run.py`).
- `relativistic_physics.py`: general relativity → keep; `nuclear_astro.py` → delete.
- Whether any domain-neutral module secretly imports astronomy (verify at surgery time).
