from .._base_effect import BaseEffect
from math import sqrt
from ...colors import Color
from ...device import Device
from ...utilities import Numeric, dimm, easeOutQuart, generate_brightness_list, mix

_metadata = {
    'name': 'Notification Cheevo',
    'reqs': [],
    'duration': 150
}

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)
    
    def apply(self, t, palettes):
        t = t-self._TICK + 0
        if t < 30:
            c = dimm([1,1,1], min(t/20, 1))
            for z in self.dev.Z.Rings:
                _p = easeOutQuart((t*10) / 360)
                for x in range(z.COUNT):
                    td = _p * 360 + t
                    if z.ANGLES[x] < td - 40:
                        z[x] = c
                    elif td - 40 <= z.ANGLES[x] < td:
                        __p = ((z.ANGLES[x] - td) / 40) % 1
                        z[x] = dimm(c, 1-__p)
                    else:
                        z[x] = [0,0,0]
        
            for z in self.dev.Z.Leds + self.dev.Z.Lines:
                z.all(c)
        elif t < 140:
            t = t-30
            _p = t/40
            c1:Color = [0.8, 0.6, 0]
            c2:Color = [0.2, 0.2, 1]
            if t < 40:
                _p = 1 - min(t/20, 1)
                c1 = mix(c1, 1-_p, [1,1,1], _p)
                c2 = mix(c2, 1-_p, [1,1,1], _p)
            elif t > 90:
                _p = 1 - (t-90) / 20
                c1 = mix([0,0,0], 1-_p, c1, _p)
                c2 = mix([0,0,0], 1-_p, c2, _p)
            td = -1*(t * 110)**0.75
            for z in self.dev.Z.Rings + self.dev.Z.Lines:
                for x in range(z.COUNT):
                    ag = (td + z.PERCENTAGE[x]) % 100
                    if ag <= 40:
                        z[x] = c1
                    elif ag < 50:
                        __p = ((ag - 40) / 10) % 1
                        z[x] = mix(c2, __p, c1, 1-__p)
                    elif ag < 90:
                        z[x] = c2
                    else:
                        __p = ((ag - 90) / 10) % 1
                        z[x] = mix(c1, __p, c2, 1-__p)
            for z in self.dev.Z.Leds:
                ag = (td) % 100 if z.PAL_ID == 0 else 99 - (td) % 100
                if ag <= 25:
                    z.all(c1)
                elif ag < 50:
                    __p = ((ag - 25) / 25) % 1
                    z.all(mix(c2, __p, c1, 1-__p))
                elif ag < 75:
                    z.all(c2)
                else:
                    __p = ((ag - 75) / 25) % 1
                    z.all(mix(c1, __p, c2, 1-__p))
        else:
            self.dev.Raw.all([0,0,0])
    
    def framekey(self, t):
        return None