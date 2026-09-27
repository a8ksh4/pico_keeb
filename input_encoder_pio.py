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


class InputModule(InputModule):
    '''This extends InputModule with functionality to support 
    adxl gyro and accelerometer mouse input.'''
    def __init__(self, input_state, debug_print=False):
        super().__init__(input_state, debug_print)

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
        # (last, new) transitions, compared as separate ints since building
        # a tuple to compare against would allocate every tick.
        self.UP_LAST, self.UP_NEW = 2, 3
        self.DOWN_LAST, self.DOWN_NEW = 0, 3

        self.STATE = input_state
        self.keys_bits_offset = 0
        self.SM = None

    def init(self, keys_bits_offset, state_machine_num=None):
        # def init(self, pio_machine_num, input_state, keys_bits_offset):
        '''Init is a standard function for pico_keeb input modules that 
        we use to store a referenc to the global InputState oject so
        any inputs can be recorded in it each tick without any allocation.
        We also can perform any needed module initialization here, like
        pio state machines as well as other hardware setup.'''

        self.keys_bits_offset = keys_bits_offset

        self.SM = rp2.StateMachine(state_machine_num, encoder_monitor,
                            freq=self.SM_FREQ,
                            in_base=self.PIN_ENCODER_A)
        self.SM.active(1)

    def get_num_keys(self):
        '''One key for the encoder click.'''
        return 1

    def update_state(self):
        '''get_state is a standard function in inupt modules.
        It returns a dict with keys a list of states of any buttons/keys,
        and 'wheel' a list of movement directions.'''
        key_value = 1 if not self.PIN_BUTTON.value() else 0
        self.set_key_state(0, key_value)

        while self.SM.rx_fifo():
            encoder_position = self.SM.get() & 0b11  # get the last two bits for A and B
            if self.debug_print:
                self.print("Encoder position:", encoder_position)

            if self.LAST_POSITION is None:
                self.LAST_POSITION = encoder_position
                continue

            if self.LAST_POSITION == self.UP_LAST and encoder_position == self.UP_NEW:
                # state['wheel'].append('up')
                self.STATE.wheel += 1
            elif self.LAST_POSITION == self.DOWN_LAST and encoder_position == self.DOWN_NEW:
                # state['wheel'].append('down')
                self.STATE.wheel -= 1

            self.LAST_POSITION = encoder_position


if __name__ == "__main__":
    from input import run_test
    run_test(InputModule,
             lambda state, module: print(state.wheel, state.buttons))
