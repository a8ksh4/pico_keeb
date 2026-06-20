'''This test tool runs monitors eight buttons attached to the board
and reports changes in their state.'''

from machine import Pin
import time

# TX,GPIO0
# RX,GPIO1
# D2,GPIO2
# D3,GPIO3
# D4,GPIO4
# D5,GPIO5
# D6,GPIO6
# D7,GPIO7
# D8,GPIO8
# D9,GPIO9
# D10,GPIO10
# MISO,GPIO20
# SCK,GPIO18
# MOSI,GPIO19
# SDA,GPIO12
# SCL,GPIO13
# A0,GPIO26
# A1,GPIO27
# A2,GPIO28
# A3,GPIO29
# NEOPIXEL_POWER,GPIO16
# NEOPIXEL,GPIO17

# PINS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 18, 19, 20, 26, 27, 28, 29]
PINS = [26, 27, 28, 29, 10, 19, 20, 18]


BUTTONS = [Pin(pin, Pin.IN, Pin.PULL_UP) for pin in PINS]

last_states = None
while True:
    states = [button.value() for button in BUTTONS]
    if last_states is not None and states != last_states:
        print([PINS[n] for n, s in enumerate(states) if s == 0])
    last_states = states
    time.sleep(0.1)