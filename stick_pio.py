'''Analog stick module
Supports two analog pins, read and translate to x,y position.'''


from machine import ADC, Pin, time_pulse_us
import rp2
import time

PUSH_PIN = 21
PUSH = Pin(PUSH_PIN, Pin.IN, Pin.PULL_UP)

CAP_SENSE_PIN = 22
CAP_TRESHOLD = 4000
# CAP = Pin(CAP_SENSE_PIN, Pin.IN)
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
    '''pretty simple raw value read'''
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
 
    # --- charge phase: drive pin high ---
    set(pindirs, 1)               # pin = output
    set(pins, 1)                  # drive high to charge
    nop()                  [31]   # let it charge (tune if needed)
    nop()                  [31]
 
    # --- discharge / measure phase ---
    set(pindirs, 0)               # release: pin = input, starts falling
    mov(x, invert(null))          # x = 0xFFFFFFFF
 
    label("loop")
    jmp(pin, "still_high")        # pin HIGH -> keep counting
    jmp("done")                   # pin LOW  -> finished
    # NOTE: to invert sense (cap charges low / bleeds high), swap the two
    # lines above: jmp(pin, "done") then jmp("still_high").
 
    label("still_high")
    jmp(x_dec, "loop")            # x-- ; loop while x != 0
    # if x underflows we just fall through to done (saturated)
 
    label("done")
    mov(isr, x)                   # report remaining X
    # push(noblock)                 # don't stall if FIFO full
    push()
    wrap()


cap_sm = rp2.StateMachine(0, cap_measure, freq=SM_FREQ,
            set_base=CAP_SENSE_PIN, jmp_pin=CAP_SENSE_PIN)
cap_sm.active(1)

# @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
# def measure_cap():
#     # I expect touch time to be around 8400 microseconds, so we need
#     # our clock freqency and count loop to be able to measure that in 31 count cycles.
#     # 15000 microseconds / 31 = 483.87 microseconds per cycle, 
#     # so we need a clock frequency of about 2.066 kHz.???

#     label("charge")
#     set(pindirs, 1)  # Set pin as output
#     set(pins, 1)  # Set pin high to charge capacitor
#     nop() [31]  # Wait for 32 cycles (adjust as needed for timing)
#     set(pins, 0)  # Set pin low to start discharging

#     # Discharge phase loops until pin goes low, counting the time and pushes the count to the FIFO
#     set(pindirs, 0)  # Set pin as input to read discharge
#     set(x, 31)
#     label("discharge")
#     nop() [31]  # Wait for 32 cycles
#     nop() [31]
#     nop() [31]
#     nop() [31]
#     jmp(pin, "write")  # break if pin goes low
#     jmp(x_dec, "discharge")  # Decrement x and loop if not zero

#     label("write")
#     mov(isr, x)  # Move the count to ISR
#     push()  # Push the count to the FIFO

# # cap_sm = rp2.StateMachine(0, measure_cap, freq=1000000, set_base=CAP)
# cap_sm = rp2.StateMachine(0, measure_cap, freq=2066, set_base=CAP)
# cap_sm.active(1)


def get_cap_time():
    # cap_sm.exec("irq(rel(0))")  # Trigger the PIO program
    # while not cap_sm.irq():
        # pass  # Wait for the PIO program to signal completion
    # return cap_sm.get()  # Get the result from the PIO program
    # Read up to four counts from the FIFO and return the average and the last one.
    counts = []
    for _ in range(4):
        if cap_sm.rx_fifo():
            counts.append(cap_sm.get())
            print("Got cap count:", counts[-1])
    if counts:
        avg_count = sum(counts) // len(counts)
        last_count = counts[-1]
        return avg_count, last_count
    else:
        return None, None


def print_cap_state():
    # t = measure_cap()
    avg, last = get_cap_time()
    print("Cap avg:", avg, "last:", last)
    print("Cap state:", 'touched' if avg > CAP_TRESHOLD else 'open', avg)


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
