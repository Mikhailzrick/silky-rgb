from .._base_effect import BaseEffect
from ...device import Device

_metadata = {
    'order': 0,
    'name': 'None',
    'reqs': []
}

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)

    def apply(self, t, palettes):
        for z in self.dev.A:
            self.dev.Raw.all([0,0,0])

    def framekey(self, t):
        return 0
