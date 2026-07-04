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

# import board
# 
# PINS = (
#     board.GP5,  board.GP4,  board.GP3,  board.GP2,
#     board.GP9,  board.GP8,  board.GP7,  board.GP6,
#     board.GP13, board.GP12, board.GP11, board.GP10,
#     board.GP17, board.GP16, board.GP15, board.GP14,
# )

# SCROLL_ENCODER = False
# Digital 1, Digital 2, Invert
# SCROLL_ENCODER = (board.GP21, board.GP20, True)
# JOYSTICK_MOUSE = False
# Analog 1, Analog 2, Swap Axes, Invert X, Invert Y
# JOYSTICK_MOUSE = (board.GP27, board.GP26, False, True, False)

# Chording matrix
# 0, 1, 2, 3
# 4, 5, 6, 7
CHORDED_NUM = 8
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
    ' ': (4, 5, 6, 7)
}

def translate_chords_to_layers(chords, num_chorded_buttons):
    layers = {'base': None }

    while True:
        # get a list of layers that haven't been conpleted yet
        todo = [l for l, b in layers.items() if b is None]
        if not todo:
            break
        # take the first from that list
        layer_name = todo[0]

        # get list of buttons that activated that layer
        if layer_name == 'base':
            layer_buttons = ()
        else:
            layer_buttons = layer_name.split(':')
            layer_buttons = tuple(int(b) for b in layer_buttons)
        #print("Working on:", layer_name, "from buttons:", layer_buttons)

        layers[layer_name] = []
        # iterate through chord buttons and check for matching keys...
        for b in range(CHORDED_NUM):
            next_buttons = set(layer_buttons).union( (b,) )
            next_keys = [k for k, bs in CHORDS.items() if next_buttons.issubset(set(bs))]
            if len(next_keys) == 0:
                # Dead end
                layers[layer_name].append(None)
            elif len(next_keys) == 1:
                # Terminus
                layers[layer_name].append(next_keys[0])
            else:
                # Branching
                next_keys_exact = [k for k, bs in CHORDS.items() 
                        if next_buttons == set(bs)]
                if next_keys_exact:
                    # With possible endpoint
                    next_key = next_keys_exact[0]
                else:
                    # Not an endpoint
                    next_key = None
                next_layer_name = (str(b) for b in sorted(next_buttons))
                next_layer_name = ':'.join(next_layer_name)
                layers[layer_name].append( (next_key, next_layer_name) )

                # Make sure we aren't duplicating another layer
                if not next_layer_name in layers:
                    #print("    New Layer:", next_layer_name)
                    layers[next_layer_name] = None
    return layers



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

if __name__ == '__main__':
    chorded_layers = translate_chords_to_layers(CHORDS, CHORDED_NUM)
    for layer_name, keys in chorded_layers.items():
        print(layer_name, keys)
