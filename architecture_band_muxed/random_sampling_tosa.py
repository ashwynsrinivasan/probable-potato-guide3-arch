"""
Random-sampling TOSA module.

Builds TOSAs for each class (200 GHz and 400 GHz) by randomly sampling one laser
from each channel (ch0–ch3) in that class. Each TOSA has 4 lasers.
"""

from __future__ import annotations

import numpy as np

# Reference 1311 nm → frequency spread: 3σ = ±1 nm in wavelength => σ in frequency (GHz)
C_M_S = 2.998e8
WL_REF_M = 1311.0 * 1e-9
SIGMA_F_GHZ = (C_M_S / (WL_REF_M**2)) * (1.0 / 3.0 * 1e-9) / 1e9

# Channel centers (frequency deviation from 1311 nm ref), GHz
CHANNELS_200_GHZ = np.array([0.0, 200.0, -200.0, -400.0])
CHANNELS_400_GHZ = np.array([0.0, 400.0, -400.0, -800.0])

# Number of TOSAs to build per class (10M each → 20M total)
N_TOSAS_PER_CLASS = 10_000_000


def sample_one_laser_per_channel(
    channel_offsets_ghz: np.ndarray,
    sigma_f_ghz: float,
) -> np.ndarray:
    """Sample one laser from each channel. Returns shape (4,) frequency deviations in GHz."""
    return np.array([
        center_ghz + np.random.normal(0, sigma_f_ghz)
        for center_ghz in channel_offsets_ghz
    ])


def build_one_tosa(
    channel_offsets_ghz: np.ndarray,
    sigma_f_ghz: float = SIGMA_F_GHZ,
) -> np.ndarray:
    """
    Build a single TOSA by randomly sampling one laser from each channel.
    Returns array of 4 laser frequency deviations (GHz) from 1311 nm ref.
    """
    return sample_one_laser_per_channel(channel_offsets_ghz, sigma_f_ghz)


def build_tosas_for_class(
    channel_offsets_ghz: np.ndarray,
    n_tosas: int,
    sigma_f_ghz: float = SIGMA_F_GHZ,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """
    Build n_tosas TOSAs for a given class (same channel grid).
    Returns shape (n_tosas, 4): each row is one TOSA (4 laser deviations in GHz).
    Vectorized for speed with large n_tosas.
    """
    if rng is None:
        rng = np.random.default_rng()
    # (n_tosas, 4) noise + (4,) centers broadcast
    noise = rng.normal(0, sigma_f_ghz, size=(n_tosas, 4))
    tosas = channel_offsets_ghz + noise
    return tosas


def get_total_tosa_count() -> int:
    """Total number of TOSAs (both classes): 2 * N_TOSAS_PER_CLASS."""
    return 2 * N_TOSAS_PER_CLASS


# Nominal adjacent spacings (ch1-ch0, ch2-ch1, ch3-ch2) in GHz
NOMINAL_SPACING_200 = np.array([
    CHANNELS_200_GHZ[1] - CHANNELS_200_GHZ[0],  # ch0-ch1
    CHANNELS_200_GHZ[2] - CHANNELS_200_GHZ[1],  # ch1-ch2
    CHANNELS_200_GHZ[3] - CHANNELS_200_GHZ[2],  # ch2-ch3
])
NOMINAL_SPACING_400 = np.array([
    CHANNELS_400_GHZ[1] - CHANNELS_400_GHZ[0],
    CHANNELS_400_GHZ[2] - CHANNELS_400_GHZ[1],
    CHANNELS_400_GHZ[3] - CHANNELS_400_GHZ[2],
])


def adjacent_spacing_errors(tosa: np.ndarray, nominal_spacings: np.ndarray) -> np.ndarray:
    """
    For one TOSA (4 laser frequencies in channel order), compute the 3 adjacent
    spacing errors: (ch1-ch0) - nominal_01, (ch2-ch1) - nominal_12, (ch3-ch2) - nominal_23.
    Returns shape (3,) in GHz.
    """
    spacings = np.diff(tosa)  # ch1-ch0, ch2-ch1, ch3-ch2
    return spacings - nominal_spacings


def ghz_to_wavelength_error_nm(f_ghz: float, wl_ref_nm: float = 1311.0) -> float:
    """Convert frequency error in GHz to wavelength error in nm at reference wavelength."""
    lam_m = wl_ref_nm * 1e-9
    delta_f_hz = f_ghz * 1e9
    delta_lam_m = (lam_m**2) * delta_f_hz / C_M_S
    return delta_lam_m * 1e9  # m -> nm


def plot_adjacent_spacing_error_histograms(
    tosas_200: np.ndarray,
    out_path: str = "random_sampling_tosa_adjacent_spacing_error_histograms.png",
) -> None:
    """
    Plot for 200 GHz class only. Four columns: (1) spacing error (signed) overlaid,
    (2) |spacing error| (magnitude) overlaid, (3) max |spacing error| per TOSA (PDF),
    (4) CDF of max |spacing error| per TOSA. Table below: % TOSAs at 20/40/100/200 GHz and λ error in nm.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Vectorized: (n_tosas, 3) spacing errors
    errors = np.diff(tosas_200, axis=1) - NOMINAL_SPACING_200
    abs_errors = np.abs(errors)
    max_abs_error_per_tosa = np.max(abs_errors, axis=1)
    n_tosas = len(max_abs_error_per_tosa)
    labels = ["ch0–ch1", "ch1–ch2", "ch2–ch3"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    bins_signed = np.linspace(-80, 80, 60)
    bins_mag = np.linspace(0, 80, 60)
    bins_max_abs = np.linspace(0, 120, 60)

    fig, axes = plt.subplots(1, 4, figsize=(16, 7))
    ax_left, ax_mid, ax_right, ax_cdf = axes
    for err_col, label, color in zip([0, 1, 2], labels, colors):
        ax_left.hist(errors[:, err_col], bins=bins_signed, color=color, alpha=0.6, density=True, edgecolor="white", label=label)
    ax_left.set_xlabel("Spacing error (GHz)")
    ax_left.set_ylabel("Probability density")
    ax_left.set_title("Spacing error (signed)")
    ax_left.axvline(0, color="gray", linestyle="--", alpha=0.8)
    ax_left.legend()
    ax_left.grid(True, alpha=0.3)

    for err_col, label, color in zip([0, 1, 2], labels, colors):
        ax_mid.hist(abs_errors[:, err_col], bins=bins_mag, color=color, alpha=0.6, density=True, edgecolor="white", label=label)
    ax_mid.set_xlabel("|Spacing error| (GHz)")
    ax_mid.set_ylabel("Probability density")
    ax_mid.set_title("|Spacing error| (magnitude)")
    ax_mid.legend()
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

    fig.suptitle("Adjacent channel spacing error in TOSA", fontsize=11, y=0.98)

    # Table: % TOSAs with max |error| <= threshold, and wavelength error (± nm)
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
    n_per_class = N_TOSAS_PER_CLASS
    total = get_total_tosa_count()
    print(f"TOSAs per class: {n_per_class:,}")
    print(f"Total TOSAs (both classes): {total:,}")

    np.random.seed(42)
    tosas_200 = build_tosas_for_class(CHANNELS_200_GHZ, n_per_class)
    plot_adjacent_spacing_error_histograms(tosas_200)
