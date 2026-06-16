import os
import re
import struct
import fcntl
import array
from math import sqrt, atan2, degrees

EV_ABS = 0x03

EVDEV_EVENT_FORMAT = 'llHHi'
EVDEV_EVENT_SIZE = struct.calcsize(EVDEV_EVENT_FORMAT)

ABS_CODES = {
    'ABS_X': 0x00,
    'ABS_Y': 0x01,
    'ABS_Z': 0x02,
    'ABS_RX': 0x03,
    'ABS_RY': 0x04,
    'ABS_RZ': 0x05,
}


def EVIOCGABS(axis):
    return 0x80184540 + axis


def get_abs_info(fd, axis):
    # input_absinfo:
    #   int value;
    #   int minimum;
    #   int maximum;
    #   int fuzz;
    #   int flat;
    #   int resolution;
    buf = array.array('i', [0, 0, 0, 0, 0, 0])

    try:
        fcntl.ioctl(fd, EVIOCGABS(axis), buf, True)
    except OSError:
        return None

    return {
        'value': buf[0],
        'min': buf[1],
        'max': buf[2],
        'fuzz': buf[3],
        'flat': buf[4],
        'resolution': buf[5],
    }


def calc_value(x, y):
    return int(sqrt(x*x + y*y))


def resolve_axis(axis):
    if isinstance(axis, str):
        return ABS_CODES[axis]
    return int(axis)


def find_event_by_name(target_name):
    try:
        with open('/proc/bus/input/devices', 'r') as f:
            data = f.read()
    except OSError:
        return None

    for block in data.strip().split('\n\n'):
        name_match = re.search(r'N: Name="(.+?)"', block)
        handlers_match = re.search(r'H: Handlers=(.+)', block)

        if not name_match or not handlers_match:
            continue

        name = name_match.group(1)
        handlers = handlers_match.group(1).split()

        if name != target_name:
            continue

        for handler in handlers:
            if handler.startswith('event'):
                return f'/dev/input/{handler}'

    return None


class StickState:
    def __init__(self, config: dict):
        self.CONFIG = config
        self.ZONES = config['zones']

        device_name = config.get('input_device_name')
        device_path = config.get('input_device')

        if device_path:
            self.input_path = device_path
        elif device_name:
            self.input_path = find_event_by_name(device_name)
            if self.input_path is None:
                raise FileNotFoundError(f"input device name not found: {device_name}")
        else:
            raise ValueError("input_device_name or input_device is required for StickState")

        self._evdev = os.open(
            self.input_path,
            os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK
        )

        self.__state = {
            zone_id: {
                'axis': [resolve_axis(axis) for axis in zone['input']],
                'raw': [0, 0],
                'polarity': zone.get('input_polarity', ['+', '+']),
                'angle': 0,
                'value': 0,
            }
            for zone_id, zone in self.ZONES.items()
            if 'input' in zone
        }

        self._axis_cache = {
            axis_id: [stick_id, i]
            for stick_id, state in self.__state.items()
            for i, axis_id in enumerate(state['axis'])
        }

        self._axis_norm = {}

        for axis_id in self._axis_cache:
            info = get_abs_info(self._evdev, axis_id)

            if info is None:
                continue

            amin = info['min']
            amax = info['max']
            center = (amin + amax) / 2.0
            radius = (amax - amin) / 2.0

            if radius <= 0:
                continue

            self._axis_norm[axis_id] = {
                'center': center,
                'scale': 127.0 / radius,
                'flat': info['flat'],
            }

    def update(self):
        while True:
            try:
                event_data = os.read(self._evdev, EVDEV_EVENT_SIZE)
            except BlockingIOError:
                break
            except OSError:
                break

            if len(event_data) != EVDEV_EVENT_SIZE:
                break

            try:
                _, _, e_type, e_code, e_value = struct.unpack(EVDEV_EVENT_FORMAT, event_data)
            except struct.error:
                break

            if e_type != EV_ABS:
                continue

            if e_code not in self._axis_cache:
                continue

            norm = self._axis_norm.get(e_code)

            if norm is not None:
                delta = e_value - norm['center']

                if norm['flat'] and abs(delta) <= norm['flat']:
                    value = 0
                else:
                    value = int(delta * norm['scale'])
                    value = max(-127, min(127, value))
            else:
                value = int(e_value // 256)

            self.calc(e_code, value)

    def calc(self, id, value):
        cached = self._axis_cache.get(id)
        if cached is None:
            return

        stick, axis = cached
        state = self.__state[stick]
        raw = state['raw']

        if state['polarity'][axis] == '-':
            value = -value

        if raw[axis] == value:
            return

        raw[axis] = value

        x, y = raw

        raw_value = calc_value(x, y)

        if raw_value <= 2:
            state['value'] = 0
            return

        state['angle'] = 180 - degrees(atan2(x, y))
        state['value'] = 1 if raw_value > 125 else raw_value / 125

    def __getitem__(self, name: str) -> dict:
        return self.__state[name]
