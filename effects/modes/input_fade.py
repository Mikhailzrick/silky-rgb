import time

from .._base_effect import BaseEffect
from ...device import Device
from ...joystick import StickState
from ...utilities import loop_d, mix

_metadata = {
    'order': 90,
    'name': 'Joystick',
    'reqs': ['has_input']
}

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)
        self.bg_scale = 0.7
        self.ST = StickState(dev.CONFIG)
        self.rings = self.dev.Z.Rings
        self.ZD = {r.ID: [0]*r.COUNT for r in self.rings}
        self.leds = sum(r.COUNT for r in self.rings)
        self.zeroes = 0
        self.next_input_update = 0.0
        self.curve = [(i / 100) ** 0.4 for i in range(101)]
        self.cone = 90
        self.inv_cone = 1.0 / self.cone

    def prepare(self):
        now = time.monotonic()

        if now >= self.next_input_update:
            self.ST.update()
            self.next_input_update = now + 0.05  # ~20 Hz

        rings = self.rings
        ST = self.ST
        ZD = self.ZD

        if self.zeroes == self.leds:
            active = False

            for r in rings:
                if ST[r.ID]['value'] > 0.3:
                    active = True
                    break

            if not active:
                return

        zeroes = 0
        cone = self.cone
        inv_cone = self.inv_cone

        for r in rings:
            s = ST[r.ID]
            value = s['value']
            zd = ZD[r.ID]

            if value <= 0.3:
                for x in range(r.COUNT):
                    z = zd[x] - 9
                    if z <= 0:
                        zd[x] = 0
                        zeroes += 1
                    else:
                        zd[x] = z
                continue

            angle = s['angle']
            strength = (value - 0.3) / 0.7

            for x in range(r.COUNT):
                d = (cone - abs(loop_d(r.ANGLES[x], angle, 360))) * inv_cone

                if d > 0:
                    d2 = d * d * strength
                    zd[x] = min(d*100, zd[x] + d2*9)
                else:
                    z = zd[x] - 9
                    if z <= 0:
                        zd[x] = 0
                        zeroes += 1
                    else:
                        zd[x] = z

        self.zeroes = zeroes

    def apply(self, t, palettes):
        curve = self.curve
        bg_scale = self.bg_scale
        ZD = self.ZD

        for r in self.rings:
            p = palettes[r.PAL_ID]
            zd = ZD[r.ID]

            for x in range(r.COUNT):
                z = int(zd[x])

                if z <= 0:
                    p_ = 0
                elif z >= 100:
                    p_ = 1
                else:
                    p_ = curve[z]

                r[x] = mix(p.fg, p_, p.bg, bg_scale*(1-p_))

    def framekey(self, t):
        return 0 if self.zeroes == self.leds else None
