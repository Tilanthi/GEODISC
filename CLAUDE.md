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
  search funnel (where candidates die) is diagnosable. **Real data wired
  (2026-07-15):** `evolved_analysis/real_data.py` loads REAL whole-rock
  geochemistry fetched from the Gard et al. (2019) global compilation (Zenodo
  3359791) by `scripts/fetch_geochem_data.py` into `$GEODISC_REAL_DATA` — major
  oxides (sio2/tio2/al2o3/feo_tot/mgo/cao/mno/na2o/k2o/p2o5) PLUS 15 trace
  elements in ppm (V, Cr, Co, Ni, Cu, Zn, Rb, Sr, Y, Zr, Nb, Ba, La, Ce, Nd) PLUS
  OPTIONAL radiogenic isotopes (87Sr/86Sr, 143Nd/144Nd, epsilon_Nd/Sr/Hf, Pb, Hf)
  and age (Ga) — merged from major.csv + trace.csv + isotope.csv + age.csv on the
  shared sample id. Oxides+trace are the dense required base; isotopes+age are
  sparse (~10% / ~2% of rows) optional columns for the thinnest-textbook niche.
  Gate 1 runs on real data — verified: the seed (SiO2-MgO Harker) gives |r|≈0.85
  on the held-out split; r(Zr,Nb)=0.55 confirms the trace data is real.
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
  autonomous_research / retrieval. The astronomy `astro-ph` category mappings
  were re-grounded to geochemistry (`physics.geo-ph` / `q-bio.OT` / etc.) in
  `literature_validator` and `GenuineDiscoveryGenerator`; the dangling
  migration-spec path reference was fixed to point at the real
  `2026-07-11-geodisc-migration-design.md`; the cosmological `PhysicsDomain` enum
  member was removed.
  **Retained as legitimate infrastructure (NOT astrophysics domain content):**
  the NASA ADS backend and arXiv *client* (multi-disciplinary literature
  databases that index geochemistry journals) and `arxiv_integration`'s genuine
  arXiv taxonomy handling; the `STAN` identifier (the system's core name — 991
  references incl. the public `create_geo_stan_system` API; renaming is
  public-API-breaking and not astronomy); and the gravitational-physics task
  type (geo-relevant: lithostatic pressure, gravity-driven sedimentation).
  **Pre-existing syntax errors:** `python -m compileall geo_core` reports 26
  errors — ALL pre-existing truncated/broken files in non-live modules
  (arc_agi, arc_reasoning, core/v105, gsd, intelligence, mathematical, parts of
  reasoning / retrieval / symbolic / self_teaching / transformational) inherited
  from the astrophysics codebase. None are on the live import path (gates +
  smoke green) and none are safely restorable without the original source, so
  they are left as-is. Gates green: 19 tests, smoke, capability, 16 domains.
- **Public repo**: https://github.com/Tilanthi/GEODISC (`main` branch; git
  remotes `origin` and `geodisc` both point here). Published as a clean
  geochemistry-only history. The precursor astrophysics history is preserved
  only on local branch `archive/astra-precursor` and on the unrelated ASTRA-dev
  repository — never push it to GEODISC.
- **Operating mode: interactive + autonomous discovery (2026-07-15).** The
  supervisor (`com.geodisc.discovery`) is INSTALLED and running (launchd,
  KeepAlive, Background priority, yields to active users), and **autonomous
  evolution is ENABLED** (LLM token in `~/.geodisc_persistent/llm_env`, chmod
  600): about every 30 min when idle it generates candidates, runs Gate 1 on real
  data, and Gate 2 against the literature. **Gate 2 now has a geochemistry
  literature source** — OpenAlex (`novelty_gate.retrieve_openalex`), which
  indexes the geochem journals arXiv/Semantic-Scholar miss (Geochimica et
  Cosmochimica Acta, EPSL, Chemical Geology, J. Petrology, ...) — plus the
  domain-relevance guard (off-topic retrieval → `retrieval-failed`) and a
  geochem-aware judge. Verified safe: textbook relations (Harker, Fenner /
  tholeiitic Fe, TAS) are correctly marked *known* (not novel), and a candidate
  run emitted 0 false positives. Genuine novelty is rare (most significant
  whole-rock relations are textbook), so the store grows slowly — which is
  correct. To disable evolution: remove the token from `llm_env`, or set
  `GEODISC_DISCOVERY_EVOLUTION_DISABLED=1` and reload. See "Commands".
- **Gate-1 quality fix (2026-07-16):** analysis of 135 recent gate1-failures
  showed the dominant cause (38%) was the proposer using bare element names
  (df["nb"]) instead of the actual columns (df["nb_ppm"]) -- KeyError in the
  sandbox. Fixed: (a) TASK_SYSTEM now lists the EXACT column names with the
  `_ppm` suffix emphasised + the correct `sklearn.linear_model` import; (b)
  `_verdict_feedback_hints` now categorises the failure pattern (missing-column
  / NaN / weak-effect / bad-import) and injects pattern-specific corrective
  guidance, closing the loop on the proposer's own errors.
