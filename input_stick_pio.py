'''Analog stick with click and capacitive touch sensing.  You could
comment out the touch stuff if your stick doesn't have it.'''

from machine import ADC, Pin
import rp2

STATE = None
PUSH_PIN = 21
PUSH = Pin(PUSH_PIN, Pin.IN, Pin.PULL_UP)

CAP_SENSE_PIN_NUM = 22
CAP_THRESHOLD = 5000
COUNT_MAX = 0xFFFFFFFF
CAP_SENSE_PIN = Pin(CAP_SENSE_PIN_NUM, Pin.OUT, value=0)
SM_FREQ = 1_000_000

LAST_TOUCH_STATE = False
# TODO: possibly implement smoothing for cap touch

X_PIN_NUM = 26
Y_PIN_NUM = 27
X_ADC = ADC(Pin(X_PIN_NUM))
Y_ADC = ADC(Pin(Y_PIN_NUM))
X_INVERT = False
Y_INVERT = False

X_LOWER_LIM = 15000
X_UPPER_LIM = 25000

Y_LOWER_LIM = 15000
Y_UPPER_LIM = 25000

X_CENTER = 20000 << 8
Y_CENTER = 20000 << 8
X_DZ = 5          # deadzone in 1/256 units (0.02)
Y_DZ = 5
DZ_CAP = 38       # 0.15
_warm = 0
# X_DEADZONE = 0.02   # in normalized units, learned at runtime
# Y_DEADZONE = 0.02
# CENTER_ALPHA = 0.01     # EMA smoothing for center learning
# WARMUP_ALPHA = 0.3
# WARMUP_SAMPLES = 20
# _warmup = 0
# DZ_MARGIN = 1.3         # deadzone = observed rest deviation * margin


def get_stick_raw_values():
    '''pretty simple raw value read'''
    x_raw = X_ADC.read_u16()
    if X_INVERT:
        x_raw = 65535 - x_raw
    y_raw = Y_ADC.read_u16()
    if Y_INVERT:
        y_raw = 65535 - y_raw
    return x_raw, y_raw


def _axis(v, lo, hi, c8):
    c = c8 >> 8
    span = (hi - c) if v >= c else (c - lo)
    if span <= 0:
        return 0
    return (v - c) * 256 // span


def get_stick_mouse_state(touched):
    global X_LOWER_LIM, X_UPPER_LIM, Y_LOWER_LIM, Y_UPPER_LIM
    global X_CENTER, Y_CENTER, X_DZ, Y_DZ, _warm

    x, y = get_stick_raw_values()          # ints from read_u16
    if x < X_LOWER_LIM: X_LOWER_LIM = x
    if x > X_UPPER_LIM: X_UPPER_LIM = x
    if y < Y_LOWER_LIM: Y_LOWER_LIM = y
    if y > Y_UPPER_LIM: Y_UPPER_LIM = y

    if not touched:
        if _warm == 0:
            X_CENTER = x << 8
            Y_CENTER = y << 8
            _warm = 1
        elif _warm < 20:
            X_CENTER += ((x << 8) - X_CENTER) >> 2   # fast warmup
            Y_CENTER += ((y << 8) - Y_CENTER) >> 2
            _warm += 1
        else:
            X_CENTER += ((x << 8) - X_CENTER) >> 7   # slow track (~0.008)
            Y_CENTER += ((y << 8) - Y_CENTER) >> 7

    xn = _axis(x, X_LOWER_LIM, X_UPPER_LIM, X_CENTER)
    yn = _axis(y, Y_LOWER_LIM, Y_UPPER_LIM, Y_CENTER)

    if not touched:
        dx = xn if xn >= 0 else -xn
        dx = dx * 13 // 10                 # 1.3 margin
        if dx > X_DZ: X_DZ = dx if dx < DZ_CAP else DZ_CAP
        dy = yn if yn >= 0 else -yn
        dy = dy * 13 // 10
        if dy > Y_DZ: Y_DZ = dy if dy < DZ_CAP else DZ_CAP

    if -X_DZ < xn < X_DZ: xn = 0
    if -Y_DZ < yn < Y_DZ: yn = 0
    return xn, yn


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


def update_touch_state():
    '''This totals up any values in the cap pio fifo.
    If the average is below the threshold, then touch is true.'''
    global LAST_TOUCH_STATE
    total = 0
    count = 0
    while SM.rx_fifo():          # drain stale samples
        value = COUNT_MAX -SM.get()
        # print("cap value", value)
        total += value
        count += 1

    if count:
        average = total / count
        # print("cap average", average, average < CAP_THRESHOLD)
        LAST_TOUCH_STATE = average < CAP_THRESHOLD


def get_num_keys():
    '''Tells the main program how many keys this module handles
    so the main program knows how much memory to allocate for it.'''
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
    SM = rp2.StateMachine(pio_machine_num, cap_measure, freq=SM_FREQ,
                       set_base=CAP_SENSE_PIN, jmp_pin=CAP_SENSE_PIN)
    SM.active(1)


def update_state():
    '''update_state is a standard function in input modules.
    It updates the internal state based on the current input values.'''    

    clicked = not PUSH.value()
    update_touch_state()
    touched = LAST_TOUCH_STATE

    stick_x, stick_y = get_stick_mouse_state(touched)
    STATE.mouse_x += stick_x
    STATE.mouse_y += stick_y
    STATE.mouse_enable = 1 if touched or clicked else 0

    KEYS_MV[0] = 1 if clicked else 0


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
    state = InputState(1)

    init(0, state, memoryview(state.keys))
    while True:
        state.clear_deltas()
        update_state()
        print(STATE.mouse_x, STATE.mouse_y, STATE.mouse_enable, STATE.keys[0])
        sleep(0.5)
