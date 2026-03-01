from .._base_effect import BaseEffect
from ...device import Device
from ...utilities import generate_brightness_list, loop_d, dimm

_metadata = {
    'name': 'frame',
    'reqs': [],
    'duration': 3
}

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)
    
    def apply(self, t, palettes):
        p = palettes[0]
        self.dev.Raw.all(p.fg)
    
    def framekey(self, t):
        return 1