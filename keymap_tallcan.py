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
    
# Map pin numbers to physical key locations
_LAYOUT = bytes((12, 13, 14, 15,    10,  9,  8,  7,
                 17, 18, 19, 20,     5,  4,  3,  2,
                     21, 16,  1,     0, 11,  6))

EXIT_KEYS = bytes((12, 13, 14, 15, 10, 9, , 7))
SHUTDOWN_KEYS = bytes((12, 13, 14, 15, 17, 18, 19, 20))

# Chords are tbd
_CHORDS = {
    # A
    'B': ('E', 'O'),
    'C': ('E', 'Y'),
    'D': ('A', 'R', 'T'),
    # E
    'F': ('A', 'R'),
    'G': ('R', 'T'),
}



_KEYMAP = (
    # 0 - Base Layer
    ('S',   'T',   'R',   'A',      'A',   'R',   'T',   'S',
     'O',   'I',   'Y',   'E',      'E',   'Y',   'I',   'O',
          'CTRL', 'SHFT',   '',       '',  'L2_(ENTR)', 'L1_(TAB)',),
    # 1 - Numbers Layer
    ('4',   '3',   '2',   '1',      '1',   '2',   '3',   '4',
     '8',   '7',   '6',   '5',      '5',   '6',   '7',   '8',
             '',    '',    '',       '',    '',    ''),
    # 2 - Symbols Layer
    ('$',   '#',   '@',   '!',      '!',   '@',   '#',   '$',
     '*',   '&',   '^',   '%',      '%',   '^',   '&',   '*',
             '',    '',    '',       '',    '',    '')
    # 3 - Meta Layer
    # 4 - Navigation Layer
)

# Check _ALIASES to see what already exists in the keymap_utils 
# file.  Add any more here that you like.  These must match what's
# in the usb.device.keyboard.KeyCodes object:
# https://github.com/micropython/micropython-lib/blob/master/micropython/usb/usb-device-keyboard/usb/device/keyboard.py
_MY_ALIASES = {'RSHFT': 'RIGHT_SHIFT', }


################################
# Don't edit stuff below here! #
################################

import keymap_utils as ku
ku.update_aliases(_MY_ALIASES)
CHORD_KEYS = ku.get_chord_keys(_CHORDS)
# CHORDS = ku.get_chords(_CHORDS
INV_LAYOUT = ku.get_inverted_layout(_LAYOUT)
ACTIONS = ku.get_actions(_KEYMAP)
