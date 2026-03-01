from math import pi, sin
from .._base_effect import BaseEffect
from ...device import Device
from ...utilities import mix, dimm, sin100, sin100_

_metadata = {
    'order': 30,
    'name': 'Knight Rider',
    'reqs': ['device:trimui-brick']
}

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)
    
    def apply(self, t, palettes):
        
        self.dev.Raw.all([0,0,0])

        for z in self.dev.Z.Lines:
            p = palettes[z.PAL_ID]
            
            for i in range(z.COUNT):
                prog = max(2-abs(i-sin100_(t*3)*7), 0) / 2
                
                # Mix the foreground and background colors based on the wave progression
                z[i] = mix([0,0,0], 1 - (prog), [1,0,0], prog)
    
    def framekey(self, t):
        return sin100_(t*3)