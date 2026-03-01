from .._base_effect import BaseEffect
from ...device import Device
import os

_metadata = {
    'order': 50,
    'name': 'Screen Aura',
    'reqs': ['dev']
}

def calc_seek(x, y, res):
    ret = []
    for x_ in range(res, x, res):
        for y_ in range(res, y, res):
            ret.append(y_*x*4 + x_*4)
    return ret

class Effect(BaseEffect):
    def __init__(self, dev: Device, initial_tick: int) -> None:
        super().__init__(dev, initial_tick)

        ret = os.popen('fbset').read().strip().split('\n')[0].split('"')[1].split('-')[0].split('x')

        self.X = int(ret[0])
        self.Y = int(ret[1])

        print(self.X, self.Y)
        self.SEEK = calc_seek(self.X, self.Y, 60)

        self.fb0 = open('/dev/fb0', 'r+b')

    
    def apply(self, t, palettes):
        
        a = [0,0,0]
        hist = {
            (.3,.3,.3): .0
        }
        for p in self.SEEK:
            self.fb0.seek(p, 0)
            a = self.fb0.read(3)
            #self.fb0.seek(p, 0)
            #self.fb0.write(bytes([0,0,255]))
            a = [int(b)/255 for b in a]

            if abs(max(a) - min(a)) > 0.1:
                hist[(a[2], a[1], a[0])] = hist.get((a[2], a[1], a[0]), 0) + max(a)

        self.dev.Raw.all(list(max(hist.keys(), key=lambda a: hist[a])))
    
    def framekey(self, t):
        return None