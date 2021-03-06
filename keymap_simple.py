# Notes on conventions used here:
# S_<word> means apply shift key with the character. E.g S_NINE is '('
# (<hold>, <tap>) means first item is applied when holding, and second
#                 item is applied for a tap.
# (<one>, <two>, <three>, ...) is for text string matching, like t9
#                 prdictive text. (once implemented...)
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
