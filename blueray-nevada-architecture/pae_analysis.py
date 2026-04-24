"""
pae_analysis.py
===============
Power-Added Efficiency (PAE) analysis for the OpenLight O-Band 15 dBm HPSOA.
Based on APP-002012 Rev 3.1 models.

PAE definition (primary metric)
--------------------------------
    PAE [%] = (P_out − P_in) / P_elec × 100

    P_out  = target optical output power [W].
    P_in   = P_out / g  (g = saturated gain via Newton-Raphson, Eq.10).
    P_elec = V × I      (electrical drive power, Eq.16 & 17).

PAE only credits added optical power; WPE counts all of P_out.

Electrical model (Eq.16, Eq.17)
    I   [A]  = J [kA/cm²] × 1e3 × W [µm]×1e-4 × Lt [µm]×1e-4
    Rs  [Ω]  = 4.34/W + 2151/Lt − 0.992
    V   [V]  = 1.05 + I × Rs
    P_elec   = V × I

Design-point sweeps
-------------------
  Plot 01 — PAE vs active length L        (J sweep,  T=80°C,  λ=1311nm, Po=15dBm)
  Plot 02 — PAE vs current density J      (L sweep,  T=80°C,  λ=1311nm, Po=15dBm)
  Plot 03 — PAE vs temperature T          (J sweep,  L=240µm, λ=1311nm, Po=15dBm)
  Plot 04 — PAE vs wavelength λ           (T sweep,  J=7,     L=240µm,  Po=15dBm)
  Plot 05 — PAE vs output power Po        (T=[35,55,80]°C × J=[3,5,7] kA/cm²)
  Plot 06 — Gain compression + PAE overlay (dual y-axes vs Po)
  Plot 07 — 2-D contour PAE in (L, J)    (T=80°C, λ=1311nm, Po=15dBm)
  Plot 08 — 2-D contour PAE in (T, J)    (L=240µm, λ=1311nm, Po=15dBm)
  Plot 09 — Power budget vs J             (P_elec, P_out, P_added, P_in + PAE)
  Plot 10 — PAE vs gain tradeoff          (across L and J)
  Plot 11 — Electrical operating point    (I and V vs L at different J)
  Plot 12 — Summary dashboard             (PAE, g0, Pos, NF vs T)
  Plot 13 — PAE & gain vs Po             (length sweep)

Saves all figures to:  results/ph18_soa/pae/
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ph18_soa import ph18_soa_15dBm

# ============================================================================
#  CORE EFFICIENCY CALCULATOR
# ============================================================================

def compute_efficiency(W, L, T, J, lam, Po_dBm, clip_Pos_lam=True):
    """
    Compute PAE, WPE, and intermediate quantities for one design point.

    Parameters
    ----------
    W, L         : float, ridge width [µm] and active length [µm]
    T, J         : float, temperature [°C] and current density [kA/cm²]
    lam          : float, wavelength [nm]
    Po_dBm       : float, target output power [dBm]
    clip_Pos_lam : bool, clamp lam to [1304,1318] for rsm_pos

    Returns dict — pae, wpe, g0_dB, g_dB, Pos_dBm,
                   P_elec_mW, P_out_mW, P_in_mW, P_added_mW, I_mA, V, Rs
    """
    soa = ph18_soa_15dBm(W=W, L=L)

    g_pk   = soa.rsm_gpk(T, J, L)
    lp     = soa.rsm_lambda_pk(T, J, L)
    fw     = soa.rsm_fwhm(T, J, L)
    g0_lin = max(soa.unsaturated_gain_spectrum([lam], g_pk, lp, fw)[0], 1.001)

    lam_pos = float(np.clip(lam, 1304, 1318)) if clip_Pos_lam else float(lam)
    Pos_dBm = soa.rsm_pos(lam_pos, J, T)

    g_lin = max(soa.newton_gain_vs_output_power(Pos_dBm, g0_lin, [Po_dBm])[0], 1.0)

    Po_W  = 10.0 ** ((Po_dBm - 30.0) / 10.0)
    Pin_W = Po_W / g_lin

    Lt     = soa.Lt
    I_A    = J * 1e3 * W * 1e-4 * Lt * 1e-4
    Rs     = soa.series_resistance()
    V      = soa.V_TURN_ON + I_A * Rs
    P_elec = V * I_A

    pae = (Po_W - Pin_W) / P_elec * 100.0
    wpe =  Po_W          / P_elec * 100.0

    return dict(
        pae        = pae,
        wpe        = wpe,
        g0_dB      = 10.0 * np.log10(g0_lin),
        g_dB       = 10.0 * np.log10(g_lin),
        Pos_dBm    = Pos_dBm,
        P_elec_mW  = P_elec * 1e3,
        P_out_mW   = Po_W   * 1e3,
        P_in_mW    = Pin_W  * 1e3,
        P_added_mW = (Po_W - Pin_W) * 1e3,
        I_mA       = I_A    * 1e3,
        V          = V,
        Rs         = Rs,
        g0_lin     = g0_lin,
        g_lin      = g_lin,
    )


# ============================================================================
#  HELPERS
# ============================================================================

STYLE  = dict(linewidth=2.0)
COLORS = plt.rcParams['axes.prop_cycle'].by_key()['color']

def _save(path):
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close('all')


# ============================================================================
#  PLOT FUNCTIONS  —  pyplot functional API throughout
# ============================================================================

def plot01_pae_vs_length(out_dir, W=2.0, T=80.0, lam=1311.0, Po_dBm=15.0):
    """PAE & gain vs active length L for J = [3, 5, 7] kA/cm²."""
    L_arr  = np.linspace(40, 440, 80)
    J_vals = [3.0, 5.0, 7.0]

    plt.figure(figsize=(11, 5))
    plt.suptitle(f'PAE & Gain vs Active Length L\n'
                 f'(T={T}°C, λ={lam} nm, Po={Po_dBm} dBm, W={W} µm)',
                 fontsize=12)

    for panel, (ylabel, title, key) in enumerate(
            [('PAE [%]', 'Power-Added Efficiency', 'pae'),
             ('g₀ [dB]', 'Unsaturated Gain',       'g0_dB')], start=1):
        plt.subplot(1, 2, panel)
        for J, color in zip(J_vals, COLORS):
            vals = [compute_efficiency(W, L, T, J, lam, Po_dBm)[key] for L in L_arr]
            plt.plot(L_arr, vals, color=color, label=f'J={J} kA/cm²', **STYLE)
        plt.xlabel('Active Length L [µm]', fontsize=11)
        plt.ylabel(ylabel, fontsize=11)
        plt.title(title, fontsize=11)
        plt.legend(fontsize=9)
        plt.grid(True, alpha=0.35)
        plt.xlim(40, 440)
        plt.ylim(bottom=0)

    _save(os.path.join(out_dir, 'plot01_pae_vs_length.png'))


def plot02_pae_vs_current_density(out_dir, W=2.0, T=80.0, lam=1311.0,
                                   Po_dBm=15.0):
    """PAE & gain vs J for L = [40, 140, 240, 340, 440] µm."""
    J_arr  = np.linspace(3, 7, 100)
    L_vals = [40, 140, 240, 340, 440]

    plt.figure(figsize=(11, 5))
    plt.suptitle(f'PAE & Gain vs Current Density J\n'
                 f'(T={T}°C, λ={lam} nm, Po={Po_dBm} dBm, W={W} µm)',
                 fontsize=12)

    for panel, (ylabel, title, key) in enumerate(
            [('PAE [%]', 'Power-Added Efficiency', 'pae'),
             ('g₀ [dB]', 'Unsaturated Gain',       'g0_dB')], start=1):
        plt.subplot(1, 2, panel)
        for L, color in zip(L_vals, COLORS):
            vals = [compute_efficiency(W, L, T, J, lam, Po_dBm)[key] for J in J_arr]
            plt.plot(J_arr, vals, color=color, label=f'L={L} µm', **STYLE)
        plt.xlabel('Current Density J [kA/cm²]', fontsize=11)
        plt.ylabel(ylabel, fontsize=11)
        plt.title(title, fontsize=11)
        plt.legend(fontsize=9)
        plt.grid(True, alpha=0.35)
        plt.xlim(3, 7)
        plt.ylim(bottom=0)

    _save(os.path.join(out_dir, 'plot02_pae_vs_J.png'))


def plot03_pae_vs_temperature(out_dir, W=2.0, L=240.0, lam=1311.0,
                               Po_dBm=15.0):
    """PAE & gain vs temperature T for J = [3, 5, 7] kA/cm²."""
    T_arr  = np.linspace(35, 80, 100)
    J_vals = [3.0, 5.0, 7.0]

    plt.figure(figsize=(11, 5))
    plt.suptitle(f'PAE & Gain vs Temperature\n'
                 f'(L={L} µm, λ={lam} nm, Po={Po_dBm} dBm, W={W} µm)',
                 fontsize=12)

    for panel, (ylabel, title, key) in enumerate(
            [('PAE [%]', 'Power-Added Efficiency', 'pae'),
             ('g₀ [dB]', 'Unsaturated Gain',       'g0_dB')], start=1):
        plt.subplot(1, 2, panel)
        for J, color in zip(J_vals, COLORS):
            vals = [compute_efficiency(W, L, T, J, lam, Po_dBm)[key] for T in T_arr]
            plt.plot(T_arr, vals, color=color, label=f'J={J} kA/cm²', **STYLE)
        plt.xlabel('Temperature T [°C]', fontsize=11)
        plt.ylabel(ylabel, fontsize=11)
        plt.title(title, fontsize=11)
        plt.legend(fontsize=9)
        plt.grid(True, alpha=0.35)
        plt.xlim(35, 80)
        plt.ylim(bottom=0)

    _save(os.path.join(out_dir, 'plot03_pae_vs_temperature.png'))


def plot04_pae_vs_wavelength(out_dir, W=2.0, L=240.0, J=7.0, Po_dBm=15.0):
    """PAE & g0 vs wavelength λ for T = [35, 55, 70, 80] °C."""
    lam_arr = np.linspace(1260, 1360, 200)
    temps   = [35, 55, 70, 80]

    plt.figure(figsize=(11, 5))
    plt.suptitle(f'PAE & Gain vs Wavelength\n'
                 f'(L={L} µm, J={J} kA/cm², Po={Po_dBm} dBm, W={W} µm)',
                 fontsize=12)

    for panel, (ylabel, title, key) in enumerate(
            [('PAE [%]', 'Power-Added Efficiency', 'pae'),
             ('g₀ [dB]', 'Unsaturated Gain',       'g0_dB')], start=1):
        plt.subplot(1, 2, panel)
        for T, color in zip(temps, COLORS):
            vals = [compute_efficiency(W, L, T, J, lam, Po_dBm,
                                       clip_Pos_lam=True)[key]
                    for lam in lam_arr]
            plt.plot(lam_arr, vals, color=color, label=f'T={T}°C', **STYLE)
        plt.axvspan(1304, 1318, alpha=0.08, color='green',
                    label='Pos validated range')
        plt.xlabel('Wavelength λ [nm]', fontsize=11)
        plt.ylabel(ylabel, fontsize=11)
        plt.title(title, fontsize=11)
        plt.legend(fontsize=8)
        plt.grid(True, alpha=0.35)
        plt.xlim(1260, 1360)
        plt.ylim(bottom=0)

    _save(os.path.join(out_dir, 'plot04_pae_vs_wavelength.png'))


def plot05_pae_vs_output_power(out_dir, W=2.0, L=240.0, lam=1311.0):
    """
    PAE vs output power Po — 3 panels (one per temperature), J = [3, 5, 7].
    T = [35, 55, 80] °C × J = [3, 5, 7] kA/cm²  →  9 conditions total.
    """
    Po_arr = np.linspace(-10, 17, 200)
    temps  = [35, 55, 80]
    J_vals = [3.0, 5.0, 7.0]
    J_colors = {3.0: COLORS[0], 5.0: COLORS[1], 7.0: COLORS[2]}
    J_styles = {3.0: ':',       5.0: '--',       7.0: '-'}

    plt.figure(figsize=(15, 5))
    plt.suptitle(f'PAE vs Output Power Po  —  T = [35, 55, 80]°C, '
                 f'J = [3, 5, 7] kA/cm²\n'
                 f'(L={L} µm, λ={lam} nm, W={W} µm)',
                 fontsize=12)

    for panel, T in enumerate(temps, start=1):
        plt.subplot(1, 3, panel)
        for J in J_vals:
            pae_arr = [compute_efficiency(W, L, T, J, lam, Po)['pae']
                       for Po in Po_arr]
            plt.plot(Po_arr, pae_arr,
                     color=J_colors[J], linestyle=J_styles[J],
                     linewidth=2.0, label=f'J={J} kA/cm²')
        plt.axvline(15.0, color='black', linestyle='--', linewidth=1,
                    alpha=0.55, label='15 dBm target')
        plt.xlabel('Output Power Po [dBm]', fontsize=11)
        plt.ylabel('PAE [%]', fontsize=11)
        plt.title(f'T = {T}°C', fontsize=11)
        plt.legend(fontsize=9)
        plt.grid(True, alpha=0.35)
        plt.xlim(-10, 17)
        plt.ylim(bottom=0)

    _save(os.path.join(out_dir, 'plot05_pae_vs_Po.png'))


def plot06_gain_compression_pae_overlay(out_dir, W=2.0, L=240.0,
                                         T=80.0, J=7.0, lam=1311.0):
    """Gain compression and PAE on dual y-axes vs output power."""
    soa = ph18_soa_15dBm(W=W, L=L)
    g_pk   = soa.rsm_gpk(T, J, L)
    lp     = soa.rsm_lambda_pk(T, J, L)
    fw     = soa.rsm_fwhm(T, J, L)
    g0_lin = max(soa.unsaturated_gain_spectrum([lam], g_pk, lp, fw)[0], 1.001)
    Pos_dBm = soa.rsm_pos(float(np.clip(lam, 1304, 1318)), J, T)

    Po_arr = np.linspace(-10, 17, 200)
    g_arr  = soa.newton_gain_vs_output_power(Pos_dBm, g0_lin, Po_arr)
    g_dB   = 10.0 * np.log10(np.maximum(g_arr, 1e-30))
    g0_dB  = 10.0 * np.log10(g0_lin)

    Lt     = soa.Lt
    I_A    = J * 1e3 * W * 1e-4 * Lt * 1e-4
    Rs     = soa.series_resistance()
    V      = soa.V_TURN_ON + I_A * Rs
    P_elec = V * I_A
    Po_W   = 10.0 ** ((Po_arr - 30.0) / 10.0)
    Pin_W  = Po_W / np.maximum(g_arr, 1.0)
    pae_arr = (Po_W - Pin_W) / P_elec * 100.0

    color_g   = '#1f77b4'
    color_pae = '#d62728'

    plt.figure(figsize=(7, 5))
    ax1 = plt.gca()
    l1, = ax1.plot(Po_arr, g_dB, color=color_g, **STYLE, label='Gain g [dB]')
    ax1.axhline(g0_dB,     color=color_g, linestyle='--', alpha=0.5, linewidth=1)
    ax1.axhline(g0_dB - 3, color=color_g, linestyle=':',  alpha=0.5, linewidth=1)
    ax1.axvline(Pos_dBm,   color='gray',  linestyle='--', alpha=0.5, linewidth=1)
    plt.xlabel('Output Power Po [dBm]', fontsize=12)
    ax1.set_ylabel('Gain g [dB]', color=color_g, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color_g)
    plt.xlim(-10, 17)
    ax1.text(Pos_dBm + 0.3, g0_dB - 5.5,
             f'Pos = {Pos_dBm:.1f} dBm', fontsize=9, color='gray')

    ax2 = ax1.twinx()
    l2, = ax2.plot(Po_arr, pae_arr, color=color_pae, linestyle='-.',
                   **STYLE, label='PAE [%]')
    ax2.set_ylabel('PAE [%]', color=color_pae, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=color_pae)
    ax2.set_ylim(bottom=0)

    ax1.legend([l1, l2], [l1.get_label(), l2.get_label()],
               fontsize=9, loc='lower left')
    ax1.grid(True, alpha=0.3)
    plt.title(
        f'Gain Compression & PAE vs Output Power\n'
        f'(T={T}°C, J={J} kA/cm², λ={lam} nm, L={L} µm, W={W} µm)',
        fontsize=11)

    _save(os.path.join(out_dir, 'plot06_gain_pae_overlay.png'))


def plot07_contour_pae_L_J(out_dir, W=2.0, T=80.0, lam=1311.0, Po_dBm=15.0):
    """2-D PAE contour map in (L, J) space."""
    L_arr = np.linspace(40, 440, 60)
    J_arr = np.linspace(3, 7, 60)
    LL, JJ = np.meshgrid(L_arr, J_arr)

    PAE = np.zeros_like(LL)
    G0  = np.zeros_like(LL)
    for i in range(LL.shape[0]):
        for j in range(LL.shape[1]):
            r = compute_efficiency(W, LL[i, j], T, JJ[i, j], lam, Po_dBm)
            PAE[i, j] = r['pae']
            G0[i, j]  = r['g0_dB']

    plt.figure(figsize=(13, 5))
    plt.suptitle(f'2-D Design Space: PAE & Gain in (L, J)\n'
                 f'(T={T}°C, λ={lam} nm, Po={Po_dBm} dBm, W={W} µm)',
                 fontsize=12)

    for panel, (data, label, cmap) in enumerate(
            [(PAE, 'PAE [%]', 'viridis'),
             (G0,  'g₀ [dB]', 'plasma')], start=1):
        plt.subplot(1, 2, panel)
        cf = plt.contourf(LL, JJ, data, levels=20, cmap=cmap)
        cs = plt.contour(LL, JJ, data, levels=10, colors='white',
                         alpha=0.4, linewidths=0.7)
        plt.clabel(cs, inline=True, fontsize=7, fmt='%.1f')
        plt.colorbar(cf, label=label)
        plt.xlabel('Active Length L [µm]', fontsize=11)
        plt.ylabel('Current Density J [kA/cm²]', fontsize=11)
        plt.title(label, fontsize=11)

    _save(os.path.join(out_dir, 'plot07_contour_pae_L_J.png'))


def plot08_contour_pae_T_J(out_dir, W=2.0, L=240.0, lam=1311.0, Po_dBm=15.0):
    """2-D PAE contour map in (T, J) space."""
    T_arr = np.linspace(35, 80, 60)
    J_arr = np.linspace(3, 7, 60)
    TT, JJ = np.meshgrid(T_arr, J_arr)

    PAE = np.zeros_like(TT)
    G0  = np.zeros_like(TT)
    for i in range(TT.shape[0]):
        for j in range(TT.shape[1]):
            r = compute_efficiency(W, L, TT[i, j], JJ[i, j], lam, Po_dBm)
            PAE[i, j] = r['pae']
            G0[i, j]  = r['g0_dB']

    plt.figure(figsize=(13, 5))
    plt.suptitle(f'2-D Design Space: PAE & Gain in (T, J)\n'
                 f'(L={L} µm, λ={lam} nm, Po={Po_dBm} dBm, W={W} µm)',
                 fontsize=12)

    for panel, (data, label, cmap) in enumerate(
            [(PAE, 'PAE [%]', 'viridis'),
             (G0,  'g₀ [dB]', 'plasma')], start=1):
        plt.subplot(1, 2, panel)
        cf = plt.contourf(TT, JJ, data, levels=20, cmap=cmap)
        cs = plt.contour(TT, JJ, data, levels=10, colors='white',
                         alpha=0.4, linewidths=0.7)
        plt.clabel(cs, inline=True, fontsize=7, fmt='%.1f')
        plt.colorbar(cf, label=label)
        plt.xlabel('Temperature T [°C]', fontsize=11)
        plt.ylabel('Current Density J [kA/cm²]', fontsize=11)
        plt.title(label, fontsize=11)

    _save(os.path.join(out_dir, 'plot08_contour_pae_T_J.png'))


def plot09_power_budget(out_dir, W=2.0, L=240.0, T=80.0, lam=1311.0,
                         Po_dBm=15.0):
    """Power budget (P_elec, P_out, P_added, P_in) and PAE vs J."""
    J_arr       = np.linspace(3, 7, 100)
    P_elec_arr  = []
    P_out_arr   = []
    P_in_arr    = []
    P_added_arr = []
    pae_arr     = []

    for J in J_arr:
        r = compute_efficiency(W, L, T, J, lam, Po_dBm)
        P_elec_arr.append(r['P_elec_mW'])
        P_out_arr.append(r['P_out_mW'])
        P_in_arr.append(r['P_in_mW'])
        P_added_arr.append(r['P_added_mW'])
        pae_arr.append(r['pae'])

    P_elec_arr  = np.array(P_elec_arr)
    P_out_arr   = np.array(P_out_arr)
    P_in_arr    = np.array(P_in_arr)
    P_added_arr = np.array(P_added_arr)
    pae_arr     = np.array(pae_arr)

    plt.figure(figsize=(12, 5))
    plt.suptitle(f'Power Budget vs Current Density J\n'
                 f'(L={L} µm, T={T}°C, λ={lam} nm, Po={Po_dBm} dBm, W={W} µm)',
                 fontsize=12)

    plt.subplot(1, 2, 1)
    plt.plot(J_arr, P_elec_arr,  'k-',  **STYLE, label='P_elec  (electrical in)')
    plt.plot(J_arr, P_out_arr,   'b-',  **STYLE, label='P_out   (optical out)')
    plt.plot(J_arr, P_in_arr,    'g--', **STYLE, label='P_in    (optical in)')
    plt.plot(J_arr, P_added_arr, 'r:',  **STYLE, label='P_added (P_out − P_in)')
    plt.xlabel('Current Density J [kA/cm²]', fontsize=11)
    plt.ylabel('Power [mW]', fontsize=11)
    plt.title('Power Budget', fontsize=11)
    plt.legend(fontsize=9)
    plt.grid(True, alpha=0.35)
    plt.xlim(3, 7)

    plt.subplot(1, 2, 2)
    ax2  = plt.gca()
    ax2b = ax2.twinx()
    ax2.plot(J_arr,  pae_arr,    'b-',  **STYLE, label='PAE [%]')
    ax2b.plot(J_arr, P_elec_arr, 'r--', **STYLE, label='P_elec [mW]')
    ax2.set_xlabel('Current Density J [kA/cm²]', fontsize=11)
    ax2.set_ylabel('PAE [%]',     color='b', fontsize=11)
    ax2b.set_ylabel('P_elec [mW]', color='r', fontsize=11)
    ax2.tick_params(axis='y',  labelcolor='b')
    ax2b.tick_params(axis='y', labelcolor='r')
    ax2.legend(ax2.get_lines() + ax2b.get_lines(),
               [l.get_label() for l in ax2.get_lines() + ax2b.get_lines()],
               fontsize=9)
    ax2.set_title('PAE vs Electrical Power', fontsize=11)
    ax2.grid(True, alpha=0.35)
    ax2.set_xlim(3, 7)
    ax2.set_ylim(bottom=0)

    _save(os.path.join(out_dir, 'plot09_power_budget.png'))


def plot10_pae_vs_gain_tradeoff(out_dir, W=2.0, T=80.0, lam=1311.0,
                                  Po_dBm=15.0):
    """PAE vs g0: efficiency–gain tradeoff across (L, J)."""
    L_vals = [40, 100, 160, 240, 340, 440]
    J_arr  = np.linspace(3, 7, 50)

    norm = Normalize(vmin=3, vmax=7)
    cmap = cm.plasma

    plt.figure(figsize=(7, 5))
    sc_last = None
    for L in L_vals:
        pae_arr = [compute_efficiency(W, L, T, J, lam, Po_dBm)['pae'] for J in J_arr]
        g0_arr  = [compute_efficiency(W, L, T, J, lam, Po_dBm)['g0_dB'] for J in J_arr]
        sc_last = plt.scatter(g0_arr, pae_arr, c=J_arr, cmap=cmap, norm=norm,
                              s=25, zorder=3)
        plt.plot(g0_arr, pae_arr, alpha=0.4, linewidth=1,
                 color=cmap(norm(float(J_arr.mean()))))
        plt.annotate(f'L={L}', xy=(g0_arr[-1], pae_arr[-1]),
                     fontsize=7, ha='left', va='bottom',
                     xytext=(3, 2), textcoords='offset points')

    plt.colorbar(sc_last, label='J [kA/cm²]')
    plt.xlabel('Unsaturated Gain g₀ [dB]', fontsize=12)
    plt.ylabel('PAE [%]', fontsize=12)
    plt.title(
        f'PAE vs Gain Tradeoff  (T={T}°C, λ={lam} nm, Po={Po_dBm} dBm)\n'
        f'Each curve = fixed L;  colour = J [kA/cm²]',
        fontsize=11)
    plt.grid(True, alpha=0.35)
    plt.ylim(bottom=0)

    _save(os.path.join(out_dir, 'plot10_pae_vs_gain_tradeoff.png'))


def plot11_electrical_operating_point(out_dir, W=2.0, T=80.0, lam=1311.0):
    """Drive current I [mA] and terminal voltage V [V] vs L at different J."""
    L_arr  = np.linspace(40, 440, 100)
    J_vals = [3.0, 5.0, 7.0]

    plt.figure(figsize=(11, 5))
    plt.suptitle(f'Electrical Operating Point vs Active Length L\n'
                 f'(T={T}°C, W={W} µm)',
                 fontsize=12)

    for panel, (ylabel, title, key) in enumerate(
            [('Drive Current I [mA]',   'Drive Current vs Length',   'I'),
             ('Terminal Voltage V [V]', 'Terminal Voltage vs Length', 'V')],
            start=1):
        plt.subplot(1, 2, panel)
        for J, color in zip(J_vals, COLORS):
            vals = []
            for L in L_arr:
                soa = ph18_soa_15dBm(W=W, L=L)
                I_A = J * 1e3 * W * 1e-4 * soa.Lt * 1e-4
                Rs  = soa.series_resistance()
                V   = soa.V_TURN_ON + I_A * Rs
                vals.append(I_A * 1e3 if key == 'I' else V)
            plt.plot(L_arr, vals, color=color, label=f'J={J} kA/cm²', **STYLE)
        plt.xlabel('Active Length L [µm]', fontsize=11)
        plt.ylabel(ylabel, fontsize=11)
        plt.title(title, fontsize=11)
        plt.legend(fontsize=9)
        plt.grid(True, alpha=0.35)
        plt.xlim(40, 440)

    _save(os.path.join(out_dir, 'plot11_electrical_operating_point.png'))


def plot12_summary_dashboard(out_dir, W=2.0, L=240.0, J=7.0, lam=1311.0,
                               Po_dBm=15.0):
    """4-panel summary dashboard: PAE, g0, Pos, NF vs temperature T."""
    T_arr = np.linspace(35, 80, 100)
    soa   = ph18_soa_15dBm(W=W, L=L)

    pae_arr = []
    g0_arr  = []
    pos_arr = []
    nf_arr  = []
    for T in T_arr:
        r = compute_efficiency(W, L, T, J, lam, Po_dBm)
        pae_arr.append(r['pae'])
        g0_arr.append(r['g0_dB'])
        pos_arr.append(soa.rsm_pos(float(np.clip(lam, 1304, 1318)), J, T))
        nf_arr.append(soa.rsm_nf(lam, J, T))

    plt.figure(figsize=(11, 8))
    plt.suptitle(
        f'HPSOA Performance Summary vs Temperature\n'
        f'(W={W} µm, L={L} µm, J={J} kA/cm², λ={lam} nm, Po={Po_dBm} dBm)',
        fontsize=12)

    panels = [
        (1, pae_arr, 'PAE [%]',   'Power-Added Efficiency',  '#1f77b4'),
        (2, g0_arr,  'g₀ [dB]',   'Unsaturated Gain',        '#ff7f0e'),
        (3, pos_arr, 'Pos [dBm]', 'Output Saturation Power', '#2ca02c'),
        (4, nf_arr,  'NF [dB]',   'Noise Figure',            '#d62728'),
    ]

    for idx, data, ylabel, title, color in panels:
        plt.subplot(2, 2, idx)
        plt.plot(T_arr, data, color=color, **STYLE)
        plt.fill_between(T_arr, data, alpha=0.12, color=color)
        plt.xlabel('Temperature T [°C]', fontsize=11)
        plt.ylabel(ylabel, fontsize=11)
        plt.title(title, fontsize=11)
        plt.grid(True, alpha=0.35)
        plt.xlim(35, 80)

    _save(os.path.join(out_dir, 'plot12_summary_dashboard.png'))


def plot13_pae_vs_Po_length_sweep(out_dir, W=2.0, L=240.0, T=80.0,
                                   lam=1311.0, J=7.0):
    """PAE & gain compression vs output power for multiple L values."""
    L_vals = [40, 140, 240, 340, 440]
    Po_arr = np.linspace(-10, 17, 200)

    plt.figure(figsize=(12, 5))
    plt.suptitle(f'PAE & Gain Compression vs Po  (length sweep)\n'
                 f'(T={T}°C, J={J} kA/cm², λ={lam} nm, W={W} µm)',
                 fontsize=12)

    for panel, (ylabel, title, key) in enumerate(
            [('PAE [%]',              'Power-Added Efficiency vs Po', 'pae'),
             ('Saturated Gain g [dB]','Gain Compression vs Po',       'g_dB')],
            start=1):
        plt.subplot(1, 2, panel)
        for L_val, color in zip(L_vals, COLORS):
            vals = [compute_efficiency(W, L_val, T, J, lam, Po)[key]
                    for Po in Po_arr]
            plt.plot(Po_arr, vals, color=color, label=f'L={L_val} µm', **STYLE)
        plt.axvline(15.0, color='black', linestyle='--', linewidth=1,
                    alpha=0.6, label='15 dBm target')
        plt.xlabel('Output Power Po [dBm]', fontsize=11)
        plt.ylabel(ylabel, fontsize=11)
        plt.title(title, fontsize=11)
        plt.legend(fontsize=8)
        plt.grid(True, alpha=0.35)
        plt.xlim(-10, 17)
        if key == 'pae':
            plt.ylim(bottom=0)

    _save(os.path.join(out_dir, 'plot13_pae_gain_vs_Po_length_sweep.png'))


# ============================================================================
#  MAIN
# ============================================================================

if __name__ == '__main__':

    OUT_DIR = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'results', 'ph18_soa', 'pae')
    os.makedirs(OUT_DIR, exist_ok=True)

    W_NOM  = 2.0
    L_NOM  = 240.0
    T_NOM  = 80.0
    J_NOM  = 7.0
    LAM    = 1311.0
    PO_DBM = 15.0

    r_nom = compute_efficiency(W_NOM, L_NOM, T_NOM, J_NOM, LAM, PO_DBM)

    print('=' * 62)
    print('  HPSOA Power-Added Efficiency Analysis  (APP-002012 Rev 3.1)')
    print('=' * 62)
    print(f'  Nominal: W={W_NOM} µm, L={L_NOM} µm, T={T_NOM}°C, '
          f'J={J_NOM} kA/cm², λ={LAM} nm')
    print(f'  Po target   = {PO_DBM:.1f} dBm')
    print(f'  g0          = {r_nom["g0_dB"]:.2f} dB')
    print(f'  g (sat)     = {r_nom["g_dB"]:.2f} dB')
    print(f'  Pos         = {r_nom["Pos_dBm"]:.2f} dBm')
    print(f'  Drive I     = {r_nom["I_mA"]:.1f} mA')
    print(f'  Terminal V  = {r_nom["V"]:.3f} V')
    print(f'  P_elec      = {r_nom["P_elec_mW"]:.1f} mW')
    print(f'  P_out       = {r_nom["P_out_mW"]:.2f} mW')
    print(f'  P_in        = {r_nom["P_in_mW"]:.2f} mW')
    print(f'  P_added     = {r_nom["P_added_mW"]:.2f} mW  (P_out − P_in)')
    print(f'  PAE         = {r_nom["pae"]:.2f} %   ← primary metric')
    print(f'  WPE         = {r_nom["wpe"]:.2f} %   (reference)')
    print()

    jobs = [
        ('Plot 01 — PAE & gain vs length L',
         lambda: plot01_pae_vs_length(OUT_DIR, W=W_NOM, T=T_NOM,
                                      lam=LAM, Po_dBm=PO_DBM)),
        ('Plot 02 — PAE & gain vs current density J',
         lambda: plot02_pae_vs_current_density(OUT_DIR, W=W_NOM, T=T_NOM,
                                               lam=LAM, Po_dBm=PO_DBM)),
        ('Plot 03 — PAE & gain vs temperature T',
         lambda: plot03_pae_vs_temperature(OUT_DIR, W=W_NOM, L=L_NOM,
                                           lam=LAM, Po_dBm=PO_DBM)),
        ('Plot 04 — PAE & gain vs wavelength λ',
         lambda: plot04_pae_vs_wavelength(OUT_DIR, W=W_NOM, L=L_NOM,
                                          J=J_NOM, Po_dBm=PO_DBM)),
        ('Plot 05 — PAE vs Po  [T=35,55,80 × J=3,5,7]',
         lambda: plot05_pae_vs_output_power(OUT_DIR, W=W_NOM, L=L_NOM,
                                            lam=LAM)),
        ('Plot 06 — Gain compression & PAE overlay',
         lambda: plot06_gain_compression_pae_overlay(OUT_DIR, W=W_NOM,
                 L=L_NOM, T=T_NOM, J=J_NOM, lam=LAM)),
        ('Plot 07 — 2-D contour PAE in (L, J)',
         lambda: plot07_contour_pae_L_J(OUT_DIR, W=W_NOM, T=T_NOM,
                                        lam=LAM, Po_dBm=PO_DBM)),
        ('Plot 08 — 2-D contour PAE in (T, J)',
         lambda: plot08_contour_pae_T_J(OUT_DIR, W=W_NOM, L=L_NOM,
                                        lam=LAM, Po_dBm=PO_DBM)),
        ('Plot 09 — Power budget vs J',
         lambda: plot09_power_budget(OUT_DIR, W=W_NOM, L=L_NOM, T=T_NOM,
                                     lam=LAM, Po_dBm=PO_DBM)),
        ('Plot 10 — PAE vs gain tradeoff',
         lambda: plot10_pae_vs_gain_tradeoff(OUT_DIR, W=W_NOM, T=T_NOM,
                                              lam=LAM, Po_dBm=PO_DBM)),
        ('Plot 11 — Electrical operating point vs L',
         lambda: plot11_electrical_operating_point(OUT_DIR, W=W_NOM,
                                                    T=T_NOM, lam=LAM)),
        ('Plot 12 — Summary dashboard vs temperature',
         lambda: plot12_summary_dashboard(OUT_DIR, W=W_NOM, L=L_NOM,
                                           J=J_NOM, lam=LAM, Po_dBm=PO_DBM)),
        ('Plot 13 — PAE & gain vs Po (length sweep)',
         lambda: plot13_pae_vs_Po_length_sweep(OUT_DIR, W=W_NOM, L=L_NOM,
                                                T=T_NOM, lam=LAM, J=J_NOM)),
    ]

    for label, fn in jobs:
        print(f'  Generating {label} ...')
        fn()

    print(f'\nAll PAE figures saved to: {os.path.abspath(OUT_DIR)}')
