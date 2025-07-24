"""
SOA Models Package

This package contains Semiconductor Optical Amplifier (SOA) model classes and thermal management components:
- HPSOA: High Power SOA model
- SOA: SOA model (formerly EuropaSOA)
- EuropaSOA_datasoa: Alternative Europa SOA implementation
- TRL: Tunable Ring Laser model with thermal management
- DFB: Distributed Feedback Laser model
- RINGHTR: Ring Heater thermal management component
- PHASEHTR: Phase Heater thermal management component
- MZIHTR: MZI Heater thermal management component
"""

from .HPSOA import HPSOA
from .SOA import SOA
from .TRL import TRL
from .DFB import DFB
from .RINGHTR import RINGHTR
from .PHASEHTR import PHASEHTR
from .MZIHTR import MZIHTR

# Also import the datasoa version if needed
try:
    from .EuropaSOA_datasoa import EuropaSOA as EuropaSOA_datasoa
except ImportError:
    EuropaSOA_datasoa = None

__all__ = ['HPSOA', 'SOA', 'EuropaSOA_datasoa', 'TRL', 'DFB', 'RINGHTR', 'PHASEHTR', 'MZIHTR'] 