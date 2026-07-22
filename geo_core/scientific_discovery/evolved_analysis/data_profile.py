"""data_profile.py — Tier 3 Part 3.1: a data-driven column contract.

WHY THIS EXISTS
---------------
The pipeline historically assumed ONE data substrate: the Gard et al. (2019)
GLOBAL IGNEOUS oxide+trace compilation. Its required-column list
(``real_data._REQUIRED_COLUMNS``) and the proposer's ``TASK_SYSTEM`` column
description were hard-coded to it. But GEODISC's mission is Proterozoic
geochemistry / the oxygenic revolution / preservation, and the relevant real
data there is sedimentary REDOX (Fe-speciation) + TOC + age -- a different
column set entirely.

A *profile* decouples the pipeline from any one dataset:
  {name, required_cols, optional_cols, on_mission_cols, build_task_system()}
``real_data.load_split`` validates the ACTIVE profile's ``required_cols``; the
proposer's system prompt is built from the active profile. Active profile via
``$GEODISC_DATA_PROFILE`` (default ``gard``).

ZERO REGRESSION: the ``gard`` profile's required_cols are exactly the existing
``_REQUIRED_COLUMNS`` and ``build_task_system("gard")`` returns the existing
``claim_task.TASK_SYSTEM`` unchanged. New profiles (``proterozoic_redox``) only
activate when explicitly selected.
"""
from __future__ import annotations

import os
from typing import List

# --------------------------------------------------------------------------- #
# GARD — default; global igneous oxides + 15 traces (+ sparse isotopes/age)    #
# --------------------------------------------------------------------------- #
GARD_REQUIRED = (
    # major oxides (wt %)
    "sio2", "tio2", "al2o3", "feo_tot", "mgo", "cao", "mno", "na2o", "k2o", "p2o5",
    # trace elements (ppm)
    "v_ppm", "cr_ppm", "co_ppm", "ni_ppm", "cu_ppm", "zn_ppm", "rb_ppm",
    "sr_ppm", "y_ppm", "zr_ppm", "nb_ppm", "ba_ppm", "la_ppm", "ce_ppm", "nd_ppm",
)
GARD_OPTIONAL = (
    "sr87_sr86", "nd143_nd144", "epsilon_nd", "epsilon_sr",
    "pb206_pb204", "pb207_pb204", "pb208_pb204", "hf176_hf177", "epsilon_hf", "age",
)

# --------------------------------------------------------------------------- #
# PROTEROZOIC_REDOX — Fe-speciation + TOC + age (the on-mission substrate)     #
# Required cols are the redox proxies the redox interpretation is built on.    #
# --------------------------------------------------------------------------- #
PROTEROZOIC_REDOX_REQUIRED = ("fe_hr", "fe_t", "fe_py", "age")
PROTEROZOIC_REDOX_OPTIONAL = (
    "toc",            # total organic carbon (wt %) -- the preservation signal
    "sio2", "tio2", "al2o3", "feo_tot", "mgo", "cao", "mno", "na2o", "k2o", "p2o5",
    "v_ppm", "cr_ppm", "co_ppm", "ni_ppm", "cu_ppm", "zn_ppm", "rb_ppm",
    "sr_ppm", "y_ppm", "zr_ppm", "nb_ppm", "ba_ppm", "la_ppm", "ce_ppm", "nd_ppm",
)

