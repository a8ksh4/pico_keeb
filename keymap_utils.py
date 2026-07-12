'''You probably don't want to modify anything in this file.
Import it from your keymap file and use its functions as shown
in the example keymap.'''

from array import array
from usb.device.keyboard import KeyCode
# This pulls in all of the keys we can use:

# And some aliases that are shorter:
# The key is what you want, and each value must exist in the
# KeyCode object: https://github.com/micropython/micropython-lib/blob/master/micropython/usb/usb-device-keyboard/usb/device/keyboard.py
_ALIASES = {'ENTR': 'ENTER',     'SHFT': 'LEFT_SHIFT',
            'CTRL': 'LEFT_CTRL',  }

def update_aliases(aliases):
    _ALIASES += aliases

# Action encoding (16 bits is plenty):
#   bits 0-7:  keycode (0 = none)
#   bits 8-10: layer number
#   bits 11-13: behavior: 0=plain key, 1=modifier, 2=hold-layer/tap-key,
#                          3=oneshot, 4=tap-tap, ...
_B_PLAIN = const(0)
_B_MOD = const(1)
_B_HOLDTAP = const(2)

def parse_keys(s):
    if not s:
        return 0
    if s.startswith('L') and '_(' in s:          # 'L2_(ENTR)'
        layer = int(s[1])
        tap = s[s.index('(')+1 : s.index(')')]
        code = _lookup(tap)
        return (_B_HOLDTAP << 11) | (layer << 8) | code
    code = _lookup(s)
    if code < 0:                                  # modifier
        return (_B_MOD << 11) | (-code)
    return code                                   # plain key, behavior 0

def _lookup(name):
    return getattr(KeyCode, _ALIASES.get(name, name))

def get_actions(keymap):
    return tuple(array('H', (parse_keys(k) for k in layer)) for layer in keymap)

# Decode an action:
# act = ACTIONS[layer][i]
# code = act & 0xFF
# behavior = (act >> 11) & 0x7

# Inverted layout is faster for lookup in event loop
def get_inverted_layout(layout):
    inv_layout = bytearray(max((len(layout), max(layout))))
    for pos, scan in enumerate(layout):
        inv_layout[scan] = pos
    return inv_layout