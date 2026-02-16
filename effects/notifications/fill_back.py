from .._base_effect import BaseEffect
from ...device import Device
from ...utilities import dimm, easeOutQuart

_metadata = {
    'name': 'Notification Fill Back',
    'reqs': [],
    'duration': 30
}

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)
    
    def apply(self, t, palettes):
        t = 29 - (t - self._TICK)
        c = dimm(palettes[0].fg, min(t/20, 1))
        #c = palettes[0].fg
        for z in self.dev.Z.Rings:
            _p = easeOutQuart(t/40) if t<30 else 1
            for x in range(z.COUNT):
                td = _p * 400
                if z.ANGLES[x] < td - 40:
                    z[x] = c
                elif td - 40 <= z.ANGLES[x] < td:
                    __p = ((z.ANGLES[x] - td) / 40) % 1
                    z[x] = dimm(c, 1-__p)
                else:
                    z[x] = [0,0,0]
        for z in self.dev.Z.Lines:
            _p = easeOutQuart(t/40) if t<30 else 1
            for x in range(z.COUNT):
                td = _p * 110
                if z.PERCENTAGE[x] < td - 10:
                    z[x] = c
                elif td - 10 <= z.PERCENTAGE[x] < td:
                    __p = ((z.PERCENTAGE[x] - td) / 40) % 1
                    z[x] = dimm(c, 1-__p)
                else:
                    z[x] = [0,0,0]
        
        for z in self.dev.Z.Leds:
            z.all(c)
    
    def framekey(self, t):
        return t