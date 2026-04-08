"""
Binned-sampling TOSA module for 8-channel, 200 GHz spacing.

Same binning schemes (4-bin and 10-bin) as 4-channel. TOSAs built by picking
one laser per channel from the same bin index. Full inventory, no per-bin cap.
"""

from __future__ import annotations

import numpy as np

C_M_S = 2.998e8
WL_REF_M = 1311.0 * 1e-9
SIGMA_F_GHZ = (C_M_S / (WL_REF_M**2)) * (1.0 / 3.0 * 1e-9) / 1e9

# 8 channels, 200 GHz spacing (GHz)
CHANNELS_8CH_200GHZ = np.array([0.0, 200.0, 400.0, 600.0, 800.0, 1000.0, 1200.0, 1400.0])
N_CHANNELS = 8
NOMINAL_SPACING_8CH = np.full(N_CHANNELS - 1, 200.0)

BIN10_EDGES_GHZ = np.array([
    -1000.0, -160.0, -120.0, -80.0, -40.0, 0.0, 40.0, 80.0, 120.0, 160.0, 200.0,
])
N_BINS_10 = len(BIN10_EDGES_GHZ) - 1
BIN4_EDGES_GHZ = np.array([-1000.0, -100.0, 0.0, 100.0, 1000.0])
N_BINS_4 = len(BIN4_EDGES_GHZ) - 1

def deviation_to_bin10(deviation_ghz: float | np.ndarray) -> int | np.ndarray:
    return np.clip(np.searchsorted(BIN10_EDGES_GHZ, deviation_ghz, side="right") - 1, 0, N_BINS_10 - 1)

def deviation_to_bin4(deviation_ghz: float | np.ndarray) -> int | np.ndarray:
    return np.clip(np.searchsorted(BIN4_EDGES_GHZ, deviation_ghz, side="right") - 1, 0, N_BINS_4 - 1)

def ghz_to_wavelength_error_nm(f_ghz: float, wl_ref_nm: float = 1311.0) -> float:
    lam_m = wl_ref_nm * 1e-9
    delta_f_hz = f_ghz * 1e9
    delta_lam_m = (lam_m**2) * delta_f_hz / C_M_S
    return delta_lam_m * 1e9

N_LASERS_PER_CHANNEL = 10_000_000


def _sample_lasers_per_channel_8ch(n_per_ch: int, rng: np.random.Generator) -> np.ndarray:
    """Shape (n_per_ch, 8). Each column is deviation from that channel's target."""
    out = np.zeros((n_per_ch, N_CHANNELS))
    for ch in range(N_CHANNELS):
        out[:, ch] = CHANNELS_8CH_200GHZ[ch] + rng.normal(0, SIGMA_F_GHZ, size=n_per_ch)
    deviations = np.zeros((n_per_ch, N_CHANNELS))
    for ch in range(N_CHANNELS):
        deviations[:, ch] = out[:, ch] - CHANNELS_8CH_200GHZ[ch]
    return deviations


def _deviations_by_bin(deviations: np.ndarray, to_bin_fn, n_bins: int) -> list[list[np.ndarray]]:
    """deviations (n, 8). Return per channel, per bin, array of deviation values."""
    result = [[] for _ in range(N_CHANNELS)]
    for ch in range(N_CHANNELS):
        result[ch] = [np.array([], dtype=float) for _ in range(n_bins)]
        bins_ch = to_bin_fn(deviations[:, ch])
        for b in range(n_bins):
            result[ch][b] = deviations[bins_ch == b, ch]
    return result


def _build_binned_tosa_spacing_errors(
    deviations_per_ch_per_bin: list[list[np.ndarray]],
    rng: np.random.Generator,
) -> np.ndarray:
    """Returns (n_total, 7) spacing errors for 8-channel."""
    n_bins = len(deviations_per_ch_per_bin[0])
    all_errors = []
    for b in range(n_bins):
        dev_ch = [deviations_per_ch_per_bin[ch][b] for ch in range(N_CHANNELS)]
        n_avail = min(len(d) for d in dev_ch)
        if n_avail == 0:
            continue
        n_build = n_avail
        tosa_deviations = np.zeros((n_build, N_CHANNELS))
        for ch in range(N_CHANNELS):
            idx = rng.choice(len(dev_ch[ch]), size=n_build, replace=(len(dev_ch[ch]) < n_build))
            tosa_deviations[:, ch] = dev_ch[ch][idx]
        tosa_freq = CHANNELS_8CH_200GHZ + tosa_deviations
        spacings = np.diff(tosa_freq, axis=1)
        errs = spacings - NOMINAL_SPACING_8CH
        all_errors.append(errs)
    return np.concatenate(all_errors, axis=0) if all_errors else np.zeros((0, N_CHANNELS - 1))


