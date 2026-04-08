"""
Binned-sampling TOSA module.

Bins each laser (per channel, per class) by its frequency deviation from the
channel target. Two binning schemes: 10 bins and 4 bins (BIN0–BIN3).
TOSAs are built by picking one laser from the same bin index in each channel.
"""

from __future__ import annotations

import numpy as np

# Reference 1311 nm → 3σ = ±1 nm in wavelength => σ in frequency (GHz)
C_M_S = 2.998e8
WL_REF_M = 1311.0 * 1e-9
SIGMA_F_GHZ = (C_M_S / (WL_REF_M**2)) * (1.0 / 3.0 * 1e-9) / 1e9

# Channel centers (frequency deviation from 1311 nm ref), GHz
CHANNELS_200_GHZ = np.array([0.0, 200.0, -200.0, -400.0])
CHANNELS_400_GHZ = np.array([0.0, 400.0, -400.0, -800.0])

# Nominal adjacent spacings (ch1-ch0, ch2-ch1, ch3-ch2) for 200 GHz class, GHz
NOMINAL_SPACING_200 = np.array([
    CHANNELS_200_GHZ[1] - CHANNELS_200_GHZ[0],
    CHANNELS_200_GHZ[2] - CHANNELS_200_GHZ[1],
    CHANNELS_200_GHZ[3] - CHANNELS_200_GHZ[2],
])

# ---------------------------------------------------------------------------
# 10-bin scheme: deviation from target (GHz)
# bin0: -1000 to -160, bin1: -160 to -120, ..., bin9: 160 to 200
# ---------------------------------------------------------------------------
BIN10_EDGES_GHZ = np.array([
    -1000.0, -160.0, -120.0, -80.0, -40.0, 0.0, 40.0, 80.0, 120.0, 160.0, 200.0,
])
N_BINS_10 = len(BIN10_EDGES_GHZ) - 1  # 10


def get_bin10_edges_ghz() -> np.ndarray:
    """Return 10-bin edges in GHz (length 11)."""
    return BIN10_EDGES_GHZ.copy()


def deviation_to_bin10(deviation_ghz: float | np.ndarray) -> int | np.ndarray:
    """
    Map deviation from target (GHz) to 10-bin index [0, 9].
    Values below -1000 go to 0; above 200 go to 9 (clipped into outer bins).
    """
    return np.clip(
        np.searchsorted(BIN10_EDGES_GHZ, deviation_ghz, side="right") - 1,
        0,
        N_BINS_10 - 1,
    )


# ---------------------------------------------------------------------------
# 4-bin scheme: BIN0 -1000 to -100, BIN1 -100 to 0, BIN2 0 to 100, BIN3 100 to 1000
# ---------------------------------------------------------------------------
BIN4_EDGES_GHZ = np.array([-1000.0, -100.0, 0.0, 100.0, 1000.0])
N_BINS_4 = len(BIN4_EDGES_GHZ) - 1  # 4


def get_bin4_edges_ghz() -> np.ndarray:
    """Return 4-bin edges in GHz (length 5)."""
    return BIN4_EDGES_GHZ.copy()


def deviation_to_bin4(deviation_ghz: float | np.ndarray) -> int | np.ndarray:
    """
    Map deviation from target (GHz) to 4-bin index [0, 3] (BIN0–BIN3).
    Values below -1000 go to 0; above 1000 go to 3 (clipped).
    """
    return np.clip(
        np.searchsorted(BIN4_EDGES_GHZ, deviation_ghz, side="right") - 1,
        0,
        N_BINS_4 - 1,
    )


def get_bin10_label(bin_idx: int) -> str:
    """Human-readable label for 10-bin index, e.g. 'bin0: -1000 to -160 GHz'."""
    if not 0 <= bin_idx < N_BINS_10:
        return f"bin{bin_idx}?"
    return f"bin{bin_idx}: {BIN10_EDGES_GHZ[bin_idx]:.0f} to {BIN10_EDGES_GHZ[bin_idx + 1]:.0f} GHz"


