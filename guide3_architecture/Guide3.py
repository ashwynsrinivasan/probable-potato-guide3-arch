import math
from .EuropaSOA import EuropaSOA

class Guide3:
    """
    Represents Guide3 functionality focused on link requirements per lambda.
    
    This class provides comprehensive modeling of link requirements per wavelength
    with detailed loss analysis and performance metrics.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize Guide3 with link requirements per lambda configuration.
        
        Args:
            **kwargs: Optional custom parameter values
        """
        
        # Link Requirements per Lambda - Default values from Guide3A
        self.target_pout = kwargs.get('target_pout', -3.3)  # dBm
        self.target_pout_3sigma = kwargs.get('target_pout_3sigma', -0.3)  # dBm
        self.soa_penalty = kwargs.get('soa_penalty', 2.0)  # dB
        self.soa_penalty_3sigma = kwargs.get('soa_penalty_3sigma', 2.0)  # dB
        
        # Loss Components - Default values from Guide3A
        self.io_in_loss = kwargs.get('io_in_loss', 1.5)  # dB
        self.io_out_loss = kwargs.get('io_out_loss', 1.5)  # dB
        self.connector_in_loss = kwargs.get('connector_in_loss', 0.25)  # dB
        self.connector_out_loss = kwargs.get('connector_out_loss', 0.25)  # dB
        self.wg_in_loss = kwargs.get('wg_in_loss', 0.25)  # dB
        self.wg_out_loss = kwargs.get('wg_out_loss', 0.25)  # dB
        self.tap_in_loss = kwargs.get('tap_in_loss', 0.3)  # dB
        self.tap_out_loss = kwargs.get('tap_out_loss', 0.3)  # dB
        self.psr_loss = kwargs.get('psr_loss', 0.5)  # dB
        self.phase_shifter_loss = kwargs.get('phase_shifter_loss', 0.5)  # dB
        self.coupler_loss = kwargs.get('coupler_loss', 0.2)  # dB
        
        # Performance parameters
        self.operating_wavelength_nm = kwargs.get('operating_wavelength_nm', 1310)
        self.temperature_c = kwargs.get('temperature_c', 25)
        
        # Validate inputs
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate all input parameters"""
        # Check for negative loss values
        loss_params = [
            self.io_in_loss, self.io_out_loss, self.connector_in_loss, self.connector_out_loss,
            self.wg_in_loss, self.wg_out_loss, self.tap_in_loss, self.tap_out_loss,
            self.psr_loss, self.phase_shifter_loss, self.coupler_loss
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
        
        if not (-10 <= self.target_pout_3sigma <= 20):
            raise ValueError(f"Target Pout 3σ must be between -10 and 20 dBm: {self.target_pout_3sigma}")
        
        # Check SOA penalty range
        if self.soa_penalty < 0:
            raise ValueError(f"SOA penalty must be non-negative: {self.soa_penalty}")
        
        if self.soa_penalty_3sigma < 0:
            raise ValueError(f"SOA penalty 3σ must be non-negative: {self.soa_penalty_3sigma}")
    
    def get_link_requirements(self):
        """
        Get link requirements per lambda.
        
        Returns:
            dict: Link requirements for median and 3σ cases
        """
        return {
            'median_case': {
                'target_pout_db': self.target_pout,
                'soa_penalty_db': self.soa_penalty,
                'total_requirement_db': self.target_pout + self.soa_penalty
            },
            'sigma_case': {
                'target_pout_db': self.target_pout_3sigma,
                'soa_penalty_db': self.soa_penalty_3sigma,
                'total_requirement_db': self.target_pout_3sigma + self.soa_penalty_3sigma
            }
        }
    
    def get_loss_breakdown(self):
        """
        Get detailed loss breakdown.
        
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
            'tap_losses': {
                'tap_in_loss': self.tap_in_loss,
                'tap_out_loss': self.tap_out_loss,
                'total_tap_loss': self.tap_in_loss + self.tap_out_loss
            },
            'other_losses': {
                'psr_loss': self.psr_loss,
                'phase_shifter_loss': self.phase_shifter_loss,
                'coupler_loss': self.coupler_loss
            }
        }
        
        # Calculate total loss
        total_loss = (breakdown['connector_losses']['total_connector_loss'] +
                     breakdown['io_losses']['total_io_loss'] +
                     breakdown['waveguide_routing_losses']['total_wg_routing_loss'] +
                     breakdown['tap_losses']['total_tap_loss'] +
                     breakdown['other_losses']['psr_loss'] +
                     breakdown['other_losses']['phase_shifter_loss'] +
                     breakdown['other_losses']['coupler_loss'])
        
        breakdown['total_loss'] = total_loss
        return breakdown
    
    def calculate_target_pout_all_wavelengths(self, num_wavelengths: int):
        """
        Calculate target Pout for all wavelengths based on the formula:
        Pout + penalty + 10*log10(number_of_wavelengths)
        
        Args:
            num_wavelengths (int): Number of wavelengths
            
        Returns:
            dict: Target Pout calculations for median and 3σ cases
        """
        if num_wavelengths <= 0:
            raise ValueError("Number of wavelengths must be positive")
        
        # Calculate wavelength penalty: 10*log10(number_of_wavelengths)
        wavelength_penalty = 10 * math.log10(num_wavelengths)
        
        # Median case calculation
        median_target_pout = self.target_pout + self.soa_penalty + wavelength_penalty
        
        # 3σ case calculation
        sigma_target_pout = self.target_pout_3sigma + self.soa_penalty_3sigma + wavelength_penalty
        
        return {
            'num_wavelengths': num_wavelengths,
            'wavelength_penalty_db': wavelength_penalty,
            'median_case': {
                'base_target_pout_db': self.target_pout,
                'soa_penalty_db': self.soa_penalty,
                'wavelength_penalty_db': wavelength_penalty,
                'total_target_pout_db': median_target_pout
            },
            'sigma_case': {
                'base_target_pout_db': self.target_pout_3sigma,
                'soa_penalty_db': self.soa_penalty_3sigma,
                'wavelength_penalty_db': wavelength_penalty,
                'total_target_pout_db': sigma_target_pout
            }
        }
    
    def set_custom_parameters(self, **kwargs):
        """
        Set custom parameter values and revalidate.
        
        Args:
            **kwargs: Custom parameter values to set
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
        link_requirements = self.get_link_requirements()
        loss_breakdown = self.get_loss_breakdown()
        
        report = f"""