def run_binned_sampling_8ch(rng: np.random.Generator | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Returns (errors_10, errors_4), each (n_tosas, 7)."""
    if rng is None:
        rng = np.random.default_rng(42)
    n = N_LASERS_PER_CHANNEL
    deviations = _sample_lasers_per_channel_8ch(n, rng)
    by_bin_10 = _deviations_by_bin(deviations, deviation_to_bin10, N_BINS_10)
    by_bin_4 = _deviations_by_bin(deviations, deviation_to_bin4, N_BINS_4)
    errors_10 = _build_binned_tosa_spacing_errors(by_bin_10, rng)
    errors_4 = _build_binned_tosa_spacing_errors(by_bin_4, rng)
    return errors_10, errors_4


def plot_binned_spacing_error_histograms(
    errors_10: np.ndarray,
    errors_4: np.ndarray,
    out_path: str = "binned_sampling_tosa_8ch_spacing_error_histograms.png",
) -> None:
    """Same 2×4 layout as 4-channel; 7 adjacent pairs overlaid with colormap."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n_pairs = N_CHANNELS - 1
    labels = [f"ch{i}–ch{i+1}" for i in range(n_pairs)]
    colors = plt.cm.tab10(np.linspace(0, 1, n_pairs))
    bins_signed = np.linspace(-80, 80, 60)
    bins_mag = np.linspace(0, 80, 60)
    bins_max_abs = np.linspace(0, 120, 60)

    abs_4 = np.abs(errors_4)
    abs_10 = np.abs(errors_10)
    max_abs_4 = np.max(abs_4, axis=1)
    max_abs_10 = np.max(abs_10, axis=1)
    n_4, n_10 = len(max_abs_4), len(max_abs_10)

    fig, axes = plt.subplots(2, 4, figsize=(16, 7), sharex="col")
    for row, (errors, max_abs, scheme) in enumerate([
        (errors_4, max_abs_4, "4-bin"),
        (errors_10, max_abs_10, "10-bin"),
    ]):
        ax0, ax1, ax2, ax3 = axes[row, 0], axes[row, 1], axes[row, 2], axes[row, 3]
        for err_col in range(n_pairs):
            ax0.hist(errors[:, err_col], bins=bins_signed, color=colors[err_col], alpha=0.5, density=True, edgecolor="white", label=labels[err_col])
        ax0.set_ylabel("Probability density")
        ax0.set_xlabel("Spacing error (GHz)")
        ax0.set_title(f"{scheme}: Spacing error (signed)")
        ax0.axvline(0, color="gray", linestyle="--", alpha=0.8)
        ax0.legend(fontsize=6)
        ax0.grid(True, alpha=0.3)

        for err_col in range(n_pairs):
            ax1.hist(np.abs(errors[:, err_col]), bins=bins_mag, color=colors[err_col], alpha=0.5, density=True, edgecolor="white", label=labels[err_col])
        ax1.set_ylabel("Probability density")
        ax1.set_xlabel("|Spacing error| (GHz)")
        ax1.set_title(f"{scheme}: |Spacing error| (magnitude)")
        ax1.legend(fontsize=6)
        ax1.grid(True, alpha=0.3)

        ax2.hist(max_abs, bins=bins_max_abs, color="#9467bd", alpha=0.7, density=True, edgecolor="white")
        ax2.set_ylabel("Probability density")
        ax2.set_xlabel("Max |spacing error| (GHz)")
        ax2.set_title(f"{scheme}: Max |spacing error| per TOSA (PDF)")
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(bottom=0)

        sort_max = np.sort(max_abs)
        cdf = np.arange(1, len(sort_max) + 1) / len(sort_max)
        ax3.plot(sort_max, cdf, color="#2ca02c", linewidth=2)
        ax3.set_ylabel("CDF")
        ax3.set_xlabel("Max |spacing error| (GHz)")
        ax3.set_title(f"{scheme}: Max |spacing error| per TOSA (CDF)")
        ax3.set_ylim(0, 1)
        ax3.grid(True, alpha=0.3)

    fig.suptitle("8-channel TOSA (200 GHz spacing): binned adjacent channel spacing error", fontsize=11, y=0.98)

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
    print("Running 8-channel binned TOSA sampling...")
    rng = np.random.default_rng(42)
    errors_10, errors_4 = run_binned_sampling_8ch(rng)
    print(f"  10-bin: {len(errors_10):,} TOSAs")
    print(f"  4-bin:  {len(errors_4):,} TOSAs")
    plot_binned_spacing_error_histograms(errors_10, errors_4)
