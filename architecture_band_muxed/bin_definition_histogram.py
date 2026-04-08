"""
Plot bin definitions for 4-bin and 10-bin schemes (deviation from target, GHz).
Single figure with two panels: laser deviation distribution with bin edges overlaid.
"""

from __future__ import annotations

import numpy as np

# Same as binned_sampling_tosa: 3σ = ±1 nm at 1311 nm => σ in frequency (GHz)
C_M_S = 2.998e8
WL_REF_M = 1311.0 * 1e-9
SIGMA_F_GHZ = (C_M_S / (WL_REF_M**2)) * (1.0 / 3.0 * 1e-9) / 1e9

BIN4_EDGES_GHZ = np.array([-1000.0, -100.0, 0.0, 100.0, 1000.0])
BIN10_EDGES_GHZ = np.array([
    -1000.0, -160.0, -120.0, -80.0, -40.0, 0.0, 40.0, 80.0, 120.0, 160.0, 200.0,
])


def plot_bin_definition_histogram(
    out_path: str = "bin_definition_histogram.png",
) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x_min, x_max = -220, 220  # GHz, show central region where most lasers fall
    x = np.linspace(x_min, x_max, 800)
    pdf = np.exp(-0.5 * (x / SIGMA_F_GHZ) ** 2) / (SIGMA_F_GHZ * np.sqrt(2 * np.pi))

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    # ---------- 4-bin scheme ----------
    ax = axes[0]
    ax.fill_between(x, pdf, alpha=0.35, color="gray", label="Laser deviation (PDF)")
    ax.plot(x, pdf, color="black", linewidth=1.2)
    for i in range(len(BIN4_EDGES_GHZ) - 1):
        lo, hi = BIN4_EDGES_GHZ[i], BIN4_EDGES_GHZ[i + 1]
        if hi < x_min or lo > x_max:
            continue
        lo_c = max(lo, x_min)
        hi_c = min(hi, x_max)
        ax.axvspan(lo_c, hi_c, alpha=0.2, color=f"C{i}")
        ax.axvline(lo, color=f"C{i}", linestyle="--", alpha=0.8, linewidth=0.8)
        mid = (lo_c + hi_c) / 2
        ax.text(mid, 0.95 * ax.get_ylim()[1] if ax.get_ylim()[1] else 0.012, f"BIN{i}",
                ha="center", va="top", fontsize=9, color=f"C{i}")
    ax.axvline(BIN4_EDGES_GHZ[-1], color="C3", linestyle="--", alpha=0.8, linewidth=0.8)
    ax.set_ylabel("Probability density")
    ax.set_title("4-bin scheme: BIN0 (−1000 to −100), BIN1 (−100 to 0), BIN2 (0 to 100), BIN3 (100 to 1000) GHz")
    ax.legend(loc=4)  # 4 = lower right
    ax.grid(True, alpha=0.3)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(bottom=0)

    # ---------- 10-bin scheme ----------
    ax = axes[1]
    ax.fill_between(x, pdf, alpha=0.35, color="gray", label="Laser deviation (PDF)")
    ax.plot(x, pdf, color="black", linewidth=1.2)
    colors_10 = plt.cm.tab10(np.linspace(0, 1, 10))
    for i in range(len(BIN10_EDGES_GHZ) - 1):
        lo, hi = BIN10_EDGES_GHZ[i], BIN10_EDGES_GHZ[i + 1]
        if hi < x_min or lo > x_max:
            continue
        lo_c = max(lo, x_min)
        hi_c = min(hi, x_max)
        ax.axvspan(lo_c, hi_c, alpha=0.25, color=colors_10[i])
        ax.axvline(lo, color=colors_10[i], linestyle="--", alpha=0.7, linewidth=0.7)
        mid = (lo_c + hi_c) / 2
        ax.text(mid, 0.92 * (ax.get_ylim()[1] if ax.get_ylim()[1] else 0.012), f"BIN{i}",
                ha="center", va="top", fontsize=7, color=colors_10[i])
    ax.axvline(BIN10_EDGES_GHZ[-1], color=colors_10[9], linestyle="--", alpha=0.7, linewidth=0.7)
    ax.set_xlabel("Deviation from target (GHz)")
    ax.set_ylabel("Probability density")
    ax.set_title("10-bin scheme: 40 GHz width bins from −160 to 160 (BIN0: −1000 to −160, BIN9: 160 to 200 GHz)")
    ax.legend(loc=4)  # 4 = lower right
    ax.grid(True, alpha=0.3)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(bottom=0)

    fig.suptitle("Bin definitions for binned TOSA assembly (deviation from channel target)", fontsize=11, y=1.02)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {out_path}")


if __name__ == "__main__":
    plot_bin_definition_histogram()
