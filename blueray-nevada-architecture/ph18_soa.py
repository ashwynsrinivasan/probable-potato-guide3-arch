"""
ph18_soa.py
===========
OpenLight O-Band 15 dBm Semiconductor Optical Amplifier Model
Based on: APP-002012, Rev 3.1 (OpenLight Photonics)

Class: ph18_soa_15dBm
  Models all equations from the app note (Eq.1–17 + Appendix).
  Provides plot methods reproducing Figures 2–9.

Equations implemented
---------------------
Eq.1   : Total gain epi length  Lt = L + 460 [µm]
Eq.2   : Current density        J  = I / (W × Lt)
Eq.3   : Gain (linear)          g  = Po / Pin
Eq.4   : Gain (dB)              g_dB = 10 log10(g)
Eq.5   : Lorentzian lineshape   f  = FWHM / ((λpk-λ)² + (FWHM/2)²)
Eq.6   : Unsaturated gain       g0 = f × 10^(0.1 g_pk) / max(f)
Eq.7   : RSM peak gain          g_pk(T, J, L)   [dB]
Eq.8   : RSM peak wavelength    λ_pk(T, J, L)   [nm]
Eq.9   : RSM FWHM               FWHM(T, J, L)   [nm]
Eq.10  : Saturated gain (implicit)  g = g0 exp(-(g-1)/g · Po/Ps)
Eq.11  : Internal sat. power    Ps = W·d·h·ν / (a·Γ·τ)
Eq.12  : Output sat. power      Pos = (g0·ln2)/(g0-2) · Ps
Eq.13  : RSM output sat. power  Pos(λ, J, T)    [dBm]
Eq.14  : Noise figure definition NF = 2·S_ASE/(h·ν·g0) + 1/g0
Eq.15  : RSM noise figure       NF(λ, J, T)     [dB]
Eq.16  : IV model               V = V_turn_on + I·Rs
Eq.17  : Series resistance RSM  Rs = 4.34/W + 2151/Lt - 0.992  [Ω]
Appendix: Newton-Raphson solver for saturated gain
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


class ph18_soa_15dBm:
    """
    OpenLight O-Band 15 dBm Semiconductor Optical Amplifier model.

    Nominal design (APP-002012 Rev 3.1):
        W  = 2 µm  (ridge width)
        L  = 240 µm (active region length)
        Lt = 700 µm (total III-V gain epi length = L + 460)

    Parameter ranges validated in the app note:
        T : [35, 80]   °C
        J : [3, 7]     kA/cm²
        L : [40, 440]  µm
        λ : [1260, 1360] nm  (gain spectrum)
        λ : [1304, 1318] nm  (Pos RSM)
        λ : [1260, 1350] nm  (NF RSM)
    """

    # Physical constants
    H_PLANCK = 6.626e-34   # J·s
    C_LIGHT  = 3.0e8       # m/s

    # Nominal design parameters
    W_NOM        = 2.0    # µm
    L_NOM        = 240.0  # µm
    V_TURN_ON    = 1.05   # V  (ideal diode turn-on, Eq.16)

    # ------------------------------------------------------------------ #
    #  Constructor                                                         #
    # ------------------------------------------------------------------ #
    def __init__(self, W: float = 2.0, L: float = 240.0):
        """
        Parameters
        ----------
        W : float
            Ridge width [µm].  Default 2.0.
        L : float
            Active region length [µm].  Range [40, 440].  Default 240.
        """
        self.W  = float(W)
        self.L  = float(L)
        self.Lt = self._lt(L)  # total gain epi length [µm]

    # ================================================================== #
    #  GEOMETRY                                                            #
    # ================================================================== #

    @staticmethod
    def _lt(L: float) -> float:
        """
        Total III-V gain epi length (Eq.1):
            Lt = L + L_input_taper + L_output_taper = L + 460  [µm]
        """
        return float(L) + 460.0

    # ================================================================== #
    #  CURRENT DENSITY                                                     #
    # ================================================================== #

    def current_density(self, I_mA: float) -> float:
        """
        Current density across the SOA cavity (Eq.2):
            J = I / (W × Lt)   [kA/cm²]

        Parameters
        ----------
        I_mA : float
            Drive current [mA].
        """
        W_cm  = self.W  * 1e-4   # µm → cm
        Lt_cm = self.Lt * 1e-4   # µm → cm
        I_A   = I_mA * 1e-3      # mA → A
        J_Acm2 = I_A / (W_cm * Lt_cm)
        return J_Acm2 * 1e-3      # A/cm² → kA/cm²

    def drive_current(self, J_kAcm2: float) -> float:
        """
        Inverse of current_density: compute I [mA] from J [kA/cm²].
        """
        W_cm  = self.W  * 1e-4
        Lt_cm = self.Lt * 1e-4
        J_Acm2 = J_kAcm2 * 1e3
        I_A = J_Acm2 * W_cm * Lt_cm
        return I_A * 1e3  # A → mA

    # ================================================================== #
    #  GAIN DEFINITIONS                                                    #
    # ================================================================== #

    @staticmethod
    def gain_linear(Po, Pin):
        """
        Optical gain (linear, unitless) (Eq.3):
            g = Po / Pin
        """
        return np.asarray(Po, dtype=float) / np.asarray(Pin, dtype=float)

    @staticmethod
    def gain_dB(g):
        """
        Gain in dB (Eq.4):
            g_dB = 10 log10(g)
        """
        return 10.0 * np.log10(np.asarray(g, dtype=float))

    @staticmethod
    def gain_linear_from_dB(g_dB):
        """Inverse of gain_dB."""
        return 10.0 ** (np.asarray(g_dB, dtype=float) / 10.0)

    # ================================================================== #
    #  UNSATURATED GAIN SPECTRUM (Lorentzian)                              #
    # ================================================================== #

    @staticmethod
    def lorentzian(lam, lam_pk: float, FWHM: float):
        """
        Lorentzian lineshape function (Eq.5):
            f = FWHM / ((λpk − λ)² + (FWHM/2)²)

        Parameters
        ----------
        lam    : array-like, wavelengths [nm]
        lam_pk : float, peak wavelength [nm]
        FWHM   : float, full-width at half-maximum [nm]

        Returns
        -------
        f : ndarray  (not normalised; max = 4/FWHM)
        """
        lam = np.asarray(lam, dtype=float)
        return FWHM / ((lam_pk - lam) ** 2 + (FWHM / 2.0) ** 2)

    @staticmethod
    def unsaturated_gain_spectrum(lam, g_pk_dB: float,
                                  lam_pk: float, FWHM: float):
        """
        Unsaturated gain spectrum, linear unitless (Eq.6):
            g0 = f × 10^(0.1 × g_pk) / max(f)
               = f × 10^(0.1 × g_pk) × FWHM / 4

        Parameters
        ----------
        lam     : array-like, wavelengths [nm]
        g_pk_dB : float, peak gain [dB]
        lam_pk  : float, peak wavelength [nm]
        FWHM    : float [nm]

        Returns
        -------
        g0 : ndarray, linear unitless
        """
        lam = np.asarray(lam, dtype=float)
        f     = FWHM / ((lam_pk - lam) ** 2 + (FWHM / 2.0) ** 2)
        f_max = 4.0 / FWHM           # analytic maximum of Lorentzian
        g0    = f * (10.0 ** (0.1 * g_pk_dB)) / f_max
        return g0

    # ================================================================== #
    #  RSM COMPACT MODELS — UNSATURATED GAIN                               #
    # ================================================================== #

    def rsm_gpk(self, T: float, J: float, L: float = None) -> float:
        """
        RSM peak gain g_pk [dB] (Eq.7).
        Valid: T [35,80] °C, J [3,7] kA/cm², L [40,440] µm.

        Parameters
        ----------
        T : float, temperature [°C]
        J : float, current density [kA/cm²]
        L : float, active length [µm]  (uses self.L if None)
        """
        if L is None:
            L = self.L
        lnJ = np.log(J)
        return (4.678
                - 0.0729      * T
                + 10.098      * lnJ
                - 0.001380    * (L + 460)
                - 0.00024     * (T - 60) * (T - 60)
                - 0.0081      * lnJ * (T - 60)
                - 2.158       * lnJ * lnJ
                - 0.0001589   * (T - 60) * (L - 240)
                + 0.02311     * lnJ * (L - 240)
                - 0.000001886 * (T - 60) * (T - 60) * (L - 240)
                - 0.00002088  * lnJ * (T - 60) * (L - 240)
                - 0.005336    * lnJ * lnJ * (L - 240))

    def rsm_lambda_pk(self, T: float, J: float, L: float = None) -> float:
        """
        RSM peak wavelength λ_pk [nm] (Eq.8).
        Valid: T [35,80] °C, J [3,7] kA/cm², L [40,440] µm.
        """
        if L is None:
            L = self.L
        lnJ = np.log(J)
        return (1273.73
                + 0.6817       * T
                - 28.73        * lnJ
                + 0.01362      * (L + 460)
                + 0.004585     * (T - 60) * (T - 60)
                - 0.1076       * lnJ * (T - 60)
                + 8.787        * lnJ * lnJ
                + 0.00004185   * (T - 60) * (L - 240)
                - 0.02367      * lnJ * (L - 240)
                - 0.0000002230 * (T - 60) * (T - 60) * (L - 240)
                + 0.000136     * lnJ * (T - 60) * (L - 240)
                + 0.004894     * lnJ * lnJ * (L - 240))

    def rsm_fwhm(self, T: float, J: float, L: float = None) -> float:
        """
        RSM gain spectrum FWHM [nm] (Eq.9).
        Valid: T [35,80] °C, J [3,7] kA/cm², L [40,440] µm.
        """
        if L is None:
            L = self.L
        lnJ = np.log(J)
        return (120.15
                - 0.08555     * T
                + 0.3837      * lnJ
                - 0.07255     * (L + 460)
                + 0.00007784  * (T - 60) * (T - 60)
                + 0.2386      * lnJ * (T - 60)
                + 2.759       * lnJ * lnJ
                - 0.0004342   * (T - 60) * (L - 240)
                + 0.003947    * lnJ * (L - 240)
                + 0.00002085  * (T - 60) * (T - 60) * (L - 240)
                + 0.000009466 * lnJ * (T - 60) * (L - 240)
                - 0.0007991   * lnJ * lnJ * (L - 240))

    def unsaturated_gain_at(self, lam, T: float, J: float,
                            L: float = None):
        """
        Full unsaturated gain pipeline: RSM params → Lorentzian spectrum.

        Returns (g0_lin, g0_dB, g_pk_dB, lam_pk, fwhm) at given λ.
        """
        if L is None:
            L = self.L
        g_pk  = self.rsm_gpk(T, J, L)
        lp    = self.rsm_lambda_pk(T, J, L)
        fw    = self.rsm_fwhm(T, J, L)
        g0_lin = self.unsaturated_gain_spectrum(lam, g_pk, lp, fw)
        g0_dB  = 10.0 * np.log10(np.maximum(g0_lin, 1e-30))
        return g0_lin, g0_dB, g_pk, lp, fw

    # ================================================================== #
    #  GAIN SATURATION                                                     #
    # ================================================================== #

    @staticmethod
    def saturation_power_ps(W_m: float, d_m: float, h_nu: float,
                            a: float, Gamma: float, tau: float) -> float:
        """
        Internal saturation power Ps [W] from material parameters (Eq.11):
            Ps = W · d · h · ν / (a · Γ · τ)

        Parameters
        ----------
        W_m   : ridge width [m]
        d_m   : active layer thickness [m]
        h_nu  : photon energy h·ν [J]
        a     : differential gain [m²]
        Gamma : optical confinement factor
        tau   : carrier lifetime [s]
        """
        return (W_m * d_m * h_nu) / (a * Gamma * tau)

    @staticmethod
    def output_sat_power_from_ps(g0_lin: float, Ps_W: float) -> float:
        """
        Output saturation power Pos [W] from g0 and Ps (Eq.12):
            Pos = (g0 · ln2) / (g0 − 2) · Ps
        """
        return (g0_lin * np.log(2) / (g0_lin - 2.0)) * Ps_W

    @staticmethod
    def rsm_pos(lam, J, T):
        """
        RSM output saturation power Pos [dBm] (Eq.13).
        Valid: λ [1304,1318] nm, J [3,7] kA/cm², T [35,80] °C.

        Parameters
        ----------
        lam : float or array, wavelength [nm]
        J   : float, current density [kA/cm²]
        T   : float, temperature [°C]
        """
        lam = np.asarray(lam, dtype=float)
        return (-74.08
                + 0.06226    * lam
                - 0.008877   * T
                + 0.994      * J
                - 0.08721    * (J - 4.571) * (J - 4.571)
                + 0.01752    * (lam - 1310.8) * (lam - 1310.8)
                - 0.00002341 * (T - 60.07) * (T - 60.07)
                - 0.001266   * (lam - 1310.8) * (T - 60.07)
                - 0.001763   * (T - 60.07) * (J - 4.571)
                - 0.008584   * (lam - 1310.8) * (J - 4.571))

    # ------------------------------------------------------------------ #
    #  Newton-Raphson saturated gain solver (Appendix)                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def newton_gain_from_pin(Pos_dBm: float, g0_lin: float,
                             Pin_dBm: float, max_iter: int = 1000) -> float:
        """
        Solve saturated gain g given input power Pin (Appendix).

        Uses the form:  g = g0 · exp((1 − g) · Pin / Ps)
        where Ps is derived from Pos via Eq.12 inverse.

        Parameters
        ----------
        Pos_dBm : float, output saturation power [dBm]
        g0_lin  : float, unsaturated gain [linear]
        Pin_dBm : float, input power [dBm]

        Returns
        -------
        g : float, saturated gain [linear]
        """
        epsilon_1 = 1e-5
        epsilon_2 = 1e-4
        Pos_W = 10.0 ** ((Pos_dBm - 30.0) / 10.0)
        Pin_W = 10.0 ** ((Pin_dBm - 30.0) / 10.0)
        Ps    = Pos_W * (g0_lin - 2.0) / g0_lin / np.log(2.0)
        x     = 2.0
        c1    = 1.0
        c2    = 1.0
        for _ in range(max_iter):
            if c1 <= epsilon_1 and c2 <= epsilon_2:
                break
            f  = x - g0_lin * np.exp(Pin_W * (1.0 - x) / Ps)
            f1 = 1.0 + g0_lin * Pin_W / Ps * np.exp(Pin_W * (1.0 - x) / Ps)
            x1 = x - f / f1
            c1 = abs(f)
            c2 = abs(x1 - x)
            x  = x1
        return x

    @staticmethod
    def newton_gain_vs_output_power(Pos_dBm: float, g0_lin: float,
                                    Po_dBm_arr, max_iter: int = 500):
        """
        Solve saturated gain g as a function of output power Po (Appendix).

        Uses the implicit form (Eq.10):
            g = g0 · exp(−(g−1)/g · Po / Ps)
        solved via Newton-Raphson for each Po value.

        Parameters
        ----------
        Pos_dBm    : float, output saturation power [dBm]
        g0_lin     : float, unsaturated gain [linear]
        Po_dBm_arr : array-like, output powers [dBm]

        Returns
        -------
        g_arr : ndarray, saturated gain [linear]
        """
        Pos_W  = 10.0 ** ((Pos_dBm - 30.0) / 10.0)
        Ps     = Pos_W * (g0_lin - 2.0) / g0_lin / np.log(2.0)
        gains  = []
        for Po_dBm in np.asarray(Po_dBm_arr, dtype=float):
            Po_W = 10.0 ** ((Po_dBm - 30.0) / 10.0)
            # f(x)  = x − g0 · exp(−(x−1)/x · Po/Ps)
            # f'(x) = 1 + g0 · (Po / (Ps·x²)) · exp(−(x−1)/x · Po/Ps)
            x = max(g0_lin / 2.0, 1.1)
            for _ in range(max_iter):
                arg = -(x - 1.0) / x * Po_W / Ps
                ex  = np.exp(np.clip(arg, -50, 50))
                f   = x - g0_lin * ex
                df  = 1.0 + g0_lin * (Po_W / (Ps * x * x)) * ex
                x1  = x - f / df
                if abs(x1 - x) < 1e-7 and abs(f) < 1e-7:
                    x = x1
                    break
                x = max(x1, 1.0 + 1e-6)
            gains.append(x)
        return np.array(gains)

    # ================================================================== #
    #  NOISE FIGURE                                                        #
    # ================================================================== #

    @staticmethod
    def noise_figure_from_ase(S_ASE: float, g0_lin: float,
                               h_nu: float) -> float:
        """
        Noise figure (linear) from ASE power spectral density (Eq.14):
            NF = 2 · S_ASE / (h·ν·g0) + 1/g0

        Parameters
        ----------
        S_ASE  : float, ASE power spectral density [W/Hz]
        g0_lin : float, unsaturated gain [linear]
        h_nu   : float, photon energy h·ν [J]
        """
        return 2.0 * S_ASE / (h_nu * g0_lin) + 1.0 / g0_lin

    @staticmethod
    def rsm_nf(lam, J: float, T: float):
        """
        RSM noise figure NF [dB] (Eq.15).
        Valid: λ [1260,1350] nm, J [3,7] kA/cm², T [35,80] °C.

        Parameters
        ----------
        lam : float or array, wavelength [nm]
        J   : float, current density [kA/cm²]
        T   : float, temperature [°C]
        """
        lam = np.asarray(lam, dtype=float)
        lnJ = np.log(J)
        dl  = lam   - 1306.38
        dT  = float(T) - 60.0
        return (131.58
                - 0.09959    * lam
                + 0.08972    * T
                - 5.0895     * lnJ
                + 2.7334     * lnJ * lnJ
                + 0.0009195  * dl * dl
                + 0.0007484  * dT * dT
                - 0.001299   * dl * dT
                - 0.07995    * dT * lnJ
                + 0.103      * dl * lnJ
                + 0.0005740  * dl * dT * lnJ
                + 0.0197     * lnJ * lnJ * dT
                - 0.02785    * lnJ * lnJ * dl
                - 0.0003141  * dT * dT * lnJ
                - 0.00001095 * dT * dT * dl
                - 0.0002678  * dl * dl * lnJ
                + 0.000003281 * dl * dl * dT
                - 0.4606     * lnJ * lnJ * lnJ
                - 0.000002634 * dl * dl * dl)

    # ================================================================== #
    #  IV CHARACTERISTICS                                                  #
    # ================================================================== #

    def series_resistance(self, W: float = None, Lt: float = None) -> float:
        """
        Series resistance Rs [Ω] from device geometry RSM (Eq.17):
            Rs = 4.34 / W[µm] + 2151 / Lt[µm] − 0.992

        Parameters
        ----------
        W  : float, ridge width [µm]    (uses self.W  if None)
        Lt : float, total epi length [µm] (uses self.Lt if None)
        """
        if W  is None: W  = self.W
        if Lt is None: Lt = self.Lt
        return 4.34 / W + 2151.0 / Lt - 0.992

    def voltage(self, I_mA):
        """
        Terminal voltage (Eq.16):
            V = V_turn_on + I · Rs   [V]

        Parameters
        ----------
        I_mA : array-like, drive current [mA]  (forward bias, > 0)
        """
        I_mA = np.asarray(I_mA, dtype=float)
        Rs   = self.series_resistance()
        return self.V_TURN_ON + I_mA * 1e-3 * Rs

    def iv_curve(self, V_arr=None):
        """
        Return (V, I_mA) for the I-V characteristic.
        Uses piecewise linear model: I=0 for V ≤ V_turn_on, then Eq.16 inverted.
        """
        if V_arr is None:
            V_arr = np.linspace(0.0, 1.6, 500)
        V_arr = np.asarray(V_arr, dtype=float)
        Rs    = self.series_resistance()
        I_mA  = np.where(V_arr > self.V_TURN_ON,
                         (V_arr - self.V_TURN_ON) / Rs * 1e3,
                         0.0)
        return V_arr, I_mA

    # ================================================================== #
    #  PLOTTING METHODS                                                    #
    # ================================================================== #

    def plot_figure2_unsaturated_gain_spectrum(self, L: float = None,
                                               J: float = 5.0,
                                               save_path: str = None):
        """
        Figure 2 — Unsaturated gain spectrum g0 [dB] vs wavelength [nm].

        Curves for T = 35, 55, 70, 80 °C.  Annotates g_pk, λ_pk, FWHM
        on the 70 °C curve, reproducing Fig.2 of APP-002012.
        """
        if L is None:
            L = self.L
        lam    = np.linspace(1260, 1360, 500)
        temps  = [35, 55, 70, 80]
        colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728']
        labels = ['35', '55', '70', '80']

        fig, ax = plt.subplots(figsize=(7, 5))
        for T, color, label in zip(temps, colors, labels):
            g_pk   = self.rsm_gpk(T, J, L)
            lp     = self.rsm_lambda_pk(T, J, L)
            fw     = self.rsm_fwhm(T, J, L)
            g0_lin = self.unsaturated_gain_spectrum(lam, g_pk, lp, fw)
            g0_dB  = 10.0 * np.log10(np.maximum(g0_lin, 1e-30))
            ax.plot(lam, g0_dB, color=color, linewidth=2, label=label)

        # --- annotations on the 70°C curve ---
        T_ann = 70
        gpk_a = self.rsm_gpk(T_ann, J, L)
        lp_a  = self.rsm_lambda_pk(T_ann, J, L)
        fw_a  = self.rsm_fwhm(T_ann, J, L)
        hm    = gpk_a - 10.0 * np.log10(2.0)

        ax.annotate(r'$g_{pk}$', xy=(lp_a, gpk_a),
                    xytext=(lp_a + 8, gpk_a + 0.8),
                    arrowprops=dict(arrowstyle='->', color='black'),
                    fontsize=11)
        ax.annotate(r'$\lambda_{pk}$', xy=(lp_a, gpk_a - 2.5),
                    xytext=(lp_a - 20, gpk_a - 4.5),
                    arrowprops=dict(arrowstyle='->', color='black'),
                    fontsize=11)
        lo = lp_a - fw_a / 2
        hi = lp_a + fw_a / 2
        ax.annotate('', xy=(hi, hm), xytext=(lo, hm),
                    arrowprops=dict(arrowstyle='<->', color='black', lw=1.4))
        ax.text((lo + hi) / 2, hm + 0.4, 'FWHM', ha='center', fontsize=10)

        ax.set_xlabel('Wavelength [nm]', fontsize=12)
        ax.set_ylabel('g₀ [dB]', fontsize=12)
        ax.set_title(
            f'Figure 2.  Unsaturated gain spectrum of SOA\n'
            f'(L = {L} µm,  J = {J} kA/cm²)', fontsize=11)
        ax.legend(title='Temperature [°C]', fontsize=10)
        ax.set_xlim(1260, 1360)
        ax.grid(True, alpha=0.35)
        fig.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig, ax

    def plot_figure3_unsaturated_gain_model(self, L: float = None,
                                            save_path: str = None):
        """
        Figure 3 — Unsaturated gain model (RSM + Lorentzian) vs wavelength.

        Grid: rows = Temperature [35, 55, 70, 80] °C,
              cols = J [3, 4, 5, 6, 7] kA/cm².
        Red curve = RSM+Lorentz model.
        """
        if L is None:
            L = self.L
        temps  = [35, 55, 70, 80]
        J_vals = [3, 4, 5, 6, 7]
        lam    = np.linspace(1260, 1350, 300)

        fig, axes = plt.subplots(len(temps), len(J_vals),
                                 figsize=(14, 9),
                                 sharex=True, sharey=False)
        fig.suptitle(
            f'Figure 3.  Unsaturated gain model (RSM + Lorentz) vs. wavelength'
            f'\n(L = {L} µm)',
            fontsize=12)

        for row, T in enumerate(temps):
            for col, J in enumerate(J_vals):
                ax     = axes[row][col]
                g_pk   = self.rsm_gpk(T, J, L)
                lp     = self.rsm_lambda_pk(T, J, L)
                fw     = self.rsm_fwhm(T, J, L)
                g0_lin = self.unsaturated_gain_spectrum(lam, g_pk, lp, fw)
                g0_dB  = 10.0 * np.log10(np.maximum(g0_lin, 1e-30))
                ax.plot(lam, g0_dB, 'r-', linewidth=1.5, label='RSM+Lorentz')
                ax.set_ylim(-4, 13)
                ax.grid(True, alpha=0.3)
                ax.tick_params(labelsize=7)
                if row == 0:
                    ax.set_title(f'J = {J} kA/cm²', fontsize=8)
                if col == 0:
                    ax.set_ylabel(f'T = {T}°C\ng₀ [dB]', fontsize=8)
                if row == len(temps) - 1:
                    ax.set_xlabel('λ [nm]', fontsize=8)
                    ax.set_xticks([1270, 1300, 1330])
                    ax.tick_params(axis='x', labelsize=7, rotation=45)

        handles, lbls = axes[0][0].get_legend_handles_labels()
        fig.legend(handles, lbls, loc='upper right', fontsize=9,
                   bbox_to_anchor=(0.99, 0.99))
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig, axes

    def plot_figure4_gain_vs_output_power(self, T: float = 80.0,
                                          J: float = 7.0,
                                          lam: float = 1311.0,
                                          L: float = None,
                                          save_path: str = None):
        """
        Figure 4 — SOA gain vs output power showing g0 and Pos (3-dB point).

        Default T=80°C, J=7 kA/cm², λ=1311 nm, L=240 µm gives
        g0 ≈ 9 dB and Pos ≈ 13 dBm matching the annotated values in App Note Fig.4.
        """
        if L is None:
            L = self.L
        g_pk   = self.rsm_gpk(T, J, L)
        lp     = self.rsm_lambda_pk(T, J, L)
        fw     = self.rsm_fwhm(T, J, L)
        g0_lin = self.unsaturated_gain_spectrum([lam], g_pk, lp, fw)[0]
        g0_dB  = 10.0 * np.log10(g0_lin)
        Pos_dBm = self.rsm_pos(lam, J, T)

        Po_arr  = np.linspace(-12, 20, 300)
        g_arr   = self.newton_gain_vs_output_power(Pos_dBm, g0_lin, Po_arr)
        g_dB_arr = 10.0 * np.log10(np.maximum(g_arr, 1e-30))

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(Po_arr, g_dB_arr, 'b-', linewidth=2)

        # Reference lines
        ax.axhline(g0_dB,       color='gray', linestyle='--', alpha=0.6, linewidth=1)
        ax.axhline(g0_dB - 3.0, color='gray', linestyle=':',  alpha=0.6, linewidth=1)
        ax.axvline(Pos_dBm,     color='red',  linestyle='--', alpha=0.6, linewidth=1)

        ax.text(-11, g0_dB + 0.2, f'$g_0$ = {g0_dB:.1f} dB', fontsize=10)
        ax.text(Pos_dBm - 10, g0_dB - 2.7, '3 dB', fontsize=9, color='gray')
        ax.annotate(f'$P_{{os}}$ = {Pos_dBm:.1f} dBm',
                    xy=(Pos_dBm, g0_dB - 3.0),
                    xytext=(Pos_dBm - 9, g0_dB - 5.5),
                    arrowprops=dict(arrowstyle='->', color='red'),
                    fontsize=10, color='red')

        ax.set_xlabel('Po [dBm]', fontsize=12)
        ax.set_ylabel('g [dB]',   fontsize=12)
        ax.set_title(
            f'Figure 4.  SOA gain as a function of output power\n'
            f'(T = {T}°C,  J = {J} kA/cm²,  λ = {lam} nm,  L = {L} µm)',
            fontsize=11)
        ax.set_xlim(-12, 20)
        ax.grid(True, alpha=0.35)
        fig.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig, ax

    def plot_figure5_gain_vs_output_power_comparison(
            self, L: float = None, save_path: str = None):
        """
        Figure 5 — Calculated gain vs output power for two operating conditions.

        Left panel:  T=80°C, J=7 kA/cm² → g0 ≈ 9 dB,  Pos ≈ 13 dBm
        Right panel: T=35°C, J=7 kA/cm² → g0 ≈ 12 dB, Pos ≈ 14 dBm
        Matches the two validation cases shown in App Note Fig.5.
        """
        if L is None:
            L = self.L
        conditions = [
            dict(T=80, J=7.0, lam=1311, label='T = 80°C, J = 7 kA/cm²'),
            dict(T=35, J=7.0, lam=1311, label='T = 35°C, J = 7 kA/cm²'),
        ]
        fig, axes = plt.subplots(1, 2, figsize=(11, 5))
        fig.suptitle(
            f'Figure 5.  Calculated gain as a function of output power  (L = {L} µm)',
            fontsize=11)

        for ax, cond in zip(axes, conditions):
            T, J, lam = cond['T'], cond['J'], cond['lam']
            g_pk   = self.rsm_gpk(T, J, L)
            lp     = self.rsm_lambda_pk(T, J, L)
            fw     = self.rsm_fwhm(T, J, L)
            g0_lin = self.unsaturated_gain_spectrum([lam], g_pk, lp, fw)[0]
            Pos    = self.rsm_pos(lam, J, T)

            Po_arr  = np.linspace(-12, 20, 300)
            g_arr   = self.newton_gain_vs_output_power(Pos, g0_lin, Po_arr)
            g_dB    = 10.0 * np.log10(np.maximum(g_arr, 1e-30))
            g0_dB   = 10.0 * np.log10(g0_lin)

            ax.plot(Po_arr, g_dB, 'r-', linewidth=2, label='calculated')
            ax.axhline(g0_dB, color='gray', linestyle='--', alpha=0.5,
                       linewidth=1, label=f'g₀ = {g0_dB:.1f} dB')
            ax.axvline(Pos, color='b', linestyle=':', alpha=0.5,
                       linewidth=1, label=f'Pos = {Pos:.1f} dBm')
            ax.set_xlabel('Po [dBm]', fontsize=11)
            ax.set_ylabel('g [dB]',   fontsize=11)
            ax.set_title(cond['label'], fontsize=10)
            ax.set_xlim(-12, 20)
            ax.grid(True, alpha=0.35)
            ax.legend(fontsize=9)

        fig.tight_layout(rect=[0, 0, 1, 0.93])
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig, axes

    def plot_figure6_output_saturation_power(self, save_path: str = None):
        """
        Figure 6 — Output saturation power Pos [dBm] vs J [kA/cm²].

        Grid: rows = λ [1304, 1311, 1318] nm,
              cols = T [35, 55, 70, 80] °C.
        Reproduces Fig.6 of APP-002012.
        """
        lam_vals = [1304, 1311, 1318]
        temps    = [35, 55, 70, 80]
        J_arr    = np.linspace(3, 7, 200)

        fig, axes = plt.subplots(len(lam_vals), len(temps),
                                 figsize=(13, 8),
                                 sharex=True, sharey=False)
        fig.suptitle(
            'Figure 6.  Output saturation power model  Pos [dBm] vs J',
            fontsize=12)

        for row, lam in enumerate(lam_vals):
            for col, T in enumerate(temps):
                ax  = axes[row][col]
                Pos = self.rsm_pos(lam, J_arr, T)
                ax.plot(J_arr, Pos, 'b-', linewidth=2, label='RSM')
                ax.set_ylim(9, 16)
                ax.grid(True, alpha=0.3)
                ax.tick_params(labelsize=7)
                if row == 0:
                    ax.set_title(f'T = {T}°C', fontsize=9)
                if col == 0:
                    ax.set_ylabel(f'λ = {lam} nm\nPos [dBm]', fontsize=8)
                if row == len(lam_vals) - 1:
                    ax.set_xlabel('J [kA/cm²]', fontsize=8)

        handles, lbls = axes[0][0].get_legend_handles_labels()
        fig.legend(handles, lbls, loc='upper right', fontsize=9)
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig, axes

    def plot_figure7_noise_figure(self, save_path: str = None):
        """
        Figure 7 — Noise figure NF [dB] vs wavelength [nm].

        Grid: rows = Temperature [35, 55, 70, 80] °C,
              cols = J [3, 4, 5, 6, 7] kA/cm².
        Reproduces Fig.7 of APP-002012.
        """
        temps  = [35, 55, 70, 80]
        J_vals = [3, 4, 5, 6, 7]
        lam    = np.linspace(1260, 1350, 300)

        fig, axes = plt.subplots(len(temps), len(J_vals),
                                 figsize=(14, 9),
                                 sharex=True, sharey=False)
        fig.suptitle(
            'Figure 7.  Noise figure model (RSM) NF [dB] vs wavelength',
            fontsize=12)

        for row, T in enumerate(temps):
            for col, J in enumerate(J_vals):
                ax = axes[row][col]
                nf = self.rsm_nf(lam, J, T)
                ax.plot(lam, nf, 'r-', linewidth=1.5, label='RSM')
                ax.set_ylim(2, 9)
                ax.grid(True, alpha=0.3)
                ax.tick_params(labelsize=7)
                if row == 0:
                    ax.set_title(f'J = {J} kA/cm²', fontsize=8)
                if col == 0:
                    ax.set_ylabel(f'T = {T}°C\nNF [dB]', fontsize=8)
                if row == len(temps) - 1:
                    ax.set_xlabel('λ [nm]', fontsize=8)
                    ax.set_xticks([1270, 1300, 1330])
                    ax.tick_params(axis='x', labelsize=7, rotation=45)

        handles, lbls = axes[0][0].get_legend_handles_labels()
        fig.legend(handles, lbls, loc='upper right', fontsize=9)
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig, axes

    def plot_figure8_iv_characteristics(self, save_path: str = None):
        """
        Figure 8 — I-V characteristics of nominal SOA design
        (W = 2 µm, Lt = 700 µm, i.e. L = 240 µm).

        Reproduces Fig.8 of APP-002012.
        """
        soa_nom = ph18_soa_15dBm(W=2.0, L=240.0)
        V_arr, I_mA = soa_nom.iv_curve(np.linspace(0.0, 1.6, 500))

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(V_arr, I_mA, 'b-', linewidth=2)
        ax.axvline(soa_nom.V_TURN_ON, color='gray', linestyle='--',
                   alpha=0.6, linewidth=1)
        ax.text(soa_nom.V_TURN_ON + 0.03, 85,
                r'$V_\mathrm{turn-on}$', fontsize=10)

        ax.set_xlabel('Voltage [V]',  fontsize=12)
        ax.set_ylabel('Current [mA]', fontsize=12)
        ax.set_title(
            'Figure 8.  I-V characteristics of a nominal SOA design\n'
            '(W = 2 µm,  Lt = 700 µm,  L = 240 µm)',
            fontsize=11)
        ax.set_xlim(0.0, 1.6)
        ax.set_ylim(0, 120)
        ax.grid(True, alpha=0.35)
        fig.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig, ax

    def plot_figure9_series_resistance_vs_length(self,
                                                  save_path: str = None):
        """
        Figure 9 — Series resistance Rs [Ω] vs SOA gain epi length Lt [µm]
        for W = 2 µm.

        Reproduces Fig.9 of APP-002012.
        """
        W       = 2.0
        Lt_arr  = np.linspace(500, 900, 300)
        Rs_arr  = 4.34 / W + 2151.0 / Lt_arr - 0.992

        # Reference points matching app note (L=40,140,240,340,440 µm)
        L_pts   = np.array([40, 140, 240, 340, 440])
        Lt_pts  = L_pts + 460.0
        Rs_pts  = 4.34 / W + 2151.0 / Lt_pts - 0.992

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(Lt_arr, Rs_arr, 'b-', linewidth=2, label='RSM model')
        ax.plot(Lt_pts, Rs_pts, 'ko', markersize=7, label='design points')

        # Nominal device marker
        Rs_nom = self.series_resistance(W=2.0, Lt=700.0)
        ax.plot(700, Rs_nom, 'r^', markersize=9,
                label=f'Nominal  Rs = {Rs_nom:.2f} Ω\n(Lt = 700 µm)')

        ax.set_xlabel('Lt [µm]', fontsize=12)
        ax.set_ylabel('Rs [Ω]',  fontsize=12)
        ax.set_title(
            'Figure 9.  Series resistance vs SOA gain epi length\n'
            '(W = 2 µm)',
            fontsize=11)
        ax.set_xlim(500, 900)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.35)
        fig.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig, ax

    # ================================================================== #
    #  CONVENIENCE: generate all figures                                   #
    # ================================================================== #

    def run_all_plots(self, results_dir: str):
        """
        Generate and save Figures 2–9 to *results_dir*.

        Parameters
        ----------
        results_dir : str
            Output directory; created if it does not exist.
        """
        os.makedirs(results_dir, exist_ok=True)
        jobs = [
            ('fig2_unsaturated_gain_spectrum.png',
             lambda p: self.plot_figure2_unsaturated_gain_spectrum(save_path=p)),
            ('fig3_unsaturated_gain_model.png',
             lambda p: self.plot_figure3_unsaturated_gain_model(save_path=p)),
            ('fig4_gain_vs_output_power.png',
             lambda p: self.plot_figure4_gain_vs_output_power(save_path=p)),
            ('fig5_gain_comparison.png',
             lambda p: self.plot_figure5_gain_vs_output_power_comparison(save_path=p)),
            ('fig6_output_saturation_power.png',
             lambda p: self.plot_figure6_output_saturation_power(save_path=p)),
            ('fig7_noise_figure.png',
             lambda p: self.plot_figure7_noise_figure(save_path=p)),
            ('fig8_iv_characteristics.png',
             lambda p: self.plot_figure8_iv_characteristics(save_path=p)),
            ('fig9_series_resistance.png',
             lambda p: self.plot_figure9_series_resistance_vs_length(save_path=p)),
        ]
        for fname, fn in jobs:
            fpath = os.path.join(results_dir, fname)
            print(f'  Generating {fname} ...')
            fn(fpath)
            plt.close('all')
        print(f'\nAll figures saved to: {os.path.abspath(results_dir)}')


# ======================================================================
#  MAIN SCRIPT
#  Run:  python ph18_soa.py
#  Saves figures to: blueray-nevada-architecture/results/ph18_soa/
# ======================================================================
if __name__ == '__main__':

    RESULTS_DIR = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'results', 'ph18_soa')

    # ------------------------------------------------------------------
    # Instantiate nominal SOA  (W=2 µm, L=240 µm → Lt=700 µm)
    # ------------------------------------------------------------------
    soa = ph18_soa_15dBm(W=2.0, L=240.0)

    print('=' * 64)
    print('  ph18_soa_15dBm  —  OpenLight O-Band 15 dBm SOA Model')
    print('  Reference: APP-002012, Rev 3.1')
    print('=' * 64)
    print(f'\nNominal design: W = {soa.W} µm,  L = {soa.L} µm,  '
          f'Lt = {soa.Lt} µm')

    # ------------------------------------------------------------------
    # Spot-check nominal operating point  (T=80°C, J=7 kA/cm², λ=1311 nm)
    # ------------------------------------------------------------------
    T_op, J_op, lam_op = 80.0, 7.0, 1311.0
    g_pk   = soa.rsm_gpk(T_op, J_op)
    lp     = soa.rsm_lambda_pk(T_op, J_op)
    fw     = soa.rsm_fwhm(T_op, J_op)
    g0_lin = soa.unsaturated_gain_spectrum([lam_op], g_pk, lp, fw)[0]
    g0_dB  = 10.0 * np.log10(g0_lin)
    nf     = soa.rsm_nf(lam_op, J_op, T_op)
    pos    = soa.rsm_pos(lam_op, J_op, T_op)
    Rs     = soa.series_resistance()
    I_mA   = soa.drive_current(J_op)

    print(f'\nOperating point: T={T_op}°C, J={J_op} kA/cm², λ={lam_op} nm')
    print(f'  RSM peak gain        g_pk  = {g_pk:.2f} dB')
    print(f'  RSM peak wavelength  λ_pk  = {lp:.1f} nm')
    print(f'  RSM FWHM                   = {fw:.1f} nm')
    print(f'  Unsaturated gain at λ_op   = {g0_dB:.2f} dB  ({g0_lin:.2f} linear)')
    print(f'  Noise figure               = {nf:.2f} dB')
    print(f'  Output saturation power    = {pos:.2f} dBm')
    print(f'  Series resistance          = {Rs:.2f} Ω')
    print(f'  Drive current (@ J_op)     = {I_mA:.1f} mA')

    # ------------------------------------------------------------------
    # Table 1 replica: unsaturated gain at T=80°C, L=440 µm
    # ------------------------------------------------------------------
    print('\n--- Table 1: Unsaturated gain [dB] at T=80°C, L=440 µm, W=2 µm ---')
    print(f"  {'':>10}  {'J=3':>8}  {'J=5':>8}  {'J=7':>8}")
    soa440 = ph18_soa_15dBm(W=2.0, L=440.0)
    for lam_t in [1304, 1311, 1318]:
        row = []
        for J_t in [3.0, 5.0, 7.0]:
            gp  = soa440.rsm_gpk(80.0, J_t)
            lpt = soa440.rsm_lambda_pk(80.0, J_t)
            fwt = soa440.rsm_fwhm(80.0, J_t)
            g0l = soa440.unsaturated_gain_spectrum([lam_t], gp, lpt, fwt)[0]
            row.append(10.0 * np.log10(max(g0l, 1e-30)))
        print(f'  λ={lam_t} nm:  {row[0]:>6.1f}    {row[1]:>6.1f}    {row[2]:>6.1f}')

    # ------------------------------------------------------------------
    # Table 2 replica: Pos at L=240 µm, J=7 kA/cm²
    # ------------------------------------------------------------------
    print('\n--- Table 2: Pos [dBm] at L=240 µm, J=7 kA/cm², W=2 µm ---')
    print(f"  {'':>10}  {'T=35':>8}  {'T=55':>8}  {'T=80':>8}")
    for lam_t in [1304, 1311, 1318]:
        row = [soa.rsm_pos(lam_t, 7.0, Tv) for Tv in [35, 55, 80]]
        print(f'  λ={lam_t} nm:  {row[0]:>6.1f}    {row[1]:>6.1f}    {row[2]:>6.1f}')

    # ------------------------------------------------------------------
    # Table 3 replica: NF at L=240 µm, J=7 kA/cm²
    # ------------------------------------------------------------------
    print('\n--- Table 3: NF [dB] at L=240 µm, J=7 kA/cm², W=2 µm ---')
    print(f"  {'':>10}  {'T=35':>8}  {'T=55':>8}  {'T=80':>8}")
    for lam_t in [1304, 1311, 1318]:
        row = [soa.rsm_nf(lam_t, 7.0, Tv) for Tv in [35, 55, 80]]
        print(f'  λ={lam_t} nm:  {row[0]:>6.1f}    {row[1]:>6.1f}    {row[2]:>6.1f}')

    # ------------------------------------------------------------------
    # Generate all figures
    # ------------------------------------------------------------------
    print(f'\nGenerating all figures → {RESULTS_DIR}')
    soa.run_all_plots(RESULTS_DIR)
