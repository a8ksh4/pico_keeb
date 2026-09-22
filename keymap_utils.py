'''You probably don't want to modify anything in this file.
Import it from your keymap file and use its functions as shown
in the example keymap.'''

from array import array
from usb.device.keyboard import KeyCode
# This pulls in all of the keys we can use:

# And some aliases that are shorter:
# The key is what you want, and each value must exist in the
# KeyCode object: https://github.com/micropython/micropython-lib/blob/master/micropython/usb/usb-device-keyboard/usb/device/keyboard.py
_ALIASES = {'0': 'N0', '1': 'N1', '2': 'N2', '3': 'N3', '4': 'N4',
            '5': 'N5', '6': 'N6', '7': 'N7', '8': 'N8', '9': 'N9',
            'ENTR': 'ENTER', 'ESC': 'ESCAPE', 'BKSP': 'BACKSPACE',
            ' ': "SPACE", '-': 'MINUS', '=': 'EQUAL', '[': 'OPEN_BRACKET',
            ']': 'CLOSED_BRACKET', '\\': 'BACKSLASH', '#': 'HASH',
            ';': 'SEMICOLON', "'": 'QUOTE', '`': 'GRAVE', ',': 'COMMA', 
            '.': 'DOT', '/': 'SLASH', 'CAPS': 'CAPS_LOCK',
            'PTSC': 'PRINT_SCREEN', 'SCRL': 'SCROLL_LOCK', 'PAUS': 'PAUSE',
            'INS': 'INSERT', 'PGUP': 'PAGEUP', 'DEL': 'DELETE',
            'PGDN': 'PAGEDOWN', 'RGHT': 'RIGHT', 
            'CTRL': 'LEFT_CTRL', 'SHFT': 'LEFT_SHIFT', 'ALT': 'LEFT_ALT',
            'UI': 'LEFT_UI', 'RCTRL': 'RIGHT_CTRL', 'RSHFT': 'RIGHT_SHIFT',
            'RALT': 'RIGHT_ALT', 'RUI': 'RIGHT_UI', }

def update_aliases(aliases):
    '''Updates the global _ALIASES dictionary with new aliases.'''
    # _ALIASES += aliases
    for alias, key in aliases.items():
        _ALIASES[alias] = key
    return _ALIASES


def get_lookup_table(chords, keymap, layout, aliases, game_layer):
    '''Returns a lookup table that we can compare pressed
    keys against, respective to the active layer, and get 
    actions, etc without any allocations!
    Structure is like:
    {0: {<keys_active>: (<tap_action>, <hold_action>, <in_chord>),
         <keys_active>: (<tap_action>, <hold_action>, <in_chord>),
         ...},
     1: {<keys_active>: (<tap_action>, <hold_action>, <in_chord>),
         ...},
     ...}
    '''
    c_keys = get_chording_keys(chords)
    lookup = {}
    print("Building lookup table...")
    for layer_num, keys in enumerate(keymap):
        print(f"Layer {layer_num}: {keys}")
        lookup[layer_num] = {}
        for key_num, key in enumerate(keys):
            pin_num = layout[key_num]
            # if isinstance(key, tuple):
            #     hold, tap = key
            assert isinstance(key, str), f"Key must be a string: {key}"
            if '_()' in key:
                hold, tap = key.split('_(')
                assert(tap.endswith(')'), f"Invalid key format: {key}")
                tap = tap[:-1]  # remove trailing ')'
            else:
                tap, hold = key, None
            # if hold == '':
            #     hold = tap
            hold_action = _lookup(hold)
            tap_action = _lookup(tap)
            in_chord = tap_action in c_keys
            pin_byte = 1 << pin_num
            oneshot_tap = False
            oneshot_hold = False
            lookup[layer_num][pin_byte] = (tap_action, hold_action, in_chord,
                                           oneshot_tap, oneshot_hold)
    return lookup

def get_chording_keys(chords):
    keys = set()
    for ckeys in chords.values():
        keys.update(ckeys)
    return keys

# def parse_keys(s):
#     if not s:
#         return 0
#     if s.startswith('L') and '_(' in s:          # 'L2_(ENTR)'
#         layer = int(s[1])
#         tap = s[s.index('(')+1 : s.index(')')]
#         code = _lookup(tap)
#         return (_B_HOLDTAP << 11) | (layer << 8) | code
#     code = _lookup(s)
#     if code < 0:                                  # modifier
#         return (_B_MOD << 11) | (-code)
#     return code                                   # plain key, behavior 0

def _lookup(name):
    if name is None:
        return None
    print('lookup1:', name)
    if name in _ALIASES:
        name = _ALIASES[name]
    print('lookup2:', name)
    if name.startswith('L') and name[1].isdigit():
        return name  # layer shift, not a keycode
    code = getattr(KeyCode, name, None)  # return None if not found
    print('lookup3:', code)
    return code

# def get_actions(keymap):
#     return tuple(array('H', (parse_keys(k) for k in layer)) for layer in keymap)

# Decode an action:
# act = ACTIONS[layer][i]
# code = act & 0xFF
# behavior = (act >> 11) & 0x7

# Inverted layout is faster for lookup in event loop
# def get_inverted_layout(layout):
#     inv_layout = bytearray(max((len(layout), max(layout))))
#     for pos, scan in enumerate(layout):
#         inv_layout[scan] = pos
#     return inv_layout