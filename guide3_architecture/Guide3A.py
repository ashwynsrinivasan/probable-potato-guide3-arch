import math
from EuropaSOA import EuropaSOA

class Guide3A:
    """
    Represents a Europa Photonic Integrated Circuit (PIC) with enhanced Guide3A functionality.
    
    This class provides comprehensive modeling of different PIC architectures
    with detailed loss analysis and performance metrics, plus module configuration.
    """
    
    # Supported architectures
    SUPPORTED_ARCHITECTURES = ['psr', 'pol_control', 'psrless']
    
    # Supported fiber input types
    SUPPORTED_FIBER_TYPES = ['pm', 'sm']
    
    def __init__(self, pic_architecture: str, fiber_input_type: str = 'pm', num_fibers: int = 40, **kwargs):
        """
        Initialize Guide3A with specified architecture and module configuration.
        
        Args:
            pic_architecture (str): PIC architecture type
            fiber_input_type (str): Fiber input type ('pm' or 'sm')
            num_fibers (int): Number of fibers (must be multiple of 20)
            **kwargs: Optional custom loss values (io_in_loss, io_out_loss, etc.)
        """
        if fiber_input_type not in self.SUPPORTED_FIBER_TYPES:
            raise ValueError(f"Unsupported fiber input type: {fiber_input_type}. "
                           f"Supported: {self.SUPPORTED_FIBER_TYPES}")
        
        if num_fibers % 20 != 0:
            raise ValueError(f"Number of fibers must be a multiple of 20. Got: {num_fibers}")
        
        # For PM fiber, architecture must be psrless
        if fiber_input_type == 'pm' and pic_architecture != 'psrless':
            raise ValueError(f"For PM fiber input type, PIC architecture must be 'psrless'. Got: {pic_architecture}")
        
        # For SM fiber, architecture must be psr or pol_control
        if fiber_input_type == 'sm' and pic_architecture not in ['psr', 'pol_control']:
            raise ValueError(f"For SM fiber input type, PIC architecture must be 'psr' or 'pol_control'. Got: {pic_architecture}")
        
        if pic_architecture not in self.SUPPORTED_ARCHITECTURES:
            raise ValueError(f"Unsupported architecture: {pic_architecture}. "
                           f"Supported: {self.SUPPORTED_ARCHITECTURES}")
        
        self.pic_architecture = pic_architecture
        self.fiber_input_type = fiber_input_type
        self.num_fibers = num_fibers
        
        # Calculate module configuration
        self.effective_architecture = pic_architecture

        if self.effective_architecture == 'psrless':
            self.num_soas = self.num_fibers
        else:
            self.num_soas = 2 * self.num_fibers

        self.num_pics = math.ceil(self.num_soas / 20)
        self.num_unit_cells = self.num_pics
        
        # Default loss values (dB)
        self.io_in_loss = kwargs.get('io_in_loss', 1.5)
        self.io_out_loss = kwargs.get('io_out_loss', 1.5)
        self.psr_loss = kwargs.get('psr_loss', 0.5)
        self.phase_shifter_loss = kwargs.get('phase_shifter_loss', 0.5)
        self.coupler_loss = kwargs.get('coupler_loss', 0.2)
        
        # Performance parameters
        self.operating_wavelength_nm = kwargs.get('operating_wavelength_nm', 1310)
        self.temperature_c = kwargs.get('temperature_c', 25)
        self.target_pout = kwargs.get('target_pout', -2.75)  # dBm
        self.soa_penalty = kwargs.get('soa_penalty', 2)  # dB
        
        # SOA parameters (for psr architecture)
        self.soa_width_um = kwargs.get('soa_width_um', 2.0)
        self.soa_active_length_um = kwargs.get('soa_active_length_um', 790)
        self.soa_j_density = kwargs.get('soa_j_density', 4)  # kA/cm^2
        self.soa_temperature_c = kwargs.get('soa_temperature_c', 40)
        self.soa_wavelength_nm = kwargs.get('soa_wavelength_nm', 1310)
        self.soa = None
        if self.effective_architecture == 'psr':
            self.soa = EuropaSOA(
                L_active_um=self.soa_active_length_um,
                W_um=self.soa_width_um,
                verbose=False
            )
        
        # Validate inputs
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate all input parameters"""
        # Check for negative loss values
        loss_params = [
            self.io_in_loss, self.io_out_loss, self.psr_loss, 
            self.phase_shifter_loss, self.coupler_loss
        ]
        
        for param in loss_params:
            if param < 0:
                raise ValueError(f"Loss parameters cannot be negative: {param}")
        
        # Check wavelength range
        if not (1260 <= self.operating_wavelength_nm <= 1360):
            raise ValueError(f"Wavelength must be between 1260-1360 nm: {self.operating_wavelength_nm}")
        
        # Check temperature range
        if not (-40 <= self.temperature_c <= 85):
            raise ValueError(f"Temperature must be between -40 and 85°C: {self.temperature_c}")
        
        # Check target Pout range
        if not (-10 <= self.target_pout <= 20):
            raise ValueError(f"Target Pout must be between -10 and 20 dBm: {self.target_pout}")
        
        # Check SOA penalty range
        if self.soa_penalty < 0:
            raise ValueError(f"SOA penalty must be non-negative: {self.soa_penalty}")
    
    def get_total_loss(self):
        """
        Calculate total loss for the PIC architecture.
        
        Returns:
            float: Total loss in dB
        """
        total_loss = self.io_in_loss + self.io_out_loss
        
        # Add architecture-specific losses
        if self.effective_architecture == 'psr':
            total_loss += 2 * self.psr_loss  # psr_in and psr_out
            total_loss += 0.6  # tap_in and tap_out (0.3 dB each)
            
        elif self.effective_architecture == 'pol_control':
            total_loss += 2 * self.psr_loss  # psr_in and psr_out
            total_loss += 2 * self.phase_shifter_loss  # phase_shifter_in_1, phase_shifter_in_2
            total_loss += 2 * self.coupler_loss  # coupler_in_1, coupler_in_2
            
        elif self.effective_architecture == 'psrless':
            # PSRless architecture has no PSR components
            pass
        
        return total_loss
    
    def get_loss_breakdown(self):
        """
        Get detailed loss breakdown for the PIC.
        
        Returns:
            dict: Detailed loss breakdown
        """
        breakdown = {
            'io_losses': {
                'io_in_loss': self.io_in_loss,
                'io_out_loss': self.io_out_loss,
                'total_io_loss': self.io_in_loss + self.io_out_loss
            },
            'architecture_specific': {}
        }
        
        # Add architecture-specific losses
        if self.effective_architecture == 'psr':
            breakdown['architecture_specific'] = {
                'psr_loss': self.psr_loss,
                'total_psr_loss': 2 * self.psr_loss,
                'tap_in_loss': 0.3,
                'tap_out_loss': 0.3,
                'total_tap_loss': 0.6
            }
            
        elif self.effective_architecture == 'pol_control':
            breakdown['architecture_specific'] = {
                'psr_loss': self.psr_loss,
                'total_psr_loss': 2 * self.psr_loss,
                'phase_shifter_loss': self.phase_shifter_loss,
                'total_phase_shifter_loss': 2 * self.phase_shifter_loss,
                'coupler_loss': self.coupler_loss,
                'total_coupler_loss': 2 * self.coupler_loss
            }
            
        elif self.effective_architecture == 'psrless':
            breakdown['architecture_specific'] = {
                'note': 'No PSR components in PSRless architecture'
            }
        
        breakdown['total_loss'] = self.get_total_loss()
        return breakdown
    
    def get_performance_metrics(self):
        """
        Calculate performance metrics for the PIC.
        
        Returns:
            dict: Performance metrics
        """
        total_loss = self.get_total_loss()
        
        # Calculate power budget
        power_budget = {
            'total_loss_db': total_loss,
            'power_penalty_db': total_loss,
            'link_margin_db': 3.0,  # Typical link margin
            'required_tx_power_db': total_loss + 3.0  # Assuming 3dB margin
        }
        
        # Calculate bandwidth considerations
        bandwidth_metrics = {
            'wavelength_nm': self.operating_wavelength_nm,
            'temperature_c': self.temperature_c
        }
        
        # Calculate efficiency metrics
        efficiency_metrics = {
            'optical_efficiency_percent': max(0, 100 - total_loss * 10),  # Rough estimate
            'insertion_loss_db': total_loss,
            'return_loss_db': -15.0  # Typical return loss
        }
        
        return {
            'power_budget': power_budget,
            'bandwidth_metrics': bandwidth_metrics,
            'efficiency_metrics': efficiency_metrics
        }
    
    def get_architecture_description(self):
        """
        Get detailed description of the PIC architecture.
        
        Returns:
            str: Architecture description
        """
        descriptions = {
            'psr': "Polarization Splitter and Rotator (PSR) - Handles polarization diversity",
            'pol_control': "Polarization Control - Advanced polarization management with phase shifters",
            'psrless': "PSRless - Simplified architecture without PSR components"
        }
        return descriptions.get(self.effective_architecture, "Unknown architecture")
    
    def get_component_count(self):
        """
        Get the number of components for the architecture.
        
        Returns:
            dict: Component counts
        """
        base_components = {
            'io_ports': 2
        }
        
        architecture_components = {
            'psr': {'psr_devices': 2},
            'pol_control': {'psr_devices': 2, 'phase_shifters': 2, 'couplers': 2},
            'psrless': {}
        }
        
        components = base_components.copy()
        components.update(architecture_components.get(self.effective_architecture, {}))
        return components
    
    def get_module_configuration(self):
        """
        Get module configuration details.
        
        Returns:
            dict: Module configuration
        """
        return {
            'fiber_input_type': self.fiber_input_type,
            'pic_architecture': self.pic_architecture,
            'effective_architecture': self.effective_architecture,
            'num_fibers': self.num_fibers,
            'num_soas': self.num_soas,
            'num_pics': self.num_pics,
            'num_unit_cells': self.num_unit_cells
        }
    
    def set_custom_losses(self, **kwargs):
        """
        Set custom loss values and revalidate.
        
        Args:
            **kwargs: Custom loss values to set
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown parameter: {key}")
        
        self._validate_parameters()
    
    def get_summary_report(self):
        """
        Generate a comprehensive summary report.
        
        Returns:
            str: Formatted summary report
        """
        breakdown = self.get_loss_breakdown()
        metrics = self.get_performance_metrics()
        components = self.get_component_count()
        module_config = self.get_module_configuration()
        
        report = f"""
Guide3A Analysis Report
{'='*50}

Module Configuration:
- Fiber Input Type: {module_config['fiber_input_type'].upper()}
- PIC Architecture: {module_config['pic_architecture'].upper()}
- Effective Architecture: {module_config['effective_architecture'].upper()}
- Number of Fibers: {module_config['num_fibers']}
- Number of SOAs: {module_config['num_soas']}
- Number of PICs: {module_config['num_pics']}
- Number of Unit Cells: {module_config['num_unit_cells']}

Architecture: {module_config['effective_architecture'].upper()}
Description: {self.get_architecture_description()}

Component Count:
"""
        for component, count in components.items():
            report += f"  - {component.replace('_', ' ').title()}: {count}\n"
        
        report += f"""
Loss Breakdown:
  - I/O Input Loss: {breakdown['io_losses']['io_in_loss']:.1f} dB
  - I/O Output Loss: {breakdown['io_losses']['io_out_loss']:.1f} dB
  - Total I/O Loss: {breakdown['io_losses']['total_io_loss']:.1f} dB
"""
        
        # Add architecture-specific losses
        arch_losses = breakdown['architecture_specific']
        for loss_type, value in arch_losses.items():
            if 'total' in loss_type:
                report += f"  - {loss_type.replace('_', ' ').title()}: {value:.1f} dB\n"
            elif loss_type == 'note':
                report += f"  - {value}\n"
        
        report += f"""
Performance Metrics:
  - Total Loss: {breakdown['total_loss']:.1f} dB
  - Power Penalty: {metrics['power_budget']['power_penalty_db']:.1f} dB
  - Required TX Power: {metrics['power_budget']['required_tx_power_db']:.1f} dBm
  - Optical Efficiency: {metrics['efficiency_metrics']['optical_efficiency_percent']:.1f}%
  - Operating Wavelength: {self.operating_wavelength_nm} nm
  - Temperature: {self.temperature_c}°C
"""
        
        return report 

    def get_soa_performance(self):
        """
        Get SOA performance metrics if SOA is configured.
        
        Returns:
            dict: SOA performance metrics or None if not configured
        """
        if self.soa is None:
            return None
        
        try:
            current_ma = self.soa.calculate_current_mA_from_J(self.soa_j_density)
            operating_voltage = self.soa.get_operating_voltage(current_ma)
            electrical_power = current_ma * operating_voltage
            
            # Calculate unsaturated gain
            unsaturated_gain_db = self.soa.get_unsaturated_gain(
                self.soa_wavelength_nm, self.soa_temperature_c, self.soa_j_density)
            
            # Calculate saturation power
            saturation_power_dbm = self.soa.get_output_saturation_power_dBm(
                self.soa_wavelength_nm, self.soa_j_density, self.soa_temperature_c)
            
            return {
                'current_ma': current_ma,
                'operating_voltage_v': operating_voltage,
                'electrical_power_mw': electrical_power,
                'unsaturated_gain_db': unsaturated_gain_db,
                'saturation_power_dbm': saturation_power_dbm
            }
        except Exception as e:
            return {'error': str(e)}

    def calculate_target_pout_all_wavelengths(self, num_wavelengths: int, target_pout_3sigma: float | None = None, soa_penalty_3sigma: float | None = None):
        """
        Calculate target Pout for all wavelengths based on the formula:
        Pout + penalty + 10*log10(number_of_wavelengths)
        
        Args:
            num_wavelengths (int): Number of wavelengths
            target_pout_3sigma (float): Target Pout for 3σ case (optional)
            soa_penalty_3sigma (float): SOA penalty for 3σ case (optional)
            
        Returns:
            dict: Target Pout calculations for median and 3σ cases
        """
        if num_wavelengths <= 0:
            raise ValueError("Number of wavelengths must be positive")
        
        # Calculate wavelength penalty: 10*log10(number_of_wavelengths)
        wavelength_penalty = 10 * math.log10(num_wavelengths)
        
        # Median case calculation
        median_target_pout = self.target_pout + self.soa_penalty + wavelength_penalty
        
        # 3σ case calculation (if provided)
        sigma_target_pout = None
        if target_pout_3sigma is not None and soa_penalty_3sigma is not None:
            sigma_target_pout = target_pout_3sigma + soa_penalty_3sigma + wavelength_penalty
        
        result = {
            'num_wavelengths': num_wavelengths,
            'wavelength_penalty_db': wavelength_penalty,
            'median_case': {
                'base_target_pout_db': self.target_pout,
                'soa_penalty_db': self.soa_penalty,
                'total_target_pout_db': median_target_pout
            }
        }
        
        # Add sigma case if all required values are provided
        if target_pout_3sigma is not None and soa_penalty_3sigma is not None and sigma_target_pout is not None:
            result['sigma_case'] = {
                'base_target_pout_db': target_pout_3sigma,
                'soa_penalty_db': soa_penalty_3sigma,
                'total_target_pout_db': sigma_target_pout
            }
        
        return result 

    def calculate_target_pout_after_soa(self, num_wavelengths: int, target_pout_3sigma: float | None = None, soa_penalty_3sigma: float | None = None):
        """
        Calculate the target Pout required from each SOA based on losses.
        Works backwards from the final target Pout to determine SOA output requirements.
        Only includes output component losses (not input losses).
        
        Args:
            num_wavelengths (int): Number of wavelengths
            target_pout_3sigma (float): Target Pout for 3σ case (optional)
            soa_penalty_3sigma (float): SOA penalty for 3σ case (optional)
            
        Returns:
            dict: Target Pout requirements for each SOA
        """
        if num_wavelengths <= 0:
            raise ValueError("Number of wavelengths must be positive")
        
        # Get the total target Pout for all wavelengths
        total_target_calc = self.calculate_target_pout_all_wavelengths(
            num_wavelengths, target_pout_3sigma, soa_penalty_3sigma
        )
        
        # Get loss breakdown
        loss_breakdown = self.get_loss_breakdown()
        
        # Calculate output-only losses (exclude input losses)
        output_losses = loss_breakdown['io_losses']['io_out_loss']
        
        # Add architecture-specific output losses
        arch_losses = loss_breakdown['architecture_specific']
        if self.effective_architecture == 'psr':
            output_losses += arch_losses.get('total_psr_loss', 0) / 2  # Only output PSR
            output_losses += arch_losses.get('total_tap_loss', 0) / 2  # Only output tap
        elif self.effective_architecture == 'pol_control':
            output_losses += arch_losses.get('total_psr_loss', 0) / 2  # Only output PSR
            output_losses += arch_losses.get('total_phase_shifter_loss', 0) / 2  # Only output phase shifter
            output_losses += arch_losses.get('total_coupler_loss', 0) / 2  # Only output coupler
        elif self.effective_architecture == 'psrless':
            # No additional output losses in PSRless architecture
            pass
        
        # Calculate SOA output requirements
        # SOA output = Final target + Output losses only (working backwards)
        median_soa_output = total_target_calc['median_case']['total_target_pout_db'] + output_losses
        
        result = {
            'num_wavelengths': num_wavelengths,
            'total_output_loss_db': output_losses,
            'median_case': {
                'final_target_pout_db': total_target_calc['median_case']['total_target_pout_db'],
                'soa_output_requirement_db': median_soa_output,
                'loss_breakdown': {
                    'io_out_loss': loss_breakdown['io_losses']['io_out_loss'],
                    'architecture_output_loss': output_losses - loss_breakdown['io_losses']['io_out_loss']
                }
            }
        }
        
        # Add 3σ case if available
        if total_target_calc['sigma_case'] is not None:
            sigma_soa_output = total_target_calc['sigma_case']['total_target_pout_db'] + output_losses
            result['sigma_case'] = {
                'final_target_pout_db': total_target_calc['sigma_case']['total_target_pout_db'],
                'soa_output_requirement_db': sigma_soa_output,
                'loss_breakdown': {
                    'io_out_loss': loss_breakdown['io_losses']['io_out_loss'],
                    'architecture_output_loss': output_losses - loss_breakdown['io_losses']['io_out_loss']
                }
            }
        
        return result 

    def estimate_optimum_soa_current_density(self, num_wavelengths: int, target_pout_3sigma: float | None = None, soa_penalty_3sigma: float | None = None, wavelengths: list[float] | None = None):
        """
        Estimate the optimum SOA current density and current such that the target Pout for the SOA 
        is at least 2dB below the average saturation power when all wavelengths are considered.
        
        Args:
            num_wavelengths (int): Number of wavelengths
            target_pout_3sigma (float): Target Pout for 3σ case (optional)
            soa_penalty_3sigma (float): SOA penalty for 3σ case (optional)
            wavelengths (list[float]): List of wavelengths in nm (optional, defaults to 1310nm)
            
        Returns:
            dict: Optimum current density and current for median and 3σ cases
        """
        if num_wavelengths <= 0:
            raise ValueError("Number of wavelengths must be positive")
        
        # Default wavelengths if not provided
        if wavelengths is None:
            wavelengths = [1310.0] * num_wavelengths
        elif len(wavelengths) != num_wavelengths:
            raise ValueError(f"Number of wavelengths ({len(wavelengths)}) must match num_wavelengths ({num_wavelengths})")
        
        # Get SOA output requirements
        soa_output_calculation = self.calculate_target_pout_after_soa(
            num_wavelengths=num_wavelengths,
            target_pout_3sigma=target_pout_3sigma,
            soa_penalty_3sigma=soa_penalty_3sigma
        )
        
        # Create SOA instance for calculations
        soa = EuropaSOA(
            L_active_um=self.soa_active_length_um,
            W_um=self.soa_width_um,
            verbose=False
        )
        
        def find_optimum_current_density(target_pout_db: float, case_name: str):
            """Find optimum current density for a given target Pout"""
            # Target Pout in mW
            target_pout_mw = 10**(target_pout_db / 10.0)
            
            # Target saturation power (2dB above target Pout)
            target_saturation_power_mw = target_pout_mw * 10**(2.0 / 10.0)  # 2dB above target Pout
            
            # Binary search for optimum current density
            j_min = 1.0  # kA/cm²
            j_max = 15.0  # kA/cm² (increased from 10.0)
            j_opt = None
            
            for _ in range(25):  # Max 25 iterations
                j_test = (j_min + j_max) / 2
                
                # Calculate average saturation power across all wavelengths
                saturation_powers = []
                for wavelength in wavelengths:
                    saturation_power_dbm = soa.get_output_saturation_power_dBm(
                        wavelength, j_test, self.soa_temperature_c
                    )
                    saturation_power_mw = 10**(saturation_power_dbm / 10.0)
                    saturation_powers.append(saturation_power_mw)
                
                avg_saturation_power_mw = sum(saturation_powers) / len(saturation_powers)
                
                if avg_saturation_power_mw >= target_saturation_power_mw:
                    j_opt = j_test
                    j_max = j_test
                else:
                    j_min = j_test
                
                if j_max - j_min < 0.005:  # Tighter convergence threshold
                    break
            
            # If we didn't find a solution within the range, use the maximum
            if j_opt is None:
                j_opt = j_max
                # Recalculate with maximum current density
                saturation_powers = []
                for wavelength in wavelengths:
                    saturation_power_dbm = soa.get_output_saturation_power_dBm(
                        wavelength, j_opt, self.soa_temperature_c
                    )
                    saturation_power_mw = 10**(saturation_power_dbm / 10.0)
                    saturation_powers.append(saturation_power_mw)
                avg_saturation_power_mw = sum(saturation_powers) / len(saturation_powers)
            
            # Calculate corresponding current
            current_ma = soa.calculate_current_mA_from_J(j_opt)
            
            return {
                'current_density_kA_cm2': j_opt,
                'current_ma': current_ma,
                'target_pout_db': target_pout_db,
                'target_saturation_power_mw': target_saturation_power_mw,
                'avg_saturation_power_mw': avg_saturation_power_mw,
                'avg_saturation_power_db': 10 * math.log10(avg_saturation_power_mw),
                'margin_db': 10 * math.log10(avg_saturation_power_mw / target_pout_mw)
            }
        
        # Calculate for median case
        median_target_pout = soa_output_calculation['median_case']['soa_output_requirement_db']
        median_result = find_optimum_current_density(median_target_pout, "Median")
        
        result = {
            'num_wavelengths': num_wavelengths,
            'wavelengths_nm': wavelengths,
            'median_case': median_result
        }
        
        # Calculate for 3σ case if available
        if soa_output_calculation['sigma_case'] is not None:
            sigma_target_pout = soa_output_calculation['sigma_case']['soa_output_requirement_db']
            sigma_result = find_optimum_current_density(sigma_target_pout, "3σ")
            result['sigma_case'] = sigma_result
        
        return result 