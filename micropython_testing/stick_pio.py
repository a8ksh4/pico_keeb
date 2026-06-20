'''Analog stick module
Supports two analog pins, read and translate to x,y position.'''


from machine import ADC, Pin
import rp2
import time

PUSH_PIN = 21
PUSH = Pin(PUSH_PIN, Pin.IN, Pin.PULL_UP)

CAP_SENSE_PIN = 22
CAP_TRESHOLD = 50000
COUNT_MAX = 0xFFFFFFFF
SM_FREQ = 1_000_000

X_PIN = 26
Y_PIN = 27
X_ADC = ADC(Pin(X_PIN))
Y_ADC = ADC(Pin(Y_PIN))
X_INVERT = False
Y_INVERT = True

X_LOWER_LIM = 0
X_UPPER_LIM = 3.3
X_MID = X_LOWER_LIM + (X_UPPER_LIM - X_LOWER_LIM) / 2

Y_LOWER_LIM = 0
Y_UPPER_LIM = 3.3
Y_MID = Y_LOWER_LIM + (Y_UPPER_LIM - Y_LOWER_LIM) / 2

def get_raw_values():
    '''pretty simple raw value read for the stick adc pins'''
    x_raw = X_ADC.read_u16()
    if X_INVERT:
        x_raw = 65535 - x_raw
    y_raw = Y_ADC.read_u16()
    if Y_INVERT:
        y_raw = 65535 - y_raw
    return x_raw, y_raw


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
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
 
 
cap_pin = Pin(CAP_SENSE_PIN, Pin.OUT, value=0)
cap_sm = rp2.StateMachine(0, cap_measure, freq=SM_FREQ,
                       set_base=cap_pin, jmp_pin=cap_pin)
cap_sm.active(1)
 
 
def read_cap(samples=4):
    """Averaged count. Lower = touched, higher = open."""
    while cap_sm.rx_fifo():          # drain stale samples
        cap_sm.get()
    total = 0
    for _ in range(samples):
        total += COUNT_MAX - cap_sm.get()
    return total // samples


# cap_sm = rp2.StateMachine(0, cap_measure, freq=SM_FREQ,
#             set_base=CAP_SENSE_PIN, jmp_pin=CAP_SENSE_PIN)
# cap_sm.active(1)

def cap_touched():
    return read_cap() < CAP_THRESHOLD


def print_cap_state():
    # t = measure_cap()
    # avg, last = get_cap_time()
    # print("Cap avg:", avg, "last:", last)
    # print("Cap state:", 'touched' if avg > CAP_TRESHOLD else 'open', avg)
    cap_time = read_cap()
    print("Cap state:", 'touched' if cap_time < CAP_TRESHOLD else 'open', cap_time)


def print_push_state():
    s = not PUSH.value()
    print("Stick button:", 'pushed' if s else 'open', s)


def get_position():
    '''Translate raw values to positional value from -1 to 1 for x and y'''
    x, y = get_raw_values()

    x_range = X_MID - X_LOWER_LIM
    if x <= X_MID:
        x = (X_MID - x) / x_range
    else:
        x = (x - X_MID) / x_range

    y_range = Y_MID - Y_LOWER_LIM
    if y <= Y_MID:
        y = (Y_MID - y) / y_range
    else:
        y = (y - Y_MID) / y_range

    return x,y


def print_position():
    '''testing print statement'''
    x, y = get_raw_values()
    print("Stick Raw X:", x, "Y:", y)
    x, y = get_position()
    print("Stick X:", x, "Y:", y)
