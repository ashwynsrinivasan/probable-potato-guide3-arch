# TOSA Adjacent Channel Spacing: Problem Statement and Strategy Comparison

This report summarizes the problem of **TOSA (Tunable Optical Sub-Assembly) yield** with respect to **adjacent channel spacing error**, and compares three assembly strategies. The goal is to maximize the fraction of TOSAs that meet a **maximum absolute spacing error** threshold (e.g. **≤ 40 GHz**).

---

## 1. Problem Statement

### 1.1 Context

- A **TOSA** contains **4 lasers**, one per channel (ch0–ch3), in a band-muxed architecture.
- Channel centers are defined in **frequency deviation** from a reference wavelength (1311 nm).
- For the **200 GHz class** (the case analyzed here), the four channel centers are:
  - **ch0:** 0 GHz  
  - **ch1:** +200 GHz  
  - **ch2:** −200 GHz  
  - **ch3:** −400 GHz  
  (all relative to the frequency at 1311 nm).

- Each laser’s actual frequency varies around its channel center due to manufacturing spread. We assume a **Gaussian** distribution with **3σ = ±1 nm** in wavelength at 1311 nm, which corresponds to **σ ≈ 58.2 GHz** in frequency.

**Laser frequency distributions by channel (200 GHz and 400 GHz spacing, centered at 1311 nm):**

![Laser frequency histograms by channel](friendly-system-lmi/src/probable-potato-guide3-arch/architecture_band_muxed/laser_frequency_histograms.png)

**Reference wavelength distributions (4 lasers at 1311 nm, 3σ = ±1 nm):**

![Laser wavelength distributions](friendly-system-lmi/src/probable-potato-guide3-arch/architecture_band_muxed/laser_wavelength_distributions.png)

### 1.2 Adjacent Spacing Error

- **Nominal adjacent spacings** (target values) are:
  - ch1 − ch0: **200 GHz**
  - ch2 − ch1: **−400 GHz**
  - ch3 − ch2: **−200 GHz**

- For a given TOSA (four laser frequencies), we compute the **three adjacent spacing errors**:
  - Spacing error (ch0–ch1) = (f₁ − f₀) − 200  
  - Spacing error (ch1–ch2) = (f₂ − f₁) − (−400)  
  - Spacing error (ch2–ch3) = (f₃ − f₂) − (−200)  

- We care about the **maximum absolute spacing error** over these three pairs **per TOSA**:
  - **Max |error| per TOSA** = max{ |e₀₁|, |e₁₂|, |e₂₃| } (in GHz).

### 1.3 Yield Metric

- A TOSA is considered **in-spec** for a threshold **T** (e.g. 40 GHz) if:
  - **Max |spacing error| ≤ T GHz.**

- **Yield** = (number of TOSAs with max |error| ≤ T) / (total number of TOSAs built), expressed as a percentage.

- The report focuses on **maximizing yield at ≤ 40 GHz** and also reports yields at 20, 100, and 200 GHz for context. At 1311 nm, **40 GHz ≈ ±0.23 nm** wavelength error.

---

## 2. Strategies Compared

Three strategies are implemented in this folder. All use the same channel grid and laser statistics (Gaussian, 3σ = ±1 nm at 1311 nm).

### 2.1 Random Sampling

- **Method:** For each TOSA, **randomly** pick one laser from each channel (independent Gaussian samples around each channel center).
- **No binning or matching** across channels.
- **Script:** `random_sampling_tosa.py`  
- **Sample size (this report):** 10 M TOSAs (200 GHz class), seed 42.

### 2.2 Binned Sampling — 4-Bin Scheme

- **Method:**  
  - Sample a **full inventory** of lasers per channel (**10 M per channel**).  
  - Assign each laser to one of **4 bins** by its **deviation from target** (GHz):  
    - **BIN0:** −1000 to −100  
    - **BIN1:** −100 to 0  
    - **BIN2:** 0 to 100  
    - **BIN3:** 100 to 1000  
  - Build TOSAs by selecting **one laser per channel from the same bin index** (e.g. one from BIN2 for ch0, one from BIN2 for ch1, etc.).  
  - **No per-bin cap:** for each bin we build as many TOSAs as the inventory allows (minimum across the four channel-bin counts). Total TOSAs ≈ 10 M.
- **Script:** `binned_sampling_tosa.py`  
- **Total TOSAs (this report):** ~10 M (full inventory).

### 2.3 Binned Sampling — 10-Bin Scheme

- **Method:** Same idea as 4-bin, but with **10 bins** of **40 GHz width** in deviation from target:  
  - BIN0: −1000 to −160, BIN1: −160 to −120, …, BIN9: 160 to 200 GHz.  
  - TOSAs are again built by picking one laser per channel from the **same bin index**. Full inventory per bin (no cap).
