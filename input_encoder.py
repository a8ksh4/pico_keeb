'''moudle to handle the encoder wheel and its clicker.
This is a standard encoder with ground, two pins for the
encoder, and a pin for the clicker.

TODO:
* Double the fifo length
* Clean up the state change handling'''

from machine import Pin
import rp2
import time

BUTTON_PIN = 5
ENCODER_A = 4
ENCODER_B = 3
SM_FREQ = 1_000_000

PIN_BUTTON = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
PIN_ENCODER_A = Pin(ENCODER_A, Pin.IN, Pin.PULL_UP)
PIN_ENCODER_B = Pin(ENCODER_B, Pin.IN, Pin.PULL_UP)

LAST = None
UP_STATES = ((0, 1), (1, 2), (2, 3), (3, 0))

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def encoder_monitor():
    '''PIO program to track state of the encoder pins and report
    new state when it changes.'''
    in_(pins, 2)  # read encoder A and B into ISR
    mov(x, isr)  # store initial state in X
    push()       # push initial state to FIFO

    wrap_target()
    in_(pins, 2)  # read encoder A and B into ISR
    mov(y, isr)  # store new state in Y
    jmp(x_not_y, "state_changed")  # if state changed, report it
    jmp("loop")  # otherwise, keep waiting

    label("state_changed")
    mov(x, y)
    push()       # push new state to FIFO

    label("loop")
    wrap()


def init(pio_machine_num):
    global SM
    SM = rp2.StateMachine(pio_machine_num, encoder_monitor, 
                          freq=SM_FREQ, 
                          in_base=0)
    SM.active(1)


def get_state():
    '''get_state is a standard function in inupt modules.
    It returns a dict with keys a list of states of any buttons/keys,
    and 'wheel' a list of movement directions.'''
    clicked = not PIN_BUTTON
    state = {'keys': [clicked],
             'wheel': []}
    while SM.rx_fifo():
        state = SM.get() & 0b11  # get the last two bits for A and B
        if PREV is None:
            PREV = state
            continue
        if (PREV, state) in UP_STATES:
            state['wheel'].append('up')
        else:
            state['wheel'].append('down')
    return state
