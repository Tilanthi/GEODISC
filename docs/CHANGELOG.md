# GEODISC Development Changelog

Detailed development history. For the current system state, see `CLAUDE.md`.
For per-commit detail, see `git log --oneline`.

## 2026-07-17 — Truncated-file cleanup
All 26 pre-existing truncated/broken files (inherited from the astrophysics
codebase) deleted — not guess-repaired. 9 dead + 17 referenced via guarded
`try/except`. `compileall` now 0 errors.

## 2026-07-16 — Quality fixes
- **Gate-1 quality fix:** analysis of 135 gate1-failures showed the dominant
  cause (38%) was the proposer using bare element names (`df["nb"]`) instead of
  the actual columns (`df["nb_ppm"]`). Fixed in TASK_SYSTEM (exact column names)
  + `_verdict_feedback_hints` (failure-pattern detection + corrective guidance).
- **Sign-consistency guard:** `claim_task._direction_consistent` rejects
  candidates whose claim direction contradicts the effect sign. 3 mismatched
  records purged from the store retroactively.
- **Discovery-performance Phases 1-4:** (1) textbook blocklist Gate-2 fast-path;
  (2) niche widening (isotopes + age); (3)+(4) verdict feedback to the proposer.

## 2026-07-15 — Full pipeline bring-up
- **Gate-2 fix:** geochemistry domain-relevance guard (off-topic retrieval →
  `retrieval-failed`); OpenAlex added as the geochemistry literature source.
- **Autonomous evolution enabled:** supervisor installed + running with LLM
  token. First genuine verified discovery: P₂O₅–Na₂O partial correlation.
- **Real data wired:** Gard et al. (2019) compilation via
  `scripts/fetch_geochem_data.py`. Gate 1 verified on real data (|r|≈0.85).
- **Measurement stack:** `capability_index.py` — CI-score + closed RSI loop.
  Stable weighting + min-sample guard. First applied fix measured (-8%,
  honestly negative; later corrected to `insufficient sample` by the guard).
- **Discovery-pipeline lessons applied:** leakage guard (§7.3), verdict logging
  (§7.2), real-data contract, OpenAlex source, textbook blocklist.

## 2026-07-14 — Full astrophysics purge
- All legacy system-name identifiers renamed to `geo`/`geodisc` (~14 files).
- All astrophysics *content* removed or re-grounded to geochemistry across
  reasoning / capabilities / theoretical_discovery / autonomy / self_teaching /
  autonomous_research / retrieval (9 subagents).
- Dead astro modules deleted (advanced_analysis, theoretical_physics,
  genuine_discovery_validator, data_repositories, autotunnel_viz, 3 backups,
  test_phase_2_4). Domain packages atomic_physics + quantum_applications removed.
- Phase-1 photo-z engine re-grounded to geochemistry TOC-prediction.
- NASA ADS + arXiv literature infra retained (multi-disciplinary; indexes geochem).
- STAN identifier retained (core system name, 991 refs, public API).

## 2026-07-11 — GEODISC creation
GEODISC created as a geochemistry-focused scientific-discovery system. Core
package is `geo_core`.
