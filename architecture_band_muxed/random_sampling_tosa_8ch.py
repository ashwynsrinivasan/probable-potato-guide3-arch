"""
Random-sampling TOSA module for 8-channel, 200 GHz spacing.

Builds TOSAs by randomly sampling one laser from each channel (ch0–ch7).
Each TOSA has 8 lasers. All adjacent spacings are 200 GHz.
"""

from __future__ import annotations

import numpy as np

# Reference 1311 nm → frequency spread: 3σ = ±1 nm in wavelength => σ in frequency (GHz)
C_M_S = 2.998e8
WL_REF_M = 1311.0 * 1e-9
SIGMA_F_GHZ = (C_M_S / (WL_REF_M**2)) * (1.0 / 3.0 * 1e-9) / 1e9

# 8 channels, 200 GHz spacing (frequency deviation from 1311 nm ref), GHz
CHANNELS_8CH_200GHZ = np.array([0.0, 200.0, 400.0, 600.0, 800.0, 1000.0, 1200.0, 1400.0])
N_CHANNELS = 8
# Nominal adjacent spacings: all 200 GHz (ch1-ch0, ch2-ch1, ..., ch7-ch6)
NOMINAL_SPACING_8CH = np.full(N_CHANNELS - 1, 200.0)

N_TOSAS = 10_000_000


def build_tosas_for_class(
    channel_offsets_ghz: np.ndarray,
    n_tosas: int,
    sigma_f_ghz: float = SIGMA_F_GHZ,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Build n_tosas TOSAs. Returns shape (n_tosas, 8)."""
    if rng is None:
        rng = np.random.default_rng()
    n_ch = len(channel_offsets_ghz)
    noise = rng.normal(0, sigma_f_ghz, size=(n_tosas, n_ch))
    return channel_offsets_ghz + noise


def ghz_to_wavelength_error_nm(f_ghz: float, wl_ref_nm: float = 1311.0) -> float:
    """Convert frequency error in GHz to wavelength error in nm at reference wavelength."""
    lam_m = wl_ref_nm * 1e-9
    delta_f_hz = f_ghz * 1e9
    delta_lam_m = (lam_m**2) * delta_f_hz / C_M_S
    return delta_lam_m * 1e9  # m -> nm


def plot_adjacent_spacing_error_histograms(
    tosas: np.ndarray,
    out_path: str = "random_sampling_tosa_8ch_adjacent_spacing_error_histograms.png",
) -> None:
    """
    Plot for 8-channel 200 GHz. Four columns: (1) spacing error (signed) overlaid (7 pairs),
    (2) |spacing error| (magnitude) overlaid, (3) max |spacing error| per TOSA (PDF),
    (4) CDF of max |spacing error| per TOSA. Table below.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    errors = np.diff(tosas, axis=1) - NOMINAL_SPACING_8CH  # (n, 7)
    abs_errors = np.abs(errors)
    max_abs_error_per_tosa = np.max(abs_errors, axis=1)
    n_tosas = len(max_abs_error_per_tosa)
    n_pairs = N_CHANNELS - 1
    labels = [f"ch{i}–ch{i+1}" for i in range(n_pairs)]
    colors = plt.cm.tab10(np.linspace(0, 1, n_pairs)) if n_pairs <= 10 else plt.cm.tab20(np.linspace(0, 1, n_pairs))
    bins_signed = np.linspace(-80, 80, 60)
    bins_mag = np.linspace(0, 80, 60)
    bins_max_abs = np.linspace(0, 120, 60)

    fig, axes = plt.subplots(1, 4, figsize=(16, 7))
    ax_left, ax_mid, ax_right, ax_cdf = axes
    for err_col in range(n_pairs):
        ax_left.hist(errors[:, err_col], bins=bins_signed, color=colors[err_col], alpha=0.5, density=True, edgecolor="white", label=labels[err_col])
    ax_left.set_xlabel("Spacing error (GHz)")
    ax_left.set_ylabel("Probability density")
    ax_left.set_title("Spacing error (signed)")
    ax_left.axvline(0, color="gray", linestyle="--", alpha=0.8)
    ax_left.legend(fontsize=7)
    ax_left.grid(True, alpha=0.3)

    for err_col in range(n_pairs):
        ax_mid.hist(abs_errors[:, err_col], bins=bins_mag, color=colors[err_col], alpha=0.5, density=True, edgecolor="white", label=labels[err_col])
    ax_mid.set_xlabel("|Spacing error| (GHz)")
    ax_mid.set_ylabel("Probability density")
    ax_mid.set_title("|Spacing error| (magnitude)")
    ax_mid.legend(fontsize=7)
    ax_mid.grid(True, alpha=0.3)

    ax_right.hist(max_abs_error_per_tosa, bins=bins_max_abs, color="#9467bd", alpha=0.7, density=True, edgecolor="white")
    ax_right.set_xlabel("Max |spacing error| (GHz)")
    ax_right.set_ylabel("Probability density")
    ax_right.set_title("Max |spacing error| per TOSA (PDF)")
    ax_right.grid(True, alpha=0.3)
    ax_right.set_ylim(bottom=0)

    sort_max = np.sort(max_abs_error_per_tosa)
    cdf_max = np.arange(1, len(sort_max) + 1) / len(sort_max)
    ax_cdf.plot(sort_max, cdf_max, color="#2ca02c", linewidth=2)
    ax_cdf.set_xlabel("Max |spacing error| (GHz)")
    ax_cdf.set_ylabel("CDF")
    ax_cdf.set_title("Max |spacing error| per TOSA (CDF)")
    ax_cdf.set_ylim(0, 1)
    ax_cdf.grid(True, alpha=0.3)

    fig.suptitle("8-channel TOSA (200 GHz spacing): adjacent channel spacing error — random sampling", fontsize=11, y=0.98)

    thresholds_ghz = [20, 40, 100, 200]
    pcts = [100 * np.sum(max_abs_error_per_tosa <= t) / n_tosas for t in thresholds_ghz]
    wl_errors_nm = [ghz_to_wavelength_error_nm(t) for t in thresholds_ghz]
    table_rows = [["Max |error|", "% TOSAs", "Wavelength error (nm)"]]
    for t, p, w in zip(thresholds_ghz, pcts, wl_errors_nm):
        table_rows.append([f"≤ {t} GHz", f"{p:.2f}", f"±{w:.3f}"])

    plt.tight_layout(rect=[0, 0.32, 1, 0.92])
    ax_table = fig.add_axes([0.12, 0.02, 0.76, 0.26])
    ax_table.axis("off")
    tbl = ax_table.table(
        cellText=table_rows[1:],
        colLabels=table_rows[0],
        loc="center",
        cellLoc="center",
        colColours=["#e8e8e8"] * 3,
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1.0, 2.5)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {out_path}")


if __name__ == "__main__":
    print(f"8-channel 200 GHz: {N_CHANNELS} channels, {N_TOSAS:,} TOSAs")
    rng = np.random.default_rng(42)
    tosas = build_tosas_for_class(CHANNELS_8CH_200GHZ, N_TOSAS, rng=rng)
    plot_adjacent_spacing_error_histograms(tosas)
