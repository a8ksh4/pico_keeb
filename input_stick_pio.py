'''Analog stick with click and capacitive touch sensing.  You could
comment out the touch stuff if your stick doesn't have it.'''

import random

from input import InputModule
from machine import ADC, Pin, freq
import rp2

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, fifo_join=rp2.PIO.JOIN_RX)
def cap_measure():
    '''Measures how long the pad takes to discharge through the internal
    pull-down after being charged high.  A finger adds capacitance, so a
    larger count means touched.  The counts of 32 discharges are summed into
    each push for resolution, since a single discharge is only ~70 counts
    at 200 MHz.'''
    wrap_target()
    mov(x, invert(null))          # x = 0xFFFFFFFF, counts down across all 32
    set(y, 31)                    # 32 discharges per push
    label("measure")
    set(pindirs, 1)               # output
    set(pins, 1)           [31]   # charge high
    nop()                  [31]
    set(pindirs, 0)               # release -> pull-down discharges the pad
    label("loop")
    jmp(pin, "still_high")        # pin high -> keep counting
    jmp("done")                   # pin low  -> this discharge is done
    label("still_high")
    jmp(x_dec, "loop")
    label("done")
    jmp(y_dec, "measure")
    mov(isr, invert(x))           # push the summed count, a small int
    push(noblock)
    wrap()


