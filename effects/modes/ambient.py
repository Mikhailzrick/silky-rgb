from __future__ import annotations

import time
from typing import Tuple

from .._base_effect import BaseEffect
from ...device import Device
from ...utilities import color_upscale

from ._ambient_sampler import AmbientSampler

_metadata = {
    'order': 91,
    'name': 'Ambient',
    'reqs': ['ambient']
}

Rgb255 = Tuple[int, int, int]
RgbFloat = Tuple[float, float, float]

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)

        self.sampler = AmbientSampler()

        self.current: RgbFloat = (0.0, 0.0, 0.0)
        self.start: RgbFloat = (0.0, 0.0, 0.0)
        self.target: RgbFloat = (0.0, 0.0, 0.0)

        now = self.now_ms()

        # Screen sampling interval.
        self.sample_interval_ms = 350
        self.last_sample_ms = now - self.sample_interval_ms

        # Desired transition duration from old color to new color.
        # Lower = faster.
        self.transition_ms = 1000
        self.transition_start_ms = now

    def prepare(self):
        now = self.now_ms()

        self.current = self.transition_color(now)

        if now - self.last_sample_ms >= self.sample_interval_ms:
            self.last_sample_ms = now

            rgb = self.sampler.dominant_rgb()

            if rgb is None:
                rgb = (0, 0, 0)

            new_target = self.rgb255_to_float(rgb)
            self.set_target(new_target, now)

        self.current = self.transition_color(now)

    def apply(self, t, palettes):
        self.dev.Raw.all(color_upscale(self.current))

    def framekey(self, t):
        return None

    def set_target(self, target: RgbFloat, now: int) -> None:
        self.start = self.current
        self.target = target
        self.transition_start_ms = now

    def transition_color(self, now: int) -> RgbFloat:
        elapsed = now - self.transition_start_ms

        if self.transition_ms <= 0:
            return self.target

        p = elapsed / self.transition_ms

        if p >= 1.0:
            return self.target

        if p <= 0.0:
            return self.start

        p = p * p * (3.0 - 2.0 * p)

        return self.mix_rgb(self.start, self.target, p)

    @staticmethod
    def rgb255_to_float(rgb: Rgb255) -> RgbFloat:
        r, g, b = rgb

        return (
            r / 255.0,
            g / 255.0,
            b / 255.0,
        )

    @staticmethod
    def mix_rgb(a: RgbFloat, b: RgbFloat, p: float) -> RgbFloat:
        return (
            a[0] + (b[0] - a[0]) * p,
            a[1] + (b[1] - a[1]) * p,
            a[2] + (b[2] - a[2]) * p,
        )

    @staticmethod
    def now_ms() -> int:
        return int(time.monotonic() * 1000)