- **Script:** `binned_sampling_tosa.py`  
- **Total TOSAs (this report):** ~10 M (full inventory).

### 2.4 Bin definitions (4-bin and 10-bin)

The figure below shows how the **4-bin** and **10-bin** schemes partition laser **deviation from target** (GHz). The gray curve is the laser deviation PDF (Gaussian, σ ≈ 58.2 GHz). Colored vertical bands are the bins; TOSAs are built by picking one laser per channel from the same bin.

![Bin definitions: 4-bin and 10-bin schemes](friendly-system-lmi/src/probable-potato-guide3-arch/architecture_band_muxed/bin_definition_histogram.png)

---

## 3. Yield Comparison (Seed 42)

Numerical results from the scripts in this folder (200 GHz class only):

| Max \|error\| threshold | Random (% TOSAs) | 4-bin (% TOSAs) | 10-bin (% TOSAs) | Wavelength error (nm) |
|------------------------|------------------|-----------------|------------------|------------------------|
| ≤ 20 GHz               | 0.98             | 9.37            | **47.48**        | ±0.115                 |
| **≤ 40 GHz**           | **6.87**         | **40.30**       | **99.88**        | ±0.229                 |
| ≤ 100 GHz              | 51.39            | 99.89           | 100.00           | ±0.573                 |
| ≤ 200 GHz              | 95.86            | 100.00          | 100.00           | ±1.147                 |

**TOSA counts (this run):**  
- Random: 10,000,000  
- 4-bin: 9,995,164  
- 10-bin: 9,993,758  

All three strategies use comparable sample sizes (~10 M TOSAs). Binned sampling uses a **full inventory** of **10 M lasers per channel** with **no per-bin cap**: for each bin we build as many TOSAs as the smallest channel-bin count allows, so nearly the entire inventory is converted to TOSAs.

**Random sampling — adjacent spacing error histograms and yield table:**

![Random sampling: spacing error (signed), \|error\|, max \|error\| PDF, max \|error\| CDF](friendly-system-lmi/src/probable-potato-guide3-arch/architecture_band_muxed/random_sampling_tosa_adjacent_spacing_error_histograms.png)

**Binned sampling (4-bin and 10-bin) — adjacent spacing error histograms and yield table:**

![Binned sampling: 4-bin and 10-bin spacing error panels and table](friendly-system-lmi/src/probable-potato-guide3-arch/architecture_band_muxed/binned_sampling_tosa_spacing_error_histograms.png)

---

## 4. Which Strategy Gives Maximum Yield for ≤ 40 GHz?

- **Random:** **6.87%** of TOSAs have max |spacing error| ≤ 40 GHz.  
- **4-bin binned:** **40.30%** — much better than random.  
- **10-bin binned:** **99.88%** — almost all TOSAs meet the 40 GHz spec.

**Conclusion:** **The 10-bin binned strategy gives the best yield for ≤ 40 GHz |error|** in this setup. By grouping lasers into narrow deviation bins and assembling TOSAs from the same bin index (full inventory, no per-bin cap), adjacent channel spacing errors are greatly reduced, and the 10-bin scheme (40 GHz bin width) aligns well with the 40 GHz error target.

---

## 5. 8-Channel TOSA (200 GHz spacing)

The same process is repeated for an **8-channel TOSA** with **all adjacent channels spaced by 200 GHz**. Channel centers (frequency deviation from 1311 nm ref) are **0, 200, 400, 600, 800, 1000, 1200, 1400 GHz** (ch0–ch7). There are **7 adjacent spacing pairs** (ch0–ch1 through ch6–ch7); each has nominal spacing **200 GHz**. Max |error| per TOSA is the maximum of the 7 absolute spacing errors. Same laser statistics (Gaussian, 3σ = ±1 nm at 1311 nm) and same strategies: **random sampling**, **4-bin binned**, and **10-bin binned** (same bin definitions by deviation from target; full inventory, no per-bin cap). Scripts: `random_sampling_tosa_8ch.py`, `binned_sampling_tosa_8ch.py`. Separate figure files are generated so 4-channel and 8-channel results are not overwritten.

### 5.1 Yield comparison (8-channel, seed 42)

| Max \|error\| threshold | Random (% TOSAs) | 4-bin (% TOSAs) | 10-bin (% TOSAs) | Wavelength error (nm) |
|------------------------|------------------|-----------------|------------------|------------------------|
| ≤ 20 GHz               | 0.00             | 0.74            | **18.55**        | ±0.115                 |
| **≤ 40 GHz**           | **0.27**         | **13.85**       | **99.77**        | ±0.229                 |
| ≤ 100 GHz              | 22.66            | 99.77           | 100.00           | ±0.573                 |
| ≤ 200 GHz              | 90.79            | 100.00          | 100.00           | ±1.147                 |

**TOSA counts (8-channel run):** Random: 10,000,000 | 4-bin: 9,992,829 | 10-bin: 9,989,597.

