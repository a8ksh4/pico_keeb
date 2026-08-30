'''Analog stick with click and capacitive touch sensing.  You could
comment out the touch stuff if your stick doesn't have it.'''

from input import InputModule
from machine import ADC, Pin
import rp2

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, fifo_join=rp2.PIO.JOIN_RX)
def cap_measure():
    wrap_target()
    set(pindirs, 1)               # output
    set(pins, 1)                  # charge high
    nop()                  [31]
    nop()                  [31]
    set(pindirs, 0)               # release -> input, starts falling
    mov(x, invert(null))          # x = 0xFFFFFFFF
    label("loop")
    jmp(pin, "still_high")        # pin high -> keep counting
    jmp("done")                   # pin low  -> done
    label("still_high")
    jmp(x_dec, "loop")
    label("done")
    mov(isr, x)
    push(noblock)
    wrap()


class InputModule(InputModule):
    '''This is a standard pick_keeb input module with init() and 
    get_state() functions to handle keyboard matrix scanning
    using pio. '''
    def __init__(self, input_state):
        super().__init__(input_state)

        self.PUSH_PIN = 21
        self.PUSH = Pin(self.PUSH_PIN, Pin.IN, Pin.PULL_UP)

        self.CAP_SENSE_PIN_NUM = 22
        self.CAP_THRESHOLD = 5000
        self.COUNT_MAX = 0xFFFFFFFF
        self.CAP_SENSE_PIN = Pin(self.CAP_SENSE_PIN_NUM, Pin.OUT, value=0)
        self.SM_FREQ = 1_000_000

        self.LAST_TOUCH_STATE = False
        # TODO: possibly implement smoothing for cap touch

        self.X_PIN_NUM = 26
        self.Y_PIN_NUM = 27
        self.X_ADC = ADC(Pin(self.X_PIN_NUM))
        self.Y_ADC = ADC(Pin(self.Y_PIN_NUM))
        self.X_INVERT = False
        self.Y_INVERT = True

        self.X_LOWER_LIM = 15000
        self.X_UPPER_LIM = 25000

        self.Y_LOWER_LIM = 15000
        self.Y_UPPER_LIM = 25000

        self.X_CENTER = 20000 << 8
        self.Y_CENTER = 20000 << 8
        self.X_DZ = 5          # deadzone in 1/256 units (0.02)
        self.Y_DZ = 5
        self.DZ_CAP = 38       # 0.15
        self._warm = 0

    def get_num_keys(self):
        '''Tells the main program how many keys this module handles
        so the main program knows how much memory to allocate for it.'''
        return 1

    def init(self, keys_bits_offset, pio_machine_num):
        '''Init is a standard function for pico_keeb input modules that 
        we use to store a referenc to the global InputState oject so
        any inputs can be recorded in it each tick without any allocation.
        We also can perform any needed module initialization here, like
        pio state machines as well as other hardware setup.'''
        self.keys_bits_offset = keys_bits_offset
        self.SM = rp2.StateMachine(pio_machine_num, cap_measure,
                                freq=self.SM_FREQ,
                                set_base=self.CAP_SENSE_PIN,
                                jmp_pin=self.CAP_SENSE_PIN)
        self.SM.active(1)

    def get_stick_raw_values(self):
        '''pretty simple raw value read'''
        x_raw = self.X_ADC.read_u16()
        if self.X_INVERT:
            x_raw = 65535 - x_raw
        y_raw = self.Y_ADC.read_u16()
        if self.Y_INVERT:
            y_raw = 65535 - y_raw
        return x_raw, y_raw

    def _axis(self,v, lo, hi, c8):
        c = c8 >> 8
        span = (hi - c) if v >= c else (c - lo)
        if span <= 0:
            return 0
        return (v - c) * 256 // span

    def get_stick_mouse_state(self, touched):
        # global X_LOWER_LIM, X_UPPER_LIM, Y_LOWER_LIM, Y_UPPER_LIM
        # global X_CENTER, Y_CENTER, X_DZ, Y_DZ, _warm

        x, y = self.get_stick_raw_values()          # ints from read_u16
        if x < self.X_LOWER_LIM: self.X_LOWER_LIM = x
        if x > self.X_UPPER_LIM: self.X_UPPER_LIM = x
        if y < self.Y_LOWER_LIM: self.Y_LOWER_LIM = y
        if y > self.Y_UPPER_LIM: self.Y_UPPER_LIM = y

        if not touched:
            if self._warm == 0:
                self.X_CENTER = x << 8
                self.Y_CENTER = y << 8
                self._warm = 1
            elif self._warm < 20:
                self.X_CENTER += ((x << 8) - self.X_CENTER) >> 2   # fast warmup
                self.Y_CENTER += ((y << 8) - self.Y_CENTER) >> 2
                self._warm += 1
            else:
                self.X_CENTER += ((x << 8) - self.X_CENTER) >> 7   # slow track (~0.008)
                self.Y_CENTER += ((y << 8) - self.Y_CENTER) >> 7

        xn = self._axis(x, self.X_LOWER_LIM, self.X_UPPER_LIM, self.X_CENTER)
        yn = self._axis(y, self.Y_LOWER_LIM, self.Y_UPPER_LIM, self.Y_CENTER)

        if not touched:
            dx = xn if xn >= 0 else -xn
            dx = dx * 13 // 10                 # 1.3 margin
            if dx > self.X_DZ:
                self.X_DZ = dx if dx < self.DZ_CAP else self.DZ_CAP
            dy = yn if yn >= 0 else -yn
            dy = dy * 13 // 10
            if dy > self.Y_DZ:
                self.Y_DZ = dy if dy < self.DZ_CAP else self.DZ_CAP

        if -self.X_DZ < xn < self.X_DZ: xn = 0
        if -self.Y_DZ < yn < self.Y_DZ: yn = 0
        return xn, yn

    def update_touch_state(self):
        '''This totals up any values in the cap pio fifo.
        If the average is below the threshold, then touch is true.'''
        total = 0
        count = 0
        while self.SM.rx_fifo():          # drain stale samples
            value = self.COUNT_MAX - self.SM.get()
            # print("cap value", value)
            total += value
            count += 1

        if count:
            average = total / count
            # print("cap average", average, average < CAP_THRESHOLD)
            self.LAST_TOUCH_STATE = average < self.CAP_THRESHOLD

    def update_state(self):
        '''update_state is a standard function in input modules.
        It updates the internal state based on the current input values.'''    

        clicked = not self.PUSH.value()
        self.update_touch_state()
        touched = self.LAST_TOUCH_STATE

        stick_x, stick_y = self.get_stick_mouse_state(touched)
        self.state.mouse_x += stick_x
        self.state.mouse_y += stick_y
        self.state.mouse_enable = 1 if touched or clicked else 0

        #We might be working on bit n of up to 32 bits in STATE.keys,
        # So we only want to adjust bit n, based on self.KEYS_OFFSET:
        value = 1 if clicked else 0
        # self.state.keys = (self.state.keys & ~(1 << self.KEYS_OFFSET)) | (value << self.KEYS_OFFSET)
        self.set_key_state(0, value)  # use the base class method to set the key state


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
    state = InputState(1)

    stick = InputStickPio(state)
    stick.init(0, 0)
    while True:
        state.clear_deltas()
        stick.update_state()
        print(stick.state.mouse_x,
              stick.state.mouse_y,
              stick.state.mouse_enable,
              stick.state.keys)
        sleep(0.5)
