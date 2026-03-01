from ...colors import GREEN
from ...effects._base_effect import BaseEffect
from ...device import Device
from ...utilities import dimm, easeOutQuart, mix, sin100, sin100_

_metadata = {
    'name': 'Battery State',
    'reqs': [],
    'duration': 30
}

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)
    
    def apply(self, t, palettes):

        pct =  self.dev.BATTERY['percentage']

        pct_dg = pct * 3.6

        palette = GREEN

        t = t - self._TICK - 5

        bg = [0.3,0.3,0.3]

        if t < 0:
            self.dev.Raw.all([0,0,0])
        else:
            for z in self.dev.Z.Rings + self.dev.Z.Lines:
                _p = easeOutQuart((t/4) / 10) if t <= 30 else 1
                for x in range(z.COUNT):
                    td = _p * 110
                    if z.PERCENTAGE[x] <= td - 10:
                        z[x] = bg
                    elif td - 10 <= z.PERCENTAGE[x] < td:
                        __p = ((z.PERCENTAGE[x] - td) / 10) % 1
                        z[x] = dimm(bg, 1-__p)
                    else:
                        z[x] = [0,0,0]

            fg = palette.fg
            if t >= 5:
                for z in self.dev.Z.Rings + self.dev.Z.Lines:
                    _p = easeOutQuart(((t-5)) / 60) * pct / 100 if t < 100 else pct / 100
                    for x in range(z.COUNT):
                        td = _p * 110
                        fg1 = dimm(fg, sin100_(-(t-6)*3 + int(z.PERCENTAGE[x]))**10*0.6 + 0.4)
                        if z.PERCENTAGE[x] <= td - 10:
                            z[x] = fg1
                        elif td - 10 <= z.PERCENTAGE[x] < td:
                            __p = ((z.PERCENTAGE[x] - td) / 10) % 1
                            z[x] = mix(fg1, 1-__p, bg, __p)
            
            for z in self.dev.Z.Leds:
                _p = easeOutQuart((t/4) / 10) if t <= 30 else 1
                z.all(dimm(bg, _p))
    
    def framekey(self, t):
        return None