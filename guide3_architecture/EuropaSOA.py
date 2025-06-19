import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import math
from scipy.optimize import brentq
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import yaml

# --- EuropaSOA CLASS DEFINITION ---
class EuropaSOA:
    """
    Represents a Semiconductor Optical Amplifier (SOA) based on the OpenLight PIC Application Note.
    Includes optical models (Gain, Psat, NF), an analytical I-V model, and WPE calculation.
    Unsaturated gain (g0) is linearly extrapolated for L_active_um > 440um up to 900um.
    Series resistance (Rs) uses its analytical formula; warnings are issued if Lt is outside Rs model validation.
    Accepts 3-sigma delta values to modify nominal behavior.
    """
    def __init__(self, L_active_um: float, W_um: float = 2.0, verbose=False,
                 v_turn_on_delta=0.0, rs_ohm_delta=0.0, g_pk_db_delta=0.0):
        self.L_active_um_orig = L_active_um
        self.L_active_um = L_active_um
        self.W_um = W_um
        self.L_tapers_total_um = 460.0
        self.V_turn_on = 1.05 + v_turn_on_delta
        self.rs_ohm_delta = rs_ohm_delta
        self.g_pk_db_delta = g_pk_db_delta
        self.verbose = verbose

        if self.verbose:
            if not (40 <= self.L_active_um_orig <= 440):
                if 440 < self.L_active_um_orig <= 900:
                    print(f"Info: L_active_um ({self.L_active_um_orig} um) is > 440um. g0 will be linearly extrapolated.")
                elif self.L_active_um_orig > 900:
                    print(f"Warning: L_active_um ({self.L_active_um_orig} um) is > 900um. g0 extrapolated using L_eff=900um.")
                else:
                    print(f"Warning: L_active_um ({self.L_active_um_orig} um) is < 40um, outside validation range.")

            calculated_Lt_um_for_Rs_warning = self.L_active_um_orig + self.L_tapers_total_um
            if not (2.0 <= W_um <= 2.7):
                print(f"Warning (Rs Model): W_um ({W_um} um) is outside validation range [2, 2.7] um.")
            if not (500 <= calculated_Lt_um_for_Rs_warning <= 1100):
                print(f"Warning (Rs Model): Lt_um ({calculated_Lt_um_for_Rs_warning:.1f} um) is outside validation range [500, 1100] um.")

    def _calculate_Lt_um(self) -> float:
        return self.L_active_um + self.L_tapers_total_um

    def calculate_series_resistance_ohm(self) -> float:
        Lt_um_for_Rs = self.L_active_um_orig + self.L_tapers_total_um
        if self.W_um <= 1e-9 or Lt_um_for_Rs <= 1e-9: return float('inf')
        Rs_ohm_base = (4.34 / self.W_um) + (2151 / Lt_um_for_Rs) - 0.992
        Rs_ohm = Rs_ohm_base + self.rs_ohm_delta
        return Rs_ohm if Rs_ohm > 0 else 1e-3

    def get_operating_voltage(self, I_mA: float) -> float:
        Rs_ohm = self.calculate_series_resistance_ohm()
        I_Amps = I_mA * 1e-3
        return self.V_turn_on + (I_Amps * Rs_ohm)

    def calculate_current_density_kA_cm2(self, I_mA: float) -> float:
        Lt_um = self._calculate_Lt_um()
        if self.W_um <= 1e-9 or Lt_um <= 1e-9: return 0.0
        return (I_mA * 100.0) / (self.W_um * Lt_um)

    def calculate_current_mA_from_J(self, J_kA_cm2: float) -> float:
        Lt_um = self.L_active_um_orig + self.L_tapers_total_um
        if self.W_um <= 1e-9 or Lt_um <= 1e-9: return 0.0
        return J_kA_cm2 * self.W_um * Lt_um / 100.0

    def _get_g_pk_dB(self, T_C: float, J_kA_cm2: float) -> float:
        L_for_RSM = self.L_active_um
        if J_kA_cm2 <= 1e-9: return -float('inf')
        Ln_J = math.log(J_kA_cm2)
        L_plus_460_for_RSM = self.L_active_um + self.L_tapers_total_um
        g_pk_base = (4.678 - 0.0729 * T_C + 10.098 * Ln_J - 0.001380 * L_plus_460_for_RSM -
                     0.00024 * (T_C - 60)**2 - 0.0081 * Ln_J * (T_C - 60) - 2.158 * Ln_J**2 -
                     0.0001589 * (T_C - 60) * (L_for_RSM - 240) + 0.02311 * Ln_J * (L_for_RSM - 240) -
                     0.000001886 * (T_C - 60)**2 * (L_for_RSM - 240) -
                     0.00002088 * Ln_J * (T_C - 60) * (L_for_RSM - 240) -
                     0.005336 * Ln_J**2 * (L_for_RSM - 240))
        return g_pk_base + self.g_pk_db_delta

    def _get_lambda_pk_nm(self, T_C: float, J_kA_cm2: float) -> float:
        L_for_RSM = self.L_active_um
        if J_kA_cm2 <= 1e-9: return float('nan')
        Ln_J = math.log(J_kA_cm2)
        L_plus_460_for_RSM = self.L_active_um + self.L_tapers_total_um
        lambda_pk = (1273.73 + 0.6817 * T_C - 28.73 * Ln_J + 0.01362 * L_plus_460_for_RSM +
                     0.004585 * (T_C - 60)**2 - 0.1076 * Ln_J * (T_C - 60) + 8.787 * Ln_J**2 +
                     0.00004185 * (T_C - 60) * (L_for_RSM - 240) - 0.02367 * Ln_J * (L_for_RSM - 240) -
                     0.0000002230 * (T_C - 60)**2 * (L_for_RSM - 240) +
                     0.000136 * Ln_J * (T_C - 60) * (L_for_RSM - 240) +
                     0.004894 * Ln_J**2 * (L_for_RSM - 240))
        return lambda_pk

    def _get_fwhm_nm(self, T_C: float, J_kA_cm2: float) -> float:
        L_for_RSM = self.L_active_um
        if J_kA_cm2 <= 1e-9: return 1e-9
        Ln_J = math.log(J_kA_cm2)
        L_plus_460_for_RSM = self.L_active_um + self.L_tapers_total_um
        fwhm = (120.15 - 0.0855 * T_C + 0.3837 * Ln_J - 0.07255 * L_plus_460_for_RSM +
                0.00007784 * (T_C - 60)**2 + 0.2386 * Ln_J * (T_C - 60) + 2.759 * Ln_J**2 -
                0.0004342 * (T_C - 60) * (L_for_RSM - 240) + 0.003947 * Ln_J * (L_for_RSM - 240) +
                0.00002085 * (T_C - 60)**2 * (L_for_RSM - 240) +
                0.00009466 * Ln_J * (T_C - 60) * (L_for_RSM - 240) -
                0.0007991 * Ln_J**2 * (L_for_RSM - 240))
        return fwhm if fwhm > 1e-9 else 1e-9

    def _calculate_g0_linear_at_L(self, L_val_um: float, lambda_nm: float, T_C: float, J_kA_cm2: float) -> float:
        original_L_temp_store = self.L_active_um
        self.L_active_um = L_val_um
        g_pk_dB = self._get_g_pk_dB(T_C, J_kA_cm2)
        lambda_pk_nm = self._get_lambda_pk_nm(T_C, J_kA_cm2)
        fwhm_nm = self._get_fwhm_nm(T_C, J_kA_cm2)
        self.L_active_um = original_L_temp_store
        if math.isnan(lambda_pk_nm) or g_pk_dB == -float('inf') or fwhm_nm <= 1e-9: return 0.0
        f_val_denominator = (lambda_pk_nm - lambda_nm)**2 + (fwhm_nm / 2.0)**2
        if f_val_denominator < 1e-12:
            return 10**(g_pk_dB / 10.0) if abs(lambda_nm - lambda_pk_nm) < 1e-9 else 0.0
        f_val = fwhm_nm / f_val_denominator
        max_f_val = 4.0 / fwhm_nm
        return 0.0 if abs(max_f_val) < 1e-12 else (f_val * (10**(0.1 * g_pk_dB))) / max_f_val

    def get_unsaturated_gain(self, lambda_nm: float, T_C: float, J_kA_cm2: float, output_in_dB: bool = True) -> float:
        if J_kA_cm2 <= 1e-9: return -float('inf') if output_in_dB else 0.0
        if 40 <= self.L_active_um_orig <= 440:
            g0_linear = self._calculate_g0_linear_at_L(self.L_active_um_orig, lambda_nm, T_C, J_kA_cm2)
        elif self.L_active_um_orig > 440:
            L_extrap_input = min(self.L_active_um_orig, 900.0)
            L_ref1, L_ref2 = 440.0, 430.0
            g0_at_L_ref1_linear = self._calculate_g0_linear_at_L(L_ref1, lambda_nm, T_C, J_kA_cm2)
            g0_at_L_ref2_linear = self._calculate_g0_linear_at_L(L_ref2, lambda_nm, T_C, J_kA_cm2)
            slope = (g0_at_L_ref1_linear - g0_at_L_ref2_linear) / (L_ref1 - L_ref2)
            g0_linear = g0_at_L_ref1_linear + slope * (L_extrap_input - L_ref1)
        else:
            g0_linear = self._calculate_g0_linear_at_L(self.L_active_um_orig, lambda_nm, T_C, J_kA_cm2)
        if g0_linear < 0: g0_linear = 0
        return 10 * math.log10(g0_linear) if output_in_dB and g0_linear > 1e-9 else g0_linear

    def get_output_saturation_power_dBm(self, lambda_nm: float, J_kA_cm2: float, T_C: float) -> float:
        return (-74.08 + 0.06226 * lambda_nm - 0.008877 * T_C + 0.994 * J_kA_cm2 -
                0.08721 * (J_kA_cm2 - 4.571)**2 + 0.01752 * (lambda_nm - 1310.8)**2 -
                0.00002341 * (T_C - 60.07)**2 - 0.001266 * (lambda_nm - 1310.8) * (T_C - 60.07) -
                0.001763 * (T_C - 60.07) * (J_kA_cm2 - 4.571) -
                0.008584 * (lambda_nm - 1310.8) * (J_kA_cm2 - 4.571))

    def _newton_iteration_for_gain(self, P_os_mW: float, g0_linear: float, P_in_mW: float) -> float:
        if g0_linear <= 2.000001: return g0_linear
        denominator_Ps_calc = g0_linear * math.log(2.0)
        if abs(denominator_Ps_calc) < 1e-12: return g0_linear
        P_s_mW = P_os_mW * (g0_linear - 2.0) / denominator_Ps_calc
        if P_s_mW <= 1e-12: return 0.0 if P_in_mW > 1e-9 else g0_linear
        x = g0_linear * 0.95 if P_in_mW > 1e-9 else g0_linear
        x = max(x, 1e-9)
        for _ in range(100):
            exp_arg = (1.0 - x) * P_in_mW / P_s_mW
            try: exp_val = math.exp(exp_arg) if -700 < exp_arg < 700 else (float('inf') if exp_arg >= 700 else 0.0)
            except OverflowError: exp_val = float('inf')
            f_x = x - g0_linear * exp_val
            f_prime_x = 1.0 + g0_linear * (P_in_mW / P_s_mW) * exp_val
            if abs(f_prime_x) < 1e-9: break
            x_next = x - f_x / f_prime_x
            if not (-0.1 * g0_linear < x_next < 1.5 * g0_linear + 1): break
            if x_next < 0: x_next = 1e-9
            c1, c2, x = abs(f_x), abs(x_next - x), x_next
            if c1 < 1e-5 and c2 < 1e-4: return max(0.0, x)
        return max(0.0, x)

    def get_saturated_gain(self, lambda_nm: float, T_C: float, J_kA_cm2: float, P_in_mW: float, output_in_dB: bool = True) -> float:
        if P_in_mW < 1e-9: P_in_mW = 0.0
        g0_linear = self.get_unsaturated_gain(lambda_nm, T_C, J_kA_cm2, output_in_dB=False)
        if g0_linear <= 1e-9 or P_in_mW == 0.0: g_saturated_linear = g0_linear
        else:
            P_os_dBm = self.get_output_saturation_power_dBm(lambda_nm, J_kA_cm2, T_C)
            P_os_mW = 10**(P_os_dBm / 10.0)
            g_saturated_linear = self._newton_iteration_for_gain(P_os_mW, g0_linear, P_in_mW)
        return 10 * math.log10(g_saturated_linear) if output_in_dB and g_saturated_linear > 1e-9 else g_saturated_linear

    def calculate_wpe(self, I_mA: float, lambda_nm: float, T_C: float, P_in_mW: float) -> float:
        if I_mA <= 1e-9: return 0.0
        operating_voltage_V = self.get_operating_voltage(I_mA)
        if operating_voltage_V <= 1e-9: return 0.0

        original_L_temp = self.L_active_um
        self.L_active_um = self.L_active_um_orig
        J_op_kA_cm2 = self.calculate_current_density_kA_cm2(I_mA)
        self.L_active_um = original_L_temp

        g_linear = self.get_saturated_gain(lambda_nm, T_C, J_op_kA_cm2, P_in_mW, output_in_dB=False)
        P_out_mW = g_linear * P_in_mW
        delta_P_optical_mW = P_out_mW - P_in_mW
        P_electrical_mW = I_mA * operating_voltage_V
        if P_electrical_mW <= 1e-9: return 0.0
        if delta_P_optical_mW < 0: return 0.0
        return (delta_P_optical_mW / P_electrical_mW) * 100.0

    def find_Pin_for_target_Pout(self, target_Pout_mW: float, I_mA: float, lambda_nm: float, T_C: float) -> float | None:
        original_L_temp = self.L_active_um
        self.L_active_um = self.L_active_um_orig
        J_kA_cm2 = self.calculate_current_density_kA_cm2(I_mA)
        self.L_active_um = original_L_temp
        if (J_kA_cm2 <= 1e-9 and I_mA > 1e-9) or (I_mA <= 1e-9 and target_Pout_mW > 1e-9): return None

        def objective_func(Pin_mW_local: float) -> float:
            if Pin_mW_local <= 0: return target_Pout_mW * 100 + 1
            gain_linear = self.get_saturated_gain(lambda_nm, T_C, J_kA_cm2, Pin_mW_local, output_in_dB=False)
            return gain_linear * Pin_mW_local - target_Pout_mW

        if target_Pout_mW <= 1e-9: return 0.0
        try:
            result = brentq(objective_func, 1e-7, max(target_Pout_mW * 10, 1e-5))
            # brentq can return a tuple or single value, we need the root value
            if isinstance(result, tuple):
                return result[0]  # Return the root value from the tuple
            return result  # Return the single value
        except (ValueError, RuntimeError):
            return None 