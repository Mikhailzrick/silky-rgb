from .._base_effect import BaseEffect
from ...device import Device
from random import randint

_metadata = {
    'order': 40,
    'name': 'Glitch',
    'reqs': ['dev']
}

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)
        self._t = [randint(0, 30) for i in range(300)]
    
    def apply(self, t, palettes):

        i = t % 300

        for z in self.dev.A:
            p = palettes[z.PAL_ID]
            for x in range(z.COUNT):
                if self._t[i] == 0:
                    z.all([0,0,0])
                elif self._t[(i+(x+1)*13+(z.POS[0]+1)*(z.POS[1]+1)) % 300] == 1:
                    z[x] = p.fg
                else:
                    z[x] = p.bg

    def framekey(self, t):
        return t % 300
