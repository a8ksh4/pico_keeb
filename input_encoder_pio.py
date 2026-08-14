'''This is a standard pico_keeb module to for handling encoder wheel
input using pio.  It is for a standard three pin encoder, ground and wheel A/B, with
a click button.

TODO:
* Double the fifo length
* Clean up the state change handling
'''
from input import InputModule
from machine import Pin
import rp2


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


class InputModuleEncoderPio(InputModule):
    '''This extends InputModule with functionality to support 
    adxl gyro and accelerometer mouse input.'''

    def get_num_keys(self):
        '''One key for the encoder click.'''
        return 1

    def __init__(self, input_state):
        super().__init__(input_state)

        self.BUTTON_PIN = 5
        self.ENCODER_A = 3
        self.ENCODER_B = 4
        # SM_FREQ = 2000  # 1_000_000
        self.SM_FREQ = 1_000_000

        self.PIN_BUTTON = Pin(self.BUTTON_PIN, Pin.IN, Pin.PULL_UP)
        self.PIN_ENCODER_A = Pin(self.ENCODER_A, Pin.IN, Pin.PULL_UP)
        self.PIN_ENCODER_B = Pin(self.ENCODER_B, Pin.IN, Pin.PULL_UP)

        self.LAST_POSITION = None
        # UP_STATES = ((0, 1), (1, 2), (2, 3), (3, 0))
        self.UP_STATE = (2, 3)
        self.DOWN_STATE = (0, 3)

        self.STATE = input_state
        self.keys_bytes_offset = 0
        self.SM = None


    def init(self, keys_bytes_offset, state_machine_num=None):
        # def init(self, pio_machine_num, input_state, keys_bytes_offset):
        '''Init is a standard function for pico_keeb input modules that 
        we use to store a referenc to the global InputState oject so
        any inputs can be recorded in it each tick without any allocation.
        We also can perform any needed module initialization here, like
        pio state machines as well as other hardware setup.'''

        self.keys_bytes_offset = keys_bytes_offset

        self.SM = rp2.StateMachine(state_machine_num, encoder_monitor,
                            freq=self.SM_FREQ,
                            in_base=self.PIN_ENCODER_A)
        self.SM.active(1)


    def update_state(self):
        '''get_state is a standard function in inupt modules.
        It returns a dict with keys a list of states of any buttons/keys,
        and 'wheel' a list of movement directions.'''
        global LAST_POSITION

        key_value = 1 if not self.PIN_BUTTON.value() else 0
        self.set_key_state(0, key_value)

        while self.SM.rx_fifo():
            encoder_position = self.SM.get() & 0b11  # get the last two bits for A and B
            print("Encoder position:", encoder_position)

            if self.LAST_POSITION is None:
                self.LAST_POSITION = encoder_position
                continue

            if (self.LAST_POSITION, encoder_position) == self.UP_STATE:
                # state['wheel'].append('up')
                self.STATE.wheel += 1
            elif (self.LAST_POSITION, encoder_position) == self.DOWN_STATE:
                # state['wheel'].append('down')
                self.STATE.wheel -= 1

            self.LAST_POSITION = encoder_position


if __name__ == "__main__":
    from time import sleep
    # It's kinda dumb to copy this class here for testing, but I don't want to have
    # main.py on the pico while doing development because the board will try to run it
    # at boot and cause probs.   So here we are!
    class InputState:
        def __init__(self, num_keys):
            # self.keys = b
            self.keys = 0  # bytearray!
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

    encoder = InputModuleEncoderPio(state)
    encoder.init(0, 0)
    while True:
        state.clear_deltas()
        encoder.update_state()
        print(encoder.STATE.wheel, encoder.STATE.keys)
        sleep(0.5)
