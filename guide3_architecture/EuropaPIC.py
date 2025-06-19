class EuropaPIC:
    """
    Represents a Europa Photonic Integrated Circuit (PIC).
    
    This class provides comprehensive modeling of different PIC architectures
    with detailed loss analysis and performance metrics.
    """
    
    # Supported architectures
    SUPPORTED_ARCHITECTURES = ['psr', 'pol_control', 'psrless']
    
    def __init__(self, pic_architecture: str, **kwargs):
        """
        Initialize EuropaPIC with specified architecture and optional custom loss values.
        
        Args:
            pic_architecture (str): PIC architecture type
            **kwargs: Optional custom loss values (io_in_loss, io_out_loss, etc.)
        """
        if pic_architecture not in self.SUPPORTED_ARCHITECTURES:
            raise ValueError(f"Unsupported architecture: {pic_architecture}. "
                           f"Supported: {self.SUPPORTED_ARCHITECTURES}")
        
        self.pic_architecture = pic_architecture
        
        # Default loss values (dB)
        self.io_in_loss = kwargs.get('io_in_loss', 1.5)
        self.io_out_loss = kwargs.get('io_out_loss', 1.5)
        self.psr_loss = kwargs.get('psr_loss', 0.5)
        self.phase_shifter_loss = kwargs.get('phase_shifter_loss', 0.5)
        self.coupler_loss = kwargs.get('coupler_loss', 0.2)
        
        # Performance parameters
        self.operating_wavelength_nm = kwargs.get('operating_wavelength_nm', 1310)
        self.temperature_c = kwargs.get('temperature_c', 25)
        
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
    
    def get_total_loss(self):
        """
        Calculate total loss for the PIC architecture.
        
        Returns:
            float: Total loss in dB
        """
        total_loss = self.io_in_loss + self.io_out_loss
        
        # Add architecture-specific losses
        if self.pic_architecture == 'psr':
            total_loss += 2 * self.psr_loss  # psr_in and psr_out
            
        elif self.pic_architecture == 'pol_control':
            total_loss += 2 * self.psr_loss  # psr_in and psr_out
            total_loss += 2 * self.phase_shifter_loss  # phase_shifter_in_1, phase_shifter_in_2
            total_loss += 2 * self.coupler_loss  # coupler_in_1, coupler_in_2
            
        elif self.pic_architecture == 'psrless':
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
        if self.pic_architecture == 'psr':
            breakdown['architecture_specific'] = {
                'psr_loss': self.psr_loss,
                'total_psr_loss': 2 * self.psr_loss
            }
            
        elif self.pic_architecture == 'pol_control':
            breakdown['architecture_specific'] = {
                'psr_loss': self.psr_loss,
                'total_psr_loss': 2 * self.psr_loss,
                'phase_shifter_loss': self.phase_shifter_loss,
                'total_phase_shifter_loss': 2 * self.phase_shifter_loss,
                'coupler_loss': self.coupler_loss,
                'total_coupler_loss': 2 * self.coupler_loss
            }
            
        elif self.pic_architecture == 'psrless':
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
        return descriptions.get(self.pic_architecture, "Unknown architecture")
    
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
        components.update(architecture_components.get(self.pic_architecture, {}))
        return components
    
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
        
        report = f"""
EuropaPIC Analysis Report
{'='*50}

Architecture: {self.pic_architecture.upper()}
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