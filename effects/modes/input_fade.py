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
        self.all_zones = (list(self.dev.Z.Lines) + list(self.dev.Z.Rings) + list(self.dev.Z.Leds))
        self.ZD = {r.ID: [0]*r.COUNT for r in self.rings}
        self.leds = sum(r.COUNT for r in self.rings)
        self.zeroes = 0
        self.next_input_update = 0.0
        self.curve = [(i / 100) ** 0.5 for i in range(101)]
        self.cone = 90
        self.inv_cone = 1.0 / self.cone
        self.fade_in_speed = 18
        self.fade_out_speed = 9

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
        fade_in_speed = self.fade_in_speed
        fade_out_speed = self.fade_out_speed

        for r in rings:
            s = ST[r.ID]
            value = s['value']
            zd = ZD[r.ID]

            if value <= 0.3:
                for x in range(r.COUNT):
                    z = zd[x] - fade_out_speed
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
                    target = d * 100
                    rise = d * strength
                    zd[x] = min(target, zd[x] + rise * fade_in_speed)
                else:
                    z = zd[x] - fade_out_speed
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

        # Set every LED to the primary color
        for zone in self.all_zones:
            p = palettes[zone.PAL_ID]

            for x in range(zone.COUNT):
                zone[x] = p.bg

        # Apply the joystick animation over the ring zones
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

                r[x] = mix(p.fg, p_, p.bg, bg_scale * (1 - p_))

    def framekey(self, t):
        return 0 if self.zeroes == self.leds else None
