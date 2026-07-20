"""inspirations.py — Tier 3 Part 2: a repertoire seed-bank for the proposer.

WHY THIS EXISTS
---------------
The proposer's ``propose(inspirations=...)`` parameter is wired in
``proposer.py:161`` ("Inspirations (other, diverse approaches -- borrow ideas")
but the search loop has always passed ``[]``. So the proposer has no varied
starting points and converges on one analytical pattern (the MgO-residual
partial correlation). This module provides correct, self-contained example
``run_claim`` sources -- ONE PER REPERTOIRE FORM -- that the loop rotates
through as inspirations, so the proposer sees threshold / conditional / ratio /
predictive patterns, not just partial correlation.

Each entry is valid Python using REAL Gard columns. They are IDEAS to borrow,
not claims to copy verbatim. Selection rotates deterministically.
"""
from __future__ import annotations

from typing import List

# --- partial / residual correlation (the existing workhorse form) -----------
_PARTIAL = '''CLAIM = "After regressing out MgO from both, residual Ce and residual Nb are positively correlated."
def run_claim(df_train, df_eval):
    import numpy as np
    from scipy.stats import spearmanr
    from sklearn.linear_model import LinearRegression
    d = df_eval.dropna(subset=["ce_ppm", "nb_ppm", "mgo"])
    mx = LinearRegression().fit(df_train[["mgo"]], df_train["ce_ppm"])
    my = LinearRegression().fit(df_train[["mgo"]], df_train["nb_ppm"])
    rx = d["ce_ppm"] - mx.predict(d[["mgo"]])
    ry = d["nb_ppm"] - my.predict(d[["mgo"]])
    r, p = spearmanr(rx, ry)
    return {"effect": float(r), "pvalue": float(p), "effect_type": "partial_residual_ce_nb", "summary": f"partial r={r:.3f}"}
'''

# --- conditional / subset (a relation that holds only in a subpopulation) ----
_CONDITIONAL = '''CLAIM = "Among evolved rocks (SiO2 > 52 wt%), Cr and Ni correlate more tightly than in primitive rocks."
def run_claim(df_train, df_eval):
    import numpy as np
    from scipy.stats import spearmanr
    d = df_eval.dropna(subset=["cr_ppm", "ni_ppm", "sio2"])
    ev = d[d["sio2"] > 52.0]
    pr = d[d["sio2"] <= 52.0]
    if len(ev) < 20 or len(pr) < 20:
        return {"effect": 0.0, "pvalue": 1.0, "effect_type": "conditional_cr_ni", "summary": "too few"}
    re, _ = spearmanr(ev["cr_ppm"], ev["ni_ppm"])
    rp, _ = spearmanr(pr["cr_ppm"], pr["ni_ppm"])
    return {"effect": float(re - rp), "pvalue": 0.0, "effect_type": "conditional_contrast_cr_ni", "summary": f"Delta rho (evolved-primitive)={re-rp:.3f}"}
'''

# --- threshold / non-monotonic (a relation that peaks/turns at a threshold) --
_THRESHOLD = '''CLAIM = "La/Ce rises with Nb up to a threshold then saturates -- a non-monotonic enrichment curve."
def run_claim(df_train, df_eval):
    import numpy as np
    from scipy.stats import spearmanr
    d = df_eval.dropna(subset=["la_ppm", "ce_ppm", "nb_ppm"])
    ratio = d["la_ppm"] / d["ce_ppm"].clip(lower=1e-6)
    nb = d["nb_ppm"]
    hi = nb > np.median(df_train["nb_ppm"])
    r_lo, _ = spearmanr(ratio[~hi], nb[~hi])
    r_hi, _ = spearmanr(ratio[hi], nb[hi])
    return {"effect": float(r_lo - r_hi), "pvalue": 0.0, "effect_type": "threshold_lace_nb", "summary": f"rho drop above Nb median={r_lo-r_hi:.3f}"}
'''

# --- ratio systematics (log-ratio process plot, à la spider-diagram) --------
_RATIO = '''CLAIM = "log(Zr/Y) and log(Nb/Y) are linearly coupled across the compilation -- a coherent HFSE ratio array."
def run_claim(df_train, df_eval):
    import numpy as np
    from scipy.stats import pearsonr
    d = df_eval.dropna(subset=["zr_ppm", "nb_ppm", "y_ppm"])
    x = np.log10(d["zr_ppm"].clip(lower=1e-6) / d["y_ppm"].clip(lower=1e-6))
    y = np.log10(d["nb_ppm"].clip(lower=1e-6) / d["y_ppm"].clip(lower=1e-6))
    r, p = pearsonr(x, y)
    return {"effect": float(r), "pvalue": float(p), "effect_type": "logratio_zry_nby", "summary": f"log-ratio r={r:.3f}"}
'''

# --- predictive validity (a ratio that predicts a held-out property) --------
_PREDICTIVE = '''CLAIM = "The Al2O3/Na2O ratio predicts MgO on held-out samples better than SiO2 alone."
def run_claim(df_train, df_eval):
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    dt = df_train.dropna(subset=["al2o3", "na2o", "sio2", "mgo"])
    de = df_eval.dropna(subset=["al2o3", "na2o", "sio2", "mgo"])
    ratio_tr = (dt["al2o3"] / dt["na2o"].clip(lower=1e-6)).to_frame("r")
    ratio_ev = (de["al2o3"] / de["na2o"].clip(lower=1e-6)).to_frame("r")
    m_ratio = LinearRegression().fit(ratio_tr, dt["mgo"])
    m_sio2 = LinearRegression().fit(dt[["sio2"]], dt["mgo"])
    gain = r2_score(de["mgo"], m_ratio.predict(ratio_ev)) - r2_score(de["mgo"], m_sio2.predict(de[["sio2"]]))
    return {"effect": float(gain), "pvalue": 0.0, "effect_type": "predictive_gain_mgo", "summary": f"R2 gain (ratio vs SiO2)={gain:.3f}"}
'''

# --- isotope / source-tracer (the under-used, less-saturated, on-mission niche) -
_ISOTOPE = '''CLAIM = "After dropna, radiogenic Sr and Nd isotopes (sr87_sr86 vs nd143_nd144) are negatively correlated across the global compilation, reflecting the depleted-mantle array."
def run_claim(df_train, df_eval):
    import numpy as np
    from scipy.stats import spearmanr
    d = df_eval.dropna(subset=["sr87_sr86", "nd143_nd144"])
    if len(d) < 20:
        return {"effect": 0.0, "pvalue": 1.0, "effect_type": "isotope_sr_nd", "summary": "too few isotope rows"}
    r, p = spearmanr(d["sr87_sr86"], d["nd143_nd144"])
    return {"effect": float(r), "pvalue": float(p), "effect_type": "isotope_sr_nd", "summary": f"Sr-Nd isotope spearman r={r:.3f}, n={len(d)}"}
'''

BANK = [
    ("partial-residual", _PARTIAL),
    ("conditional-subset", _CONDITIONAL),
    ("threshold-nonmonotonic", _THRESHOLD),
    ("ratio-systematics", _RATIO),
    ("predictive-validity", _PREDICTIVE),
    ("isotope-source-tracer", _ISOTOPE),
]


def pick(step: int, k: int = 2) -> List[str]:
    """Return k inspirations for the given step, rotating through the bank."""
    k = max(1, min(k, len(BANK)))
    return [BANK[(step + i) % len(BANK)][1] for i in range(k)]