Guide3 Link Requirements per Lambda Report
{'='*50}

Link Requirements:
  - Target Pout (Median): {link_requirements['median_case']['target_pout_db']:.1f} dBm
  - SOA Penalty (Median): {link_requirements['median_case']['soa_penalty_db']:.1f} dB
  - Total Requirement (Median): {link_requirements['median_case']['total_requirement_db']:.1f} dB
  - Target Pout (3σ): {link_requirements['sigma_case']['target_pout_db']:.1f} dBm
  - SOA Penalty (3σ): {link_requirements['sigma_case']['soa_penalty_db']:.1f} dB
  - Total Requirement (3σ): {link_requirements['sigma_case']['total_requirement_db']:.1f} dB

Loss Breakdown:
  - Optical Connector Input Loss: {loss_breakdown['connector_losses']['connector_in_loss']:.2f} dB
  - Optical Connector Output Loss: {loss_breakdown['connector_losses']['connector_out_loss']:.2f} dB
  - Total Optical Connector Loss: {loss_breakdown['connector_losses']['total_connector_loss']:.2f} dB
  - I/O Input Loss: {loss_breakdown['io_losses']['io_in_loss']:.1f} dB
  - I/O Output Loss: {loss_breakdown['io_losses']['io_out_loss']:.1f} dB
  - Total I/O Loss: {loss_breakdown['io_losses']['total_io_loss']:.1f} dB
  - Waveguide Routing Input Loss: {loss_breakdown['waveguide_routing_losses']['wg_in_loss']:.2f} dB
  - Waveguide Routing Output Loss: {loss_breakdown['waveguide_routing_losses']['wg_out_loss']:.2f} dB
  - Total Waveguide Routing Loss: {loss_breakdown['waveguide_routing_losses']['total_wg_routing_loss']:.2f} dB
  - Tap Input Loss: {loss_breakdown['tap_losses']['tap_in_loss']:.1f} dB
  - Tap Output Loss: {loss_breakdown['tap_losses']['tap_out_loss']:.1f} dB
  - Total Tap Loss: {loss_breakdown['tap_losses']['total_tap_loss']:.1f} dB
  - PSR Loss: {loss_breakdown['other_losses']['psr_loss']:.1f} dB
  - Phase Shifter Loss: {loss_breakdown['other_losses']['phase_shifter_loss']:.1f} dB
  - Coupler Loss: {loss_breakdown['other_losses']['coupler_loss']:.1f} dB
  - Total Loss: {loss_breakdown['total_loss']:.2f} dB

Performance Parameters:
  - Operating Wavelength: {self.operating_wavelength_nm} nm
  - Temperature: {self.temperature_c}°C
"""
        
        return report 