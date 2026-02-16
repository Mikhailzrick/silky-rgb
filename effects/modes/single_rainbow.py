from .._base_effect import BaseEffect
from ...device import Device
from ...utilities import color_upscale, hsv_fl

_metadata = {
    'order': 21,
    'name': 'Single Rainbow',
    'reqs': []
}

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)
    
    def apply(self, t, palettes):
        key = (t / 600) % 1
        self.dev.Raw.all(color_upscale(hsv_fl((key) % 1, 1, 0.5)))
    
    def framekey(self, t):
        return (t / 600) % 1
