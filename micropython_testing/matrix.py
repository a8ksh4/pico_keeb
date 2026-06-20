'''micropython matrix scanning


Copilot free seems to think this is something
Peter Hinch would write.  lol.
'''

from machine import Pin

# DIODE_DIR = 'COL2ROW'  # or 'ROW2COL'
COL2ROW = False
ROWS = [8, 9, 10, 11]
COLS = [16, 17, 18, 20, 19]

if COL2ROW:
    DRIVEN_PINS = COLS
    READ_PINS = ROWS
else:
    DRIVEN_PINS = ROWS
    READ_PINS = COLS

DRIVEN_PINS = [Pin(i, Pin.OUT) for i in DRIVEN_PINS]
READ_PINS = [Pin(i, Pin.IN, Pin.PULL_DOWN) for i in READ_PINS]


def scan_matrix():
    active_keys = []
    for di, dp in enumerate(DRIVEN_PINS):
        dp.value(1)
        for ri, rp in enumerate(READ_PINS):
            if rp.value():  # Active low
                if COL2ROW:
                    active_keys.append((ri, di))  # Row, Col
                else:
                    active_keys.append((di, ri))  # Row, Col
        dp.value(0)
    return active_keys


def print_active_keys():
    active_keys = scan_matrix()
    print(active_keys)