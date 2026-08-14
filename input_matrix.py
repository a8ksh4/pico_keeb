'''This is a standard pick_keeb input module with init() and 
get_state() functions to handle keyboard matrix scanning
using pio. '''

from input import InputModule
from machine import Pin


class InputModuleMatrix(InputModule):
    '''This is a standard pick_keeb input module with init() and 
    get_state() functions to handle keyboard matrix scanning
    using pio. '''
    def __init__(self, input_state):
        super().__init__(input_state)

        # DIODE_DIR = 'COL2ROW'  # or 'ROW2COL'
        self.COL2ROW = False
        self.ROWS = [8, 9, 10, 11]
        self.COLS = [16, 17, 18, 20, 19]

        if self.COL2ROW:
            self.DRIVEN_PINS = self.COLS
            self.READ_PINS = self.ROWS
        else:
            self.DRIVEN_PINS = self.ROWS
            self.READ_PINS = self.COLS

        self.DRIVEN_PINS = [Pin(i, Pin.OUT) for i in self.DRIVEN_PINS]
        self.READ_PINS = [Pin(i, Pin.IN, Pin.PULL_DOWN) for i in self.READ_PINS]
        self.keys_bytes_offset = 0


    def get_num_keys(self):
        '''Standard pico_keeb input module function that tells
        the main program how many keys this module handles so the main
        program can allocate memory for it.'''
        return 20


    def init(self, keys_bytes_offset, pio_machine_num):
        '''Init is a standard function for pico_keeb input modules that 
        we use to store a referenc to the global InputState oject so
        any inputs can be recorded in it each tick without any allocation.
        We also can perform any needed module initialization here, like
        pio state machines as well as other hardware setup.'''
        self.keys_bytes_offset = keys_bytes_offset


    def update_state(self):
        '''update_state is a standarc pico_keeb function.  It
    updates the global InputState object, captured from the init function,
    with data from this module.'''

        key_count = 0
        for dp in self.DRIVEN_PINS:
            dp.value(1)
            for rp in self.READ_PINS:
                # Set the corresponding bit in the keys field
                key_value = 1 if rp.value() else 0
                self.set_key_state(key_count, key_value)
                key_count += 1
            dp.value(0)


if __name__ == "__main__":
    from time import sleep
    # It's kinda dumb to copy this class here for testing, but I don't want to have
    # main.py on the pico while doing development because the board will try to run it
    # at boot and cause probs.   So here we are!
    class InputState:
        def __init__(self, num_keys):
            self.keys = 0
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

    matrix = InputModuleMatrix(state)
    matrix.init(0, 0)
    while True:
        state.clear_deltas()
        matrix.update_state()
        print(matrix.state.keys)
        sleep(0.5)