_PROTEROZOIC_TASK_SYSTEM = (
    "You are an expert geochemist searching for a NOVEL, real statistical "
    "relationship in a PROTEROZOIC FINE-GRAINED CLASTIC (shale) redox + "
    "preservation dataset that is NOT already a well-known textbook result. You "
    "are given the current candidate (a natural-language CLAIM plus a "
    "`run_claim(df_train, df_eval)` function that tests it on real data and "
    "returns {effect, pvalue, effect_type, summary}).\n"
    "The available REAL data columns (use these EXACT names in df[col]):\n"
    "  Fe-speciation redox proxies: fe_hr (highly-reactive Fe), fe_t (total Fe), "
    "fe_py (pyrite Fe). DERIVE FeHR/FeT = fe_hr/fe_t and FePy/FeHR = fe_py/fe_hr "
    "in your code (both are ratios in [0,1]).\n"
    "  toc (total organic carbon, wt % -- the preservation signal)\n"
    "  age (Ga)\n"
    "  optional majors (wt %) / traces (ppm): sio2/tio2/al2o3/feo_tot/mgo/cao/"
    "mno/na2o/k2o/p2o5; v_ppm/cr_ppm/.../nd_ppm (the _ppm suffix is REQUIRED).\n"
    "Redox interpretation thresholds (Poulton/Canfield): FeHR/FeT >= 0.38 "
    "indicates ANOXIC deposition (ferruginous or euxinic); FePy/FeHR >= 0.7-0.8 "
    "indicates EUXINIC (sulfidic) conditions. ALWAYS df.dropna(subset=[your_cols]) "
    "before computing. You may use numpy/scipy/pandas/sklearn only.\n"
    "HARD RULES:\n"
    "- Keep the EXACT signature: def run_claim(df_train, df_eval)\n"
    "- Set a module-level CLAIM = \"...\" string: a specific, quantitative claim.\n"
    "- Return a dict with keys effect (a correlation/contrast magnitude in [-1,1] "
    "or a normalized contrast), pvalue (a real significance), effect_type, summary.\n"
    "- DO NOT propose a textbook restatement (e.g. 'FeHR/FeT >= 0.38 means anoxic').\n"
    "- INSTEAD propose a NON-OBVIOUS relation: redox state (FePy/FeHR) coupled to "
    "TOC preservation; redox evolution through time (age); a trace-element "
    "signature that tracks euxinia vs ferruginous; a threshold/non-monotonic "
    "redox-TOC relation; a predictive relation (a ratio that predicts TOC or "
    "redox on held-out data).\n"
    "- The relationship must be genuinely significant on the held-out data. No "
    "file I/O, no network, no plotting. Correct and self-contained.\n"
    "RESPOND WITH EITHER:\n"
    "  (a) one or more diff blocks (<<<SEARCH>>>...<<<REPLACE>>>...<<<END>>>)\n"
    "  (b) one complete ```python``` module (CLAIM + run_claim).\n"
    "Output ONLY the diff or code, no explanation."
)

# --------------------------------------------------------------------------- #
# PALEO — fossil collections from the Paleobiology Database (PBDB).           #
# Paleontology / fossil record / early-Earth atmosphere focus.                #
# --------------------------------------------------------------------------- #
PALEO_REQUIRED = ("mid_age_ma", "n_occurrences")
PALEO_OPTIONAL = (
    "late_age_ma", "early_age_ma", "paleolatitude", "paleolongitude",
    "latitude", "longitude", "environment", "lithology", "epoch",
    "formation", "country", "n_references",
)

