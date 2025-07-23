"""
SOA Models Package

This package contains Semiconductor Optical Amplifier (SOA) model classes:
- HPSOA: High Power SOA model
- EuropaSOA: Europa SOA model
- EuropaSOA_datasoa: Alternative Europa SOA implementation
"""

from .HPSOA import HPSOA
from .EuropaSOA import EuropaSOA

# Also import the datasoa version if needed
try:
    from .EuropaSOA_datasoa import EuropaSOA as EuropaSOA_datasoa
except ImportError:
    EuropaSOA_datasoa = None

__all__ = ['HPSOA', 'EuropaSOA', 'EuropaSOA_datasoa'] 