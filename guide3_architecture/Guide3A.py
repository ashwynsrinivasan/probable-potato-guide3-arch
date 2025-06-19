import math
from .EuropaSOA import EuropaSOA
from .EuropaPIC import EuropaPIC

class Guide3A:
    """
    Represents a module with multiple PICs, each with a EuropaSOA.
    """
    def __init__(self, num_fibers: int, fiber_input_type: str, pic_architecture: str, soa_configs: dict):
        if num_fibers % 20 != 0:
            raise ValueError("Number of fibers must be a multiple of 20.")
        
        self.num_fibers = num_fibers
        self.fiber_input_type = fiber_input_type
        
        if self.fiber_input_type == 'pm':
            self.pic_architecture = 'psrless'
        else:
            self.pic_architecture = pic_architecture

        if self.pic_architecture == 'psrless':
            self.num_soas = self.num_fibers
        else:
            self.num_soas = 2 * self.num_fibers

        self.num_pics = math.ceil(self.num_soas / 20)
        self.num_unit_cells = self.num_pics

        self.pics = [EuropaPIC(pic_architecture) for _ in range(self.num_pics)]
        self.soas = [EuropaSOA(**soa_configs) for _ in range(self.num_soas)] 