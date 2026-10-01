'''You probably don't want to modify anything in this file.
Import it from your keymap file and use its functions as shown
in the example keymap.'''

from array import array
from usb.device.keyboard import KeyCode

# Keymap entries use QMK names, without the KC_ prefix (it's allowed, though):
# https://docs.qmk.fm/keycodes_basic
#   Basic keys:      'A', '1', 'ENT', 'BSPC', 'LSFT', ...
#   Momentary layer: 'MO(1)'                active while held
#   Default layer:   'DF(4)'                switches the base layer
#   Layer tap:       'LT(1, MS_BTN1)'       MO(1) when held, MS_BTN1 on tap
#   Mod tap:         'MT(LSFT, A)'          LSFT when held, A on tap
#   Modified key:    'LSFT(8)' or 'S(8)'    shift + 8, also C(), A(), G()
#   Mouse keys:      'MS_BTN1'..'MS_BTN3', 'MS_UP', 'MS_DOWN', 'MS_LEFT',
#                    'MS_RGHT'
# Single character shortcuts like '*' or '?' work too (see _ALIASES).

# Special actions (not keyboard keys) are ints >= 0x100: the kind in the high
# byte and an argument (layer, button, direction) in the low byte.  Keycodes
# are 0..0xFF and modifiers are negative, as in usb.device.keyboard, so
# main.py can tell them apart with `action & 0xFF00` without allocating.
MO = 0x100       # momentary layer, arg = layer
DF = 0x200       # set default layer, arg = layer
MS_BTN = 0x300   # mouse button, arg = 0 left, 1 right, 2 middle
MS_MOVE = 0x400  # mouse movement, arg = 0 up, 1 down, 2 left, 3 right

_SPECIAL_NAMES = {
    'MS_BTN1': MS_BTN | 0, 'MS_BTN2': MS_BTN | 1, 'MS_BTN3': MS_BTN | 2,
    'MS_UP': MS_MOVE | 0, 'MS_DOWN': MS_MOVE | 1,
    'MS_LEFT': MS_MOVE | 2, 'MS_RGHT': MS_MOVE | 3,
}

# QMK names that differ from the usb.device.keyboard KeyCode names.  Names
# not listed here are looked up in KeyCode directly, e.g. 'A', 'TAB', 'HOME'.
# https://github.com/micropython/micropython-lib/blob/master/micropython/usb/usb-device-keyboard/usb/device/keyboard.py
_KEYCODE_NAMES = {
    '1': 'N1', '2': 'N2', '3': 'N3', '4': 'N4', '5': 'N5',
    '6': 'N6', '7': 'N7', '8': 'N8', '9': 'N9', '0': 'N0',
    'ENT': 'ENTER', 'ESC': 'ESCAPE', 'BSPC': 'BACKSPACE', 'SPC': 'SPACE',
    'MINS': 'MINUS', 'EQL': 'EQUAL', 'LBRC': 'OPEN_BRACKET',
    'RBRC': 'CLOSE_BRACKET', 'BSLS': 'BACKSLASH', 'NUHS': 'HASH',
    'SCLN': 'SEMICOLON', 'QUOT': 'QUOTE', 'GRV': 'GRAVE', 'COMM': 'COMMA',
    'SLSH': 'SLASH', 'CAPS': 'CAPS_LOCK', 'PSCR': 'PRINTSCREEN',
    'SCRL': 'SCROLL_LOCK', 'PAUS': 'PAUSE', 'INS': 'INSERT',
    'PGUP': 'PAGEUP', 'DEL': 'DELETE', 'PGDN': 'PAGEDOWN', 'RGHT': 'RIGHT',
    'NUM': 'KP_NUM_LOCK', 'PSLS': 'KP_DIVIDE', 'PAST': 'KP_MULTIPLY',
    'PMNS': 'KP_MINUS', 'PPLS': 'KP_PLUS', 'PENT': 'KP_ENTER',
    'P1': 'KP_1', 'P2': 'KP_2', 'P3': 'KP_3', 'P4': 'KP_4', 'P5': 'KP_5',
    'P6': 'KP_6', 'P7': 'KP_7', 'P8': 'KP_8', 'P9': 'KP_9', 'P0': 'KP_0',
    'LCTL': 'LEFT_CTRL', 'LSFT': 'LEFT_SHIFT', 'LALT': 'LEFT_ALT',
    'LGUI': 'LEFT_UI', 'RCTL': 'RIGHT_CTRL', 'RSFT': 'RIGHT_SHIFT',
    'RALT': 'RIGHT_ALT', 'RGUI': 'RIGHT_UI',
}