_PALEO_TASK_SYSTEM = (
    "You are an expert PALEONTOLOGIST and Earth-system scientist searching for a "
    "NOVEL, real statistical relationship in a FOSSIL COLLECTION database (from the "
    "Paleobiology Database, PBDB) spanning the Proterozoic-early Paleozoic (the "
    "window of early life, the Great Oxidation Event, Snowball Earth, and the "
    "Cambrian explosion).\n"
    "The available REAL data columns (use these EXACT names in df[col]):\n"
    "  mid_age_ma (geological age of each fossil collection, Ma)\n"
    "  n_occurrences (number of fossil occurrences at the collection -- a diversity/"
    "abundance proxy)\n"
    "  paleolatitude / paleolongitude (paleogeographic position)\n"
    "  environment (depositional environment, e.g. 'carbonate', 'deep-water', "
    "'peritidal', 'fluvial')\n"
    "  lithology (rock type, e.g. 'limestone', 'shale', 'sandstone')\n"
    "  epoch / formation / country\n"
    "ALWAYS df.dropna(subset=[your_cols]) before computing. "
    "You may use numpy/scipy/pandas/sklearn only.\n"
    "DATA HANDLING (critical for PBDB): n_occurrences is LONG-TAILED (most "
    "collections have 1-5; a few have 50+). ALWAYS log10-transform it before "
    "correlating: df['log_occ'] = np.log10(df['n_occurrences'] + 1). Correlate "
    "log_occ, not raw n_occurrences. Use EXACT column names: 'mid_age_ma' (not "
    "'age'), 'n_occurrences' (not 'diversity' or 'abundance'). String columns "
    "('environment', 'lithology') need encoding: use groupby + mean contrast "
    "(e.g. compare log_occ between environment groups) or one-hot encoding, not "
    "direct correlation.\n"
    "HARD RULES:\n"
    "- Keep the EXACT signature: def run_claim(df_train, df_eval)\n"
    "- Set a module-level CLAIM = \"...\" string: a specific, quantitative claim.\n"
    "- Return a dict with keys effect (correlation/contrast in [-1,1] or normalized), "
    "pvalue (a real significance), effect_type, summary.\n"
    "- DO NOT propose a textbook restatement.\n"
    "INSTEAD explore these on-mission question types:\n"
    "  (i) DIVERSITY through time -- does occurrence density shift across key "
    "transitions (GOE ~2400 Ma, Snowball Earth ~700 Ma, Cambrian explosion ~540 Ma)?\n"
    "  (ii) PRESERVATION bias -- does environment or lithology predict fossil "
    "occurrence density? Compare mean n_occurrences across environments.\n"
    "  (iii) PALEOGEOGRAPHIC gradients -- does diversity vary with paleolatitude?\n"
    "  (iv) AGE-CONDITIONAL patterns -- does a relationship strengthen or reverse "
    "across an age threshold (e.g. before vs after the Cambrian explosion)?\n"
    "  (v) PREDICTIVE validity -- does a combination of environment + lithology + "
    "age predict occurrence density better than age alone?\n"
    "- The relationship must be genuinely significant on the held-out data.\n"
    "- No file I/O, no network, no plotting. Correct and self-contained.\n"
    "RESPOND WITH EITHER:\n"
    "  (a) one or more diff blocks (<<<SEARCH>>>...<<<REPLACE>>>...<<<END>>>)\n"
    "  (b) one complete ```python``` module (CLAIM + run_claim).\n"
    "Output ONLY the diff or code, no explanation.\n"
    "INTEGRITY: state the sign HONESTLY. The sign-consistency guard rejects claims "
    "whose stated direction disagrees with their computed effect; the p-value guard "
    "rejects recycled/hardcoded p-values. Compute first, report honestly."
)

_PROFILES = {
    "gard": {
        "required_cols": GARD_REQUIRED,
        "optional_cols": GARD_OPTIONAL,
        "on_mission_cols": GARD_OPTIONAL,
        "effect_min": 0.30,
        "pmax": 1e-3,
    },
    "proterozoic_redox": {
        "required_cols": PROTEROZOIC_REDOX_REQUIRED,
        "optional_cols": PROTEROZOIC_REDOX_OPTIONAL,
        "on_mission_cols": ("fe_hr", "fe_t", "fe_py", "toc", "age"),
        "effect_min": 0.25,
        "pmax": 1e-3,
    },
    "paleo": {
        "required_cols": PALEO_REQUIRED,
        "optional_cols": PALEO_OPTIONAL,
        "on_mission_cols": ("mid_age_ma", "n_occurrences", "environment",
                             "lithology", "paleolatitude"),
        "effect_min": 0.12,   # paleo correlations are inherently weaker than igneous
        "pmax": 0.01,
    },
}


def active_name() -> str:
    return os.environ.get("GEODISC_DATA_PROFILE", "gard")


def active() -> dict:
    return _PROFILES.get(active_name(), _PROFILES["gard"])


def required_cols() -> tuple:
    return active()["required_cols"]


def build_task_system(profile: str = None):
    """Return the proposer system prompt for the given (or active) profile.

    For ``gard`` this returns the EXISTING ``claim_task.TASK_SYSTEM`` unchanged
    (zero regression). Other profiles return their own redox/sediment-framed
    prompt (with the Tier-2 surprise guidance appended, matching gard's prompt).
    """
    name = profile or active_name()
    if name == "gard":
        from . import claim_task
        return claim_task.TASK_SYSTEM
    if name == "proterozoic_redox":
        base = _PROTEROZOIC_TASK_SYSTEM
        try:
            from . import claim_task, surprise as _sur
            if claim_task.SURPRISE_GUIDANCE and _sur.enabled():
                base = base + claim_task.SURPRISE_GUIDANCE
        except Exception:
            pass
        return base
    if name == "paleo":
        return _PALEO_TASK_SYSTEM
    # unknown profile -> fall back to gard's task system
    from . import claim_task
    return claim_task.TASK_SYSTEM


def known_profiles() -> List[str]:
    return sorted(_PROFILES)
