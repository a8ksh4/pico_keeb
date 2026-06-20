'''moudle to handle the encoder wheel and its clicker.
This is a standard encoder with ground, two pins for the
encoder, and a pin for the clicker.'''

from machine import Pin
import time

BUTTON_PIN = 5
ENCODER_A = 4
ENCODER_B = 3

PIN_BUTTON = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
PIN_ENCODER_A = Pin(ENCODER_A, Pin.IN, Pin.PULL_UP)
PIN_ENCODER_B = Pin(ENCODER_B, Pin.IN, Pin.PULL_UP)

def monitor_position(duration = 1):
    '''test code to monitor the encoder position for a
    given duration and report any changes.'''
    if PIN_BUTTON.value() == 0:
        print("Encoder button pressed!")
    else:
        print("Encoder button released.")
    print(f"Monitoring encoder for {duration} seconds...")
    time.sleep(0.2)  # small delay to allow user response
    start_time = time.ticks_ms()
    last_a = PIN_ENCODER_A.value()
    last_b = PIN_ENCODER_B.value()
    while time.ticks_diff(time.ticks_ms(), start_time) < duration * 1000:
        a = PIN_ENCODER_A.value()
        b = PIN_ENCODER_B.value()
        if (a, b) != (last_a, last_b):
            print(f"Encoder changed: A={a} B={b}")
            last_a, last_b = a, b
        # time.sleep_ms(1)  # small delay to avoid bounce
