# Notes on conventions used here:
# S_<word> means apply shift key with the character. E.g S_NINE is '('
# (<hold>, <tap>) means first item is applied when holding, and second
#                 item is applied for a tap.
# Ctrl, Shift, Alt are on three rows so that any key in the row can
#                 be used with any key in another column for, e.g ctrl+c
#                 via ctrl and tap tap tap on A to get the c.
# All words in the key map are compared against dir(adafruit_hid.keycode.Keycode)
#                 to see if they are a key, and then against KMAP.keys() to see
#                 if they are a layer.  Mouse stuff is compared to the adafriut mouse lib.
#
# Mouse stuff is:
# MOUSE_DOWN, MOUSE_LEFT, MOUSE_RIGHT, MOUSE_UP
# LEFT_BUTTON, MIDDLE_BUTTON, RIGHT_BUTTON
# 
# Chorded combos must be completed in less than the hold duration.  
# Chorded combos can result in a hold/key situation?? where hold of chord is keypress 
#    if it's released or hold function if held for hold-duration?

import board

PINS = (
    board.GP5,  board.GP4,  board.GP3,  board.GP2,
    board.GP9,  board.GP8,  board.GP7,  board.GP6,
    board.GP13, board.GP12, board.GP11, board.GP10,

    board.GP17, board.GP16, board.GP15, board.GP14,
)

# SCROLL_ENCODER = False
# Digital 1, Digital 2, Invert
SCROLL_ENCODER = (board.GP21, board.GP20, True)
# JOYSTICK_MOUSE = False
# Analog 1, Analog 2, Swap Axes, Invert X, Invert Y
JOYSTICK_MOUSE = (board.GP27, board.GP26, False, True, False)

# Chording matrix
# 0, 1, 2, 3
# 4, 5, 6, 7
chorded_keys = 8
CHORDS = {
    'a': (3,),
    'b': (4, 7),
    'c': (6, 7),
    'd': (1, 2, 3),
    'e': (7,),
    'f': (2, 3),
    'g': (1, 2),
    'h': (5, 7),
    'i': (5,),
    'j': (0, 1),
    'k': (4, 6),
    'l': (5, 6, 7),
    'm': (4, 5, 6),
    'n': (4, 5),
    'o': (4,),
    'p': (4, 5, 7),
    'q': (0, 1, 3),
    'r': (2,),
    's': (0,), 
    't': (1,),
    'u': (5, 6),
    'v': (0, 2),
    'w': (0, 3),
    'x': (0, 1, 2),
    'y': (6,),
    'z': (0, 1, 2, 3),
}

n = 0
layers = {'base': [] }
for key, buttons in sorted(CHORDS.items(), key=lambda k, v: min(value)):
    if len(buttons) > 1:
        continue
    button = buttons[0]
    # layers['base'].append( (key, f'{key}_layer') )
    # is this terminus?
    if [bs for bs in CHORDS.values() if len(bs) > 1 and button in bs]:
        layers['base'].append( (key, (button,) )
        layers[f'{button}'] = None
    else:
        layers['base'].append( key )

while True:
    # get a list of layers that haven't been conpleted yet
    todo = [l for l, b in layers.items() if b is None]
    if not todo:
        break
    # take the first from that list
    layer = todo[0]

    # get list of buttons that activated that layer
    lbuttons = ','.split(layer)
    lbuttons = [int(b) for b in lbuttons]

    # identify keys that include those buttons
    keys = [k for k, bs in CHORDS.items() if set(bs).issubset(set(lbuttons))]
    assert(keys)
    if len(keys) == 1:
        
    layers[layer] = []
    for l, k in layers.items() if k i

path = ['base',]
while path:
    for n, key in layers[path[-1]]:
print(layers)


for key in range(chorded_keys):
    

#kmap
#  0,  1,  2,  3
#  4,  5,  6,  7
#  8,  9,  0, 10
# 11, 12, 13, 14

KMAP = {
    'BASE': ('COMMA',           ('PERIOD', 'LEFT_ALT'),
                                                 ('A', 'LEFT_ALT'),
                                                                 ('F', 'LEFT_ALT'),
             'SEMICOLON',           ('G', 'LEFT_SHIFT'),
                                                 ('J', 'LEFT_SHIFT'),
                                                                 ('M', 'LEFT_SHIFT'),
             'QUOTE',           ('P', 'LEFT_CONTROL'),
                                                 ('T', 'LEFT_CONTROL'),
                                                                 ('W', 'LEFT_CONTROL'),
             ('BACKSPACE', 'METAS'),
                                ('ESCAPE', 'NAVIGATION'),
                                                 ('SPACE', 'NUMBERS'),
                                                                 ('ENTER', 'SYMBOLS')),
    'NUMBERS': ('MINUS',         'ONE',          'TWO',           'THREE',
             'EQUALS',           'FOUR',         'FIVE',          'SIX',
             'FORWARD_SLASH',    'SEVEN',        'EIGHT',         'NINE',
             'BACKSPACE',        'ZERO',          None,           'ENTER'),

    'SYMBOLS': ('S_MINUS',       'S_ONE',         'S_TWO',        'S_THREE',
             'S_EQUALS',         'S_FOUR',        'S_FIVE',       'S_SIX',
             'S_FORWARD_SLASH',  'S_SEVEN',       'S_EIGHT',      'S_NINE',
             'DELETE',           'ESCAPE',        'SPACE',         None),

    'METAS': ('S_LEFT_BRACKET',   'LEFT_BRACKET', 'RIGHT_BRACKET', 'S_RIGHT_BRACKET',
             'FORWARD_SLASH',     'S_NINE',       'S_ZERO',        'BACKSLASH',
             'PRINT_SCREEN',      'F2',           'F10',           'F11',
             'DELETE',            'ESCAPE',       'SPACE',         None),

    'NAVIGATION': ('MOUSE_LEFT',  'MOUSE_DOWN',   'MOUSE_UP',      'MOUSE_RIGHT',
             'LEFT_ARROW',        'DOWN_ARROW',   'UP_ARROW',      'RIGHT_ARROW',
             'HOME',              'PAGE_DOWN',    'PAGE_UP',       'END',
             'LEFT_BUTTON',       None,           'MIDDLE_BUTTON', 'RIGHT_BUTTON')

}
