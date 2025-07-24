"""
SOA Models Package

This package contains Semiconductor Optical Amplifier (SOA) model classes and thermal management components:
- HPSOA: High Power SOA model
- EuropaSOA: Europa SOA model
- EuropaSOA_datasoa: Alternative Europa SOA implementation
- TRL: Tunable Ring Laser model with thermal management
- RINGHTR: Ring Heater thermal management component
- PHASEHTR: Phase Heater thermal management component
"""

from .HPSOA import HPSOA
from .EuropaSOA import EuropaSOA
from .TRL import TRL
from .RINGHTR import RINGHTR
from .PHASEHTR import PHASEHTR

# Also import the datasoa version if needed
try:
    from .EuropaSOA_datasoa import EuropaSOA as EuropaSOA_datasoa
except ImportError:
    EuropaSOA_datasoa = None

__all__ = ['HPSOA', 'EuropaSOA', 'EuropaSOA_datasoa', 'TRL', 'RINGHTR', 'PHASEHTR'] 