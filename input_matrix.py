'''This is a standard pick_keeb input module with init() and 
get_state() functions to handle keyboard matrix scanning
using pio. '''

from machine import Pin

# DIODE_DIR = 'COL2ROW'  # or 'ROW2COL'
COL2ROW = False
ROWS = [8, 9, 10, 11]
COLS = [16, 17, 18, 20, 19]

if COL2ROW:
    DRIVEN_PINS = COLS
    READ_PINS = ROWS
else:
    DRIVEN_PINS = ROWS
    READ_PINS = COLS

DRIVEN_PINS = [Pin(i, Pin.OUT) for i in DRIVEN_PINS]
READ_PINS = [Pin(i, Pin.IN, Pin.PULL_DOWN) for i in READ_PINS]


def scan_matrix():
    keys_states = []
    for dp in DRIVEN_PINS:
        dp.value(1)
        for rp in READ_PINS:
            keys_states.append(True if rp.value() else False)
        dp.value(0)
    return keys_states


def init(pio_machine_num):
    '''Init is a standard function for input modules that 
    can perform any needede initialization.  Probably this
    is on ly needed to assign unique state machine nums.'''
    pass


def get_state():
    '''get_state is a standard function in inupt modules.
    It returns a dict with keys a list of boolean states of any buttons/keys
    In this case, we have 20 relevant keys from the 4x5 matrix, so
    we'll return a list of 20 booleans in the dict.
    TODO: If we have bouncing issues, we may need to add some debouncing logic
            here.  Rather than drop older states, we could track history or something.'''

    keys = scan_matrix()
    state = {'keys': keys}
    return state


if __name__ == "__main__":
    from time import sleep
    init(0)
    while True:
        changes = get_state()
        print(changes)
        sleep(1)
