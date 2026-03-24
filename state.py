from enum import Enum
import json

from .colors import BLACK, BLUE, COLORS, GREEN, RED, WHITE, PALETTES, Palette, get_palette
from .device import Device
from .effects.effect_store import MODES, NOTIS, STATES
from .effects._base_effect import BaseEffect
from .utilities import mix
from .confloader import CONFIG, read_config_knulli

read_config_knulli()

MAX_BR = 100

class RGBState:
    def __init__(self) -> None:
        self.DEV = Device()
        self._br = 100
        self._tr = 100
        self._sc = 100
        self._palette = [Palette([0,0,0], [0,0,0]), Palette([0,0,0], [0,0,0])]
        self._target_palette = [Palette([0,0,0], [0,0,0]), Palette([0,0,0], [0,0,0])]
        self._target_br = 100
        self._target_tr = 100
        self._target_sc = 100

        # Flip true if config changes
        self._idle = False

        self._tick = 0

        self.FPS = 30
        #self.FPS = 1
        self.FRTM = int(1000 / self.FPS)

        self._mode = 'static'
        self.modes:list[BaseEffect] = [MODES['static']['class'](self.DEV, self._tick)]
        self.events:list[Event] = [
            #Event(EventType.RunEffect, 'up', 1, RED),
            #Event(EventType.RunEffect, 'up', 1, GREEN),
            #Event(EventType.RunEffect, 'up', 1, BLUE),
            #Event(EventType.Notification, 'round', 1, WHITE),
            #Event(EventType.Notification, 'blink_off', 1, WHITE),
            Event(EventType.Notification, 'frame', 1, BLACK),
            Event(EventType.FadeIn)
        ]
    
    @staticmethod
    def get() -> 'RGBState':
        global _INSTANCE
        if _INSTANCE is None:
            _INSTANCE = RGBState()
        return _INSTANCE

    def manage_events(self):
        if len(self.events) > 0:
            #print([f"{a.type.name}/{a.payload}: {a.timer} {a.running}" for a in self.events])
            self._idle = False
            event = self.events[0]
            if event.type == EventType.LoadConfig:
                print(f"[state] LoadConfig")
                self.load_config()
                self.events.pop(0)
                if "has_hw_modes" in self.DEV.TRAITS and hasattr(self.DEV.driver, "sync"):
                    # Force variables to target so the first frame isn't black/wrong
                    self._br = self._target_br
                    self._tr = MAX_BR 
                    self.apply_brightness()
                    self.DEV.driver.sync(self)
                return True
            if event.type == EventType.Die:
                print(f"[state] Die")
                self.DEV.close()
                quit()
            if event.type == EventType.FadeIn:
                print(f"[state] FadeIn")
                self.DEV.nuke_savestates()
                self._target_tr = MAX_BR
                self.events.pop(0)
                return True
            if event.type == EventType.FadeOut:
                if not event.running:
                    print(f"[state] FadeOut")
                    self.DEV.nuke_savestates()
                    self._target_tr = 0
                    event.running = True
                    event.timer = 4
                if(self._tr == 0):
                    event.timer -= 1
                    if event.timer == 0:
                        self.events.pop(0)
                        return True
            if event.type == EventType.AddLayer:
                if not event.running:
                    running = False
                    for i in range(len(self.modes)):
                        if self.modes[i].__class__ is STATES[event.payload]['class']:
                            running = True
                    if not running:
                        print(f"[state] AddLayer [{event.payload}]")
                        event.running = True
                        self._target_tr = 0
                        self.DEV.nuke_savestates()
                    else:
                        self.events.pop(0)
                if event.running and self._tr == 0:
                    self.modes.append(STATES[event.payload]['class'](self.DEV, self._tick))
                    self.events.pop(0)
                    self._target_tr = MAX_BR

            if event.type == EventType.RemoveLayer:
                if not event.running:
                    for m in self.modes:
                        if m.__class__ is STATES[event.payload]['class']:
                            event.running = True
                            print(f"[state] RemoveLayer [{event.payload}]")
                            self._target_tr = 0
                
                if not event.running:
                    self.events.pop(0)
                    return True

                if event.running and self._tr == 0:
                    self.events.pop(0)
                    for i in range(len(self.modes)):
                        if self.modes[i].__class__ is STATES[event.payload]['class']:
                            self.modes.pop(i)
                            break
                    self.DEV.nuke_savestates()
                    self._target_tr = MAX_BR
                    return True

            if event.type == EventType.ChangeMode:
                print(f"[state] ChangeMode [{event.payload}]")
                self._mode = event.payload

                # 1. Check if it's a standard software mode
                if event.payload in MODES:
                    self.modes[0] = MODES[event.payload]['class'](self.DEV, self._tick)
                
                # 2. Check if it's a hardware-specific mode supported by the driver
                elif hasattr(self.DEV.driver, 'HW_MODES') and event.payload in self.DEV.driver.HW_MODES:
                    # Instantiate the HW mode class and put it in the active modes list
                    self.modes[0] = MODES['static']['class'](self.DEV, self._tick)

                self._tr = 0
                self.events.pop(0)
                self.DEV.nuke_savestates()
                self.events.append(Event(EventType.FadeIn))
            if event.type == EventType.Notification:
                if not event.running:
                    print(f"[state] Notification [{event.payload}]")
                    self.DEV.nuke_savestates()
                    self._tr = MAX_BR
                    self._target_tr = MAX_BR
                    self.apply_brightness()
                    event.running = True
                    self.modes.append(NOTIS[event.payload]['class'](self.DEV, self._tick))
                    event.timer = event.repeat * NOTIS[event.payload]['metadata']['duration']
                else:
                    event.timer -= 1
                    if event.timer == 0:
                        self.events.pop(0)
                        self.modes.pop()
                        self._tr = 0
                        self._target_tr = 0
                        self.apply_brightness()
                        self.DEV.nuke_savestates()
                        return True

    def get_palette(self):
        if len(self.events) > 0:
            if self.events[0].palette is not None:
                return [self.events[0].palette, self.events[0].palette]
        return self._palette

    def render(self, TICK):
        #print("[render]", TICK, self._tr)
        self._tick = TICK
        while self.manage_events(): pass
        mode = self.modes[-1]
        conf_done = True

        if not self._idle:
            conf_done = self.smooth_conf()
            if conf_done and not self._idle and len(self.modes) == 1:
                self._idle = True
                print('[render] Entered IDLE')
            #print("Idle", self._idle)

        #print("cd:", conf_done, "id:", self._idle, "br:", int(self.DEV.BR*100))
        mode.prepare()

        framekey = mode.framekey(TICK)
        if not self.DEV.recall(framekey):
            mode.apply(TICK, self.get_palette())
            if conf_done:
                self.DEV.savestate(framekey)

    def write(self):
        self.DEV.write()
    
    def load_config(self):

        print("\n(Re)Loaded Config:")
        for k, v in CONFIG.items():
            print(f"    [{k}]: {v}")

        self.DEV.nuke_savestates()

        if CONFIG['mode'] != self._mode:
            if self._mode != "null":
                self.events.append(Event(EventType.FadeOut))
            self.events.append(Event(EventType.ChangeMode, CONFIG['mode']))
            self.events.append(Event(EventType.FadeIn))
            self._mode = CONFIG['mode']

        self._target_br = 40 + int(CONFIG['brightness'] * 0.6) 

        raw_palette = [[0,0,0], [0,0,0]]
        if CONFIG['color.palette'] is not None:
            raw_palette = get_palette('-'.join(PALETTES[CONFIG['color.palette']]))
        if CONFIG['color.primary'] is not None:
            raw_palette[0] = COLORS[CONFIG['color.primary']]
        if CONFIG['color.secondary'] is not None:
            raw_palette[1] = COLORS[CONFIG['color.secondary']]
        self._target_palette = [Palette(*raw_palette), Palette(*raw_palette)]
        if CONFIG['color.invert.secondary']:
            self._target_palette[1] = self._target_palette[1].swap()
        if CONFIG['color.mod'] == 'twilight':
            self._target_palette[0].bg = [.0,.0,.0]
            self._target_palette[1].bg = [.0,.0,.0]
        if CONFIG['color.mod'] == 'sparkle':
            self._target_palette[0].fg = mix([1.0,1.0,1.0], 0.7, self._target_palette[0].bg, 0.3)
            self._target_palette[1].fg = mix([1.0,1.0,1.0], 0.7, self._target_palette[1].bg, 0.3)
        if CONFIG['color.mod'] == 'haze':
            self._target_palette[0].bg = mix([.7,.7,.7], 0.7, self._target_palette[0].fg, 0.2)
            self._target_palette[1].bg = mix([.7,.7,.7], 0.7, self._target_palette[1].fg, 0.2)
        if not CONFIG['brightness.adaptive']:
            self._target_sc = MAX_BR

        # If the driver has a sync method, we call it now to init the hardware state
        if "has_hw_modes" in self.DEV.TRAITS: #
            # 1. Update the actual palette used by the driver to the one we just calculated
            self._palette = [self._target_palette[0], self._target_palette[1]] #
            
            # 2. Slam the brightness/scale to targets (bypassing smooth_conf)
            self._br = self._target_br #
            self._sc = self._target_sc #
            self._tr = MAX_BR # Force transparency to 100% so it's not "fading in"
            self.apply_brightness() #

            # 3. Now sync the hardware while the variables are exactly where they need to be
            if hasattr(self.DEV.driver, "sync"): #
                print(f"[state] Hardware Sync: Mode={self._mode} BR={self._br}") #
                self.DEV.driver.sync(self) #

    
    def apply_brightness(self):
        self.DEV.BR = self._tr*self._tr*self._br*self._br*self._sc / (100**5)

    def smooth_conf(self):

        done = True

        for i in range(2):
            done = self._palette[i].paintdrop(self._target_palette[i]) and done
        
        if self._br != self._target_br:
            self._br += -2 if self._target_br < self._br else 2
            if abs(self._br - self._target_br) < 2:
                self._br = self._target_br
            done = False

        if self._sc != self._target_sc:
            self._sc += -5 if self._target_sc < self._sc else 5
            if abs(self._sc - self._target_sc) < 5:
                self._sc = self._target_sc
            done = False

        if self._tr != self._target_tr:
            self._tr += -10 if self._target_tr < self._tr else 10
            done = False
        
        if not done:
            self.apply_brightness()
        
        return done

_INSTANCE:RGBState|None = None

class EventType(Enum):
    Die = 'die'
    LoadConfig = 'load_config'
    ChangeMode = 'change_mode'
    AddLayer = 'add_layer'
    RemoveLayer = 'remove_layer'
    Notification = 'notification'
    FadeOut = 'fadeout'
    FadeIn = 'fadein'

class Event:
    def __init__(self, type:EventType, payload:str='', repeat:int=1, palette:Palette|None=None) -> None:
        self.type = type
        self.payload = payload
        self.repeat = repeat
        self.palette = palette
        self.timer = 0
        self.running = False
    
    def __str__(self) -> str:
        return f'Event: {self.type}/{self.payload}'