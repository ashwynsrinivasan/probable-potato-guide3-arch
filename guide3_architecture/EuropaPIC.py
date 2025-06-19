class EuropaPIC:
    """
    Represents a Europa Photonic Integrated Circuit (PIC).
    """
    def __init__(self, pic_architecture: str):
        self.pic_architecture = pic_architecture
        self.io_in_loss = 1.5  # dB
        self.io_out_loss = 1.5 # dB
        self.psr_loss = 0.5 #dB
        self.phase_shifter_loss = 0.5 # dB
        self.coupler_loss = 0.2 # dB

    def get_total_loss(self):
        total_loss = self.io_in_loss + self.io_out_loss
        if self.pic_architecture == 'psr':
            total_loss += 2 * self.psr_loss # psr_in and psr_out
        elif self.pic_architecture == 'pol_control':
            total_loss += 2 * self.psr_loss # psr_in and psr_out
            total_loss += 2 * self.phase_shifter_loss # phase_shifter_in_1, phase_shifter_in_2
            total_loss += 2 * self.coupler_loss # coupler_in_1, coupler_in_2
        return total_loss 