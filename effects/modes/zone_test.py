from .._base_effect import BaseEffect
from ...device import Device
from ...utilities import mix, dimm, sin100

_metadata = {
    'order': 100,
    'name': 'Zone Test',
    'reqs': ['dev']
}

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)
    
    def apply(self, t, palettes):
        
        self.dev.Raw.all([0,0,0])
        
        z = self.dev.A[(t//30)%len(self.dev.A)]
        p = palettes[z.PAL_ID]
        
        z.all(p.bg)
        for i in range(z.COUNT):
            if(t%z.COUNT == i):
                z[i] = p.fg
     
    def framekey(self, t):
        return None