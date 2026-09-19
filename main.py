'''main function!'''

# disable pylint import error:
# pylint: disable=import-error

import machine

machine.freq(200_000_000)  # Set the CPU frequency to 200 MHz

import input_encoder_pio
import input_stick_pio
import input_matrix
import input_adxl
from input import scale_mouse_movement

import keymap_tallcan as KEYMAP
LOOKUP = KEYMAP.LOOKUP

# import pyb
# pyb.usb_mode("VCP+HID", hid=pyb.hid_keyboard)
import usb.device
from usb.device.mouse import MouseInterface
from usb.device.keyboard import KeyboardInterface, KeyCode, LEDCode

from time import sleep, ticks_us, ticks_add, ticks_diff

from micropython import const, mem_info

INPUTS = [input_encoder_pio, input_stick_pio,
          input_matrix, input_adxl]
# If pio machines are too many instructions, different
# clocks, ..., they need to be on separate pio blocks.
PIO_MAP = [0, 4, None, None]


# PERIOD_US = 1000  # 1 kHz
PERIOD_US = 1_000_000  # 1 Hz

MOUSE_SCALE = 0.5  # Must be less than 0.5...

# class KeyboardInterfaceMod(KeyboardInterface):
#     '''This is an override for the keyboard interface in 
#     the micropython usb.device.keyboard module.  It adds a method to send
#     a list of keys with modifiers.  The original send_keys method only
#     sends a list of keys with no modifiers.
#     I think maybe this is not necessary.  tbd.'''
#     def send_keys_mod(self, down_keys, modifiers, timeout_ms=100):
#         '''foo.'''
#         r, s = self._key_reports
#         r[0] = modifiers
#         i = 2
#         for k in down_keys:
#             if k and i < 8:
#                 r[i] = k
#                 i += 1
#         while i < 8:
#             r[i] = 0
#             i += 1
#         if self.send_report(r, timeout_ms):
#             self._key_reports[0] = s
#             self._key_reports[1] = r
#             return True
#         return False


class KeyboardEvent:
    '''We pre-allocate a few of these at start and use them to associate
    key presses with actions.  We  call cleanup when the event is done.'''
    def __init__(self, num_keys):
        self.active_layer = 0
        self.buttons = 0
        self.zeros = bytes(num_keys)
        self.modifiers = 0
        self.output_keys = bytearray(6)
        self.uinput_codes = bytearray(6)
        self.hold_time_exceeded = False
        # self.status = 0
        # 0: idle,   1: active,   2: released,   3: cleanup...

    def cleanup(self):
        '''Resets the event for reuse.'''
        # self.status = 0
        self.active_layer = 0
        self.modifiers = 0
        self.buttons = 0
        # self.output_keys[:] = self.zeros  # no allocation
        # self.uinput_codes[:] = self.zeros[:6]  # one byte allocation?

    # def set_key(self, code):
    #     '''foo'''
    #     if code < 0:
    #         self.modifiers |= -code
    #     else:
    #         for n in range(6):  # step through array
    #             if self.output_keys[n] == 0:
    #                 self.output_keys[n] = code

    def compare_buttons(self, new_buttons):
        '''Returns (Bool, Bool), where first bool is True if any new buttons
        are pressed, and second bool is True if any buttons were released.'''
        any_pressed = (self.buttons & new_buttons) != new_buttons
        any_released = (self.buttons & new_buttons) != self.buttons
        return any_pressed, any_released


class InputState:
    '''An instance of this is passed to the input modules to track state.'''
    def __init__(self, ):
        # self.keys = bytearray(num_keys)  # 0/1 per key
        self.buttons = 0                     # accumulated key presses as a bitfield
        self.wheel = 0                    # accumulated detents this tick
        self.mouse_x = 0                  # fixed-point, e.g. 1/256 px units
        self.mouse_y = 0
        self.mouse_enable = 0
        self.mouse = MouseInterface()
        self.keyboard = KeyboardInterface()
        self.active_events = []  # list of active KeyboardEvent objects
        self.idle_events = []    # list of idle KeyboardEvent objects for reuse
        self.current_event = None  # the current event being processed
        self.send_keys = [0 for _ in range(10)]
        # hid send_keys can pass up to six regular keys,
        # and puts shift ctrl alt gui in the modifyer byte,
        # but we pass them as regular keys.

    def clear_deltas(self):
        '''After each tick, we clear these values.'''
        self.wheel = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_enable = 0

    def tick(self):
        '''Make sure we have an event objest to work on.'''
        if self.current_event is None:
            self.current_event = self.idle_events.pop()  # get an idle event

    def queue_current_event(self):
        '''Adds the current event to the active list and clears it.'''
        self.active_events.append(self.current_event)
        self.current_event = None

    def recycle_event(self, event):
        '''Recycles an event back to the idle pool.'''
        event.cleanup()
        if self.current_event == event:
            self.current_event = None
        if event in self.active_events:
            self.active_events.remove(event)
        self.idle_events.append(event)

    def get_active_layer(self):
        '''Returns the active layer of the top event, or 0 if no events.'''
        last_active_event = self.active_events[-1] if self.active_events else None
        if last_active_event is None:
            return 0
        return last_active_event.active_layer


