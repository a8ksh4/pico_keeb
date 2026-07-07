

import machine

machine.freq(200_000_000)  # Set the CPU frequency to 200 MHz

import input_encoder_pio
import input_stick_pio
import input_matrix
import input_adxl

# import pyb
# pyb.usb_mode("VCP+HID", hid=pyb.hid_keyboard)
import usb.device
from usb.device.mouse import MouseInterface

from time import sleep, ticks_us, ticks_add, ticks_diff

from micropython import const, mem_info

INPUTS = [input_encoder_pio, input_stick_pio, input_matrix, input_adxl]
# If pio machines are too many instructions, different
# clocks, ..., they need to be on separate pio blocks.
PIO_MAP = [0, 4, None, None]


# PERIOD_US = 1000  # 1 kHz
PERIOD_US = 1_000_000  # 1 Hz

MOUSE_SCALE = 0.5  # Must be less than 0.5...

class InputState:
    def __init__(self, num_keys):
        self.keys = bytearray(num_keys)  # 0/1 per key
        self.wheel = 0                    # accumulated detents this tick
        self.mouse_x = 0                  # fixed-point, e.g. 1/256 px units
        self.mouse_y = 0
        self.mouse_enable = 0
        self.mouse = MouseInterface()

    def clear_deltas(self):
        self.wheel = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_enable = 0


def scale_mouse_movement(dx, dy):
    dx = int(MOUSE_SCALE * dx)
    dy = int(MOUSE_SCALE * dy)
    if dx > 127:
        dx = 127
    if dx < -127:
        dx = -127
    if dy > 127:
        dy = 127
    if dy < -127:
        dy = -127
    return dx, dy


def tick(input_state):
    '''Does stuff every PERIOD_US microseconds.'''
    input_state.clear_deltas()
    for im in INPUTS:
        im.update_state()
    # if input_state.mouse_enable and \
            # (input_state.mouse_x or input_state.mouse_y):
    mdx, mdy = scale_mouse_movement(input_state.mouse_x, input_state.mouse_y)
    input_state.mouse.move_by(mdx, mdy)

    print()
    print(input_state.mouse_x, input_state.mouse_y,
          input_state.mouse_enable, input_state.wheel,
          input_state.keys)
    for n, key in enumerate(input_state.keys):
        if key:
            print(n)


def main():
    '''Main program loop...'''
    # global INPUT_STATE

    print("Get shapes of all inputs to build state shaps...")
    state_num_keys = 0

    for im in INPUTS:
        im_keys_num = im.get_num_keys()
        print('    ', im.__name__, im_keys_num)
        state_num_keys += im_keys_num
    print("  * State total keys:", state_num_keys)
    input_state = InputState(state_num_keys)

    # Enable usb mouse
    usb.device.get().init(input_state.mouse, builtin_driver=True)

    print("Initializing input moudles...")

    state_num_keys = 0  # reset to count keys as we init each module
    for im, pio_addr in zip(INPUTS, PIO_MAP):
        print("Initializing", im, pio_addr)
        im_keys_num = im.get_num_keys()
        if im_keys_num == 0:
            im_keys_mv = None
        else:
            im_keys_mv = memoryview(input_state.keys)[state_num_keys:state_num_keys + im_keys_num]
        im.init(pio_addr, input_state, im_keys_mv)
        state_num_keys += im_keys_num
        # print(dir(im))

    print("Looping forever...")
    next_t = ticks_us()
    while True:
        print()
        mem_info()
        tick(input_state)
        next_t = ticks_add(next_t, PERIOD_US)
        while ticks_diff(next_t, ticks_us()) > 0:
            pass


if __name__ == "__main__":
    
    # Your main code logic here
    main()
