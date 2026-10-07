'''This is a pico_keeb keyboard layout for the "tallcan" handheld 
computer.

p     i   i     p
i     n   n     i
n     d   d     n
k     e   e     k
y     x   x     y

a b c d   e f g h - furthest finger row
i j k l   m n o p - nearest finger row
  q r u   v s t   - thumbs buttons around joystick/wheel clickers
'''
    
# Map pin numbers to physical key locations.  Key numbers follow the input
# modules in main.INPUTS: 0 encoder click, 1 stick click, 2 stick touch, then
# the matrix from 3.
_LAYOUT = bytes((13, 14, 15, 16,    11, 10,  9,  8,
                 18, 19, 20, 21,     6,  5,  4,  3,
                     22, 17,  1,     0, 12,  7,
                 2))

# Special key combinations outside keymap.
# exit_keys will halt micropython script and return to repl
EXIT_KEYS = bytes((13, 14, 15, 16, 11, 10, 9, 8))
# shutdown_keys will signal the device to power down.
SHUTDOWN_KEYS = bytes((13, 14, 15, 16, 18, 19, 20, 21))

HOLD_TIME_MS = 200  # how long to wait for a hold tap to become a hold
                    # and how long to wait for chords to be completed.
                    # 200 (1/5th of a second) is recommended. Increase
                    # a little when learning.
HOLD_TIME_US = 1000 * HOLD_TIME_MS
_GAME_LAYER = 5


# Keymap entries use QMK names (https://docs.qmk.fm/keycodes_basic) and
# functions like MO(1), DF(4), LT(1, MS_BTN1) and LSFT(8).  See KEYS.md
# for supported entries and examples.
_KEYMAP = (
    # 0 - Base Layer
    ('S',   'T',   'R',   'A',      'A',   'R',   'T',   'S',
     'O',   'I',   'Y',   'E',      'E',   'Y',   'I',   'O',
          'LCTL', 'LSFT', 'DF(5)',  'MS_BTN2',  'MO(1)', 'MO(2)',
     # stick touch
     'MO(4)'),
    # 1 - Numbers Layer
    ('4',   '3',   '2',   '1',      '1',   '2',   '3',   '4',
     '8',   '7',   '6',   '5',      '5',   '6',   '7',   '8',
             '',    '',    '',       '',    '',    '',
     # stick touch
     ''),
    # 2 - Symbols Layer
    ('$',   '#',   '@',   '!',      '!',   '@',   '#',   '$',
     '*',   '&',   '^',   '%',      '%',   '^',   '&',   '*',
             '',    '',    '',       '',    '',    '',
     # stick touch
     ''),
    # 3 - Symbols Layer 2
    ('{', '[',   ']',   '}',      '=',   '-',   '`',   '~',
     '/', '<',   '>',   '\\',      '|',   ';',   '',   '',
             '',    '',    '',       '',    '',    '',
     # stick touch
     ''),
    # 4 - Navigation Layer
    ('PGUP', 'HOME',   'UP',   'END',      'MS_BTN1',  'MS_UP',   'MS_BTN2',   'MS_WHLU',
     'PGDN', 'LEFT', 'DOWN', 'RIGHT',      'MS_LEFT',  'MS_DOWN', 'MS_RGHT',   'MS_WHLD',
             '',    '',    'DF(5)',             'MS_BTN3',  'MS_BTN1', 'MS_BTN2',
     # stick touch
     ''),
    # 5 - Game Layer has no chords or fancy stuff for fast response
    ('', '',   'UP',   '',      '',   '',   '',   '',
     '', 'LEFT','DOWN', 'RIGHT',      '',   '',   '',   '',
         '',    '',  'DF(0)', '',    '',    '',
     # stick touch
     ''),
)

# You can define aliases for keys here...
_MY_ALIASES = {}


# Chords per layer, in the same order as _KEYMAP.  Each chord is
# (output, (keys...)), where the output is any keymap entry and the keys are
# entries from that layer of _KEYMAP, written exactly as they are there.  Keys
# can be on either side.  Outputs can repeat, so more than one chord can do
# the same thing.  Layers past the end of this have no chords.
_CHORDS = (
    # 0 - Base Layer
    [
        # A
        ('B', ('E', 'O')),
        ('C', ('E', 'Y')),
        ('D', ('A', 'R', 'T')),
        # E
        ('F', ('A', 'R')),
        ('G', ('R', 'T')),
        ('H', ('E', 'I')),
        # I
        ('J', ('T', 'S')),
        ('K', ('Y', 'O')),
        ('L', ('E', 'Y', 'I')),
        ('M', ('Y', 'I', 'O')),
        ('N', ('I', 'O')),
        # O
        ('P', ('E', 'I', 'O')),
        ('Q', ('A', 'T', 'S')),
        # R
        # S
        # T
        ('U', ('Y', 'I')),
        ('V', ('R', 'S')),
        ('W', ('A', 'S')),
        ('X', ('R', 'T', 'S')),
        # Y
        ('Z', ('A', 'R', 'T', 'S')),
        (',', ('A', 'Y')),
        ('.', ('A', 'I')),
        ('/', ('A', 'O')),
        ("'", ('R', 'Y')),
        ('!', ('T', 'I')),
        ('?', ('S', 'O')),
        ('SPC', ('E', 'Y', 'I', 'O')),
        ('BSPC', ('R', 'E')),
        ('DEL', ('R', 'I')),
        ('ENT', ('A', 'E')),
        ('ESC', ('A', 'R', 'O')),
        ('TAB', ('A', 'R', 'T', 'O')),
        ('LCTL', ('S', 'E')),
        ('LGUI', ('S', 'Y')),
        ('LALT', ('S', 'I')),
        ('LSFT', ('A', 'Y', 'I', 'O')),
        ('DF(4)', ('E', 'R', 'I')),
        ('MO(3)', ('LSFT', 'LCTL')),  # Symbols 2
    ],
    # 1 - Numbers Layer
    [
        ('9', ('1', '2')),
        ('0', ('2', '3')),
        ('SPC', ('5', '6', '7', '8')),
        ('BSPC', ('2', '5')),
        ('DEL', ('2', '7')),
        ('ENT', ('1', '5')),
        ('ESC', ('1', '2', '8')),
        ('TAB', ('1', '2', '3', '8')),
    ],
    # 2 - Symbols Layer
    [
        ('SPC', ('%', '^', '&', '*')),
        ('BSPC', ('@', '%')),
    ],
    # 3 - Meta Layer
    [

    ],
    # 4 - Navigation Layer
    [
        ('BSPC', ('UP', 'RIGHT')),
        ('DEL', ('LEFT', 'UP')),
        ('ENT', ('END', 'RIGHT')),
        ('ESC', ('PGDN', 'UP', 'END')),
        ('TAB', ('PGDN', 'HOME', 'UP', 'END')),
        ('DF(0)', ('LEFT', 'UP', 'RIGHT')),
    ]
)





################################
# Don't edit stuff below here! #
################################

import keymap_utils as ku
# from keymap_utils import *
_ALIASES = ku.update_aliases(_MY_ALIASES)
LOOKUP = ku.get_lookup_table(_CHORDS, _KEYMAP, _LAYOUT, _ALIASES, _GAME_LAYER)

# CHORD_KEYS = ku.get_chording_keys(_CHORDS)
# # CHORDS = ku.get_chords(_CHORDS
# INV_LAYOUT = ku.get_inverted_layout(_LAYOUT)
# ACTIONS = ku.get_actions(_KEYMAP)