def tick(input_state):
    '''Does stuff every PERIOD_US microseconds.'''
    input_state.clear_deltas()
    mouse = input_state.mouse
    keeb = input_state.keyboard

    # Update all input modules:
    for im in INPUTS:
        im.update_state()

    # Handle mouse movement:
    print("Mouse enabled:", input_state.mouse_enable)
    if input_state.mouse_enable and \
            (input_state.mouse_x or input_state.mouse_y):
        mdx, mdy = scale_mouse_movement(input_state.mouse_x, input_state.mouse_y)
        print("Moving mouse:", mdx, mdy)
        input_state.mouse.move_by(mdx, mdy)

    # 
    input_state.tick()
    current_layer = input_state.get_active_layer()
    current_event = input_state.current_event

    # Check for exit and shutdown key combos
    # for pin in keymap.EXIT_KEYS:
    #     if not input_state.buttons[pin]:
    #         break
    # else:
    #     print('EXIT_KEYS matched.  Calling Quit.')

    # for n, key in enumerate(input_state.buttons):
    #     if key:
    #         print(n)

    # remove buttons that are part of an active event
    buttons = input_state.buttons
    for event in input_state.active_events:
        buttons &= ~event.buttons
    print(input_state.buttons, '->', buttons)

    # recycle completed events back to the idle pool
    for event in input_state.active_events:
        if not (event.buttons & input_state.buttons):
            print("Recycling event:", event.action)
            input_state.recycle_event(event)

    ########
    # New event block
    ########
    # variables - buttons, current_event.buttons
    process_current_event = False
    current_time = ticks_us()
    if not buttons and not current_event.buttons:
        pass
    elif buttons and not current_event.buttons:
        current_event.buttons = buttons
        print("Event starting:", current_event.buttons)
        current_event.start_time = current_time
    elif not buttons and current_event.buttons:
        # current_event.status = 2  # released
        print("Event released:", current_event.buttons)
        process_current_event = True
    elif buttons and current_event.buttons:
        any_pressed, any_released = current_event.compare_buttons(buttons)
        if any_released:
            # current_event.status = 2  # released
            print("Event released:", current_event.buttons)
            process_current_event = True
        elif any_pressed:
            # current_event.status = 1  # active
            current_event.buttons = buttons
            print("Event continuing:", current_event.buttons)
        elif current_time - current_event.start_time > KEYMAP.HOLD_TIME_MS * 1000:
            current_event.held_time_exceeded = True
            process_current_event = True

    if process_current_event:
        held = current_event.held_time_exceeded
        # Check what actions the current event maps to:
        foo = LOOKUP[current_layer].get(current_event.buttons, (None, None, None, None))
        hold_action, tap_action, in_chord, is_holdtap = foo
        print("Actions:", hold_action, tap_action, in_chord, is_holdtap)
        current_event.action = hold_action if held else tap_action
        input_state.queue_current_event()  # move to active list
        print("Event queued:", current_event.action)

    send_keys_num = 0
    for event in input_state.active_events:
        if event.action in KeyCode:
            input_state.send_keys[send_keys_num] = event.action
            send_keys_num += 1
    for n in range(send_keys_num, len(input_state.send_keys)):
        input_state.send_keys[n] = 0
    print("Send keys:", input_state.send_keys, 'Num active events:', len(input_state.active_events))
    input_state.keyboard.send_keys(input_state.send_keys)
    

    # pass active keys to hid keyboard





def main():
    '''Main program loop...'''
    # global INPUT_STATE
    global INPUTS

    print("Get shapes of all inputs to build state shaps...")
    state_num_keys = 0

    input_state = InputState()
    new = []
    for im in INPUTS:
        im_obj = im.InputModule(input_state)
        new.append(im_obj)
        print("  * Input module:", im.__name__)
        im_keys_num = im_obj.get_num_keys()
        print('    ', im.__name__, im_keys_num)
        state_num_keys += im_keys_num
    INPUTS = new
    print("  * State total keys:", state_num_keys)

    print("Allocating events...")
    events = [KeyboardEvent(state_num_keys) for _ in range(8)]
    input_state.idle_events += events

    # Enable usb mouse
    print("Initializing USB mouse and keyboard...")
    print("pyboard will crash, re-run it to reconnect serial.")
    sleep(1)
    usb.device.get().init(input_state.keyboard,
                          input_state.mouse,
                          builtin_driver=True)
    while not ( input_state.keyboard.is_open()
                and input_state.mouse.is_open() ):
        pass
    sleep(5)  # Wait for reconnect before continuiing... 
    print("Mouse and keyboard are initialized...")

    print("Initializing input moudles...")
    state_num_keys = 0  # reset to count keys as we init each module
    for im, pio_addr in zip(INPUTS, PIO_MAP):
        print("Initializing", im, pio_addr)
        im_keys_num = im.get_num_keys()
        # state_num_keys is the bit offset that the module can write at.
        im.init(state_num_keys, pio_addr)
        state_num_keys += im_keys_num
        # print(dir(im))

    # keymap.LOOKUP
    # {layer: {bitfield: (action, action_args, delay_ms, ?????)}}
    # by layer table of key press (combinatinos) to actions.
    # delay is for chords - pressed keys could be a chord or part of a larger chord,
    # so we either wait for the delay tieout or for any of the keys to be released 
    # to trigger the action.  

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
