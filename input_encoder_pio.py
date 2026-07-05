'''This is a standard pico_keeb module to for handling encoder wheel
input using pio.  It is for a standard three pin encoder, ground and wheel A/B, with
a click button.

TODO:
* Double the fifo length
* Clean up the state change handling
'''

from machine import Pin
import rp2


BUTTON_PIN = 5
ENCODER_A = 3
ENCODER_B = 4
# SM_FREQ = 2000  # 1_000_000
SM_FREQ = 1_000_000

PIN_BUTTON = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
PIN_ENCODER_A = Pin(ENCODER_A, Pin.IN, Pin.PULL_UP)
PIN_ENCODER_B = Pin(ENCODER_B, Pin.IN, Pin.PULL_UP)

LAST_POSITION = None
# UP_STATES = ((0, 1), (1, 2), (2, 3), (3, 0))
UP_STATE = (2, 3)
DOWN_STATE = (0, 3)

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, fifo_join=rp2.PIO.JOIN_RX)
def encoder_monitor():
    '''PIO program to track state of the encoder pins and report
    new state when it changes.'''

    # mov(y, invert(null))

    label("loop")
    mov(isr, null)
    in_(pins, 2)  # read encoder A and B into ISR
    mov(x, isr)  # store initial state in X

    jmp(x_not_y, "changed")
    jmp("loop")

    label("changed")
    mov(y, x)
    mov(osr, y)
    push(noblock)
    jmp("loop")


def get_num_keys():
    '''Standard pico_keeb input module function that tells
    the main program how many keys this module handles so the main
    program can allocate memory for it.'''
    return 1


def init(pio_machine_num, input_state, keys_mv):
    '''Init is a standard function for pico_keeb input modules that 
    we use to store a referenc to the global InputState oject so
    any inputs can be recorded in it each tick without any allocation.
    We also can perform any needed module initialization here, like
    pio state machines as well as other hardware setup.'''
    global STATE
    global KEYS_MV
    global SM

    STATE = input_state
    KEYS_MV = keys_mv

    SM = rp2.StateMachine(pio_machine_num, encoder_monitor,
                          freq=SM_FREQ,
                          in_base=PIN_ENCODER_A)
    SM.active(1)


def update_state():
    '''get_state is a standard function in inupt modules.
    It returns a dict with keys a list of states of any buttons/keys,
    and 'wheel' a list of movement directions.'''
    global LAST_POSITION

    # clicked = not PIN_BUTTON.value()
    KEYS_MV[0] = 1 if not PIN_BUTTON.value() else 0

    while SM.rx_fifo():
        encoder_position = SM.get() & 0b11  # get the last two bits for A and B
        print("Encoder position:", encoder_position)

        if LAST_POSITION is None:
            LAST_POSITION = encoder_position
            continue

        if (LAST_POSITION, encoder_position) == UP_STATE:
            # state['wheel'].append('up')
            STATE.wheel += 1
        elif (LAST_POSITION, encoder_position) == DOWN_STATE:
            # state['wheel'].append('down')
            STATE.wheel -= 1

        LAST_POSITION = encoder_position


if __name__ == "__main__":
    from time import sleep
    # It's kinda dumb to copy this class here for testing, but I don't want to have
    # main.py on the pico while doing development because the board will try to run it
    # at boot and cause probs.   So here we are!
    class InputState:
        def __init__(self, num_keys):
            self.keys = bytearray(num_keys)
            self.wheel = 0
            self.mouse_x = 0
            self.mouse_y = 0
            self.mouse_enable = 0

        def clear_deltas(self):
            self.wheel = 0
            self.mouse_x = 0
            self.mouse_y = 0
            self.mouse_enable = 0
    state = InputState(1)
    keys_mv = memoryview(state.keys)

    init(0, state, keys_mv)
    while True:
        state.clear_deltas()
        update_state()
        print(STATE.wheel, STATE.keys)
        sleep(0.5)
# if __name__ == "__main__":
#     from time import sleep
#     init(0)
#     while True:
#         module_state = get_state()
#         print(module_state)
#         sleep(1)