- **Sign-consistency guard + store purge (2026-07-16):** added a Gate-1 check
  (`claim_task._direction_consistent` / `_claim_stated_direction`, wired into
  `two_gate_eval`) that rejects candidates whose CLAIM text asserts a correlation
  direction ('positive'/'negative') opposite to the computed effect's sign — a
  recurring proposer flaw where the natural-language claim misstates its own
  finding's direction (Gate 1 previously checked only `|effect|`). Applied
  retroactively: stopped the supervisor, purged **3** sign-mismatched records
  from BOTH the verified store and the emit queue (race-safe stop/purge/restart),
  leaving **3 clean, sign-consistent** discoveries. Future direction-misstated
  candidates are now rejected at Gate 1.
- **Discovery-performance improvements (2026-07-15, Phases 1-4):**
  (1) **Textbook blocklist** -- `novelty_gate._matches_textbook_blocklist` is a
  deterministic Gate-2 fast-path that marks obvious textbook relations (Harker /
  Fenner / TAS / Fe-Mg / silica-saturation, or simple canonical oxide pairs)
  `known` BEFORE retrieval/LLM -- saves a judge call and removes false-novel risk
  for known families (conservative: partial/residual relations are never
  blocklisted). (2) **Niche widening** -- the dataset also carries OPTIONAL
  radiogenic isotopes (Sr/Nd/Pb/Hf) + age, the thinnest-textbook-coverage space.
  (3)+(4) **Verdict feedback** -- `run_claim_search._verdict_feedback_hints`
  feeds the proposer its recent gate2-known claims (textbook families to AVOID)
  and gate1-failed claims (generate STRONGER-effect relations), closing the loop
  on the proposer itself.
- **Measurement stack + closed RSI loop (2026-07-15):** `evolved_analysis/
  capability_index.py` turns the verdict log (`claim_verdicts.jsonl`) from a
  passive diagnostic into a measured self-improvement signal (the discipline
  borrowed from the *Unleashing the Beast* working paper, adapted to discovery):
  a **capability index** (engineering health: Gate-1 proposer effectiveness +
  Gate-2 literature coverage + a measured-fix "learning" sub-score; the
  domain-bounded `novel_rate` and human-judged `novelty_quality` reported
  separately), plus the loop **mine the failure ledger -> propose a human-gated
  fix -> (human applies + registers it) -> measure whether the targeted failure
  class dropped -> fold into the CI -> watch the trend**. Run it with
  `python -m evolved_analysis.capability_index`; register an applied fix with
  `register_applied_fix(...)` (the approval gate is never automatic).
  **Boundary claims are load-bearing** (attached to every CI): it is a
  self-reported heuristic, NOT an external benchmark; trend over level;
  `novel_rate` is bounded by the textbook ceiling; `ci_score=100` means
  saturation of the formula, not a breakthrough. Baseline measurement (119
  verdicts): CI 73.2 (old weighting), gate2-coverage 0.95, dominant failure
  `gate2-known` (the textbook ceiling, 48%). **Instrument hardened (2026-07-15):**
  the CI now uses STABLE weighting (always 0.3/0.4/0.3; an unmeasured learning
  term is 0, not a re-weighting) so it is comparable over time, AND a min-sample
  guard (>=20 verdicts per window) stops tiny windows emitting noisy numbers -- a
  trustworthy CI of 53.1. Priming fixes are measured against the YIELD
  (`novel_rate`, increase), not `gate2-known` (ceiling-bounded). Applied fixes:
  proposer-residual-priming + trace-niche-widening (both novel_rate-targeted;
  both `insufficient sample` until enough post-fix verdicts accrue). The trend
  over more episodes is the thing to watch.
- **Spec**: `docs/superpowers/specs/2026-07-11-geodisc-migration-design.md`
- **Plan**: `docs/superpowers/plans/2026-07-11-geodisc-migration.md`

---

## Quick Start

GEODISC is used **interactively for user-requested tasks**:

```python
from geo_core import create_geo_stan_system
system = create_geo_stan_system()   # constructs the EnhancedUnifiedSTANSystem
```

The autonomous discovery supervisor (`com.geodisc.discovery`) is **installed
and running via launchd** (Background priority, yields to active users), in
**ingest-only** mode — it ingests verified records but does NOT run the
evolutionary engine (evolution is OFF until Gate 2's geochemistry retrieval is
fixed; see "Operating mode" above). Run it manually to observe a cycle:

```bash
python -m geo_core.autonomous_discovery_supervisor   # foreground, one-process view
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

**Service management** (`com.geodisc.discovery`) — **installed and running
(launchd), ingest-only** (evolution OFF pending the Gate-2 fix; see "Operating
mode"). To manage it:
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
python -m pytest geo_core/tests/test_discovery_chokepoint.py geo_core/tests/test_claim_gates.py geo_core/tests/test_novelty_gate.py geo_core/tests/test_capability_index.py -q  # chokepoint (11) + gate discipline (13) + Gate-2/OpenAlex/blocklist (12) + capability-index/RSI (7)
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
