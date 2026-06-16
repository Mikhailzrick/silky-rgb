from __future__ import annotations

import fcntl
import mmap
import os
import struct
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Tuple


Rgb255 = Tuple[int, int, int]


@dataclass
class AmbientSamplerConfig:
    fb_path: str = "/dev/fb0"
    sysfs_path: str = "/sys/class/graphics/fb0"

    width: int = 0
    height: int = 0
    xoffset: int = 0
    yoffset: int = 0
    xres_virtual: int = 0
    yres_virtual: int = 0
    bpp: int = 0
    stride: int = 0

    sample_size: int = 12
    dark_threshold: int = 24
    saturation_threshold: int = 14
    quantize_bits: int = 3


class AmbientSampler:
    FBIOGET_VSCREENINFO = 0x4600

    def __init__(self, config: Optional[AmbientSamplerConfig] = None) -> None:
        self.config = config if config is not None else AmbientSamplerConfig()
        self.available = False
        self._fb = None
        self._mem = None
        self._bytes_per_pixel = 0
        self._shift = 5

        self.detect_framebuffer()
        self._open_framebuffer()

    def close(self) -> None:
        if self._mem is not None:
            try:
                self._mem.close()
            except Exception:
                pass
            self._mem = None

        if self._fb is not None:
            try:
                self._fb.close()
            except Exception:
                pass
            self._fb = None

    def dominant_rgb(self) -> Optional[Rgb255]:
        cfg = self.config

        if not self.available or self._mem is None:
            return None

        buckets = defaultdict(lambda: [0, 0, 0, 0])
        mem = self._mem
        bpp = self._bytes_per_pixel
        shift = self._shift

        try:
            for sy in range(cfg.sample_size):
                local_y = int((sy + 0.5) * cfg.height / cfg.sample_size)
                y = cfg.yoffset + local_y

                if y < 0:
                    y = 0
                elif y >= cfg.yres_virtual:
                    y = cfg.yres_virtual - 1

                row_offset = y * cfg.stride

                for sx in range(cfg.sample_size):
                    local_x = int((sx + 0.5) * cfg.width / cfg.sample_size)
                    x = cfg.xoffset + local_x

                    if x < 0:
                        x = 0
                    elif x >= cfg.xres_virtual:
                        x = cfg.xres_virtual - 1

                    offset = row_offset + (x * bpp)
                    raw = mem[offset:offset + bpp]

                    if cfg.bpp == 32:
                        r = raw[2]
                        g = raw[1]
                        b = raw[0]
                    else:
                        r, g, b = self._decode_rgb565(raw)

                    brightness = max(r, g, b)
                    saturation = brightness - min(r, g, b)
                    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b

                    if brightness < cfg.dark_threshold:
                        continue

                    if saturation < cfg.saturation_threshold and luma < 120:
                        continue

                    key = (r >> shift, g >> shift, b >> shift)
                    bucket = buckets[key]
                    bucket[0] += r
                    bucket[1] += g
                    bucket[2] += b
                    bucket[3] += 1

        except Exception:
            return None

        if not buckets:
            return None

        best = max(buckets.values(), key=lambda v: v[3])
        r_sum, g_sum, b_sum, count = best

        if count <= 0:
            return None

        return (
            r_sum // count,
            g_sum // count,
            b_sum // count,
        )

    def detect_framebuffer(self) -> None:
        self.available = False

        if not os.path.exists(self.config.fb_path):
            return

        self._detect_var_screeninfo()
        self._detect_stride()

        self.available = self._validate()

        if self.available:
            self._bytes_per_pixel = self.config.bpp // 8
            qbits = self.config.quantize_bits
            if qbits < 1:
                qbits = 1
            elif qbits > 8:
                qbits = 8
            self._shift = 8 - qbits

    def _open_framebuffer(self) -> None:
        cfg = self.config

        if not self.available:
            return

        fb_size = cfg.stride * cfg.yres_virtual
        if fb_size <= 0:
            self.available = False
            return

        try:
            self._fb = open(cfg.fb_path, "rb", buffering=0)
            self._mem = mmap.mmap(
                self._fb.fileno(),
                fb_size,
                access=mmap.ACCESS_READ,
            )
        except Exception:
            self.close()
            self.available = False

    def _detect_var_screeninfo(self) -> None:
        cfg = self.config

        try:
            buf = bytearray(160)

            with open(cfg.fb_path, "rb") as fb:
                fcntl.ioctl(fb, self.FBIOGET_VSCREENINFO, buf, True)

            (
                cfg.width,
                cfg.height,
                cfg.xres_virtual,
                cfg.yres_virtual,
                cfg.xoffset,
                cfg.yoffset,
                cfg.bpp,
                _grayscale,
            ) = struct.unpack_from("8I", buf, 0)

        except Exception:
            pass

    def _detect_stride(self) -> None:
        cfg = self.config

        try:
            with open(f"{cfg.sysfs_path}/stride", "r") as f:
                stride = int(f.read().strip())

            if stride > 0:
                cfg.stride = stride
                return

        except Exception:
            pass

        if cfg.xres_virtual > 0 and cfg.bpp > 0:
            cfg.stride = cfg.xres_virtual * (cfg.bpp // 8)

    def _validate(self) -> bool:
        cfg = self.config

        return (
            cfg.width > 0 and
            cfg.height > 0 and
            cfg.xres_virtual > 0 and
            cfg.yres_virtual > 0 and
            cfg.bpp in (16, 32) and
            cfg.stride > 0 and
            0 <= cfg.xoffset < cfg.xres_virtual and
            0 <= cfg.yoffset < cfg.yres_virtual and
            cfg.sample_size > 0
        )

    @staticmethod
    def _decode_rgb565(raw: bytes) -> Rgb255:
        value = raw[0] | (raw[1] << 8)

        r5 = (value >> 11) & 0x1F
        g6 = (value >> 5) & 0x3F
        b5 = value & 0x1F

        return (
            (r5 << 3) | (r5 >> 2),
            (g6 << 2) | (g6 >> 4),
            (b5 << 3) | (b5 >> 2),
        )

    def __del__(self) -> None:
        self.close()
