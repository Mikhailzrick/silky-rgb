from .._base_effect import BaseEffect
from ...device import Device
from ...utilities import loop_d, dimm, mix

_metadata = {
    'name': 'Pulse',
    'reqs': [],
    'duration': 23
}

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)
    
    def apply(self, t, palettes):
        t = (t-self._TICK + 0) % 23
        t_ = 1 - min(abs(11-t), 11) / 11
        p = palettes[0]
        for z in self.dev.Z.Rings:
            for x in range(z.COUNT):
                td = (t*20) % 450
                _d = abs(td - abs(loop_d(z.ANGLES[x], 180, 360)) - 120)
                if(_d < 120):
                    z[x] = dimm(p.fg, 1 - abs(_d) / 120)
                else:
                    z[x] = [0, 0, 0]
        for z in self.dev.Z.Leds:
            z.all(dimm(p.fg, t_))
        for z in self.dev.Z.Lines:
            t__ = (1 - t / 22) * (z.COUNT_2_C + 4)
            for i in range(z.COUNT_2_C):
                prog = max(2-abs(2+i-t__), 0) / 2
                z[i] = mix([0,0,0], 1 - (prog), p.fg, prog)
                z[z.COUNT-i-1] = mix([0,0,0], 1 - (prog), p.fg, prog)
    
    def framekey(self, t):
        return t-self._TICK + 0