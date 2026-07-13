#!/usr/bin/env python3
"""Generate fig_v7_scatter.png: criteria-scored fidelity vs silicification across 7 biotas.

Scores are illustrative criteria-based values compiled from the descriptive literature
(same source as Table 1). Overlapping points are slightly offset for visibility.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Okabe-Ito-inspired, colorblind-safe palette
C_PRE = "#0072B2"   # blue   - pre-GOE
C_SPAN = "#9467BD"  # purple - spans GOE
C_POST = "#D55E00"  # vermillion - post-GOE

# (formation, silicification, fidelity, group)
data = [
    ("Strelley Pool", 3, 3, "pre"),
    ("Moodies",       1, 1, "pre"),
    ("Tumbiana",      1, 1, "pre"),
    ("Turee Creek",   3, 3, "span"),
    ("Belcher",       3, 3, "post"),
    ("Gunflint",      4, 4, "post"),
    ("Sokoman",       3, 3, "post"),
]

# Deterministic small offsets so overlapping markers/labels are visible.
jitter = {
    "Strelley Pool": ( 0.00,  0.00),
    "Turee Creek":   ( 0.10,  0.10),
    "Belcher":       ( 0.10, -0.10),
    "Sokoman":       (-0.10,  0.00),
    "Moodies":       (-0.06,  0.06),
    "Tumbiana":      ( 0.06, -0.06),
    "Gunflint":      ( 0.00,  0.00),
}

colmap = {"pre": C_PRE, "span": C_SPAN, "post": C_POST}

fig, ax = plt.subplots(figsize=(6.6, 5.0))

# 1:1 reference line
lim = (0.3, 4.7)
ax.plot(lim, lim, ls="--", lw=1.0, color="#888888", zorder=1,
        label="1:1 reference")

for name, sil, fid, grp in data:
    dx, dy = jitter[name]
    ax.scatter(sil + dx, fid + dy, s=95, c=colmap[grp],
               edgecolors="black", linewidths=0.7, zorder=3)

# Labels: offset away from crowded centre; anchor manually
label_off = {
    "Strelley Pool": ( 0.12,  0.12),
    "Turee Creek":   ( 0.12,  0.12),
    "Belcher":       ( 0.12, -0.16),
    "Sokoman":       (-0.12,  0.12),
    "Moodies":       (-0.12,  0.12),
    "Tumbiana":      ( 0.12, -0.16),
    "Gunflint":      ( 0.12,  0.12),
}
ha_map = {
    "Strelley Pool": "left", "Turee Creek": "left", "Belcher": "left",
    "Sokoman": "right", "Moodies": "right", "Tumbiana": "left",
    "Gunflint": "left",
}
for name, sil, fid, grp in data:
    dx, dy = jitter[name]
    lox, loy = label_off[name]
    ax.annotate(name, (sil + dx, fid + dy),
                xytext=(sil + dx + lox, fid + dy + loy),
                fontsize=9.0, ha=ha_map[name], va="center", zorder=4)

ax.set_xlabel("Silicification score (criteria-based)", fontsize=11)
ax.set_ylabel("Cellular-fidelity score (criteria-based)", fontsize=11)
ax.set_xlim(lim)
ax.set_ylim(lim)
ax.set_xticks([1, 2, 3, 4])
ax.set_yticks([1, 2, 3, 4])
ax.set_aspect("equal")
ax.grid(True, ls=":", lw=0.5, color="#cccccc", alpha=0.6, zorder=0)

legend_handles = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor=C_PRE,
           markeredgecolor="black", markersize=9, label="pre-GOE"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=C_SPAN,
           markeredgecolor="black", markersize=9, label="spans GOE"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=C_POST,
           markeredgecolor="black", markersize=9, label="post-GOE"),
    Line2D([0], [0], ls="--", color="#888888", lw=1.0, label="1:1 reference"),
]
ax.legend(handles=legend_handles, loc="upper left", frameon=True,
          fontsize=9, framealpha=0.95)

ax.set_title("Criteria-scored fidelity versus silicification across seven biotas",
             fontsize=11, pad=8)

plt.tight_layout()
plt.savefig("/Users/gjw255/astrodata/SWARM/GEODISC/Seb/fig_v7_scatter.png",
            dpi=220, bbox_inches="tight")
print("Wrote fig_v7_scatter.png")