def get_bin4_label(bin_idx: int) -> str:
    """Human-readable label for 4-bin index (BIN0–BIN3)."""
    if not 0 <= bin_idx < N_BINS_4:
        return f"BIN{bin_idx}?"
    return f"BIN{bin_idx}: {BIN4_EDGES_GHZ[bin_idx]:.0f} to {BIN4_EDGES_GHZ[bin_idx + 1]:.0f} GHz"


def ghz_to_wavelength_error_nm(f_ghz: float, wl_ref_nm: float = 1311.0) -> float:
    """Convert frequency error in GHz to wavelength error in nm at reference wavelength."""
    lam_m = wl_ref_nm * 1e-9
    delta_f_hz = f_ghz * 1e9
    delta_lam_m = (lam_m**2) * delta_f_hz / C_M_S
    return delta_lam_m * 1e9  # m -> nm


# ---------------------------------------------------------------------------
# Binned TOSA: one laser per channel from the same bin
# ---------------------------------------------------------------------------
N_LASERS_PER_CHANNEL = 10_000_000  # lasers to sample per channel for bin occupancy (full inventory)


def _sample_lasers_per_channel_200(
    n_per_ch: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample laser deviations from target for each of 4 channels (200 GHz class). Shape (n_per_ch, 4)."""
    out = np.zeros((n_per_ch, 4))
    for ch in range(4):
        out[:, ch] = CHANNELS_200_GHZ[ch] + rng.normal(0, SIGMA_F_GHZ, size=n_per_ch)
    # Deviation from target (channel center) for each channel
    deviations = np.zeros((n_per_ch, 4))
    for ch in range(4):
        deviations[:, ch] = out[:, ch] - CHANNELS_200_GHZ[ch]
    return deviations


def _build_binned_tosa_spacing_errors(
    deviations_per_ch_per_bin: list[list[np.ndarray]],
    rng: np.random.Generator,
) -> np.ndarray:
    """
    deviations_per_ch_per_bin[ch][bin_idx] = 1d array of deviations for that channel in that bin.
    Build as many TOSAs per bin as the full inventory allows (one laser per channel from that bin).
    Returns (n_total, 3) spacing errors.
    """
    n_bins = len(deviations_per_ch_per_bin[0])
    all_errors = []
    for b in range(n_bins):
        # For each channel, get deviations in this bin; need at least one per channel
        dev_ch = [deviations_per_ch_per_bin[ch][b] for ch in range(4)]
        n_avail = min(len(d) for d in dev_ch)
        if n_avail == 0:
            continue
        n_build = n_avail  # use full inventory per bin
        # Random indices into each channel's bin
        for ch in range(4):
            idx = rng.choice(len(dev_ch[ch]), size=n_build, replace=(len(dev_ch[ch]) < n_build))
            if ch == 0:
                tosa_deviations = np.zeros((n_build, 4))
            tosa_deviations[:, ch] = dev_ch[ch][idx]
        # TOSA laser freq = channel_center + deviation
        tosa_freq = CHANNELS_200_GHZ + tosa_deviations
        spacings = np.diff(tosa_freq, axis=1)
        errs = spacings - NOMINAL_SPACING_200
        all_errors.append(errs)
    return np.concatenate(all_errors, axis=0) if all_errors else np.zeros((0, 3))


def _deviations_by_bin(
    deviations: np.ndarray,
    to_bin_fn,
    n_bins: int,
) -> list[list[np.ndarray]]:
    """deviations shape (n, 4). Return list of list: per channel, per bin, array of deviation values."""
    result = [[] for _ in range(4)]
    for ch in range(4):
        result[ch] = [np.array([], dtype=float) for _ in range(n_bins)]
        bins_ch = to_bin_fn(deviations[:, ch])
        for b in range(n_bins):
            result[ch][b] = deviations[bins_ch == b, ch]
    return result


def run_binned_sampling_200ghz(
    rng: np.random.Generator | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Sample lasers per channel, assign to 10-bin and 4-bin, build TOSAs (one laser per ch from same bin).
    Returns (errors_10, errors_4), each shape (n_tosas_total, 3) for ch0-1, ch1-2, ch2-3 spacing error.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    n = N_LASERS_PER_CHANNEL
    deviations = _sample_lasers_per_channel_200(n, rng)
    by_bin_10 = _deviations_by_bin(deviations, deviation_to_bin10, N_BINS_10)
    by_bin_4 = _deviations_by_bin(deviations, deviation_to_bin4, N_BINS_4)
    errors_10 = _build_binned_tosa_spacing_errors(by_bin_10, rng)
    errors_4 = _build_binned_tosa_spacing_errors(by_bin_4, rng)
    return errors_10, errors_4


def plot_binned_spacing_error_histograms(
    errors_10: np.ndarray,
    errors_4: np.ndarray,
    out_path: str = "binned_sampling_tosa_spacing_error_histograms.png",
) -> None:
    """
    Same set of plots as random_sampling_tosa: for each scheme (4-bin, 10-bin) one row with
    (1) spacing error (signed) overlaid, (2) |spacing error| (magnitude) overlaid,
    (3) max |spacing error| per TOSA (PDF), (4) max |spacing error| per TOSA (CDF).
    Table at bottom: % TOSAs at 20/40/100/200 GHz and wavelength error (nm) for both schemes.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = ["ch0–ch1", "ch1–ch2", "ch2–ch3"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    bins_signed = np.linspace(-80, 80, 60)
    bins_mag = np.linspace(0, 80, 60)
    bins_max_abs = np.linspace(0, 120, 60)

    abs_4 = np.abs(errors_4)
    abs_10 = np.abs(errors_10)
    max_abs_4 = np.max(abs_4, axis=1)
    max_abs_10 = np.max(abs_10, axis=1)
    n_4, n_10 = len(max_abs_4), len(max_abs_10)

    fig, axes = plt.subplots(2, 4, figsize=(16, 7), sharex="col")
    # Row 0: 4-bin scheme — same four panels as random_sampling
    ax0, ax1, ax2, ax3 = axes[0, 0], axes[0, 1], axes[0, 2], axes[0, 3]
    for err_col, label, color in zip([0, 1, 2], labels, colors):
        ax0.hist(errors_4[:, err_col], bins=bins_signed, color=color, alpha=0.6, density=True, edgecolor="white", label=label)
    ax0.set_ylabel("Probability density")
    ax0.set_xlabel("Spacing error (GHz)")
    ax0.set_title("4-bin: Spacing error (signed)")
    ax0.axvline(0, color="gray", linestyle="--", alpha=0.8)
    ax0.legend()
    ax0.grid(True, alpha=0.3)

    for err_col, label, color in zip([0, 1, 2], labels, colors):
        ax1.hist(abs_4[:, err_col], bins=bins_mag, color=color, alpha=0.6, density=True, edgecolor="white", label=label)
    ax1.set_ylabel("Probability density")
    ax1.set_xlabel("|Spacing error| (GHz)")
    ax1.set_title("4-bin: |Spacing error| (magnitude)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.hist(max_abs_4, bins=bins_max_abs, color="#9467bd", alpha=0.7, density=True, edgecolor="white")
    ax2.set_ylabel("Probability density")
    ax2.set_xlabel("Max |spacing error| (GHz)")
    ax2.set_title("4-bin: Max |spacing error| per TOSA (PDF)")
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)

    sort_max_4 = np.sort(max_abs_4)
    cdf_4 = np.arange(1, len(sort_max_4) + 1) / len(sort_max_4)
    ax3.plot(sort_max_4, cdf_4, color="#2ca02c", linewidth=2)
    ax3.set_ylabel("CDF")
    ax3.set_xlabel("Max |spacing error| (GHz)")
    ax3.set_title("4-bin: Max |spacing error| per TOSA (CDF)")
    ax3.set_ylim(0, 1)
    ax3.grid(True, alpha=0.3)

    # Row 1: 10-bin scheme
    ax0, ax1, ax2, ax3 = axes[1, 0], axes[1, 1], axes[1, 2], axes[1, 3]
    for err_col, label, color in zip([0, 1, 2], labels, colors):
        ax0.hist(errors_10[:, err_col], bins=bins_signed, color=color, alpha=0.6, density=True, edgecolor="white", label=label)
    ax0.set_ylabel("Probability density")
    ax0.set_xlabel("Spacing error (GHz)")
    ax0.set_title("10-bin: Spacing error (signed)")
    ax0.axvline(0, color="gray", linestyle="--", alpha=0.8)
    ax0.legend()
    ax0.grid(True, alpha=0.3)

    for err_col, label, color in zip([0, 1, 2], labels, colors):
        ax1.hist(abs_10[:, err_col], bins=bins_mag, color=color, alpha=0.6, density=True, edgecolor="white", label=label)
    ax1.set_ylabel("Probability density")
    ax1.set_xlabel("|Spacing error| (GHz)")
    ax1.set_title("10-bin: |Spacing error| (magnitude)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.hist(max_abs_10, bins=bins_max_abs, color="#9467bd", alpha=0.7, density=True, edgecolor="white")
    ax2.set_ylabel("Probability density")
    ax2.set_xlabel("Max |spacing error| (GHz)")
    ax2.set_title("10-bin: Max |spacing error| per TOSA (PDF)")
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)

    sort_max_10 = np.sort(max_abs_10)
    cdf_10 = np.arange(1, len(sort_max_10) + 1) / len(sort_max_10)
    ax3.plot(sort_max_10, cdf_10, color="#2ca02c", linewidth=2)
    ax3.set_ylabel("CDF")
    ax3.set_xlabel("Max |spacing error| (GHz)")
    ax3.set_title("10-bin: Max |spacing error| per TOSA (CDF)")
    ax3.set_ylim(0, 1)
    ax3.grid(True, alpha=0.3)

    fig.suptitle("Binned TOSA adjacent channel spacing error", fontsize=11, y=0.98)

    # Table: Max |error|, 4-bin % TOSAs, 10-bin % TOSAs, Wavelength error (nm)
    thresholds_ghz = [20, 40, 100, 200]
    pcts_4 = [100 * np.sum(max_abs_4 <= t) / n_4 for t in thresholds_ghz]
    pcts_10 = [100 * np.sum(max_abs_10 <= t) / n_10 for t in thresholds_ghz]
    wl_errors_nm = [ghz_to_wavelength_error_nm(t) for t in thresholds_ghz]
    table_rows = [["Max |error|", "4-bin % TOSAs", "10-bin % TOSAs", "Wavelength error (nm)"]]
    for t, p4, p10, w in zip(thresholds_ghz, pcts_4, pcts_10, wl_errors_nm):
        table_rows.append([f"≤ {t} GHz", f"{p4:.2f}", f"{p10:.2f}", f"±{w:.3f}"])

    plt.tight_layout(rect=[0, 0.32, 1, 0.92])
    ax_table = fig.add_axes([0.12, 0.02, 0.76, 0.26])
    ax_table.axis("off")
    tbl = ax_table.table(
        cellText=table_rows[1:],
        colLabels=table_rows[0],
        loc="center",
        cellLoc="center",
        colColours=["#e8e8e8"] * 4,
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1.0, 2.5)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {out_path}")


if __name__ == "__main__":
    print("10-bin scheme (deviation from target, GHz):")
    for i in range(N_BINS_10):
        print(f"  {get_bin10_label(i)}")
    print("\n4-bin scheme (BIN0–BIN3):")
    for i in range(N_BINS_4):
        print(f"  {get_bin4_label(i)}")
    print("\nExample: deviation -50 GHz -> 10-bin", deviation_to_bin10(-50), "-> 4-bin", deviation_to_bin4(-50))
    print("Example: deviation +150 GHz -> 10-bin", deviation_to_bin10(150), "-> 4-bin", deviation_to_bin4(150))

    print("\nRunning binned TOSA sampling (200 GHz class) and plotting...")
    rng = np.random.default_rng(42)
    errors_10, errors_4 = run_binned_sampling_200ghz(rng)
    print(f"  10-bin: {len(errors_10):,} TOSAs")
    print(f"  4-bin:  {len(errors_4):,} TOSAs")
    plot_binned_spacing_error_histograms(errors_10, errors_4)
