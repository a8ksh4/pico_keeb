

import machine

machine.freq(200_000_000)  # Set the CPU frequency to 200 MHz

import input_encoder_pio
import input_stick_pio
import input_matrix
import input_adxl

import keymap_tallcan as keymap

# import pyb
# pyb.usb_mode("VCP+HID", hid=pyb.hid_keyboard)
import usb.device
from usb.device.mouse import MouseInterface
from usb.device.keyboard import KeyboardInterface, KeyCode, LEDCode

from time import sleep, ticks_us, ticks_add, ticks_diff

from micropython import const, mem_info

INPUTS = [input_encoder_pio, input_stick_pio, input_matrix, input_adxl]
# If pio machines are too many instructions, different
# clocks, ..., they need to be on separate pio blocks.
PIO_MAP = [0, 4, None, None]


# PERIOD_US = 1000  # 1 kHz
PERIOD_US = 1_000_000  # 1 Hz

MOUSE_SCALE = 0.5  # Must be less than 0.5...

class KeyboardInterfaceMod(KeyboardInterface):
    def send_keys_mod(self, down_keys, modifiers, timeout_ms=100):
        r, s = self._key_reports
        r[0] = modifiers
        i = 2
        for k in down_keys:
            if k and i < 8:
                r[i] = k
                i += 1
        while i < 8:
            r[i] = 0
            i += 1
        if self.send_report(r, timeout_ms):
            self._key_reports[0] = s
            self._key_reports[1] = r
            return True
        return False


class KeyboardEvent:
    def __init__(self, num_keys):
        self.active_layer = 0
        self.buttons = bytearray(num_keys)  # 1 for pressed
        self.zeros = bytes(num_keys)
        self.modifiers = 0
        self.output_keys = bytearray(6)
        self.uinput_codes = bytearray(6)
        self.status = 0
        # 0: idle, 1: active, 2: released, 3: cleanup...
    def cleanup(self):
        self.status = 0
        self.active_layer = 0
        self.modifiers = 0
        num_buttons = len(self.buttons)
        self.buttons[:] = self.zeros[:num_buttons]
        self.output_keys[:] = self.zeros  # no allocation
        self.uinput_codes[:] = self.zeros[:6]  # one byte allocation?
        # for n in range(num_buttons):
        #     self.buttons[n] = 0
        
        # for n in range(6):
        #     self.output_keys[n] = 0
        #     self.uinput_codes[n] = 0
    def set_key(code):
        if code < 0:
            self.modifiers |= -code
        else:
            for n in range(6):  # step through array
                if self.output_keys[n] == 0:
                    self.output_keys[n] = code



class InputState:
    def __init__(self, num_keys):
        self.keys = bytearray(num_keys)  # 0/1 per key
        self.wheel = 0                    # accumulated detents this tick
        self.mouse_x = 0                  # fixed-point, e.g. 1/256 px units
        self.mouse_y = 0
        self.mouse_enable = 0
        self.mouse = MouseInterface()
        self.keyboard = KeyboardInterface()

    def clear_deltas(self):
        self.wheel = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_enable = 0


def scale_mouse_movement(dx, dy):
    # Avoiding float math to avoid memory alloc in our main loop!
    # Scale to 1/2:
    dx = dx >> 1
    dy = dy >> 1
    # Scale to 1/4:
    # dx = dx >> 1
    # dy = dy >> 1
    # Scale to 3/8:
    # dx = dx * 96 >> 8  # 96 / 256 = 0.375
    # dy = dy * 96 >> 8
    return dx, dy


def tick(input_state):
    '''Does stuff every PERIOD_US microseconds.'''
    input_state.clear_deltas()
    mouse = input_state.mouse
    keeb = input_state.keyboard

    for im in INPUTS:
        im.update_state()
    if input_state.mouse_enable and \
            (input_state.mouse_x or input_state.mouse_y):
        mdx, mdy = scale_mouse_movement(input_state.mouse_x, input_state.mouse_y)
        input_state.mouse.move_by(mdx, mdy)

    print()
    print(input_state.mouse_x, input_state.mouse_y, input_state.mouse_enable,
          input_state.wheel, input_state.keys)

    # Check for exit and shutdown key combos
    for pin in keymap.EXIT_KEYS:
        if not input_state.keys[pin]:
            break
    else:
        print('EXIT_KEYS matched.  Calling Quit.')

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
    usb.device.get().init(input_state.keyboard,
                          input_state.mouse,
                          builtin_driver=True)
    while not (input_state.keyboard.is_open()and input_state.mouse.is_open()):
        pass
    print("Mouse and keyboard are initialized...")

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
