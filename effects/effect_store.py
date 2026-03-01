import os
from importlib import import_module

dirname = os.path.dirname(os.path.abspath(__file__)) + '/modes'

print('\nLoading Effect Modes:')

MODES = {}

modes_list = []

for f in os.listdir(dirname):
    if f[0] != '_' and os.path.isfile("%s/%s" % (dirname, f)) and f[-3:] == ".py":
        name = f.replace('.py','')
        effect_module = import_module(".effects.modes."+name, package="silkyrgb")
        modes_list.append([effect_module._metadata.get('order', 10000), name, effect_module])

for _, name, effect_module in sorted(modes_list):
    MODES[name] = {
        'metadata': effect_module._metadata,
        'class': effect_module.Effect
    }
    print(f'    [{name}]: {effect_module._metadata["name"]}')

dirname = os.path.dirname(os.path.abspath(__file__)) + '/notifications'

print('\nLoading Notification Modes:')

NOTIS = {}

for f in os.listdir(dirname):
    if f[0] != '_' and os.path.isfile("%s/%s" % (dirname, f)) and f[-3:] == ".py":
        name = f.replace('.py','')
        effect_module = import_module(".effects.notifications."+name, package="silkyrgb")
        NOTIS[name] = {
            'metadata': effect_module._metadata,
            'class': effect_module.Effect
        }
        print(f'    [{name}]: {effect_module._metadata["name"]}')

dirname = os.path.dirname(os.path.abspath(__file__)) + '/states'

print('\nLoading State Modes:')

STATES = {}

for f in os.listdir(dirname):
    if f[0] != '_' and os.path.isfile("%s/%s" % (dirname, f)) and f[-3:] == ".py":
        name = f.replace('.py','')
        effect_module = import_module(".effects.states."+name, package="silkyrgb")
        STATES[name] = {
            'metadata': effect_module._metadata,
            'class': effect_module.Effect
        }
        print(f'    [{name}]: {effect_module._metadata["name"]}')

