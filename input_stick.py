'''Analog stick with click and capacitive touch sensing.  You could
comment out the touch stuff if your stick doesn't have it.'''


from machine import ADC, Pin
import rp2
import time

PUSH_PIN = 21
PUSH = Pin(PUSH_PIN, Pin.IN, Pin.PULL_UP)

CAP_SENSE_PIN = 22
CAP_THRESHOLD = 50000
COUNT_MAX = 0xFFFFFFFF
CAP = Pin(CAP_SENSE_PIN, Pin.OUT, value=0)
SM_FREQ = 1_000_000

LAST_TOUCH_STATE = False
# TODO: possibly implement smoothing for cap touch

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

def get_stick_raw_values():
    '''pretty simple raw value read'''
    x_raw = X_ADC.read_u16()
    if X_INVERT:
        x_raw = 65535 - x_raw
    y_raw = Y_ADC.read_u16()
    if Y_INVERT:
        y_raw = 65535 - y_raw
    return x_raw, y_raw

def get_stick_position():
    '''Translate raw values to positional value from -1 to 1 for x and y'''
    x, y = get_stick_raw_values()

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


def update_touch_state():
    '''This totals up any values in the cap pio fifo.
    If the average is below the threshold, then touch is true.'''
    total = 0
    count = 0
    while SM.rx_fifo():          # drain stale samples
        total += SM.get()
        count += 1
    total = total / count
    LAST_TOUCH_STATE = total < CAP_THRESHOLD
 

def init(pio_machine_num):
    '''Init is a standard function for input modules that 
    can perform any needede initialization.  Probably this
    is on ly needed to assign unique state machine nums.'''
    global SM
    SM = rp2.StateMachine(0, cap_measure, freq=SM_FREQ,
                       set_base=CAP, jmp_pin=CAP)
    SM.active(1)

def get_state():
    '''get_state is a standard function in inupt modules.
    It returns a dict with keys, a list of states of the stick click
    and capacitive touch state, which can be treated like any other key
    press events and 'mouse' the current x/y mouse velocity.'''
    clicked = not PUSH.value()
    update_touch_state()
    touched = LAST_TOUCH_STATE
    stick_x, stick_y = get_stick_position()
    state = {'keys': [clicked, touched],
             'mouse': (stick_x, stick_y)}
    return state