With more adjacent pairs (7 instead of 3), **random yield at ≤ 40 GHz drops sharply** (0.27% vs 6.87% for 4-channel). **10-bin binned again gives the best yield** (99.77% at ≤ 40 GHz); 4-bin is much better than random (13.85%) but well below 10-bin.

**8-channel random sampling — adjacent spacing error histograms and yield table:**

![8-channel random sampling: spacing error histograms and table](friendly-system-lmi/src/probable-potato-guide3-arch/architecture_band_muxed/random_sampling_tosa_8ch_adjacent_spacing_error_histograms.png)

**8-channel binned sampling (4-bin and 10-bin) — adjacent spacing error histograms and yield table:**

![8-channel binned sampling: 4-bin and 10-bin spacing error panels and table](friendly-system-lmi/src/probable-potato-guide3-arch/architecture_band_muxed/binned_sampling_tosa_8ch_spacing_error_histograms.png)

---

## 6. Artifacts in This Folder

| File | Description |
|------|-------------|
| `random_sampling_tosa.py` | Random TOSA assembly; computes spacing errors and plots histograms + summary table. |
| `random_sampling_tosa_adjacent_spacing_error_histograms.png` | One row: signed spacing error, \|error\|, max \|error\| PDF, max \|error\| CDF; table with % TOSAs and λ error. |
| `binned_sampling_tosa.py` | 4-bin and 10-bin binned TOSA assembly; same plot layout per scheme. |
| `binned_sampling_tosa_spacing_error_histograms.png` | Two rows (4-bin, 10-bin), four columns each (same as above); table with 4-bin and 10-bin % TOSAs and wavelength error. |
| `bin_definition_histogram.py` | Plots 4-bin and 10-bin scheme definitions (deviation from target) with laser PDF. |
| `bin_definition_histogram.png` | Single figure: two panels showing bin edges and laser deviation PDF for 4-bin and 10-bin. |
| `laser_frequency_histograms.py` | Histograms of laser frequency deviation per channel (200 / 400 GHz classes). |
| `laser_wavelength_distributions.py` | Wavelength distribution visualization (reference). |
| `random_sampling_tosa_8ch.py` | Random TOSA assembly for 8-channel 200 GHz; outputs `random_sampling_tosa_8ch_adjacent_spacing_error_histograms.png`. |
| `random_sampling_tosa_8ch_adjacent_spacing_error_histograms.png` | 8-channel random: signed \|error\|, max \|error\| PDF/CDF and table. |
| `binned_sampling_tosa_8ch.py` | Binned TOSA assembly for 8-channel 200 GHz; outputs `binned_sampling_tosa_8ch_spacing_error_histograms.png`. |
| `binned_sampling_tosa_8ch_spacing_error_histograms.png` | 8-channel binned (4-bin and 10-bin) spacing error panels and table. |

---

## 7. Reproducibility

- **Random:** `np.random.seed(42)` then `build_tosas_for_class(CHANNELS_200_GHZ, N_TOSAS_PER_CLASS)`.  
- **Binned:** `np.random.default_rng(42)` then `run_binned_sampling_200ghz(rng)`. Uses 10 M lasers per channel and full inventory (no per-bin cap).  
- Run `python random_sampling_tosa.py`, `python binned_sampling_tosa.py`, and `python bin_definition_histogram.py` from `architecture_band_muxed` to regenerate 4-channel figures. For 8-channel: `python random_sampling_tosa_8ch.py`, `python binned_sampling_tosa_8ch.py`.

---

## Export to PDF (with figures)

To export this report to PDF with all figures embedded:

1. **Pandoc (command line)**  
   From the **repository root** (so image paths in the doc resolve correctly):
   ```bash
   pandoc src/probable-potato-guide3-arch/architecture_band_muxed/TOSA_SPACING_YIELD_REPORT.md -o src/probable-potato-guide3-arch/architecture_band_muxed/TOSA_SPACING_YIELD_REPORT.pdf
   ```
   Requires [pandoc](https://pandoc.org/) and a LaTeX engine (e.g. MacTeX, TeX Live) or use `--pdf-engine=wkhtmltopdf` if installed.

2. **Cursor / VS Code**  
   Install the **Markdown PDF** extension. Open this file, then run **Markdown PDF: Export (pdf)** from the Command Palette (`Cmd+Shift+P`). Export uses the same folder as the `.md` file; ensure image paths in the report match how the extension resolves paths (workspace root vs file-relative).

3. **Jupyter notebook**  
   Use `TOSA_SPACING_YIELD_REPORT.ipynb`: run all cells to generate figures, then **File → Print → Save as PDF** or `jupyter nbconvert --to pdf TOSA_SPACING_YIELD_REPORT.ipynb` (requires LaTeX or `--to webpdf` with playwright).
