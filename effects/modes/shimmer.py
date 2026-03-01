from .._base_effect import BaseEffect
from ...device import Device
from ...utilities import dimm, mix, sin100
from random import randint

_metadata = {
    'order': 10,
    'name': 'Shimmer',
    'reqs': []
}

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)
        self.shimmer_density = 8
        self.shimmer_table_ = [randint(0, self.shimmer_density)]
        while len(self.shimmer_table_) < 50:
            n = randint(0, self.shimmer_density)
            if self.shimmer_table_[-1] != n:
                self.shimmer_table_.append(n)

    
    def apply(self, t, palettes):
        for z in self.dev.A:
            p = palettes[z.PAL_ID]
            
            for i in range(z.COUNT):
                t_ = ((t/2+7*z._ind[i]) / 30) % self.shimmer_density
                if int(t_) == self.shimmer_table_[z._ind[i]]:
                    prog = sin100(int((t_%1)*100))
                    z[i] = mix(p.bg, 0.5-prog*0.5, p.fg, prog)
                else:
                    z[i] = dimm(p.bg, 0.5)
    
    def framekey(self, t):
        return ((t/2) / 30) % self.shimmer_density
