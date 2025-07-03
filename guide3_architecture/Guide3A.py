import math
from .EuropaSOA import EuropaSOA

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
        self.psr_loss_te = kwargs.get('psr_loss_te', 0.37)  # PSR loss for TE polarization
        self.psr_loss_tm = kwargs.get('psr_loss_tm', 0.93)  # PSR loss for TM polarization
        self.phase_shifter_loss = kwargs.get('phase_shifter_loss', 0.5)
        self.coupler_loss = kwargs.get('coupler_loss', 0.2)
        
        # New optical connector components (0.25dB each)
        self.connector_in_loss = kwargs.get('connector_in_loss', 0.25)
        self.connector_out_loss = kwargs.get('connector_out_loss', 0.25)
        
        # New waveguide routing components (0.25dB each)
        self.wg_in_loss = kwargs.get('wg_in_loss', 0.25)
        self.wg_out_loss = kwargs.get('wg_out_loss', 0.25)
        
        # Tap components (0.3dB each)
        self.tap_in_loss = kwargs.get('tap_in_loss', 0.3)
        self.tap_out_loss = kwargs.get('tap_out_loss', 0.3)
        
        # TE Polarization Fraction - new parameter
        self.te_polarization_fraction = kwargs.get('te_polarization_fraction', 0.5)  # Default: 50% TE
        
        # Performance parameters
        self.operating_wavelength_nm = kwargs.get('operating_wavelength_nm', 1310)
        self.temperature_c = kwargs.get('temperature_c', 25)
        self.target_pout = kwargs.get('target_pout', -2.75)  # dBm
        self.soa_penalty = kwargs.get('soa_penalty', 2)  # dB
        
        # Module parameters for power and efficiency calculations
        self.idac_voltage_overhead = kwargs.get('idac_voltage_overhead', 0.4)  # V
        self.ir_drop_nominal = kwargs.get('ir_drop_nominal', 0.1)  # V
        self.ir_drop_3sigma = kwargs.get('ir_drop_3sigma', 0.2)  # V
        self.vrm_efficiency = kwargs.get('vrm_efficiency', 80)  # %
        self.tec_cop_nominal = kwargs.get('tec_cop_nominal', 2)
        self.tec_cop_3sigma = kwargs.get('tec_cop_3sigma', 4)
        self.tec_power_efficiency = kwargs.get('tec_power_efficiency', 80)  # %
        self.driver_peripherals_power = kwargs.get('driver_peripherals_power', 1.0)  # W
        self.mcu_power = kwargs.get('mcu_power', 0.5)  # W
        self.misc_power = kwargs.get('misc_power', 0.25)  # W
        self.digital_core_efficiency = kwargs.get('digital_core_efficiency', 80)  # %
        
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
            self.phase_shifter_loss, self.coupler_loss,
            self.connector_in_loss, self.connector_out_loss,
            self.wg_in_loss, self.wg_out_loss,
            self.tap_in_loss, self.tap_out_loss
        ]
        
        for param in loss_params:
            if param < 0:
                raise ValueError(f"Loss parameters cannot be negative: {param}")
        
        # Check degree of polarization range
        if not (0.0 <= self.te_polarization_fraction <= 1.0):
            raise ValueError(f"TE polarization fraction must be between 0.0 and 1.0: {self.te_polarization_fraction}")
        
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
        
        # Validate module parameters
        if self.idac_voltage_overhead < 0:
            raise ValueError(f"IDAC voltage overhead cannot be negative: {self.idac_voltage_overhead}")
        
        if self.ir_drop_nominal < 0 or self.ir_drop_3sigma < 0:
            raise ValueError(f"IR drop values cannot be negative: nominal={self.ir_drop_nominal}, 3σ={self.ir_drop_3sigma}")
        
        if not (0 <= self.vrm_efficiency <= 100):
            raise ValueError(f"VRM efficiency must be between 0 and 100%: {self.vrm_efficiency}")
        
        if self.tec_cop_nominal <= 0 or self.tec_cop_3sigma <= 0:
            raise ValueError(f"TEC COP values must be positive: nominal={self.tec_cop_nominal}, 3σ={self.tec_cop_3sigma}")
        
        if not (0 <= self.tec_power_efficiency <= 100):
            raise ValueError(f"TEC power efficiency must be between 0 and 100%: {self.tec_power_efficiency}")
        
        if self.driver_peripherals_power < 0 or self.mcu_power < 0 or self.misc_power < 0:
            raise ValueError(f"Power consumption values cannot be negative: driver={self.driver_peripherals_power}, mcu={self.mcu_power}, misc={self.misc_power}")
        
        if not (0 <= self.digital_core_efficiency <= 100):
            raise ValueError(f"Digital core efficiency must be between 0 and 100%: {self.digital_core_efficiency}")
    
    def get_total_loss(self):
        """
        Calculate total loss for the PIC architecture.
        
        Returns:
            float: Total loss in dB
        """
        # Start with optical connector losses (present in all architectures)
        total_loss = self.connector_in_loss + self.connector_out_loss
        
        # Add I/O losses
        total_loss += self.io_in_loss + self.io_out_loss
        
        # Add waveguide routing losses (present in all architectures)
        total_loss += self.wg_in_loss + self.wg_out_loss
        
        # Add architecture-specific losses
        if self.effective_architecture == 'psr':
            # Calculate polarization-dependent PSR loss based on TE fraction
            te_fraction = self.te_polarization_fraction
            tm_fraction = 1.0 - self.te_polarization_fraction
            
            # PSR_in: Each path has its own loss based on the actual path taken
            # - TE/TE path: psr_in_tetm → psr_in_te2te (TE loss)
            # - TM/TE path: psr_in_tetm → psr_in_tm2te (TM loss)
            te2te_psr_in_loss = self.psr_loss_te  # TE path through PSR_in
            tm2te_psr_in_loss = self.psr_loss_tm  # TM path through PSR_in
            
            # PSR_out: With connection swap:
            # - psr_out_tm2te connects to tap_out_te2te (TE path)
            # - psr_out_te2te connects to tap_out_tm2te (TM path)
            # Each path has different PSR_out loss based on the connection
            te2te_psr_out_loss = self.psr_loss_tm  # TM2TE port connects to TE2TE path
            tm2te_psr_out_loss = self.psr_loss_te  # TE2TE port connects to TM2TE path
            
            # Total PSR loss: weighted average of both paths
            te2te_total_psr_loss = te2te_psr_in_loss + te2te_psr_out_loss
            tm2te_total_psr_loss = tm2te_psr_in_loss + tm2te_psr_out_loss
            total_psr_loss = (te_fraction * te2te_total_psr_loss) + (tm_fraction * tm2te_total_psr_loss)
            total_loss += total_psr_loss
            
            # Dual path components - only tap losses (waveguide routing is already included above)
            # TE/TE path components
            total_loss += self.tap_in_loss + self.tap_out_loss  # taps for TE/TE path
            
            # TM/TE path components  
            total_loss += self.tap_in_loss + self.tap_out_loss  # taps for TM/TE path
            
            # Note: SOAs don't contribute to loss (amplification), but are present in both paths
            
        elif self.effective_architecture == 'pol_control':
            # Pol-control architecture should be identical to PSR
            # Calculate polarization-dependent PSR loss based on TE fraction
            te_fraction = self.te_polarization_fraction
            tm_fraction = 1.0 - self.te_polarization_fraction
            
            # PSR_in: Each path has its own loss based on the actual path taken
            # - TE/TE path: psr_in_tetm → psr_in_te2te (TE loss)
            # - TM/TE path: psr_in_tetm → psr_in_tm2te (TM loss)
            te2te_psr_in_loss = self.psr_loss_te  # TE path through PSR_in
            tm2te_psr_in_loss = self.psr_loss_tm  # TM path through PSR_in
            
            # PSR_out: With connection swap:
            # - psr_out_tm2te connects to tap_out_te2te (TE path)
            # - psr_out_te2te connects to tap_out_tm2te (TM path)
            # Each path has different PSR_out loss based on the connection
            te2te_psr_out_loss = self.psr_loss_tm  # TM2TE port connects to TE2TE path
            tm2te_psr_out_loss = self.psr_loss_te  # TE2TE port connects to TM2TE path
            
            # Total PSR loss: weighted average of both paths
            te2te_total_psr_loss = te2te_psr_in_loss + te2te_psr_out_loss
            tm2te_total_psr_loss = tm2te_psr_in_loss + tm2te_psr_out_loss
            total_psr_loss = (te_fraction * te2te_total_psr_loss) + (tm_fraction * tm2te_total_psr_loss)
            total_loss += total_psr_loss
            
            # Dual path components - only tap losses (waveguide routing is already included above)
            # TE/TE path components
            total_loss += self.tap_in_loss + self.tap_out_loss  # taps for TE/TE path
            
            # TM/TE path components  
            total_loss += self.tap_in_loss + self.tap_out_loss  # taps for TM/TE path
            
            # Note: SOAs don't contribute to loss (amplification), but are present in both paths
            
        elif self.effective_architecture == 'psrless':
            # PSRless architecture has tap components
            total_loss += self.tap_in_loss + self.tap_out_loss  # tap_in and tap_out
        
        return total_loss
    
    def get_loss_breakdown(self):
        """
        Get detailed loss breakdown for the PIC.
        
        Returns:
            dict: Detailed loss breakdown
        """
        breakdown = {
            'connector_losses': {
                'connector_in_loss': self.connector_in_loss,
                'connector_out_loss': self.connector_out_loss,
                'total_connector_loss': self.connector_in_loss + self.connector_out_loss
            },
            'io_losses': {
                'io_in_loss': self.io_in_loss,
                'io_out_loss': self.io_out_loss,
                'total_io_loss': self.io_in_loss + self.io_out_loss
            },
            'waveguide_routing_losses': {
                'wg_in_loss': self.wg_in_loss,
                'wg_out_loss': self.wg_out_loss,
                'total_wg_routing_loss': self.wg_in_loss + self.wg_out_loss
            },
            'architecture_specific': {}
        }
        
        # Add architecture-specific losses
        if self.effective_architecture == 'psr':
            total_loss = 0.0  # Initialize total_loss for breakdown calculation
            # Calculate polarization-dependent PSR loss based on TE fraction
            te_fraction = self.te_polarization_fraction
            tm_fraction = 1.0 - self.te_polarization_fraction
            
            # PSR_in: Each path has its own loss based on the actual path taken
            # - TE/TE path: psr_in_tetm → psr_in_te2te (TE loss)
            # - TM/TE path: psr_in_tetm → psr_in_tm2te (TM loss)
            te2te_psr_in_loss = self.psr_loss_te  # TE path through PSR_in
            tm2te_psr_in_loss = self.psr_loss_tm  # TM path through PSR_in
            
            # PSR_out: With connection swap:
            # - psr_out_tm2te connects to tap_out_te2te (TE path)
            # - psr_out_te2te connects to tap_out_tm2te (TM path)
            # Each path has different PSR_out loss based on the connection
            te2te_psr_out_loss = self.psr_loss_tm  # TM2TE port connects to TE2TE path
            tm2te_psr_out_loss = self.psr_loss_te  # TE2TE port connects to TM2TE path
            
            # Total PSR loss: weighted average of both paths
            te2te_total_psr_loss = te2te_psr_in_loss + te2te_psr_out_loss
            tm2te_total_psr_loss = tm2te_psr_in_loss + tm2te_psr_out_loss
            total_psr_loss = (te_fraction * te2te_total_psr_loss) + (tm_fraction * tm2te_total_psr_loss)
            total_loss += total_psr_loss
            
            # Dual path components - only tap losses (waveguide routing is already included above)
            # TE/TE path components
            total_loss += self.tap_in_loss + self.tap_out_loss  # taps for TE/TE path
            
            # TM/TE path components  
            total_loss += self.tap_in_loss + self.tap_out_loss  # taps for TM/TE path
            
            # Note: SOAs don't contribute to loss (amplification), but are present in both paths
            
            breakdown['architecture_specific'] = {
                'psr_loss_te': self.psr_loss_te,
                'psr_loss_tm': self.psr_loss_tm,
                'te_polarization_fraction': self.te_polarization_fraction,
                'tm_polarization_fraction': tm_fraction,
                'psr_in_loss': te2te_psr_in_loss + tm2te_psr_in_loss,
                'psr_out_loss': te2te_psr_out_loss + tm2te_psr_out_loss,
                'te2te_psr_in_loss': te2te_psr_in_loss,
                'tm2te_psr_in_loss': tm2te_psr_in_loss,
                'te2te_psr_out_loss': te2te_psr_out_loss,
                'tm2te_psr_out_loss': tm2te_psr_out_loss,
                'te2te_total_psr_loss': te2te_total_psr_loss,
                'tm2te_total_psr_loss': tm2te_total_psr_loss,
                'total_psr_loss': total_psr_loss,
                'dual_path_components': {
                    'te2te_path': {
                        'tap_loss': self.tap_in_loss + self.tap_out_loss,
                        'psr_in_loss': te2te_psr_in_loss,
                        'psr_out_loss': te2te_psr_out_loss,
                        'total_path_loss': te2te_total_psr_loss + self.tap_in_loss + self.tap_out_loss
                    },
                    'tm2te_path': {
                        'tap_loss': self.tap_in_loss + self.tap_out_loss,
                        'psr_in_loss': tm2te_psr_in_loss,
                        'psr_out_loss': tm2te_psr_out_loss,
                        'total_path_loss': tm2te_total_psr_loss + self.tap_in_loss + self.tap_out_loss
                    }
                },
                'total_dual_path_loss': 2 * (self.tap_in_loss + self.tap_out_loss),
                'tap_in_loss': self.tap_in_loss,
                'tap_out_loss': self.tap_out_loss,
                'total_tap_loss': 2 * (self.tap_in_loss + self.tap_out_loss),  # Both paths
                'note': 'total_path_loss now includes psr_in_loss, psr_out_loss (for that path), and tap losses; updated for swapped connections.'
            }
            
        elif self.effective_architecture == 'pol_control':
            total_loss = 0.0  # Initialize total_loss for breakdown calculation
            # Pol-control architecture should be identical to PSR
            # Calculate polarization-dependent PSR loss based on TE fraction
            te_fraction = self.te_polarization_fraction
            tm_fraction = 1.0 - self.te_polarization_fraction
            
            # PSR_in: Each path has its own loss based on the actual path taken
            # - TE/TE path: psr_in_tetm → psr_in_te2te (TE loss)
            # - TM/TE path: psr_in_tetm → psr_in_tm2te (TM loss)
            te2te_psr_in_loss = self.psr_loss_te  # TE path through PSR_in
            tm2te_psr_in_loss = self.psr_loss_tm  # TM path through PSR_in
            
            # PSR_out: With connection swap:
            # - psr_out_tm2te connects to tap_out_te2te (TE path)
            # - psr_out_te2te connects to tap_out_tm2te (TM path)
            # Each path has different PSR_out loss based on the connection
            te2te_psr_out_loss = self.psr_loss_tm  # TM2TE port connects to TE2TE path
            tm2te_psr_out_loss = self.psr_loss_te  # TE2TE port connects to TM2TE path
            
            # Total PSR loss: weighted average of both paths
            te2te_total_psr_loss = te2te_psr_in_loss + te2te_psr_out_loss
            tm2te_total_psr_loss = tm2te_psr_in_loss + tm2te_psr_out_loss
            total_psr_loss = (te_fraction * te2te_total_psr_loss) + (tm_fraction * tm2te_total_psr_loss)
            total_loss += total_psr_loss
            
            # Dual path components - only tap losses (waveguide routing is already included above)
            # TE/TE path components
            total_loss += self.tap_in_loss + self.tap_out_loss  # taps for TE/TE path
            
            # TM/TE path components  
            total_loss += self.tap_in_loss + self.tap_out_loss  # taps for TM/TE path
            
            # Note: SOAs don't contribute to loss (amplification), but are present in both paths
            
            breakdown['architecture_specific'] = {
                'psr_loss_te': self.psr_loss_te,
                'psr_loss_tm': self.psr_loss_tm,
                'te_polarization_fraction': self.te_polarization_fraction,
                'tm_polarization_fraction': tm_fraction,
                'psr_in_loss': te2te_psr_in_loss + tm2te_psr_in_loss,
                'psr_out_loss': te2te_psr_out_loss + tm2te_psr_out_loss,
                'te2te_psr_in_loss': te2te_psr_in_loss,
                'tm2te_psr_in_loss': tm2te_psr_in_loss,
                'te2te_psr_out_loss': te2te_psr_out_loss,
                'tm2te_psr_out_loss': tm2te_psr_out_loss,
                'te2te_total_psr_loss': te2te_total_psr_loss,
                'tm2te_total_psr_loss': tm2te_total_psr_loss,
                'total_psr_loss': total_psr_loss,
                'dual_path_components': {
                    'te2te_path': {
                        'tap_loss': self.tap_in_loss + self.tap_out_loss,
                        'psr_in_loss': te2te_psr_in_loss,
                        'psr_out_loss': te2te_psr_out_loss,
                        'total_path_loss': te2te_total_psr_loss + self.tap_in_loss + self.tap_out_loss
                    },
                    'tm2te_path': {
                        'tap_loss': self.tap_in_loss + self.tap_out_loss,
                        'psr_in_loss': tm2te_psr_in_loss,
                        'psr_out_loss': tm2te_psr_out_loss,
                        'total_path_loss': tm2te_total_psr_loss + self.tap_in_loss + self.tap_out_loss
                    }
                },
                'total_dual_path_loss': 2 * (self.tap_in_loss + self.tap_out_loss),
                'tap_in_loss': self.tap_in_loss,
                'tap_out_loss': self.tap_out_loss,
                'total_tap_loss': 2 * (self.tap_in_loss + self.tap_out_loss),  # Both paths
                'note': 'total_path_loss now includes psr_in_loss, psr_out_loss (for that path), and tap losses; updated for swapped connections.'
            }
            
        elif self.effective_architecture == 'psrless':
            breakdown['architecture_specific'] = {
                'tap_in_loss': self.tap_in_loss,
                'tap_out_loss': self.tap_out_loss,
                'total_tap_loss': self.tap_in_loss + self.tap_out_loss
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
            'psrless': "PSRless - Simplified architecture with tap components for monitoring"
        }
        return descriptions.get(self.effective_architecture, "Unknown architecture")
    
    def get_component_count(self):
        """
        Get the number of components for the architecture.
        
        Returns:
            dict: Component counts
        """
        base_components = {
            'io_ports': 2,
            'optical_connectors': 2,  # connector_in and connector_out
            'waveguide_routing': 2    # wg_in and wg_out (for non-PSR architectures)
        }
        
        architecture_components = {
            'psr': {
                'psr_devices': 2,  # PSR_in and PSR_out
                'waveguide_routing_te2te': 2,  # wg_in_te2te and wg_out_te2te
                'waveguide_routing_tm2te': 2,  # wg_in_tm2te and wg_out_tm2te
                'taps_te2te': 2,  # tap_in_te2te and tap_out_te2te
                'taps_tm2te': 2,  # tap_in_tm2te and tap_out_tm2te
                'soas': 2,  # SOA_te2te and SOA_tm2te
                'total_dual_path_components': 12  # 2 PSR + 4 waveguide routing + 4 taps + 2 SOAs
            },
            'pol_control': {
                'psr_devices': 2,  # PSR_in and PSR_out
                'waveguide_routing_te2te': 2,  # wg_in_te2te and wg_out_te2te
                'waveguide_routing_tm2te': 2,  # wg_in_tm2te and wg_out_tm2te
                'taps_te2te': 2,  # tap_in_te2te and tap_out_te2te
                'taps_tm2te': 2,  # tap_in_tm2te and tap_out_tm2te
                'soas': 2,  # SOA_te2te and SOA_tm2te
                'total_dual_path_components': 12  # 2 PSR + 4 waveguide routing + 4 taps + 2 SOAs
            },
            'psrless': {'tap_devices': 2}
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
            'num_unit_cells': self.num_unit_cells,
            'te_polarization_fraction': self.te_polarization_fraction
        }
    
    def get_analog_specifications(self):
        """
        Get Analog Specifications for power and efficiency calculations.
        
        Returns:
            dict: Analog specifications
        """
        return {
            'idac_voltage_overhead': self.idac_voltage_overhead,
            'ir_drop_nominal': self.ir_drop_nominal,
            'ir_drop_3sigma': self.ir_drop_3sigma,
            'analog_supply_efficiency': self.vrm_efficiency
        }
    
    def get_digital_specifications(self):
        """
        Get Digital Specifications for power and efficiency calculations.
        
        Returns:
            dict: Digital specifications
        """
        return {
            'driver_peripherals_power': self.driver_peripherals_power,
            'mcu_power': self.mcu_power,
            'misc_power': self.misc_power,
            'digital_supply_efficiency': self.digital_core_efficiency
        }
    
    def get_thermal_specifications(self):
        """
        Get Thermal Specifications for power and efficiency calculations.
        
        Returns:
            dict: Thermal specifications
        """
        return {
            'tec_cop_nominal': self.tec_cop_nominal,
            'tec_cop_3sigma': self.tec_cop_3sigma,
            'tec_supply_efficiency': self.tec_power_efficiency
        }
    
    def get_module_parameters(self):
        """
        Get module parameters for power and efficiency calculations.
        
        Returns:
            dict: Module parameters
        """
        return {
            'idac_voltage_overhead': self.idac_voltage_overhead,
            'ir_drop_nominal': self.ir_drop_nominal,
            'ir_drop_3sigma': self.ir_drop_3sigma,
            'vrm_efficiency': self.vrm_efficiency,
            'tec_cop_nominal': self.tec_cop_nominal,
            'tec_cop_3sigma': self.tec_cop_3sigma,
            'tec_power_efficiency': self.tec_power_efficiency,
            'driver_peripherals_power': self.driver_peripherals_power,
            'mcu_power': self.mcu_power,
            'misc_power': self.misc_power,
            'digital_core_efficiency': self.digital_core_efficiency
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
- TE Polarization Fraction: {module_config['te_polarization_fraction']:.2f}

Architecture: {module_config['effective_architecture'].upper()}
Description: {self.get_architecture_description()}

Component Count:
"""
        for component, count in components.items():
            report += f"  - {component.replace('_', ' ').title()}: {count}\n"
        
        report += f"""
Loss Breakdown:
  - Optical Connector Input Loss: {breakdown['connector_losses']['connector_in_loss']:.1f} dB
  - Optical Connector Output Loss: {breakdown['connector_losses']['connector_out_loss']:.1f} dB
  - Total Optical Connector Loss: {breakdown['connector_losses']['total_connector_loss']:.1f} dB
  - I/O Input Loss: {breakdown['io_losses']['io_in_loss']:.1f} dB
  - I/O Output Loss: {breakdown['io_losses']['io_out_loss']:.1f} dB
  - Total I/O Loss: {breakdown['io_losses']['total_io_loss']:.1f} dB
  - Waveguide Routing Input Loss: {breakdown['waveguide_routing_losses']['wg_in_loss']:.1f} dB
  - Waveguide Routing Output Loss: {breakdown['waveguide_routing_losses']['wg_out_loss']:.1f} dB
  - Total Waveguide Routing Loss: {breakdown['waveguide_routing_losses']['total_wg_routing_loss']:.1f} dB
"""
        
        # Add architecture-specific losses
        arch_losses = breakdown['architecture_specific']
        for loss_type, value in arch_losses.items():
            # Only include total_tap_loss and not the removed keys
            if loss_type == 'total_tap_loss':
                report += f"  - {loss_type.replace('_', ' ').title()}: {value:.1f} dB\n"
            elif loss_type == 'note':
                report += f"  - {value}\n"
        
        # Add special handling for PSR and pol-control dual paths (they are identical)
        if self.effective_architecture in ['psr', 'pol_control'] and 'dual_path_components' in arch_losses:
            report += f"\nDual Path Architecture Details:\n"
            dual_paths = arch_losses['dual_path_components']
            report += f"  - TE/TE Path Loss: {dual_paths['te2te_path']['total_path_loss']:.2f} dB (psr_in + psr_out + tap losses)\n"
            report += f"    • PSR_in Loss: {dual_paths['te2te_path']['psr_in_loss']:.2f} dB\n"
            report += f"    • PSR_out Loss (TM2TE port): {dual_paths['te2te_path']['psr_out_loss']:.2f} dB\n"
            report += f"    • Tap Components: {dual_paths['te2te_path']['tap_loss']:.2f} dB\n"
            report += f"  - TM/TE Path Loss: {dual_paths['tm2te_path']['total_path_loss']:.2f} dB (psr_in + psr_out + tap losses)\n"
            report += f"    • PSR_in Loss: {dual_paths['tm2te_path']['psr_in_loss']:.2f} dB\n"
            report += f"    • PSR_out Loss (TE2TE port): {dual_paths['tm2te_path']['psr_out_loss']:.2f} dB\n"
            report += f"    • Tap Components: {dual_paths['tm2te_path']['tap_loss']:.2f} dB\n"
            report += f"  - Total Dual Path Loss (tap only): {arch_losses['total_dual_path_loss']:.2f} dB\n"
            
            # Add PSR-specific information
            if 'psr_in_loss' in arch_losses and 'psr_out_loss' in arch_losses:
                report += f"  - Connection Scheme: psr_out_tm2te→tap_out_te2te, psr_out_te2te→tap_out_tm2te\n"
            
            if 'note' in arch_losses:
                report += f"  - Note: {arch_losses['note']}\n"
        
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
        Calculate the target Pout required from each SOA based on the correct formula:
        Base Target Pout + SOA Penalty + Wavelength-margin (10*log10(num_wavelengths)) + Loss from SOA to output of Guide3A
        
        Args:
            num_wavelengths (int): Number of wavelengths
            target_pout_3sigma (float): Target Pout for 3σ case (optional)
            soa_penalty_3sigma (float): SOA penalty for 3σ case (optional)
            
        Returns:
            dict: Target Pout requirements for each SOA
        """
        if num_wavelengths <= 0:
            raise ValueError("Number of wavelengths must be positive")
        
        # Get loss breakdown
        loss_breakdown = self.get_loss_breakdown()
        
        # Calculate total loss from SOA to output of Guide3A
        # This includes ALL losses that occur after the SOA
        soa_to_output_loss = 0.0
        
        # Add waveguide routing output loss
        soa_to_output_loss += loss_breakdown['waveguide_routing_losses']['wg_out_loss']
        
        # Add optical connector output loss
        soa_to_output_loss += loss_breakdown['connector_losses']['connector_out_loss']
        
        # Add I/O output loss
        soa_to_output_loss += loss_breakdown['io_losses']['io_out_loss']
        
        # Add architecture-specific losses that occur after the SOA
        arch_losses = loss_breakdown['architecture_specific']
        if self.effective_architecture == 'psr':
            # In PSR architecture, SOA is before PSR, so add PSR loss
            soa_to_output_loss += arch_losses.get('total_psr_loss', 0)
            # Add tap_out_loss for the specific path (both TE/TE and TM/TE paths have tap_out_loss)
            # Since both paths have the same loss, we use the single path loss
            soa_to_output_loss += arch_losses.get('tap_out_loss', 0)
            # Note: waveguide_routing_out_loss is already included in the base calculation
        elif self.effective_architecture == 'pol_control':
            # In pol_control architecture, SOA is before PSR, phase shifter, and coupler
            soa_to_output_loss += arch_losses.get('total_psr_loss', 0)
            soa_to_output_loss += arch_losses.get('total_phase_shifter_loss', 0)
            soa_to_output_loss += arch_losses.get('total_coupler_loss', 0)
        elif self.effective_architecture == 'psrless':
            # In PSRless architecture, SOA is before tap components
            # Add only tap_out_loss (not total tap loss) since tap_in_loss occurs before SOA
            soa_to_output_loss += arch_losses.get('tap_out_loss', 0)
        
        # Calculate wavelength penalty: 10*log10(number_of_wavelengths)
        wavelength_penalty = 10 * math.log10(num_wavelengths)
        
        # Calculate SOA output requirements using the correct formula:
        median_soa_output = self.target_pout + self.soa_penalty + wavelength_penalty + soa_to_output_loss
        
        result = {
            'num_wavelengths': num_wavelengths,
            'wavelength_penalty_db': wavelength_penalty,
            'soa_to_output_loss_db': soa_to_output_loss,
            'median_case': {
                'base_target_pout_db': self.target_pout,
                'soa_penalty_db': self.soa_penalty,
                'wavelength_penalty_db': wavelength_penalty,
                'soa_to_output_loss_db': soa_to_output_loss,
                'soa_output_requirement_db': median_soa_output,
                'loss_breakdown': {
                    'wg_out_loss': loss_breakdown['waveguide_routing_losses']['wg_out_loss'],
                    'connector_out_loss': loss_breakdown['connector_losses']['connector_out_loss'],
                    'io_out_loss': loss_breakdown['io_losses']['io_out_loss'],
                    'architecture_loss': soa_to_output_loss - loss_breakdown['waveguide_routing_losses']['wg_out_loss'] - loss_breakdown['connector_losses']['connector_out_loss'] - loss_breakdown['io_losses']['io_out_loss']
                }
            }
        }
        
        # Add 3σ case if available
        if target_pout_3sigma is not None and soa_penalty_3sigma is not None:
            sigma_soa_output = target_pout_3sigma + soa_penalty_3sigma + wavelength_penalty + soa_to_output_loss
            result['sigma_case'] = {
                'base_target_pout_db': target_pout_3sigma,
                'soa_penalty_db': soa_penalty_3sigma,
                'wavelength_penalty_db': wavelength_penalty,
                'soa_to_output_loss_db': soa_to_output_loss,
                'soa_output_requirement_db': sigma_soa_output,
                'loss_breakdown': {
                    'wg_out_loss': loss_breakdown['waveguide_routing_losses']['wg_out_loss'],
                    'connector_out_loss': loss_breakdown['connector_losses']['connector_out_loss'],
                    'io_out_loss': loss_breakdown['io_losses']['io_out_loss'],
                    'architecture_loss': soa_to_output_loss - loss_breakdown['waveguide_routing_losses']['wg_out_loss'] - loss_breakdown['connector_losses']['connector_out_loss'] - loss_breakdown['io_losses']['io_out_loss']
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

    def calculate_pic_power_consumption(self, current_density_kA_cm2: float, soa_active_length_um: float, soa_width_um: float):
        """
        Calculate PIC power consumption for a given current density.
        
        Args:
            current_density_kA_cm2 (float): Current density in kA/cm²
            soa_active_length_um (float): SOA active length in µm
            soa_width_um (float): SOA width in µm
            
        Returns:
            dict: PIC power consumption details
        """
        try:
            # Create SOA instance for power calculations
            soa = EuropaSOA(L_active_um=soa_active_length_um, W_um=soa_width_um, verbose=False)
            
            # Calculate current and voltage for this current density
            current_ma = soa.calculate_current_mA_from_J(current_density_kA_cm2)
            operating_voltage_v = soa.get_operating_voltage(current_ma)
            electrical_power_mw = current_ma * operating_voltage_v
            
            # Calculate total PIC power consumption
            # Number of SOAs per PIC is typically 20, but we'll use the actual number from module config
            soas_per_pic = 20  # Standard SOAs per PIC
            total_pic_power_mw = soas_per_pic * electrical_power_mw
            
            return {
                'current_ma': current_ma,
                'operating_voltage_v': operating_voltage_v,
                'electrical_power_mw': electrical_power_mw,
                'soas_per_pic': soas_per_pic,
                'total_pic_power_mw': total_pic_power_mw
            }
        except Exception as e:
            return {'error': str(e)}

    def calculate_pic_efficiency_and_heat_load(self, target_pout_db: float, total_pic_power_mw: float, fibers_per_pic: int = 20):
        """
        Calculate PIC efficiency and heat load.
        
        Args:
            target_pout_db (float): Target Pout in dBm
            total_pic_power_mw (float): Total PIC power consumption in mW
            fibers_per_pic (int): Number of fibers per PIC (default: 20)
            
        Returns:
            dict: PIC efficiency and heat load details
        """
        try:
            # Convert target Pout from dBm to mW
            target_pout_mw = 10**(target_pout_db / 10.0)
            
            # Calculate total optical output power (Target Pout * number of fibers per PIC)
            total_optical_power_mw = target_pout_mw * fibers_per_pic
            
            # Calculate PIC efficiency as percentage
            pic_efficiency_percent = (total_optical_power_mw / total_pic_power_mw) * 100 if total_pic_power_mw > 0 else 0
            
            # Calculate heat load (Total PIC Power - Total Optical Power)
            heat_load_mw = total_pic_power_mw - total_optical_power_mw
            heat_load_w = heat_load_mw / 1000.0
            
            return {
                'target_pout_mw': target_pout_mw,
                'total_optical_power_mw': total_optical_power_mw,
                'pic_efficiency_percent': pic_efficiency_percent,
                'heat_load_mw': heat_load_mw,
                'heat_load_w': heat_load_w
            }
        except Exception as e:
            return {'error': str(e)}

    def calculate_module_performance(self, pic_power_data: dict, pic_efficiency_data: dict, case_name: str = "Median"):
        """
        Calculate comprehensive module performance including all power components.
        
        Args:
            pic_power_data (dict): PIC power consumption data
            pic_efficiency_data (dict): PIC efficiency and heat load data
            case_name (str): Case name ("Median" or "3σ")
            
        Returns:
            dict: Comprehensive module performance details
        """
        try:
            if 'error' in pic_power_data or 'error' in pic_efficiency_data:
                return {'error': 'PIC performance data not available'}
            
            # Get module configuration
            module_config = self.get_module_configuration()
            num_unit_cells = module_config['num_unit_cells']
            num_soas_per_pic = 20  # Standard SOAs per PIC
            
            # Get PIC power and current data
            pic_power_w = pic_power_data['total_pic_power_mw'] / 1000.0
            soa_current_ma = pic_power_data['current_ma']
            soa_operating_voltage_v = pic_power_data['operating_voltage_v']
            
            # Get heat load per PIC
            heat_load_per_pic_w = pic_efficiency_data['heat_load_w']
            
            # 1. Digital Core Power Consumption = (Driver Peripheral power + MCU power consumption + MISC power consumption) * Number of Unit Cells / Digital Core Efficiency
            digital_core_efficiency = self.digital_core_efficiency / 100.0  # Convert to decimal
            digital_core_power_w = ((self.driver_peripherals_power + self.mcu_power + self.misc_power) * 
                                   num_unit_cells / digital_core_efficiency)
            
            # 2. Analog Core Power Consumption = (max(PIC operating voltage) + IDAC Voltage Overhead + IR drop) * max(SOA current) * number of SOA per PIC * number of unit cells / VRM Efficiency
            # Use appropriate IR drop based on case
            ir_drop = self.ir_drop_3sigma if case_name == "3σ" else self.ir_drop_nominal
            vrm_efficiency = self.vrm_efficiency / 100.0  # Convert to decimal
            analog_core_power_w = ((soa_operating_voltage_v + self.idac_voltage_overhead + ir_drop) * 
                                  soa_current_ma * num_soas_per_pic * num_unit_cells / vrm_efficiency/1000)
            
            # 3. Thermal Power Consumption = Heat load per PIC * number of unit cells / TEC COP / TEC Power Efficiency
            # Use appropriate TEC COP based on case
            tec_cop = self.tec_cop_3sigma if case_name == "3σ" else self.tec_cop_nominal
            tec_power_efficiency = self.tec_power_efficiency / 100.0  # Convert to decimal
            thermal_power_w = (heat_load_per_pic_w * num_unit_cells / tec_cop / tec_power_efficiency)
            
            # 4. Total Module Power Consumption = Digital Core Power Consumption + Analog Core Power Consumption + Thermal Power Consumption
            total_module_power_w = digital_core_power_w + analog_core_power_w + thermal_power_w
            
            # Calculate module efficiency (optical power / total module power)
            total_optical_power_w = pic_efficiency_data['total_optical_power_mw'] / 1000.0
            module_efficiency_percent = (total_optical_power_w / total_module_power_w) * 100 if total_module_power_w > 0 else 0
            
            # Calculate total heat load (total module power - optical power)
            total_heat_load_w = total_module_power_w - total_optical_power_w
            
            return {
                'pic_power_w': pic_power_w,
                'digital_core_power_w': digital_core_power_w,
                'analog_core_power_w': analog_core_power_w,
                'thermal_power_w': thermal_power_w,
                'driver_peripherals_power_w': self.driver_peripherals_power,
                'mcu_power_w': self.mcu_power,
                'misc_power_w': self.misc_power,
                'total_module_power_w': total_module_power_w,
                'total_optical_power_w': total_optical_power_w,
                'module_efficiency_percent': module_efficiency_percent,
                'total_heat_load_w': total_heat_load_w,
                'case_name': case_name,
                'num_unit_cells': num_unit_cells
            }
        except Exception as e:
            return {'error': str(e)}

    def calculate_comprehensive_performance(self, num_wavelengths: int, target_pout_3sigma: float | None = None, 
                                          soa_penalty_3sigma: float | None = None, wavelengths: list[float] | None = None,
                                          soa_active_length_um: float | None = None, soa_width_um: float | None = None):
        """
        Calculate comprehensive performance including PIC and module performance for both median and 3σ cases.
        
        Args:
            num_wavelengths (int): Number of wavelengths
            target_pout_3sigma (float): Target Pout for 3σ case (optional)
            soa_penalty_3sigma (float): SOA penalty for 3σ case (optional)
            wavelengths (list[float]): List of wavelengths in nm (optional)
            soa_active_length_um (float): SOA active length in µm (optional, uses default if None)
            soa_width_um (float): SOA width in µm (optional, uses default if None)
            
        Returns:
            dict: Comprehensive performance analysis for both cases
        """
        # Use default SOA parameters if not provided
        if soa_active_length_um is None:
            soa_active_length_um = self.soa_active_length_um
        if soa_width_um is None:
            soa_width_um = self.soa_width_um
        
        # Ensure SOA parameters are valid
        if soa_active_length_um is None or soa_width_um is None:
            raise ValueError("SOA parameters must be provided or available in the Guide3A instance")
        
        # Get target Pout calculations
        target_pout_calculation = self.calculate_target_pout_all_wavelengths(
            num_wavelengths=num_wavelengths,
            target_pout_3sigma=target_pout_3sigma,
            soa_penalty_3sigma=soa_penalty_3sigma
        )
        
        # Get optimum current density calculations
        optimum_current_calculation = self.estimate_optimum_soa_current_density(
            num_wavelengths=num_wavelengths,
            target_pout_3sigma=target_pout_3sigma,
            soa_penalty_3sigma=soa_penalty_3sigma,
            wavelengths=wavelengths
        )
        
        # Calculate PIC power consumption for median case
        median_pic_power = self.calculate_pic_power_consumption(
            optimum_current_calculation['median_case']['current_density_kA_cm2'],
            soa_active_length_um,
            soa_width_um
        )
        
        # Calculate PIC efficiency for median case
        median_pic_efficiency = None
        if 'error' not in median_pic_power and 'total_pic_power_mw' in median_pic_power:
            median_pic_efficiency = self.calculate_pic_efficiency_and_heat_load(
                target_pout_calculation['median_case']['total_target_pout_db'],
                float(median_pic_power['total_pic_power_mw'])
            )
        
        # Calculate module performance for median case
        median_module_performance = None
        if median_pic_efficiency and 'error' not in median_pic_efficiency:
            median_module_performance = self.calculate_module_performance(
                median_pic_power, median_pic_efficiency, "Median"
            )
        
        # Initialize result structure
        result = {
            'num_wavelengths': num_wavelengths,
            'wavelengths_nm': wavelengths,
            'target_pout_calculation': target_pout_calculation,
            'optimum_current_calculation': optimum_current_calculation,
            'median_case': {
                'pic_power': median_pic_power,
                'pic_efficiency': median_pic_efficiency,
                'module_performance': median_module_performance
            }
        }
        
        # Calculate for 3σ case if available
        if (target_pout_calculation['sigma_case'] is not None and 
            optimum_current_calculation['sigma_case'] is not None):
            
            # Calculate PIC power consumption for 3σ case
            sigma_pic_power = self.calculate_pic_power_consumption(
                optimum_current_calculation['sigma_case']['current_density_kA_cm2'],
                soa_active_length_um,
                soa_width_um
            )
            
            # Calculate PIC efficiency for 3σ case
            sigma_pic_efficiency = None
            if 'error' not in sigma_pic_power and 'total_pic_power_mw' in sigma_pic_power:
                sigma_pic_efficiency = self.calculate_pic_efficiency_and_heat_load(
                    target_pout_calculation['sigma_case']['total_target_pout_db'],
                    float(sigma_pic_power['total_pic_power_mw'])
                )
            
            # Calculate module performance for 3σ case
            sigma_module_performance = None
            if sigma_pic_efficiency and 'error' not in sigma_pic_efficiency:
                sigma_module_performance = self.calculate_module_performance(
                    sigma_pic_power, sigma_pic_efficiency, "3σ"
                )
            
            result['sigma_case'] = {
                'pic_power': sigma_pic_power,
                'pic_efficiency': sigma_pic_efficiency,
                'module_performance': sigma_module_performance
            }
        
        return result 

    def get_total_loss_by_polarization_case(self, polarization_case: str = 'mixed'):
        """
        Calculate total loss for different polarization cases in PSR architecture.
        
        Args:
            polarization_case (str): 'pure_te', 'pure_tm', or 'mixed' (50% TE, 50% TM)
            
        Returns:
            dict: Total loss and breakdown for the specified polarization case
        """
        if self.effective_architecture != 'psr':
            return {'error': 'Polarization case analysis only applies to PSR architecture'}
        
        if polarization_case not in ['pure_te', 'pure_tm', 'mixed']:
            return {'error': 'Polarization case must be pure_te, pure_tm, or mixed'}
        
        # Start with base losses (shared across all cases)
        base_loss = self.connector_in_loss + self.connector_out_loss  # 0.50 dB
        base_loss += self.io_in_loss + self.io_out_loss  # 3.00 dB
        base_loss += self.wg_in_loss + self.wg_out_loss  # 0.50 dB
        
        # Calculate PSR losses based on polarization case
        if polarization_case == 'pure_te':
            # Pure TE: all light goes TE->TE path with 0.37dB loss per PSR
            psr_loss = 2 * self.psr_loss_te  # PSR_in + PSR_out
            path_description = "Pure TE polarization: all light follows TE->TE path"
            
        elif polarization_case == 'pure_tm':
            # Pure TM: all light goes TM->TE path with 0.93dB loss per PSR
            psr_loss = 2 * self.psr_loss_tm  # PSR_in + PSR_out
            path_description = "Pure TM polarization: all light follows TM->TE path"
            
        else:  # mixed case
            # 50% TE, 50% TM: need to properly average in linear power domain
            # Convert dB losses to linear transmission
            te_transmission = 10**(-self.psr_loss_te / 10)
            tm_transmission = 10**(-self.psr_loss_tm / 10)
            
            # Average the linear transmissions (50% each)
            avg_transmission = (te_transmission + tm_transmission) / 2
            
            # Convert back to dB loss
            avg_psr_loss = -10 * math.log10(avg_transmission)
            
            # Total PSR loss for both PSR devices
            psr_loss = 2 * avg_psr_loss
            
            path_description = "Mixed polarization (50% TE, 50% TM): properly averaged in linear power domain"
        
        # Add dual path components (same for all cases since both paths are always present)
        dual_path_loss = 2 * (self.wg_in_loss + self.wg_out_loss + self.tap_in_loss + self.tap_out_loss)
        
        total_loss = base_loss + psr_loss + dual_path_loss
        
        return {
            'polarization_case': polarization_case,
            'path_description': path_description,
            'base_loss': base_loss,
            'psr_loss': psr_loss,
            'dual_path_loss': dual_path_loss,
            'total_loss': total_loss,
            'loss_breakdown': {
                'connector_losses': self.connector_in_loss + self.connector_out_loss,
                'io_losses': self.io_in_loss + self.io_out_loss,
                'base_waveguide_routing': self.wg_in_loss + self.wg_out_loss,
                'psr_loss_te': self.psr_loss_te,
                'psr_loss_tm': self.psr_loss_tm,
                'dual_path_components': dual_path_loss
            }
        }

    def compare_polarization_cases(self):
        """
        Compare total loss for all three polarization cases in PSR architecture.
        
        Returns:
            dict: Comparison of losses for pure TE, pure TM, and mixed polarization cases
        """
        if self.effective_architecture != 'psr':
            return {'error': 'Polarization case comparison only applies to PSR architecture'}
        
        # Calculate losses for all three cases
        pure_te = self.get_total_loss_by_polarization_case('pure_te')
        pure_tm = self.get_total_loss_by_polarization_case('pure_tm')
        mixed = self.get_total_loss_by_polarization_case('mixed')
        
        if 'error' in pure_te or 'error' in pure_tm or 'error' in mixed:
            return {'error': 'Failed to calculate one or more polarization cases'}
        
        # Calculate differences
        te_vs_tm_diff = pure_te['total_loss'] - pure_tm['total_loss']
        te_vs_mixed_diff = pure_te['total_loss'] - mixed['total_loss']
        tm_vs_mixed_diff = pure_tm['total_loss'] - mixed['total_loss']
        
        return {
            'polarization_cases': {
                'pure_te': pure_te,
                'pure_tm': pure_tm,
                'mixed': mixed
            },
            'comparison': {
                'te_vs_tm_difference_db': te_vs_tm_diff,
                'te_vs_mixed_difference_db': te_vs_mixed_diff,
                'tm_vs_mixed_difference_db': tm_vs_mixed_diff,
                'best_case': 'pure_te' if pure_te['total_loss'] < pure_tm['total_loss'] else 'pure_tm',
                'worst_case': 'pure_tm' if pure_tm['total_loss'] > pure_te['total_loss'] else 'pure_te'
            },
            'summary': {
                'lowest_loss': min(pure_te['total_loss'], pure_tm['total_loss'], mixed['total_loss']),
                'highest_loss': max(pure_te['total_loss'], pure_tm['total_loss'], mixed['total_loss']),
                'loss_range': max(pure_te['total_loss'], pure_tm['total_loss'], mixed['total_loss']) - min(pure_te['total_loss'], pure_tm['total_loss'], mixed['total_loss'])
            }
        }

    def get_psr_loss_for_te_polarization_degree(self, te_percentage: float):
        """
        Calculate PSR loss for any degree of TE polarization from 0% to 100%.
        
        Args:
            te_percentage (float): Percentage of TE polarization (0.0 to 100.0)
            
        Returns:
            dict: PSR loss calculation for the specified TE polarization degree
        """
        if self.effective_architecture != 'psr':
            return {'error': 'Polarization degree analysis only applies to PSR architecture'}
        
        if not (0.0 <= te_percentage <= 100.0):
            return {'error': 'TE percentage must be between 0.0 and 100.0'}
        
        # Calculate TM percentage
        tm_percentage = 100.0 - te_percentage
        
        # Convert percentages to fractions
        te_fraction = te_percentage / 100.0
        tm_fraction = tm_percentage / 100.0
        
        # Convert dB losses to linear transmission
        te_transmission = 10**(-self.psr_loss_te / 10)
        tm_transmission = 10**(-self.psr_loss_tm / 10)
        
        # Weighted average in linear domain
        weighted_transmission = (te_fraction * te_transmission) + (tm_fraction * tm_transmission)
        
        # Convert back to dB loss
        avg_psr_loss = -10 * math.log10(weighted_transmission)
        
        # Total PSR loss for both PSR devices
        total_psr_loss = 2 * avg_psr_loss
        
        return {
            'te_percentage': te_percentage,
            'tm_percentage': tm_percentage,
            'te_fraction': te_fraction,
            'tm_fraction': tm_fraction,
            'te_transmission': te_transmission,
            'tm_transmission': tm_transmission,
            'weighted_transmission': weighted_transmission,
            'avg_psr_loss_per_device': avg_psr_loss,
            'total_psr_loss': total_psr_loss,
            'description': f"{te_percentage:.1f}% TE, {tm_percentage:.1f}% TM polarization"
        }

    def analyze_psr_loss_vs_te_polarization(self, step_size: float = 5.0):
        """
        Analyze PSR loss across the full range of TE polarization degrees.
        
        Args:
            step_size (float): Step size for TE percentage (default: 5.0%)
            
        Returns:
            dict: Comprehensive analysis of PSR loss vs TE polarization degree
        """
        if self.effective_architecture != 'psr':
            return {'error': 'Polarization analysis only applies to PSR architecture'}
        
        if step_size <= 0 or step_size > 100:
            return {'error': 'Step size must be between 0 and 100'}
        
        # Generate TE percentages from 0% to 100%
        te_percentages = []
        current_te = 0.0
        while current_te <= 100.0:
            te_percentages.append(current_te)
            current_te += step_size
        
        # Ensure we include exactly 100%
        if te_percentages[-1] != 100.0:
            te_percentages.append(100.0)
        
        # Calculate PSR loss for each TE percentage
        results = []
        for te_pct in te_percentages:
            result = self.get_psr_loss_for_te_polarization_degree(te_pct)
            if 'error' not in result:
                results.append(result)
        
        # Find minimum and maximum losses
        if results:
            min_loss_result = min(results, key=lambda x: x['total_psr_loss'])
            max_loss_result = max(results, key=lambda x: x['total_psr_loss'])
            
            # Calculate total system loss for each case
            base_loss = (self.connector_in_loss + self.connector_out_loss + 
                        self.io_in_loss + self.io_out_loss + 
                        self.wg_in_loss + self.wg_out_loss)
            dual_path_loss = 2 * (self.wg_in_loss + self.wg_out_loss + 
                                 self.tap_in_loss + self.tap_out_loss)
            
            min_total_loss = base_loss + min_loss_result['total_psr_loss'] + dual_path_loss
            max_total_loss = base_loss + max_loss_result['total_psr_loss'] + dual_path_loss
            
            return {
                'step_size': step_size,
                'te_percentages': te_percentages,
                'results': results,
                'analysis': {
                    'min_psr_loss': {
                        'te_percentage': min_loss_result['te_percentage'],
                        'total_psr_loss': min_loss_result['total_psr_loss'],
                        'total_system_loss': min_total_loss,
                        'description': min_loss_result['description']
                    },
                    'max_psr_loss': {
                        'te_percentage': max_loss_result['te_percentage'],
                        'total_psr_loss': max_loss_result['total_psr_loss'],
                        'total_system_loss': max_total_loss,
                        'description': max_loss_result['description']
                    },
                    'loss_range': {
                        'psr_loss_range': max_loss_result['total_psr_loss'] - min_loss_result['total_psr_loss'],
                        'total_system_loss_range': max_total_loss - min_total_loss
                    }
                },
                'base_loss_components': {
                    'connector_losses': self.connector_in_loss + self.connector_out_loss,
                    'io_losses': self.io_in_loss + self.io_out_loss,
                    'base_waveguide_routing': self.wg_in_loss + self.wg_out_loss,
                    'dual_path_components': dual_path_loss,
                    'total_base_loss': base_loss + dual_path_loss
                }
            }
        else:
            return {'error': 'No valid results generated'}

    def calculate_soa_power_requirements_for_polarization(self, target_pout_db: float, te_percentage: float, 
                                                        num_wavelengths: int = 1, target_pout_3sigma: float | None = None, 
                                                        soa_penalty_3sigma: float | None = None):
        """
        Calculate required SOA output power for both TE/TE and TM/TE paths given a specific polarization fraction.
        
        This method determines how much power each SOA needs to output to achieve the target Pout
        considering the polarization-dependent PSR losses and the power splitting between paths.
        
        Args:
            target_pout_db (float): Target output power in dBm
            te_percentage (float): Percentage of TE polarization (0.0 to 100.0)
            num_wavelengths (int): Number of wavelengths (default: 1)
            target_pout_3sigma (float): Target Pout for 3σ case (optional)
            soa_penalty_3sigma (float): SOA penalty for 3σ case (optional)
            
        Returns:
            dict: SOA power requirements for both paths and polarization analysis
        """
        if self.effective_architecture != 'psr':
            return {'error': 'SOA power analysis only applies to PSR architecture'}
        
        if not (0.0 <= te_percentage <= 100.0):
            return {'error': 'TE percentage must be between 0.0 and 100.0'}
        
        if num_wavelengths <= 0:
            return {'error': 'Number of wavelengths must be positive'}
        
        # Calculate TM percentage
        tm_percentage = 100.0 - te_percentage
        te_fraction = te_percentage / 100.0
        tm_fraction = tm_percentage / 100.0
        
        # Use the configured TE polarization fraction
        effective_te_fraction = self.te_polarization_fraction
        effective_tm_fraction = 1.0 - self.te_polarization_fraction
        
        # Calculate wavelength penalty
        wavelength_penalty = 10 * math.log10(num_wavelengths)
        
        # Get PSR loss for this polarization fraction
        psr_analysis = self.get_psr_loss_for_te_polarization_degree(te_percentage)
        if 'error' in psr_analysis:
            return psr_analysis
        
        # Calculate losses from SOA to output for each path
        # Base losses that occur after SOA (same for both paths)
        base_soa_to_output_loss = (self.wg_out_loss + self.connector_out_loss + 
                                  self.io_out_loss + self.tap_out_loss)
        
        # PSR output loss with connection swap:
        # - TE/TE path: uses psr_out_tm2te (connects to tap_out_te2te)
        # - TM/TE path: uses psr_out_te2te (connects to tap_out_tm2te)
        te2te_psr_out_loss = self.psr_loss_tm  # TM2TE port connects to TE2TE path
        tm2te_psr_out_loss = self.psr_loss_te  # TE2TE port connects to TM2TE path
        
        # Calculate total loss from SOA to output for each path
        te2te_soa_to_output_loss = base_soa_to_output_loss + te2te_psr_out_loss
        tm2te_soa_to_output_loss = base_soa_to_output_loss + tm2te_psr_out_loss
        
        # Calculate required SOA output power for each path
        # Formula: Target Pout + Wavelength Penalty + SOA Penalty + Loss from SOA to Output
        te2te_soa_output_required = (target_pout_db + wavelength_penalty + 
                                   self.soa_penalty + te2te_soa_to_output_loss)
        tm2te_soa_output_required = (target_pout_db + wavelength_penalty + 
                                   self.soa_penalty + tm2te_soa_to_output_loss)
        
        # Calculate power splitting effect
        # The power in each path is reduced by the polarization fraction
        te2te_power_reduction_db = -10 * math.log10(effective_te_fraction) if effective_te_fraction > 0 else float('inf')
        tm2te_power_reduction_db = -10 * math.log10(effective_tm_fraction) if effective_tm_fraction > 0 else float('inf')
        
        # Final SOA output requirements considering power splitting
        te2te_soa_output_final = te2te_soa_output_required + te2te_power_reduction_db
        tm2te_soa_output_final = tm2te_soa_output_required + tm2te_power_reduction_db
        
        result = {
            'input_parameters': {
                'target_pout_db': target_pout_db,
                'te_percentage': te_percentage,
                'tm_percentage': tm_percentage,
                'te_fraction': te_fraction,
                'tm_fraction': tm_fraction,
                'te_polarization_fraction': self.te_polarization_fraction,
                'num_wavelengths': num_wavelengths,
                'wavelength_penalty_db': wavelength_penalty
            },
            'effective_polarization_analysis': {
                'input_parameters': {
                    'te_percentage': te_percentage,
                    'tm_percentage': tm_percentage,
                    'te_polarization_fraction': self.te_polarization_fraction
                },
                'polarized_components': {
                    'te_fraction': te_fraction,
                    'tm_fraction': tm_fraction,
                    'polarized_te_fraction': effective_te_fraction,
                    'polarized_tm_fraction': effective_tm_fraction,
                    'unpolarized_fraction': 1.0 - self.te_polarization_fraction
                },
                'effective_fractions': {
                    'effective_te_fraction': effective_te_fraction,
                    'effective_tm_fraction': effective_tm_fraction,
                    'effective_te_percentage': effective_te_fraction * 100.0,
                    'effective_tm_percentage': effective_tm_fraction * 100.0
                },
                'description': f"TE fraction={self.te_polarization_fraction:.2f}: effective TE={effective_te_fraction*100:.1f}%, TM={effective_tm_fraction*100:.1f}%"
            },
            'psr_analysis': psr_analysis,
            'loss_analysis': {
                'base_soa_to_output_loss': base_soa_to_output_loss,
                'te2te_psr_out_loss': te2te_psr_out_loss,
                'tm2te_psr_out_loss': tm2te_psr_out_loss,
                'te2te_soa_to_output_loss': te2te_soa_to_output_loss,
                'tm2te_soa_to_output_loss': tm2te_soa_to_output_loss
            },
            'power_splitting_analysis': {
                'te2te_power_reduction_db': te2te_power_reduction_db,
                'tm2te_power_reduction_db': tm2te_power_reduction_db,
                'effective_te_fraction': effective_te_fraction,
                'effective_tm_fraction': effective_tm_fraction
            },
            'soa_requirements': {
                'te2te_path': {
                    'soa_output_required_db': te2te_soa_output_required,
                    'soa_output_final_db': te2te_soa_output_final,
                    'power_required_mw': 10**(te2te_soa_output_final / 10) if te2te_soa_output_final != float('inf') else 0,
                    'is_active': effective_te_fraction > 0
                },
                'tm2te_path': {
                    'soa_output_required_db': tm2te_soa_output_required,
                    'soa_output_final_db': tm2te_soa_output_final,
                    'power_required_mw': 10**(tm2te_soa_output_final / 10) if tm2te_soa_output_final != float('inf') else 0,
                    'is_active': effective_tm_fraction > 0
                }
            },
            'summary': {
                'total_soa_power_mw': (10**(te2te_soa_output_final / 10) if te2te_soa_output_final != float('inf') else 0) +
                                     (10**(tm2te_soa_output_final / 10) if tm2te_soa_output_final != float('inf') else 0),
                'max_soa_output_db': max(te2te_soa_output_final, tm2te_soa_output_final) if te2te_soa_output_final != float('inf') and tm2te_soa_output_final != float('inf') else (
                    te2te_soa_output_final if te2te_soa_output_final != float('inf') else tm2te_soa_output_final
                ),
                'description': f"TE/TE path requires {te2te_soa_output_final:.2f} dBm, TM/TE path requires {tm2te_soa_output_final:.2f} dBm for {te_percentage:.1f}% TE polarization (TE fraction={self.te_polarization_fraction:.2f})"
            }
        }
        
        # Add 3σ case if provided
        if target_pout_3sigma is not None and soa_penalty_3sigma is not None:
            sigma_wavelength_penalty = 10 * math.log10(num_wavelengths)
            
            te2te_soa_output_sigma = (target_pout_3sigma + sigma_wavelength_penalty + 
                                    soa_penalty_3sigma + te2te_soa_to_output_loss + te2te_power_reduction_db)
            tm2te_soa_output_sigma = (target_pout_3sigma + sigma_wavelength_penalty + 
                                    soa_penalty_3sigma + tm2te_soa_to_output_loss + tm2te_power_reduction_db)
            
            result['sigma_case'] = {
                'te2te_path': {
                    'soa_output_required_db': target_pout_3sigma + sigma_wavelength_penalty + soa_penalty_3sigma + te2te_soa_to_output_loss,
                    'soa_output_final_db': te2te_soa_output_sigma,
                    'power_required_mw': 10**(te2te_soa_output_sigma / 10) if te2te_soa_output_sigma != float('inf') else 0
                },
                'tm2te_path': {
                    'soa_output_required_db': target_pout_3sigma + sigma_wavelength_penalty + soa_penalty_3sigma + tm2te_soa_to_output_loss,
                    'soa_output_final_db': tm2te_soa_output_sigma,
                    'power_required_mw': 10**(tm2te_soa_output_sigma / 10) if tm2te_soa_output_sigma != float('inf') else 0
                }
            }
        
        return result

    # Pol-Control Architecture Methods (copied from PSR with adaptations)
    
    def get_pol_control_loss_for_te_polarization_degree(self, te_percentage: float):
        """
        Calculate pol-control loss for any degree of TE polarization from 0% to 100%.
        
        Args:
            te_percentage (float): Percentage of TE polarization (0.0 to 100.0)
            
        Returns:
            dict: Pol-control loss calculation for the specified TE polarization degree
        """
        if self.effective_architecture != 'pol_control':
            return {'error': 'Polarization degree analysis only applies to pol_control architecture'}
        
        if not (0.0 <= te_percentage <= 100.0):
            return {'error': 'TE percentage must be between 0.0 and 100.0'}
        
        # Calculate TM percentage
        tm_percentage = 100.0 - te_percentage
        
        # Convert percentages to fractions
        te_fraction = te_percentage / 100.0
        tm_fraction = tm_percentage / 100.0
        
        # Convert dB losses to linear transmission
        te_transmission = 10**(-self.psr_loss_te / 10)
        tm_transmission = 10**(-self.psr_loss_tm / 10)
        
        # Weighted average in linear domain
        weighted_transmission = (te_fraction * te_transmission) + (tm_fraction * tm_transmission)
        
        # Convert back to dB loss
        avg_psr_loss = -10 * math.log10(weighted_transmission)
        
        # Total PSR loss for both PSR devices
        total_psr_loss = 2 * avg_psr_loss
        
        # Add phase shifter and coupler losses (same for both paths)
        total_phase_shifter_loss = 2 * self.phase_shifter_loss
        total_coupler_loss = 2 * self.coupler_loss
        
        # Total pol-control specific loss
        total_pol_control_loss = total_psr_loss + total_phase_shifter_loss + total_coupler_loss
        
        return {
            'te_percentage': te_percentage,
            'tm_percentage': tm_percentage,
            'te_fraction': te_fraction,
            'tm_fraction': tm_fraction,
            'te_transmission': te_transmission,
            'tm_transmission': tm_transmission,
            'weighted_transmission': weighted_transmission,
            'avg_psr_loss_per_device': avg_psr_loss,
            'total_psr_loss': total_psr_loss,
            'total_phase_shifter_loss': total_phase_shifter_loss,
            'total_coupler_loss': total_coupler_loss,
            'total_pol_control_loss': total_pol_control_loss,
            'description': f"{te_percentage:.1f}% TE, {tm_percentage:.1f}% TM polarization with pol-control components"
        }

    def analyze_pol_control_loss_vs_te_polarization(self, step_size: float = 5.0):
        """
        Analyze pol-control loss across the full range of TE polarization degrees.
        
        Args:
            step_size (float): Step size for TE percentage (default: 5.0%)
            
        Returns:
            dict: Comprehensive analysis of pol-control loss vs TE polarization degree
        """
        if self.effective_architecture != 'pol_control':
            return {'error': 'Polarization analysis only applies to pol_control architecture'}
        
        if step_size <= 0 or step_size > 100:
            return {'error': 'Step size must be between 0 and 100'}
        
        # Generate TE percentages from 0% to 100%
        te_percentages = []
        current_te = 0.0
        while current_te <= 100.0:
            te_percentages.append(current_te)
            current_te += step_size
        
        # Ensure we include exactly 100%
        if te_percentages[-1] != 100.0:
            te_percentages.append(100.0)
        
        # Calculate pol-control loss for each TE percentage
        results = []
        for te_pct in te_percentages:
            result = self.get_pol_control_loss_for_te_polarization_degree(te_pct)
            if 'error' not in result:
                results.append(result)
        
        # Find minimum and maximum losses
        if results:
            min_loss_result = min(results, key=lambda x: x['total_pol_control_loss'])
            max_loss_result = max(results, key=lambda x: x['total_pol_control_loss'])
            
            # Calculate total system loss for each case
            base_loss = (self.connector_in_loss + self.connector_out_loss + 
                        self.io_in_loss + self.io_out_loss + 
                        self.wg_in_loss + self.wg_out_loss)
            
            min_total_loss = base_loss + min_loss_result['total_pol_control_loss']
            max_total_loss = base_loss + max_loss_result['total_pol_control_loss']
            
            return {
                'step_size': step_size,
                'te_percentages': te_percentages,
                'results': results,
                'analysis': {
                    'min_pol_control_loss': {
                        'te_percentage': min_loss_result['te_percentage'],
                        'total_pol_control_loss': min_loss_result['total_pol_control_loss'],
                        'total_system_loss': min_total_loss,
                        'description': min_loss_result['description']
                    },
                    'max_pol_control_loss': {
                        'te_percentage': max_loss_result['te_percentage'],
                        'total_pol_control_loss': max_loss_result['total_pol_control_loss'],
                        'total_system_loss': max_total_loss,
                        'description': max_loss_result['description']
                    },
                    'loss_range': {
                        'pol_control_loss_range': max_loss_result['total_pol_control_loss'] - min_loss_result['total_pol_control_loss'],
                        'total_system_loss_range': max_total_loss - min_total_loss
                    }
                },
                'base_loss_components': {
                    'connector_losses': self.connector_in_loss + self.connector_out_loss,
                    'io_losses': self.io_in_loss + self.io_out_loss,
                    'base_waveguide_routing': self.wg_in_loss + self.wg_out_loss,
                    'total_base_loss': base_loss
                }
            }
        else:
            return {'error': 'No valid results generated'}

    def calculate_soa_power_requirements_for_pol_control(self, target_pout_db: float, te_percentage: float, 
                                                        num_wavelengths: int = 1, target_pout_3sigma: float | None = None, 
                                                        soa_penalty_3sigma: float | None = None):
        """
        Calculate required SOA output power for pol-control architecture given a specific polarization fraction.
        
        This method determines how much power the SOA needs to output to achieve the target Pout
        considering the polarization-dependent pol-control losses.
        
        Args:
            target_pout_db (float): Target output power in dBm
            te_percentage (float): Percentage of TE polarization (0.0 to 100.0)
            num_wavelengths (int): Number of wavelengths (default: 1)
            target_pout_3sigma (float | None): Target Pout for 3σ case (optional)
            soa_penalty_3sigma (float | None): SOA penalty for 3σ case (optional)
            
        Returns:
            dict: SOA power requirements and polarization analysis for pol-control
        """
        if self.effective_architecture != 'pol_control':
            return {'error': 'SOA power analysis only applies to pol_control architecture'}
        
        if not (0.0 <= te_percentage <= 100.0):
            return {'error': 'TE percentage must be between 0.0 and 100.0'}
        
        if num_wavelengths <= 0:
            return {'error': 'Number of wavelengths must be positive'}
        
        # Calculate TM percentage
        tm_percentage = 100.0 - te_percentage
        te_fraction = te_percentage / 100.0
        tm_fraction = tm_percentage / 100.0
        
        # Use the configured TE polarization fraction
        effective_te_fraction = self.te_polarization_fraction
        effective_tm_fraction = 1.0 - self.te_polarization_fraction
        
        # Calculate wavelength penalty
        wavelength_penalty = 10 * math.log10(num_wavelengths)
        
        # Get pol-control loss for this polarization fraction
        pol_control_analysis = self.get_pol_control_loss_for_te_polarization_degree(te_percentage)
        if 'error' in pol_control_analysis:
            return pol_control_analysis
        
        # Calculate losses from SOA to output
        # Base losses that occur after SOA
        base_soa_to_output_loss = (self.wg_out_loss + self.connector_out_loss + 
                                  self.io_out_loss)
        
        # Pol-control specific losses (PSR + Phase Shifter + Coupler)
        pol_control_loss = pol_control_analysis['total_pol_control_loss']
        
        # Calculate total loss from SOA to output
        total_soa_to_output_loss = base_soa_to_output_loss + pol_control_loss
        
        # Calculate required SOA output power
        # Formula: Target Pout + Wavelength Penalty + SOA Penalty + Loss from SOA to Output
        soa_output_required = (target_pout_db + wavelength_penalty + 
                             self.soa_penalty + total_soa_to_output_loss)
        
        result = {
            'input_parameters': {
                'target_pout_db': target_pout_db,
                'te_percentage': te_percentage,
                'tm_percentage': tm_percentage,
                'te_fraction': te_fraction,
                'tm_fraction': tm_fraction,
                'te_polarization_fraction': self.te_polarization_fraction,
                'num_wavelengths': num_wavelengths,
                'wavelength_penalty_db': wavelength_penalty
            },
            'effective_polarization_analysis': {
                'input_parameters': {
                    'te_percentage': te_percentage,
                    'tm_percentage': tm_percentage,
                    'te_polarization_fraction': self.te_polarization_fraction
                },
                'polarized_components': {
                    'te_fraction': te_fraction,
                    'tm_fraction': tm_fraction,
                    'polarized_te_fraction': effective_te_fraction,
                    'polarized_tm_fraction': effective_tm_fraction,
                    'unpolarized_fraction': 1.0 - self.te_polarization_fraction
                },
                'effective_fractions': {
                    'effective_te_fraction': effective_te_fraction,
                    'effective_tm_fraction': effective_tm_fraction,
                    'effective_te_percentage': effective_te_fraction * 100.0,
                    'effective_tm_percentage': effective_tm_fraction * 100.0
                },
                'description': f"TE fraction={self.te_polarization_fraction:.2f}: effective TE={effective_te_fraction*100:.1f}%, TM={effective_tm_fraction*100:.1f}%"
            },
            'pol_control_analysis': pol_control_analysis,
            'loss_analysis': {
                'base_soa_to_output_loss': base_soa_to_output_loss,
                'pol_control_loss': pol_control_loss,
                'total_soa_to_output_loss': total_soa_to_output_loss,
                'psr_loss_component': pol_control_analysis['total_psr_loss'],
                'phase_shifter_loss_component': pol_control_analysis['total_phase_shifter_loss'],
                'coupler_loss_component': pol_control_analysis['total_coupler_loss']
            },
            'soa_requirements': {
                'soa_output_required_db': soa_output_required,
                'power_required_mw': 10**(soa_output_required / 10),
                'description': f"SOA requires {soa_output_required:.2f} dBm for {te_percentage:.1f}% TE polarization with pol-control architecture"
            },
            'summary': {
                'total_soa_power_mw': 10**(soa_output_required / 10),
                'max_soa_output_db': soa_output_required,
                'description': f"Pol-control SOA requires {soa_output_required:.2f} dBm for {te_percentage:.1f}% TE polarization (TE fraction={self.te_polarization_fraction:.2f})"
            }
        }
        
        # Add 3σ case if provided
        if target_pout_3sigma is not None and soa_penalty_3sigma is not None:
            sigma_wavelength_penalty = 10 * math.log10(num_wavelengths)
            
            soa_output_sigma = (target_pout_3sigma + sigma_wavelength_penalty + 
                              soa_penalty_3sigma + total_soa_to_output_loss)
            
            result['sigma_case'] = {
                'soa_output_required_db': target_pout_3sigma + sigma_wavelength_penalty + soa_penalty_3sigma + total_soa_to_output_loss,
                'soa_output_final_db': soa_output_sigma,
                'power_required_mw': 10**(soa_output_sigma / 10)
            }
        
        return result

    def get_total_loss_by_pol_control_case(self, polarization_case: str = 'mixed'):
        """
        Calculate total loss for pol-control architecture for different polarization cases.
        
        Args:
            polarization_case (str): 'pure_te', 'pure_tm', or 'mixed'
            
        Returns:
            dict: Total loss calculation for the specified polarization case
        """
        if self.effective_architecture != 'pol_control':
            return {'error': 'Polarization case analysis only applies to pol_control architecture'}
        
        if polarization_case not in ['pure_te', 'pure_tm', 'mixed']:
            return {'error': 'Polarization case must be pure_te, pure_tm, or mixed'}
        
        # Base losses (same for all cases)
        base_loss = (self.connector_in_loss + self.connector_out_loss + 
                    self.io_in_loss + self.io_out_loss + 
                    self.wg_in_loss + self.wg_out_loss)
        
        # Pol-control specific losses depend on polarization case
        if polarization_case == 'pure_te':
            # 100% TE polarization
            psr_loss = 2 * self.psr_loss_te
            phase_shifter_loss = 2 * self.phase_shifter_loss
            coupler_loss = 2 * self.coupler_loss
            total_pol_control_loss = psr_loss + phase_shifter_loss + coupler_loss
            description = "Pure TE polarization (100% TE)"
            
        elif polarization_case == 'pure_tm':
            # 100% TM polarization
            psr_loss = 2 * self.psr_loss_tm
            phase_shifter_loss = 2 * self.phase_shifter_loss
            coupler_loss = 2 * self.coupler_loss
            total_pol_control_loss = psr_loss + phase_shifter_loss + coupler_loss
            description = "Pure TM polarization (100% TM)"
            
        else:  # mixed
            # Use configured TE polarization fraction
            te_fraction = self.te_polarization_fraction
            tm_fraction = 1.0 - self.te_polarization_fraction
            
            # Weighted average PSR loss
            avg_psr_loss = (te_fraction * self.psr_loss_te) + (tm_fraction * self.psr_loss_tm)
            psr_loss = 2 * avg_psr_loss
            phase_shifter_loss = 2 * self.phase_shifter_loss
            coupler_loss = 2 * self.coupler_loss
            total_pol_control_loss = psr_loss + phase_shifter_loss + coupler_loss
            description = f"Mixed polarization ({self.te_polarization_fraction:.1%} TE, {tm_fraction:.1%} TM)"
        
        total_loss = base_loss + total_pol_control_loss
        
        return {
            'polarization_case': polarization_case,
            'description': description,
            'base_loss': base_loss,
            'pol_control_loss': {
                'psr_loss': psr_loss,
                'phase_shifter_loss': phase_shifter_loss,
                'coupler_loss': coupler_loss,
                'total_pol_control_loss': total_pol_control_loss
            },
            'total_loss': total_loss
        }

    def compare_pol_control_cases(self):
        """
        Compare total losses for different polarization cases in pol-control architecture.
        
        Returns:
            dict: Comparison of losses for pure TE, pure TM, and mixed polarization cases
        """
        if self.effective_architecture != 'pol_control':
            return {'error': 'Polarization case comparison only applies to pol_control architecture'}
        
        # Calculate losses for each case
        pure_te = self.get_total_loss_by_pol_control_case('pure_te')
        pure_tm = self.get_total_loss_by_pol_control_case('pure_tm')
        mixed = self.get_total_loss_by_pol_control_case('mixed')
        
        if 'error' in pure_te or 'error' in pure_tm or 'error' in mixed:
            return {'error': 'Failed to calculate one or more polarization cases'}
        
        return {
            'architecture': 'pol_control',
            'cases': {
                'pure_te': pure_te,
                'pure_tm': pure_tm,
                'mixed': mixed
            },
            'comparison': {
                'lowest_loss': min(pure_te['total_loss'], pure_tm['total_loss'], mixed['total_loss']),
                'highest_loss': max(pure_te['total_loss'], pure_tm['total_loss'], mixed['total_loss']),
                'loss_range': max(pure_te['total_loss'], pure_tm['total_loss'], mixed['total_loss']) - min(pure_te['total_loss'], pure_tm['total_loss'], mixed['total_loss'])
            }
        }