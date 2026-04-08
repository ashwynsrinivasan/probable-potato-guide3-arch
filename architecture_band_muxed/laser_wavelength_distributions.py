"""
Four laser types with center wavelengths at 1308, 1310, 1312, 1314 nm.
Each has a 3-sigma distribution of +/- 1 nm in center wavelength.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for saving without display
import matplotlib.pyplot as plt

# Laser center wavelengths (nm)
CENTERS = [1308, 1310, 1312, 1314]

# 3-sigma = +/- 1 nm  =>  sigma = 1/3 nm
SIGMA = 1.0 / 3.0  # nm

# Wavelength range for plotting
WL_MIN = 1304
WL_MAX = 1318
N_POINTS = 1000

wavelength = np.linspace(WL_MIN, WL_MAX, N_POINTS)


def gaussian(wl: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Normal (Gaussian) PDF."""
    return (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((wl - mu) / sigma) ** 2)


def main():
    fig, ax = plt.subplots(figsize=(10, 5))

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    labels = [f"{c} nm" for c in CENTERS]

    for center, color, label in zip(CENTERS, colors, labels):
        pdf = gaussian(wavelength, center, SIGMA)
        ax.plot(wavelength, pdf, color=color, label=label, linewidth=2)

    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Probability density")
    ax.set_title("Laser center wavelength distributions (3σ = ±1 nm)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(WL_MIN, WL_MAX)
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig("laser_wavelength_distributions.png", dpi=150)
    print("Saved laser_wavelength_distributions.png")


if __name__ == "__main__":
    main()
