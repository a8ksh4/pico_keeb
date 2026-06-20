'''moudle to handle the encoder wheel and its clicker.
This is a standard encoder with ground, two pins for the
encoder, and a pin for the clicker.'''

from machine import Pin
import rp2
import time

BUTTON_PIN = 5
ENCODER_A = 4
ENCODER_B = 3
ENCODER_FREQ = 1_000_000

PIN_BUTTON = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
PIN_ENCODER_A = Pin(ENCODER_A, Pin.IN, Pin.PULL_UP)
PIN_ENCODER_B = Pin(ENCODER_B, Pin.IN, Pin.PULL_UP)

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def encoder_monitor():
    '''PIO program to track state of the encoder pins and report
    new state when it changes.'''
    in_(pins, 2)  # read encoder A and B into ISR
    mov(x, isr)  # store initial state in X
    push()       # push initial state to FIFO

    wrap_target()
    in_(pins, 2)  # read encoder A and B into ISR
    mov(y, isr)  # store new state in Y
    jmp(x_not_y, "state_changed")  # if state changed, report it
    jmp("loop")  # otherwise, keep waiting

    label("state_changed")
    mov(x, y)
    push()       # push new state to FIFO

    label("loop")
    wrap()


encoder_pins = [PIN_ENCODER_A, PIN_ENCODER_B]
encoder_sm = rp2.StateMachine(1, encoder_monitor, 
                          freq=ENCODER_FREQ, 
                          in_base=0,
                          )
encoder_sm.active(1)

def get_encoder_changes():
    '''check the FIFO for any new encoder states and return them as a list.'''
    changes = []
    while encoder_sm.rx_fifo():
        state = encoder_sm.get() & 0b11  # get the last two bits for A and B
        changes.append(state)
    return changes

def print_encoder_changes():
    '''check for new encoder states and print them.'''
    changes = get_encoder_changes()
    for state in changes:
        a = (state >> 1) & 1
        b = state & 1
        print(f"Encoder changed: A={a} B={b}")

# def monitor_position(duration = 1):
#     '''test code to monitor the encoder position for a
#     given duration and report any changes.'''
#     if PIN_BUTTON.value() == 0:
#         print("Encoder button pressed!")
#     else:
#         print("Encoder button released.")
#     print(f"Monitoring encoder for {duration} seconds...")
#     time.sleep(0.2)  # small delay to allow user response
#     start_time = time.ticks_ms()
#     last_a = PIN_ENCODER_A.value()
#     last_b = PIN_ENCODER_B.value()
#     while time.ticks_diff(time.ticks_ms(), start_time) < duration * 1000:
#         a = PIN_ENCODER_A.value()
#         b = PIN_ENCODER_B.value()
#         if (a, b) != (last_a, last_b):
#             print(f"Encoder changed: A={a} B={b}")
#             last_a, last_b = a, b
#         # time.sleep_ms(1)  # small delay to avoid bounce
