"""
Two laser classes with 200 GHz and 400 GHz channel spacing, centered at 1311 nm.
3σ = ±1 nm in wavelength per channel. Sample 10k lasers per class.
Histogram of frequency deviation from f(1311 nm), one subplot per class.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Reference: 1311 nm
C_M_S = 2.998e8  # m/s
WL_REF_NM = 1311.0
WL_REF_M = WL_REF_NM * 1e-9
F_REF_HZ = C_M_S / WL_REF_M  # Hz
F_REF_GHZ = F_REF_HZ / 1e9

# 3σ = ±1 nm in wavelength => σ_λ = 1/3 nm. Convert to frequency: Δf ≈ -c Δλ/λ²
# At 1311 nm: |df/dλ| = c/λ² ≈ 2.998e8 / (1311e-9)^2 = 174.5e9 Hz/nm => σ_f = 174.5/3 GHz
SIGMA_WL_NM = 1.0 / 3.0
SIGMA_F_GHZ = (C_M_S / (WL_REF_M ** 2)) * (SIGMA_WL_NM * 1e-9) / 1e9  # GHz

N_SAMPLES = 4_000_000  # 1M per channel per class

# 200 GHz spacing: 0, +200, -200, -400 GHz
CHANNELS_200_GHZ = np.array([0.0, 200.0, -200.0, -400.0])

# 400 GHz spacing: 0, +400, -400, -800 GHz
CHANNELS_400_GHZ = np.array([0.0, 400.0, -400.0, -800.0])


# Color and label for each channel (ch0, ch1, ch2, ch3)
CHANNEL_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
CHANNEL_LABELS = ["ch0", "ch1", "ch2", "ch3"]


def sample_lasers_ghz(
    channel_offsets_ghz: np.ndarray,
    n_samples: int,
    sigma_f_ghz: float,
) -> list[np.ndarray]:
    """
    Sample laser center frequencies per channel. Each channel gets n_samples/4 lasers.
    Returns list of deviation arrays (one per channel), each deviation from f(1311 nm) in GHz.
    """
    n_ch = len(channel_offsets_ghz)
    n_per_ch = n_samples // n_ch
    result = []
    for ch in range(n_ch):
        center_ghz = channel_offsets_ghz[ch]
        deviations_ghz = center_ghz + np.random.normal(0, sigma_f_ghz, size=n_per_ch)
        result.append(deviations_ghz)
    return result


def main():
    np.random.seed(42)
    samples_200 = sample_lasers_ghz(CHANNELS_200_GHZ, N_SAMPLES, SIGMA_F_GHZ)
    samples_400 = sample_lasers_ghz(CHANNELS_400_GHZ, N_SAMPLES, SIGMA_F_GHZ)

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    bins = np.linspace(-1000, 500, 80)  # GHz deviation (covers -800 to +400)

    for ax, samples, title in [
        (axes[0], samples_200, "200 GHz channel spacing (centered at 1311 nm)"),
        (axes[1], samples_400, "400 GHz channel spacing (centered at 1311 nm)"),
    ]:
        for dev_ghz, color, label in zip(samples, CHANNEL_COLORS, CHANNEL_LABELS):
            ax.hist(dev_ghz, bins=bins, color=color, alpha=0.6, edgecolor="white", density=True, label=label)
        ax.set_ylabel("Probability density")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(bins[0], bins[-1])

    axes[1].set_xlabel("Frequency deviation from f(1311 nm) (GHz)")

    plt.tight_layout()
    plt.savefig("laser_frequency_histograms.png", dpi=150)
    print("Saved laser_frequency_histograms.png")


if __name__ == "__main__":
    main()