class InputModule(InputModule):
    '''This is a standard pick_keeb input module with init() and 
    get_state() functions to handle keyboard matrix scanning
    using pio. '''
    def __init__(self, input_state, debug_print=False):
        super().__init__(input_state, debug_print)

        self.PUSH_PIN = 21
        self.PUSH = Pin(self.PUSH_PIN, Pin.IN, Pin.PULL_UP)

        # The pad has no external bleed resistor, so the internal ~50k
        # pull-down discharges it.  Left floating, the pad picks up 60 Hz hum
        # through a finger and readings are garbage.  The discharge only
        # takes ~1us, so the SM runs at the full system clock.
        self.CAP_SENSE_PIN_NUM = 22
        self.CAP_SENSE_PIN = Pin(self.CAP_SENSE_PIN_NUM, Pin.IN, Pin.PULL_DOWN)
        self.SM_FREQ = freq()

        # Touch is detected relative to a learned untouched baseline, with
        # hysteresis.  A touch measured ~+10% over baseline.
        self.CAP_ON_SHIFT = 4          # touched above baseline + 1/16 (6.25%)
        self.CAP_OFF_SHIFT = 5         # released below baseline + 1/32 (3.1%)
        self._cap_base = 0             # baseline << 8, 0 until the first reading
        self.cap_value = 0             # latest averaged reading, for debugging

        self.LAST_TOUCH_STATE = False

        self.X_PIN_NUM = 26
        self.Y_PIN_NUM = 27
        self.X_ADC = ADC(Pin(self.X_PIN_NUM))
        self.Y_ADC = ADC(Pin(self.Y_PIN_NUM))
        self.X_INVERT = False
        self.Y_INVERT = False

        self.X_LOWER_LIM = 15000
        self.X_UPPER_LIM = 25000

        self.Y_LOWER_LIM = 15000
        self.Y_UPPER_LIM = 25000

        self.X_CENTER = 20000 << 8
        self.Y_CENTER = 20000 << 8
        self.X_DZ = 5          # deadzone in 1/256 units (0.02)
        self.Y_DZ = 5
        self.DZ_CAP = 38       # 0.15
        self.ADC_SAMPLES_SHIFT = 2  # average 4 ADC reads per axis, less noise
        self._warm = 0

        # Per tick results are stored here rather than returned as tuples,
        # since returning multiple values allocates a tuple.
        self.x_raw = 0
        self.y_raw = 0
        self.stick_x = 0
        self.stick_y = 0

    def get_num_keys(self):
        '''Tells the main program how many keys this module handles
        so the main program knows how much memory to allocate for it.
        Key 0 is the stick click, key 1 is the capacitive touch.'''
        return 2

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
        '''Reads each axis a few times and averages, since the ADC is noisy.'''
        x_raw = 0
        y_raw = 0
        for _ in range(1 << self.ADC_SAMPLES_SHIFT):
            x_raw += self.X_ADC.read_u16()
            y_raw += self.Y_ADC.read_u16()
        x_raw >>= self.ADC_SAMPLES_SHIFT
        y_raw >>= self.ADC_SAMPLES_SHIFT
        if self.X_INVERT:
            x_raw = 65535 - x_raw
        if self.Y_INVERT:
            y_raw = 65535 - y_raw
        self.x_raw = x_raw
        self.y_raw = y_raw

    def _axis(self,v, lo, hi, c8):
        c = c8 >> 8
        span = (hi - c) if v >= c else (c - lo)
        if span <= 0:
            return 0
        return (v - c) * 256 // span

    def _isqrt(self, n):
        '''Integer square root, floor(sqrt(n)), without floats (which
        allocate).  n must be < 2 ** 30.'''
        res = 0
        bit = 1 << 28
        while bit > n:
            bit >>= 2
        while bit:
            if n >= res + bit:
                n -= res + bit
                res = (res >> 1) + bit
            else:
                res >>= 1
            bit >>= 2
        return res

    def _radial_curve(self, x, y):
        '''Applies the deadzone and response curve to the stick's distance
        from center, rather than to each axis separately, so the direction is
        kept.  Per axis, the smaller axis would get zeroed or shrunk more,
        pulling diagonals toward horizontal/vertical.
        Rescales so output starts from 0 at the deadzone edge rather than
        jumping to dz, then squares it, so small deflections give fine
        control and full deflection is still full speed.  Sets
        self.stick_x/y.'''
        dz = self.X_DZ if self.X_DZ > self.Y_DZ else self.Y_DZ
        r = self._isqrt(x * x + y * y)
        if r <= dz:
            self.stick_x = 0
            self.stick_y = 0
            return
        a = (r - dz) * 256 // (256 - dz)
        if a > 256:
            a = 256
        a = a * a >> 8
        # Scale each axis by a / r, on magnitudes so negative values
        # don't round further from 0 than positive ones.
        sx = (x if x > 0 else -x) * a // r
        sy = (y if y > 0 else -y) * a // r
        self.stick_x = sx if x > 0 else -sx
        self.stick_y = sy if y > 0 else -sy

    def get_stick_mouse_state(self, touched):
        # global X_LOWER_LIM, X_UPPER_LIM, Y_LOWER_LIM, Y_UPPER_LIM
        # global X_CENTER, Y_CENTER, X_DZ, Y_DZ, _warm

        self.get_stick_raw_values()
        x = self.x_raw          # ints from read_u16
        y = self.y_raw
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

        self._radial_curve(xn, yn)

    def update_touch_state(self):
        '''Averages any readings in the cap pio fifo and compares that to the
        learned untouched baseline to update LAST_TOUCH_STATE.'''
        total = 0
        count = 0
        while self.SM.rx_fifo():
            total += self.SM.get()
            count += 1
        if not count:
            return
        value = total // count
        self.cap_value = value

        if not self._cap_base:
            self._cap_base = value << 8
        base = self._cap_base >> 8

        if self.LAST_TOUCH_STATE:
            self.LAST_TOUCH_STATE = value > base + (base >> self.CAP_OFF_SHIFT)
        else:
            self.LAST_TOUCH_STATE = value > base + (base >> self.CAP_ON_SHIFT)

        if value < base:
            # Follow drops quickly, which also recovers from a touch at boot.
            self._cap_base += ((value << 8) - self._cap_base) >> 2
        elif not self.LAST_TOUCH_STATE:
            # Slowly track drift (temperature, etc) while untouched.
            self._cap_base += ((value << 8) - self._cap_base) >> 8

        if self.debug_print:
            if random.randint(0,1000) < 5:
                self.print("cap value", value, "baseline", base,
                       "touched", self.LAST_TOUCH_STATE)

    def update_state(self):
        '''update_state is a standard function in input modules.
        It updates the internal state based on the current input values.'''    

        clicked = not self.PUSH.value()
        self.update_touch_state()
        touched = self.LAST_TOUCH_STATE

        self.get_stick_mouse_state(touched)
        self.state.mouse_x += self.stick_x
        self.state.mouse_y += self.stick_y
        self.state.mouse_enable = 1 if touched or clicked else 0

        #We might be working on bit n of up to 32 bits in STATE.keys,
        # So we only want to adjust bit n, based on self.KEYS_OFFSET:
        value = 1 if clicked else 0
        # self.state.keys = (self.state.keys & ~(1 << self.KEYS_OFFSET)) | (value << self.KEYS_OFFSET)
        self.set_key_state(0, value)  # use the base class method to set the key state
        # Touch is a key too, so the keymap can give it an action, like a layer.
        self.set_key_state(1, 1 if touched else 0)


if __name__ == "__main__":
    from input import run_test
    run_test(InputModule,
             lambda state, module: print(state.mouse_x,
                                         state.mouse_y,
                                         state.mouse_enable,
                                         state.buttons))
