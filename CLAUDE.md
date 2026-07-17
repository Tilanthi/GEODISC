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
   That folder is the unrelated predecessor system. GEODISC and ASTRA-dev-main
   are **entirely unrelated** — no imports, paths, or references between them.
2. **Never refer to "ASTRA" / "Astra" within GEODISC.** This system is GEODISC.
   All code, docs, services, and identifiers use the GEODISC / `geo_core` naming.
3. **No fictional / synthetic / mock discoveries.** Only genuine, machine-verified
   results may be written. The single write chokepoint
   `geo_core/scientific_discovery/discovery_store.py` rejects any record lacking
   a machine `verification` block.

---

## Current State (2026-07-17)

- **Codebase:** geochemistry-only, fully purged of astrophysics.
  `compileall` 0 errors; full module import sweep clean (0 broken); 43 gate
  tests green; smoke + 16 domains + mechanistic process-graph capability OK.
  Zero "ASTRA"/"RASTI" references in code; legacy astrophysics `data/` purged.
  (The only remaining "ASTRA" mentions in the repo are the protective fence
  below — invariant #1/#2 — and the migration-history docs that record how
  GEODISC was created from the geochemistry repurposing.)
- **Code hardening (2026-07-17 audit):** emit path is now atomic (temp +
  `os.replace`; a timeout-kill can no longer truncate the staging file and
  silently drop both-gate survivors). Restored broken public APIs:
  `geo_core.MORKOntology` + kernel-memory block, physics autodiff
  (`DualNumber`/`GradientTape`), `VectorRecord` `@dataclass`, and capabilities
  `__all__` (None-pruned, 207 honest names). Fixed the legacy `process_query`
  crash via an `AdvancedMetaCognitiveReasoner.evaluate_task` adapter. Peripheral
  `causal/` made honest (counterfactual `compute()` raises `NotImplementedError`
  instead of a silent fake result; `scm.do_intervention` late-binding closure
  bug fixed so multi-var `do(X=5,Z=10)` no longer collapses to the last value;
  `InterventionPlanner._compute_confidence` implemented). Orphan modules whose
  siblings were purged in the truncated-file cleanup (605f55b) are import-guarded
  so package surfaces stay clean. Removed confirmed-dead trees: `arc_reasoning/`,
  `gsd/`, duplicate `intelligence/mind_arbitrator.py` + `mind_synergy.py`.
- **Discovery pipeline:** autonomous, running via launchd with evolution ENABLED.
  Two-gate EVALUATE: Gate 1 (real-data significance + held-out leakage guard +
  sign-consistency guard); Gate 2 (OpenAlex geochem literature + textbook
  blocklist + domain-relevance guard + LLM judge). Real data: Gard et al. (2019)
  whole-rock compilation (Zenodo 3359791) — oxides + 15 trace elements + optional
  isotopes + age, fetched by `scripts/fetch_geochem_data.py`.
- **Quality guards:** (1) held-out leakage guard; (2) sign-consistency guard
  (claim direction must match effect sign); (3) textbook blocklist (Gate-2
  fast-path); (4) verdict-feedback (proposer sees its own failures + corrective
  guidance); (5) domain-relevance guard (off-topic retrieval → retrieval-failed).
- **Measurement stack:** `evolved_analysis/capability_index.py` — CI-score +
  closed RSI loop over the verdict log. Run: `python -m
  evolved_analysis.capability_index`.
- **Recent performance:** novel-rate ~7%; Gate-1 failure ~13%; ~10 clean,
  sign-consistent discoveries in the store (residual trace-element/isotope
  partial correlations). The textbook ceiling (80% gate2-known) is the domain
  limit.
- **Full development history:** see `docs/CHANGELOG.md`.

---

## Quick Start

```python
from geo_core import create_geo_stan_system
system = create_geo_stan_system()   # constructs the EnhancedUnifiedSTANSystem
```

The autonomous discovery supervisor (`com.geodisc.discovery`) is **installed,
running, and evolving** via launchd (Background priority, yields to active users).
LLM token in `~/.geodisc_persistent/llm_env` (chmod 600). It generates + evaluates
candidates ~every 30 min when idle.

```bash
python -m geo_core.autonomous_discovery_supervisor   # foreground, one-process view
python -m evolved_analysis.capability_index           # capability index + RSI loop
```

