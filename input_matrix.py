'''This is a standard pick_keeb input module with init() and 
get_state() functions to handle keyboard matrix scanning
using pio. '''

from machine import Pin

STATE = None
KEYS_MV = None

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


def get_num_keys():
    '''Standard pico_keeb input module function that tells
    the main program how many keys this module handles so the main
    program can allocate memory for it.'''
    return 20


def init(pio_machine_num, input_state, keys_mv):
    '''Init is a standard function for pico_keeb input modules that 
    we use to store a referenc to the global InputState oject so
    any inputs can be recorded in it each tick without any allocation.
    We also can perform any needed module initialization here, like
    pio state machines as well as other hardware setup.'''
    global STATE
    STATE = input_state
    global KEYS_MV
    KEYS_MV = keys_mv


def update_state():
    '''update_state is a standarc pico_keeb function.  It
    updates the global InputState object, captured from the init function,
    with data from this module.'''

    key_count = 0
    for dp in DRIVEN_PINS:
        dp.value(1)
        for rp in READ_PINS:
            KEYS_MV[key_count] = rp.value()
            key_count += 1
        dp.value(0)


if __name__ == "__main__":
    from time import sleep
    # It's kinda dumb to copy this class here for testing, but I don't want to have
    # main.py on the pico while doing development because the board will try to run it
    # at boot and cause probs.   So here we are!
    class InputState:
        def __init__(self, num_keys):
            self.keys = bytearray(num_keys)
            self.wheel = []
            self.mouse_x = 0
            self.mouse_y = 0
            self.mouse_enable = 0

        def clear_deltas(self):
            self.wheel = []
            self.mouse_x = 0
            self.mouse_y = 0
            self.mouse_enable = 0
    state = InputState(20)
    keys_mv = memoryview(state.keys)

    init(0, state, keys_mv)
    while True:
        state.clear_deltas()
        update_state()
        print(STATE.keys)
        sleep(0.5)
