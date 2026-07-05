'''Analog stick with click and capacitive touch sensing.  You could
comment out the touch stuff if your stick doesn't have it.'''

from machine import ADC, Pin
import rp2


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
Y_INVERT = True

X_LOWER_LIM = 15000
X_UPPER_LIM = 25000

Y_LOWER_LIM = 15000
Y_UPPER_LIM = 25000

X_CENTER = 20000.0
Y_CENTER = 20000.0
X_DEADZONE = 0.02   # in normalized units, learned at runtime
Y_DEADZONE = 0.02
CENTER_ALPHA = 0.01     # EMA smoothing for center learning
WARMUP_ALPHA = 0.3
WARMUP_SAMPLES = 20
_warmup = 0
DZ_MARGIN = 1.3         # deadzone = observed rest deviation * margin


def get_stick_raw_values():
    '''pretty simple raw value read'''
    x_raw = X_ADC.read_u16()
    if X_INVERT:
        x_raw = 65535 - x_raw
    y_raw = Y_ADC.read_u16()
    if Y_INVERT:
        y_raw = 65535 - y_raw
    return x_raw, y_raw


def _scale(v, lo, hi, center):
    '''Scale each side of center independently so both extremes hit +/-1'''
    if v >= center:
        span = hi - center
    else:
        span = center - lo
    return (v - center) / span if span else 0.0


def get_stick_position(touched):
    global X_LOWER_LIM, X_UPPER_LIM, Y_LOWER_LIM, Y_UPPER_LIM
    global X_CENTER, Y_CENTER, X_DEADZONE, Y_DEADZONE, _warmup
    x, y = get_stick_raw_values()
    X_LOWER_LIM = min(x, X_LOWER_LIM)
    X_UPPER_LIM = max(x, X_UPPER_LIM)
    Y_LOWER_LIM = min(y, Y_LOWER_LIM)
    Y_UPPER_LIM = max(y, Y_UPPER_LIM)

    if not touched:
        # stick is at rest: learn true center (EMA)
        if _warmup < WARMUP_SAMPLES:
            a = WARMUP_ALPHA if _warmup else 1.0  # first sample: snap directly
            _warmup += 1
        else:
            a = CENTER_ALPHA
        X_CENTER += a * (x - X_CENTER)
        Y_CENTER += a * (y - Y_CENTER)

    xn = _scale(x, X_LOWER_LIM, X_UPPER_LIM, X_CENTER)
    yn = _scale(y, Y_LOWER_LIM, Y_UPPER_LIM, Y_CENTER)

    if not touched:
        # grow deadzone to cover observed rest deviation
        X_DEADZONE = max(X_DEADZONE, min(abs(xn) * DZ_MARGIN, 0.15))
        Y_DEADZONE = max(Y_DEADZONE, min(abs(yn) * DZ_MARGIN, 0.15))

    if abs(xn) < X_DEADZONE:
        xn = 0.0
    if abs(yn) < Y_DEADZONE:
        yn = 0.0
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


def init(pio_machine_num):
    '''Init is a standard function for input modules that 
    can perform any needede initialization.  Probably this
    is on ly needed to assign unique state machine nums.'''
    global SM
    SM = rp2.StateMachine(pio_machine_num, cap_measure, freq=SM_FREQ,
                       set_base=CAP_SENSE_PIN, jmp_pin=CAP_SENSE_PIN)
    SM.active(1)


def get_state():
    '''get_state is a standard function in inupt modules.
    It returns a dict with keys, a list of states of the stick click
    and capacitive touch state, which can be treated like any other key
    press events and 'mouse' the current x/y mouse velocity.'''
    clicked = not PUSH.value()
    update_touch_state()
    touched = LAST_TOUCH_STATE
    stick_x, stick_y = get_stick_position(touched)
    state = {'keys': [clicked],
             'mouse_enable': [touched or clicked],
             'mouse': (stick_x, stick_y)}
    return state


if __name__ == "__main__":
    from time import sleep
    init(0)
    while True:
        module_state = get_state()
        print(module_state)
        sleep(0.5)