---

## Architecture

GEODISC keeps a **domain-independent core** and adds a **geochemistry domain
layer** plus a **mechanistic process-graph capability**.

### Domain-independent core
`core/` (unified system), `reasoning/`, `causal/`, `swarm/`, `memory/`,
`symbolic/`, `intelligence/` (LLM gateway), `metacognitive/`,
`theoretical_discovery/`, `self_teaching/`, `knowledge/`, `mathematical/`,
`neural/`, `retrieval/`, `simulation/`, `autonomy/`, `utils/`, `physics/`.

### Discovery pipeline (fiction-free)
`scientific_discovery/discovery_store.py` — single machine-verified write
chokepoint. `autonomous_discovery_supervisor.py` — always-on, user-yielding
supervisor. `scientific_discovery/evolved_analysis/` — the AlphaEvolve two-gate
engine (Gate 1: real-data significance, sandboxed; Gate 2: literature novelty).
Key files: `run_claim_search.py` (two_gate_eval + the proposer loop),
`claim_task.py` (seed + TASK_SYSTEM + gate checks), `novelty_gate.py` (Gate 2 +
blocklist + OpenAlex), `capability_index.py` (measurement stack), `real_data.py`
(data loader), `verdict_log.py` (per-candidate verdict logging).

### Geochemistry domain layer — `geo_core/domains/geochemistry/`
16 `BaseDomainModule` scaffolds (Levels 2-17). Registered via `register_all`.

### Mechanistic process-graph capability — `geo_core/mechanistic_process_graphs/`
The headline novel feature. Represents scientific statements as a causal-
mechanistic network where every edge carries `{probability, uncertainty,
supporting_evidence, mechanistic_type}`. See `CLAUDE_GEO_ARCHITECTURE.md`.

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

---

## Commands

**Service management** (`com.geodisc.discovery`) — **installed, running, evolving**
(launchd, KeepAlive, Background priority, yields to active users):
```bash
launchctl load ~/Library/LaunchAgents/com.geodisc.discovery.plist
launchctl list com.geodisc.discovery
tail -f .geodisc_service.log
```
To disable evolution: remove the token from `~/.geodisc_persistent/llm_env`, or
set `GEODISC_DISCOVERY_EVOLUTION_DISABLED=1` and reload.
To disable the agent entirely:
```bash
launchctl unload ~/Library/LaunchAgents/com.geodisc.discovery.plist
```
> Do **not** touch `com.astra.discovery` — that agent belongs to the unrelated
> ASTRA-dev-main system.

---

## Persistent Memory & Key Files
- `~/.geodisc_persistent/` — GEODISC persistent state, LLM env
- `~/.geodisc_persistent/genuine_discoveries.json` — verified discoveries store
- `~/.geodisc_persistent/evolved_discoveries.json` — both-gate survivors (emit queue)
- `~/.geodisc_persistent/evolved_programs/claim_verdicts.jsonl` — per-candidate verdict log
- `~/.geodisc_persistent/evolved_programs/applied_fixes.json` — RSI applied-fix registry
- `~/.geodisc_persistent/geochem_real.csv` — the real data cache (`$GEODISC_REAL_DATA`)
- `.geodisc_state.json`, `.geodisc_service.log` — runtime state/logs (gitignored)

---

## Testing
```bash
python -m pytest geo_core/tests/test_discovery_chokepoint.py geo_core/tests/test_claim_gates.py geo_core/tests/test_novelty_gate.py geo_core/tests/test_capability_index.py -q  # 43 tests
python -c "import geo_core; from geo_core import create_geo_stan_system; create_geo_stan_system()"  # smoke
python -c "from geo_core import mechanistic_process_graphs as mpg; mpg.explain_preservation()"     # capability
python -c "from geo_core.domains import geochemistry; print(len(geochemistry.ALL_GEODISC_DOMAINS))" # 16
python -m compileall -q geo_core   # should report 0 errors
```

---

## GitHub
Push target: `main` branch of https://github.com/Tilanthi/GEODISC (the `geodisc`
git remote). Both `origin` and `geodisc` remotes point to GEODISC. This repo is
geochemistry-only — never push astrophysics content or the precursor history.
