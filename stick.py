'''Analog stick module
Supports two analog pins, read and translate to x,y position.'''


from machine import ADC, Pin, time_pulse_us
import time

PUSH_PIN = 21
PUSH = Pin(PUSH_PIN, Pin.IN, Pin.PULL_UP)

CAP_SENSE_PIN = 22
CAP_TRESHOLD = 500
CAP = Pin(CAP_SENSE_PIN, Pin.IN)

X_PIN = 27
Y_PIN = 26
X_ADC = ADC(Pin(X_PIN))
Y_ADC = ADC(Pin(Y_PIN))

X_LOWER_LIM = 0
X_UPPER_LIM = 3.3
X_MID = X_LOWER_LIM + (X_UPPER_LIM - X_LOWER_LIM) / 2

Y_LOWER_LIM = 0
Y_UPPER_LIM = 3.3
Y_MID = Y_LOWER_LIM + (Y_UPPER_LIM - Y_LOWER_LIM) / 2

def get_raw_values():
    '''pretty simple raw value read'''
    x_raw = X_ADC.read_u16()
    y_raw = Y_ADC.read_u16()
    return x_raw, y_raw


def measure_cap():
    CAP.init(Pin.OUT)
    CAP.value(0)
    time.sleep_us(10)
    CAP.init(Pin.IN)
    t = time_pulse_us(CAP, 1, 10000)
    return t


def print_cap_state():
    t = measure_cap()
    print("Cap state:", 'touched' if t > CAP_TRESHOLD else 'open', t)


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
