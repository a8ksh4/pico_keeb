

import machine

machine.freq(200_000_000)  # Set the CPU frequency to 200 MHz

import input_encoder_pio
import input_stick_pio
import input_matrix
import input_adxl
from time import sleep, ticks_us, ticks_add, ticks_diff

INPUTS = [input_encoder_pio, input_stick_pio, input_matrix, input_adxl]
# If pio machines are too many instructions, different
# clocks, ..., they need to be on separate pio blocks.
PIO_MAP = [0, 4, None, None]

# PERIOD_US = 1000  # 1 kHz
PERIOD_US = 1_000_000  # 1 Hz


def tick():
    '''Does stuff every PERIOD_US microseconds.'''
    state = {'keys': [], 'mouse': (0, 0), 'wheel': []}
    for im in INPUTS:
        changes = im.get_state()
        print(im.__name__, changes)
        if 'keys' in changes:
            state['keys'].extend(changes['keys'])
        if 'mouse' in changes:
            state['mouse'] = (state['mouse'][0] + changes['mouse'][0],
                                state['mouse'][1] + changes['mouse'][1])
        if 'mouse_enable' in changes:
            state['mouse_enable'] = changes['mouse_enable']
        if 'wheel' in changes:
            state['wheel'].extend(changes['wheel'])
    print()
    print(state)
    print()
    sleep(1)
    print('foo')


def main():
    '''Main program loop...'''
    print("Initializing input moudles...")
    for im, n in zip(INPUTS, PIO_MAP):
        print("Initializing", im, n)
        im.init(n)
        print(dir(im))

    print("Looping forever...")
    next_t = ticks_us()
    while True:
        tick()
        next_t = ticks_add(next_t, PERIOD_US)
        while ticks_diff(next_t, ticks_us()) > 0:
            pass


if __name__ == "__main__":
    
    # Your main code logic here
    main()
