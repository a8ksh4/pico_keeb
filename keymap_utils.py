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
            ']': 'CLOSE_BRACKET', '\\': 'BACKSLASH', #  '#': 'HASH', not on US layout
            ';': 'SEMICOLON', "'": 'QUOTE', '`': 'GRAVE', ',': 'COMMA', 
            '.': 'DOT', '/': 'SLASH', 'CAPS': 'CAPS_LOCK',
            'PTSC': 'PRINT_SCREEN', 'SCRL': 'SCROLL_LOCK', 'PAUS': 'PAUSE',
            'INS': 'INSERT', 'PGUP': 'PAGEUP', 'DEL': 'DELETE',
            'PGDN': 'PAGEDOWN', 'RGHT': 'RIGHT', 
            'CTRL': 'LEFT_CTRL', 'SHFT': 'LEFT_SHIFT', 'ALT': 'LEFT_ALT',
            'UI': 'LEFT_UI', 'RCTRL': 'RIGHT_CTRL', 'RSHFT': 'RIGHT_SHIFT',
            'RALT': 'RIGHT_ALT', 'RUI': 'RIGHT_UI', 

            '!': 'LEFT_SHIFT:N1', '@': 'LEFT_SHIFT:N2', '#': 'LEFT_SHIFT:N3',
            '$': 'LEFT_SHIFT:N4', '%': 'LEFT_SHIFT:N5', '^': 'LEFT_SHIFT:N6',
            '&': 'LEFT_SHIFT:N7', '*': 'LEFT_SHIFT:N8', '(': 'LEFT_SHIFT:N9',
            ')': 'LEFT_SHIFT:N0',
            '{': 'LEFT_SHIFT:OPEN_BRACKET', '}': 'LEFT_SHIFT:CLOSE_BRACKET',
            '?': 'LEFT_SHIFT:SLASH', 'GUI': 'LEFT_UI'
            }

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
    {0: {<keys_active>: (<tap_action>, <hold_action>, <in_chord>, ...),
         <keys_active>: (...),
         ...},
     1: {<keys_active>: (...),
         ...},
     ...}

     Current items in the table list:
     tap_action, hold_action, in_chord, oneshot_tap, oneshot_hold, shift_mod, ctrl_mod?
     <keys_active>: (<tap_action>, <hold_actin, <in_chord>,
                        <oneshot_tap>, <oneshot_hold>, 
                        <tap_modifiers>, <hold_modifiers>)
    '''
    if len(chords) > len(keymap):
        raise ValueError(f"_CHORDS has {len(chords)} layers, but _KEYMAP only has {len(keymap)}")
    lookup = {}
    print("Building lookup table...")
    for layer_num, keys in enumerate(keymap):
        print(f"Layer {layer_num}: {keys}")
        layer_chords = chords[layer_num] if layer_num < len(chords) else ()
        chords_keys = get_chording_keys(layer_chords)
        lookup[layer_num] = {}
        for key_num, key in enumerate(keys):
            pin_num = layout[key_num]
            assert isinstance(key, str), f"Key must be a string: {key}"
            if '_()' in key:
                hold, tap = key.split('_(')
                assert(tap.endswith(')'), f"Invalid key format: {key}")
                tap = tap[:-1]  # remove trailing ')'
            else:
                tap, hold = key, None
            hold_action, hold_modifier = _lookup(hold)
            tap_action, tap_modifier = _lookup(tap)
            # Keys that are part of a chord wait to see if the rest of it
            # gets pressed, so this checks the key name, not its keycode.
            in_chord = tap in chords_keys
            pin_byte = 1 << pin_num
            oneshot_tap = False
            oneshot_hold = False
            lookup[layer_num][pin_byte] = (tap_action, hold_action, in_chord,
                                           oneshot_tap, oneshot_hold,
                                           tap_modifier, hold_modifier)

        # add items to the lookup dict for this layer directly for each chord
        add_chording_keys(layer_num, layer_chords, keys, layout, lookup[layer_num])
        add_partial_chords(lookup[layer_num])
    return lookup

def _combinations(list_of_lists, origin=False):
    '''returns list of all combinations of elements from list
    of lists.'''
    if origin:
        print("Combinations lol:", list_of_lists)
    out = []
    # sublist = list_of_lists.pop()
    sublist = list_of_lists[0]
    sublist = [[element] for element in sublist]  # transpose?
    if len(list_of_lists) == 1:  # last one
        return sublist

    # at least one more sub list in the list of lists
    remaining = list_of_lists[1:]
    combs = _combinations(remaining)

    out = []
    for element in sublist:
        for comb in combs:
            out.append(element + comb)
    if origin:
        print("Combinations out:", out)
    return out


def add_chording_keys(layer_num, layer_chords, layer_keymap, layout, layer_lookup):
    '''Adds an entry to one layer's lookup dict for each of that layer's
    chords.  A key name that's on the keyboard more than once (e.g. on both
    sides) gives the chord every combination of those positions.
    Raises ValueError for mistakes in the chords, rather than silently
    dropping a chord.'''
    chord_names = {}  # chord_byte -> chord, to report conflicts
    for result, chord_keys in layer_chords:
        action, modifier = _lookup(result)  # Handle alias or whatever.
        if action is None:
            raise ValueError(f"Layer {layer_num} chord {chord_keys}: output {result!r} isn't a KeyCode or alias")
        pin_byte_sets = []
        for ck in chord_keys:
            pin_bytes = [1 << layout[n] for n, k in enumerate(layer_keymap) if k == ck]
            if not pin_bytes:
                raise ValueError(f"Layer {layer_num} chord {result!r}: key {ck!r} isn't in that layer of _KEYMAP")
            pin_byte_sets.append(pin_bytes)

        for comb in _combinations(pin_byte_sets, True):
            chord_byte = 0
            for key_byte in comb:
                chord_byte |= key_byte
            if chord_byte in chord_names:
                raise ValueError(f"Layer {layer_num}: chords {chord_names[chord_byte]} and {(result, chord_keys)} use the same keys")
            chord_names[chord_byte] = (result, chord_keys)
            print('Chord', result, chord_keys, chord_byte, action, modifier)
            # The chord result is its tap action, so pressing and
            # releasing the chord sends it.
            layer_lookup[chord_byte] = (action, None, True,
                                        False, False,
                                        modifier, 0)


# Entry for a combination of keys that isn't a chord, but is part of one, so
# the event keeps waiting for the rest of the chord.  One shared tuple.
_PARTIAL_CHORD = (None, None, True, False, False, 0, 0)


def add_partial_chords(layer_lookup):
    '''Adds a _PARTIAL_CHORD entry for every combination of two or more keys
    that is part of a chord in this layer, and isn't already an entry.  This
    lets chord keys be pressed in any order, e.g. A, T, R for the A+R+T chord
    even though A+T alone isn't a chord.'''
    chord_bytes = [key_byte for key_byte, entry in layer_lookup.items()
                   if entry[2] and key_byte & (key_byte - 1)]
    for chord_byte in chord_bytes:
        # Walk every sub-mask of the chord's bits.
        sub = (chord_byte - 1) & chord_byte
        while sub:
            if sub & (sub - 1) and sub not in layer_lookup:  # 2+ keys
                layer_lookup[sub] = _PARTIAL_CHORD
            sub = (sub - 1) & chord_byte


def get_chording_keys(layer_chords):
    '''Returns a set of keys used in any chord in a layer so that we know to
    wait for hold timeout on actions using these keys even if there
    isn't an associated hold action (tap only)'''
    out = set()
    for _, keys in layer_chords:
        out.update(keys)
    return out

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
    modifier = 0
    if name is None:
        return None, modifier
    print('lookup1:', name)
    if name in _ALIASES:
        name = _ALIASES[name]
    print('lookup2:', name)
    if ':' in name:
        mod, name = name.split(':')
        mod = getattr(KeyCode, mod, 0)
        assert(mod is not None)
        modifier = mod
        print('modifier:', modifier)
    if name.startswith('L') and len(name) > 1 and name[1].isdigit():
        return name, modifier  # layer shift, not a keycode
    code = getattr(KeyCode, name, None)  # return None if not found
    print('lookup3:', code)
    return code, modifier

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