# Names that stand for another keymap entry: QMK's shifted key names, and
# single character shortcuts.  The keymap can add more with update_aliases().
_ALIASES = {
    # QMK shifted keys
    'TILD': 'S(GRV)', 'EXLM': 'S(1)', 'AT': 'S(2)', 'HASH': 'S(3)',
    'DLR': 'S(4)', 'PERC': 'S(5)', 'CIRC': 'S(6)', 'AMPR': 'S(7)',
    'ASTR': 'S(8)', 'LPRN': 'S(9)', 'RPRN': 'S(0)', 'UNDS': 'S(MINS)',
    'PLUS': 'S(EQL)', 'LCBR': 'S(LBRC)', 'RCBR': 'S(RBRC)',
    'PIPE': 'S(BSLS)', 'COLN': 'S(SCLN)', 'DQUO': 'S(QUOT)',
    'LABK': 'S(COMM)', 'RABK': 'S(DOT)', 'QUES': 'S(SLSH)',
    # Single characters
    ' ': 'SPC', '-': 'MINS', '=': 'EQL', '[': 'LBRC', ']': 'RBRC',
    '\\': 'BSLS', ';': 'SCLN', "'": 'QUOT', '`': 'GRV', ',': 'COMM',
    '.': 'DOT', '/': 'SLSH',
    '~': 'TILD', '!': 'EXLM', '@': 'AT', '#': 'HASH', '$': 'DLR',
    '%': 'PERC', '^': 'CIRC', '&': 'AMPR', '*': 'ASTR', '(': 'LPRN',
    ')': 'RPRN', '_': 'UNDS', '+': 'PLUS', '{': 'LCBR', '}': 'RCBR',
    '|': 'PIPE', ':': 'COLN', '"': 'DQUO', '<': 'LABK', '>': 'RABK',
    '?': 'QUES',
}

# Modifier functions like 'LSFT(8)', and QMK's one letter forms like 'S(8)'.
_MOD_FUNCS = {'LSFT': 'LSFT', 'LCTL': 'LCTL', 'LALT': 'LALT', 'LGUI': 'LGUI',
              'RSFT': 'RSFT', 'RCTL': 'RCTL', 'RALT': 'RALT', 'RGUI': 'RGUI',
              'S': 'LSFT', 'C': 'LCTL', 'A': 'LALT', 'G': 'LGUI'}


def update_aliases(aliases):
    '''Updates the global _ALIASES dictionary with new aliases.'''
    for alias, key in aliases.items():
        _ALIASES[alias] = key
    return _ALIASES


def parse_key(name):
    '''Parses a keymap entry, e.g. 'A', 'LSFT(8)' or 'LT(1, MS_BTN1)', into
    (tap_action, tap_modifier, hold_action, hold_modifier).  An action is a
    keycode, a negative modifier keycode, a special action (MO | layer, ...)
    or None for nothing.  A modifier is 0 or negative, like modifier keycodes,
    with several combined as -(bits | bits).'''
    if name in _ALIASES:
        return parse_key(_ALIASES[name])
    name = name.strip()
    if not name or name == 'NO':
        return None, 0, None, 0
    if name.startswith('KC_'):
        return parse_key(name[3:])
    if name.endswith(')') and '(' in name:
        func, args = name[:-1].split('(', 1)
        return _parse_function(name, func.strip(), _split_args(args))
    if name in _SPECIAL_NAMES:
        return _SPECIAL_NAMES[name], 0, None, 0
    code = getattr(KeyCode, _KEYCODE_NAMES.get(name, name), None)
    if code is None:
        print(f"Unknown key name: {name!r}")
    return code, 0, None, 0


def _parse_function(name, func, args):
    '''Parses a function entry like 'MO(1)', given its name and arguments.'''
    def expect(n):
        if len(args) != n:
            raise ValueError(f"{name}: {func}() takes {n} argument(s)")

    if func in ('MO', 'DF'):
        expect(1)
        return (MO if func == 'MO' else DF) | int(args[0]), 0, None, 0
    if func == 'LT':
        expect(2)
        tap, tap_mod, _, _ = parse_key(args[1])
        return tap, tap_mod, MO | int(args[0]), 0
    if func == 'MT':
        expect(2)
        tap, tap_mod, _, _ = parse_key(args[1])
        return tap, tap_mod, parse_key(args[0])[0], 0
    if func in _MOD_FUNCS:
        expect(1)
        tap, tap_mod, hold, hold_mod = parse_key(args[0])
        mod = parse_key(_MOD_FUNCS[func])[0]
        return tap, -((-tap_mod) | (-mod)), hold, hold_mod
    raise ValueError(f"{name}: unknown function {func!r}")


def _split_args(args):
    '''Splits function arguments on commas that aren't inside parentheses.
    Inside a function, use names (COMM, LPRN) rather than ',' or '('.'''
    out = []
    depth = 0
    start = 0
    for i, ch in enumerate(args):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif ch == ',' and depth == 0:
            out.append(args[start:i].strip())
            start = i + 1
    out.append(args[start:].strip())
    return out


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
            if not isinstance(key, str):
                raise ValueError(f"Layer {layer_num}: key must be a string: {key!r}")
            tap_action, tap_modifier, hold_action, hold_modifier = parse_key(key)
            # Keys that are part of a chord wait to see if the rest of it
            # gets pressed, so this checks the key name, not its keycode.
            in_chord = key in chords_keys
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
        action, modifier, _, _ = parse_key(result)
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