from .bottle import run, route, get, request
from .colors import AMBER, BLUE, GREEN, PALETTES, RED, WHITE, Palette
from .confloader import CONFIG, conf_map, read_config_knulli, set_option
from .effects.effect_store import MODES, NOTIS
from .state import RGBState, Event, EventType
from .utilities import Color, hex_to_rgb
from copy import deepcopy
from json import dumps

STATE = RGBState.get()

presets = {
    'battery_charging': [
        Event(EventType.Notification, 'pulse', 3, GREEN),
    ],
    'battery_discharging1': [
        Event(EventType.Notification, 'pulse_back', 1, RED),
    ],
    'battery_discharging2': [
        Event(EventType.Notification, 'pulse_back', 1, Palette([1,0.7,0])),
    ],
    'battery_discharging3': [
        Event(EventType.Notification, 'pulse_back', 1, GREEN),
    ],
    'battery_full': [
        Event(EventType.Notification, 'pulse', 1, GREEN),
        Event(EventType.Notification, 'fill', 1, GREEN),
        Event(EventType.Notification, 'blink_off', 1, GREEN),
    ],
    'battery_low1': [
        Event(EventType.Notification, 'blink', 2, AMBER),
    ],
    'battery_low2': [
        Event(EventType.Notification, 'blink', 3, RED),
    ],
    'cheevo': [
        Event(EventType.Notification, 'cheevo', 1),
    ]
}

def run_preset_effect(preset):
    print(f"[animation] preset: [{preset}]")
    STATE.events.append(Event(EventType.FadeOut))
    for e in presets[preset]:
        STATE.events.append(deepcopy(e))
    STATE.events.append(Event(EventType.FadeIn))

@route("/reload-config")
def reload_config():
    read_config_knulli()
    STATE.events.append(Event(EventType.LoadConfig))
    return ""

@route("/set-config", method='POST')
def set_config():
    req = request.body.read().decode().split(' ', maxsplit=1) # pyright: ignore[reportAttributeAccessIssue]
    set_option(req[0], req[1])
    STATE.events.append(Event(EventType.LoadConfig))
    return f"[{req[0]}]: {req[1]}\n"

@route("/animation", method='POST')
def animation():
    req = request.body.read().decode().split(";") # pyright: ignore[reportAttributeAccessIssue]

    command_list = []

    for com in req:
        com2 = com.strip()
        if com2 in presets:
            run_preset_effect(com2)
        else:
            try:
                n, c, hex_ = com2.split()
                command_list.append(Event(EventType.Notification, n, int(c), Palette(hex_to_rgb(hex_))))
            except Exception as e:
                return "Error while processing Command:\n[name] [count] [hex_color]\n"
            
    if len(command_list) > 0:
        STATE.events.append(Event(EventType.FadeOut))
        for c in command_list:
            STATE.events.append(c)
        STATE.events.append(Event(EventType.FadeIn))

    return ""


