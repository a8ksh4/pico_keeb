'''This is a standard pick_keeb input module with init() and 
get_state() functions to handle keyboard matrix scanning
using pio. '''

from machine import Pin


IN_PIN_NUMS = [8, 9, 10, 11]
OUT_PIN_NUMS = [16, 17, 18, 19, 20]
# IN_PIN_NUMS = [16, 17, 18, 19, 20]
# OUT_PIN_NUMS = [8, 9, 10, 11]

IN_PINS = [Pin(n, Pin.IN, Pin.PULL_UP) for n in IN_PIN_NUMS]
OUT_PINS = [Pin(n, Pin.OUT) for n in OUT_PIN_NUMS]

# SM_FREQ = 1_000_000
SM_FREQ = 2000


def matrix_scan():
    '''Scan the keyboard matrix and return a list of boolean states for each key.
    This function will iterate through the output pins, setting one high at a time,
    and read the input pins to determine which keys are pressed.'''

    key_states = []
    for out_pin in OUT_PINS:
        # Set the current output pin high
        out_pin.value(1)
        # Read the state of each input pin
        for in_pin in IN_PINS:
            key_states.append(not in_pin.value())  # Assuming active low
        # Set the current output pin low before moving to the next
        out_pin.value(0)

    return key_states


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

    keys = matric_scan()
    state = {'keys': keys}
    return state


if __name__ == "__main__":
    from time import sleep
    init(0)
    while True:
        changes = get_state()
        print(changes)
        sleep(1)
