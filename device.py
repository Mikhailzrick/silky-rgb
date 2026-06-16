import json
import os
from importlib import import_module
from typing import Sequence
from .utilities import Numeric

def identify_device():
    board = ""

    try:
        with open('/boot/boot/knulli.board', 'r') as f:
            board = f.read().strip()
    except (IOError, FileNotFoundError):
        pass

    return board

config = json.load(open(os.path.dirname(__file__)+'/device_configs/'+identify_device()+'.json'))

RGBDriver = import_module("silkyrgb.drivers."+config['driver']).RGBDriver

print("Loaded Driver:", config['driver']) # pyright: ignore[reportPossiblyUnboundVariable]

class Device:
    def __init__(self) -> None:
        self.CONFIG = config

        self.LED_COUNT = config['leds']

        self.FB0 = [0, 0, 0] * config['leds']
        self.BR:float = 1

        self.BATTERY = {
            'percentage': 0,
            'state': 'Discharging'
        }

        self.TRAITS = []
        self.TRAITS.append('device:'+identify_device())

        for trait in self.CONFIG.get('traits', []):
            if trait not in self.TRAITS:
                self.TRAITS.append(trait)

        self.nuke_savestates()

        self.driver = RGBDriver(config.get('driver_extra_params', {})) # pyright: ignore[reportPossiblyUnboundVariable]

        self.Raw = RawZone(
            self,
            {
                'id': 'raw',
                'leds': self.LED_COUNT,
                'led_indexes': list(range(self.LED_COUNT))
            }
        )

        self.Z = ZoneStore()
        self.A = []

        for zone_id in config['zones']:
            config['zones'][zone_id]['id'] = zone_id
            zone_config = config['zones'][zone_id]
            if zone_config['type'] == 'Ring':
                self.Z.Rings.append(RingZone(self, zone_config))
            if zone_config['type'] == 'Line':
                self.Z.Lines.append(LineZone(self, zone_config))
            if zone_config['type'] == 'Led':
                self.Z.Leds.append(RawZone(self, zone_config))

        self.A = self.Z.Leds + self.Z.Lines + self.Z.Rings

        # calculate capabilities
        if len(self.Z.Rings) > 0:
            self.TRAITS.append('has_ring')
        if len(list(filter(lambda a: a.PAL_ID == 1, self.A))) > 0:
            self.TRAITS.append('has_secondary')
        if len(list(filter(lambda a: a.COUNT > 6, self.A))):
            self.TRAITS.append('high_res')
        if len(list(filter(lambda a: "input" in a, self.CONFIG["zones"].values()))):
            self.TRAITS.append('has_input')
        extra = self.CONFIG.get("driver_extra_params", {})
        hw_modes = extra.get("hw_modes", {})

        if isinstance(hw_modes, dict) and len(hw_modes) > 0:
            # If the JSON defines hardware modes, we use them
            self.TRAITS.append("has_hw_modes")
        else:
            # If not, this is a standard Silky-RGB software-rendered device
            self.TRAITS.append("supports_silky_modes")

        # Currently, all known devices support dual colors
        self.TRAITS.append("supports_dual_colors")

        print("\nCalculated Device Traits:")
        for i in self.TRAITS:
            print(f"    {i}")

    def savestate(self, key):
        self.CACHED_BYTESTREAM = self.render()
        self.CACHE[key] = self.CACHED_BYTESTREAM
        self.CACHE_LAST_KEY = key

    def nuke_savestates(self):
        self.CACHE = {}
        self.CACHE_SKIP = False
        self.CACHE_LAST_KEY = None
        self.CACHED_BYTESTREAM = None

    def recall(self, key):
        if key is not None and key in self.CACHE:
            self.CACHED_BYTESTREAM = self.CACHE[key]
            if self.CACHE_LAST_KEY == key:
                self.CACHE_SKIP = True
            self.CACHE_LAST_KEY = key
            return True
        self.CACHED_BYTESTREAM = None
        return False

    def render(self):
        # If the config says hardware manages the LEDs, we don't calculate frames
        if "has_hw_modes" in self.TRAITS:
            return
        brc = self.BR*255+0.49
        return self.driver.render([int(a*a*brc) for a in self.FB0])

    def write(self) -> None:
        bytestream = self.CACHED_BYTESTREAM
        if bytestream is None:
            bytestream = self.render()
        if not self.CACHE_SKIP:
            self.driver.write(bytestream)
        else:
            self.CACHE_SKIP = False

    def close(self) -> None:
        self.driver.close()

    def __getitem__(self, index) -> Sequence[float]:
        return [
            self.FB0[index*3],
            self.FB0[index*3+1],
            self.FB0[index*3+2]
        ]

    def __setitem__(self, index:int, c:Sequence[float]):
        self.FB0[index*3] = c[0]
        self.FB0[index*3+1] = c[1]
        self.FB0[index*3+2] = c[2]

class ZoneStore:
    def __init__(self):
        self.Rings:list[RingZone] = []
        self.Lines:list[LineZone]  = []
        self.Leds:list[RawZone] = []

class RawZone:
    def __init__(self, dev:Device, zone_config):
        self.ID = zone_config['id']
        self._dev = dev
        self._ind = zone_config['led_indexes']
        self.COUNT = zone_config['leds']
        self.PAL_ID:int = zone_config.get('secondary', 0)
        self.COUNT_2_F = self.COUNT // 2
        self.COUNT_2_C = (self.COUNT + 1) // 2
        self.POS = zone_config.get('pos', [0, 0])

    def all(self, c) -> None:
        for index in self._ind:
            self._dev.FB0[index*3] = c[0]
            self._dev.FB0[index*3+1] = c[1]
            self._dev.FB0[index*3+2] = c[2]

    def __getitem__(self, index) -> Sequence[float]:
        return [
            self._dev.FB0[index*3],
            self._dev.FB0[index*3+1],
            self._dev.FB0[index*3+2]
        ]

    def __setitem__(self, index:int, c:Sequence[Numeric]) -> None:
        self._dev.FB0[self._ind[index]*3] = c[0]
        self._dev.FB0[self._ind[index]*3+1] = c[1]
        self._dev.FB0[self._ind[index]*3+2] = c[2]

class LineZone(RawZone):
    def __init__(self, dev:Device, zone_config):
        super().__init__(dev, zone_config)
        if 'led_percentage' not in zone_config:
            self.PERCENTAGE = [i/self.COUNT*100 for i in range(len(self._ind))]
        else:
            self.PERCENTAGE = zone_config['led_percentage']

class RingZone(RawZone):
    def __init__(self, dev:Device, zone_config):
        super().__init__(dev, zone_config)
        if 'led_angles' not in zone_config:
            self.ANGLES = [i/self.COUNT*360 for i in range(len(self._ind))]
        else:
            self.ANGLES = zone_config['led_angles']

        self.PERCENTAGE = [i/3.6 for i in self.ANGLES]