@route("/update-battery-state", method='POST')
def battery():
    req = request.body.read().decode().split() # pyright: ignore[reportAttributeAccessIssue]

    last_pct = STATE.DEV.BATTERY['percentage']
    cur_pct = int(req[0])

    thresh_pct = CONFIG["battery.low.threshold"]

    last_state = STATE.DEV.BATTERY['state']
    cur_state = req[1]

    if cur_state != last_state or cur_pct != last_pct:

        print(f"[bat] [{last_pct}/{last_state}] -> [{cur_pct}/{cur_state}]")

        if CONFIG['battery.charging'] == 'notification' and cur_state != last_state: # notification mode
            if cur_state == 'Charging':
                run_preset_effect('battery_charging')
            if cur_state == 'Full':
                run_preset_effect('battery_full')
            if cur_state == 'Discharging':
                if STATE.DEV.BATTERY['percentage'] < 5:
                    run_preset_effect('battery_discharging1')
                elif STATE.DEV.BATTERY['percentage'] < 50:
                    run_preset_effect('battery_discharging2')
                else:
                    run_preset_effect('battery_discharging3')
            STATE.events.append(Event(EventType.RemoveLayer, 'charging'))
        elif CONFIG['battery.charging'] == 'continuous' and cur_state != last_state:
            if cur_state != last_state:
                if cur_state == 'Charging':
                    STATE.events.append(Event(EventType.AddLayer, 'charging'))
                else:
                    STATE.events.append(Event(EventType.RemoveLayer, 'charging'))
        elif cur_state != last_state:
            STATE.events.append(Event(EventType.RemoveLayer, 'charging'))

        if CONFIG['battery.low'] == 'notification' and cur_state == 'Discharging' and cur_pct != last_pct:
            if cur_pct <= thresh_pct:
                run_preset_effect('battery_low1')
            elif cur_pct <= 5:
                run_preset_effect('battery_low2')
        elif CONFIG['battery.low'] == 'continuous' and cur_state == 'Discharging' and (cur_pct != last_pct or cur_state != last_state):
            if cur_pct <= thresh_pct:
                STATE.events.append(Event(EventType.AddLayer, 'bat_low'))
        elif cur_state != 'Discharging' or cur_pct > thresh_pct:
            STATE.events.append(Event(EventType.RemoveLayer, 'bat_low'))

        STATE.DEV.BATTERY['state'] = cur_state
        STATE.DEV.BATTERY['percentage'] = cur_pct

@route("/update-screen-state", method='POST')
def screen():
    req = request.body.read().decode() # pyright: ignore[reportAttributeAccessIssue]
    
    try:
        # Clamp value between 0 and 100 immediately
        cur_pct = max(0, min(int(req), 100))
    except ValueError:
        print("[screen] Error: Received invalid integer payload")
        return

    if CONFIG['brightness.adaptive']:
        # Use the cleaned variable for the comparison
        if STATE._target_sc != cur_pct:
            STATE._target_sc = 16 + int(cur_pct * 0.84) if cur_pct > 0 else 0
            print(f"[screen] [{STATE._sc}] -> [{STATE._target_sc}]")
            STATE.DEV.nuke_savestates()
            STATE._idle = False

@get("/kill")
def kill():
    STATE.events.append(Event(EventType.FadeOut))
    #STATE.events.append(Event(EventType.Notification, 'blink_on', 1, WHITE))
    #STATE.events.append(Event(EventType.Notification, 'round_back', 1, WHITE))
    STATE.events.append(Event(EventType.Die))

@get("/get-settings")
def settings():
    c = {}
    for k, v in conf_map.items():
        add = True
        if "reqs" in v:
            for r in v["reqs"]:
                if r not in STATE.DEV.TRAITS:
                    add = False
        if add:
            c[k] = v

    return dumps(c, indent=4)+"\n"

@get("/get-modes")
def get_modes():
    m = {}
    for k, v in MODES.items():
        add = True
        if "reqs" in v["metadata"]:
            for r in v["metadata"]["reqs"]:
                if r not in STATE.DEV.TRAITS:
                    add = False
        if add:
            m[k] = {
                "name": v["metadata"]["name"]
            }
    return dumps(m, indent=4)+"\n"

@get("/get-animations")
def get_anim():
    m = {}
    for k, v in NOTIS.items():
        add = True
        if "reqs" in v["metadata"]:
            for r in v["metadata"]["reqs"]:
                if r not in STATE.DEV.TRAITS:
                    add = False
        if add:
            m[k] = {
                "name": v["metadata"]["name"]
            }
    return dumps(m, indent=4)+"\n"

@get("/get-palettes")
def get_palettes():
    p = {}
    for k, v1 in PALETTES.items():
        p[k] = {
            "name": f"{k} ({v1[0]}, {v1[1]})"
        }

    return dumps(p, indent=4)+"\n"

def run_api():
    print("Starting HTTP Daemon: http://localhost:1235/")
    run(host='localhost', port=1235, quiet=True)

if __name__ == '__main__':
    run_api()