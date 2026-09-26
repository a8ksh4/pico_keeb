'''main function!'''

# disable pylint import error:
# pylint: disable=import-error

import machine

machine.freq(200_000_000)  # Set the CPU frequency to 200 MHz

import array

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


PERIOD_US = 1000  # 1 kHz
# PERIOD_US = 500   # 0.5 kHz
# PERIOD_US = 1_000_000  # 1 Hz
DEBUG_INTERVAL = 30_000_000  # 30 seconds
DEBUG_PRINT = False

MOUSE_SCALE = 0.5  # Must be less than 0.5...


class KeyboardEvent:
    '''We pre-allocate a few of these at start and use them to associate
    key presses with actions.  We  call cleanup when the event is done.'''
    def __init__(self):
        self.set_layer = None
        self.buttons = 0
        self.modifier = 0
        self.is_held = False
        self.start_time = None
        self.oneshot = False
        self.action = None

    def cleanup(self):
        '''Resets the event for reuse.'''
        self.set_layer = None
        self.buttons = 0
        self.modifier = 0
        self.buttons = 0
        self.start_time = None
        self.is_held = False
        self.oneshot = False
        self.action = None

    def compare_buttons(self, new_buttons):
        '''Returns (Bool, Bool), where first bool is True if any new buttons
        are pressed, and second bool is True if any buttons were released.'''
        any_pressed = (self.buttons & new_buttons) != new_buttons
        any_released = (self.buttons & new_buttons) != self.buttons
        return any_pressed, any_released


class InputState:
    '''An instance of this is passed to the input modules to track state.'''
    def __init__(self, ):
        self.buttons = 0            # accumulated key presses as a bitfield
        self.wheel = 0              # accumulated detents this tick
        self.mouse_x = 0            # fixed-point, e.g. 1/256 px units
        self.mouse_y = 0
        self.mouse_enable = 0
        self.mouse = MouseInterface()
        self.keyboard = KeyboardInterface()
        self.active_events = []  # list of active KeyboardEvent objects
        self.idle_events = []    # list of idle KeyboardEvent objects for reuse
        self.current_event = None  # the current event being processed
        # self.send_keys = bytearray(10)  # pre-allocated array for sending keys
        # self.send_keys = array.array('b', 10)
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

    def ensure_current_event(self):
        '''Make sure we have an event object to work on.'''
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
    # print("Mouse enabled:", input_state.mouse_enable)
    if input_state.mouse_enable and \
            (input_state.mouse_x or input_state.mouse_y):
        mdx, mdy = scale_mouse_movement(input_state.mouse_x, input_state.mouse_y)
        mouse.move_by(mdx, mdy)

    input_state.ensure_current_event()
    current_layer = 0
    for event in input_state.active_events:
        if event.set_layer is not None:
            current_layer = event.set_layer

    current_event = input_state.current_event

    # remove buttons that are part of an active event
    buttons = input_state.buttons
    for event in input_state.active_events:
        buttons &= ~event.buttons
    # print(input_state.buttons, '->', buttons)

    # recycle completed events back to the idle pool
    for event in input_state.active_events:
        if not (event.buttons & input_state.buttons):
            print("Recycling event:", event.action)
            mem_info()
            input_state.recycle_event(event)

    ########
    # New event block
    ########
    # variables:
    # is_held, any_pressed, any_released, in_chord, buttons, c_e.buttons
    # Wait for is_held if:
    #   * in_chord
    #   * hold_action is not None
    # Deciding Variables: hold_reqd, any_pressed, new_pressed, new_released, is_held
    # hold_reqd | is_held   | any_pressed | new_pressed | new_released | GO
    # N         | N         | N           | N           | N             | N
    # N         | N         | N         | N             | Y             | N/invalid
    # N         | N         | N         | Y             | N             | N/invalid
    # N         |           | N         | Y             | Y             | N/invalid
    # N         | N
    # if event_started - have start time and buttons
    #   look up actions, is_chord
    #   check is_held
    #   if hold_

    current_time = ticks_us()
    foo = LOOKUP[current_layer].get(current_event.buttons, (None, None, None, None, None, 0, 0))
    tap_action, hold_action, in_chord, \
        oneshot_tap, oneshot_hold, \
        modifier_tap, modifier_hold = foo
    hold_reqd = hold_action is not None or in_chord
    any_pressed = current_event.buttons != 0

    if current_event.start_time is not None:
        held_time = current_time - current_event.start_time
        current_event.is_held = held_time > KEYMAP.HOLD_TIME_MS * 1000

    new_pressed, new_released = current_event.compare_buttons(buttons)

    if not buttons and not current_event.buttons:
        pass

    # Starting event
    elif buttons and not current_event.buttons:
        current_event.buttons = buttons
        print("Event starting:", current_event.buttons, current_event.modifier, 'Layer:', current_layer)
        current_event.start_time = current_time

    elif new_pressed:  # and buttons and current_event.buttons
        # current_event.buttons
        pass

    # Check for event processing needed
    process_current_event = False
    if not hold_reqd:
        if any_pressed:
            process_current_event = True
    else:  # hold_reqq!
        if new_released:
            assert(any_pressed)
            process_current_event = True
        elif current_event.is_held:  # hold time exceeded
            assert(any_pressed)
            process_current_event = True

    if process_current_event:
        # Check what actions the current event maps to:
        print("Actions:", tap_action, hold_action, in_chord)
        if current_event.is_held and hold_reqd:  # Hold
            action = hold_action
            oneshot = oneshot_hold
            modifier = modifier_hold
        else:  # Tap
            action = tap_action
            oneshot = oneshot_tap
            modifier = modifier_tap

        current_event.oneshot = oneshot
        current_event.modifier = modifier

        if isinstance(action, str) and action.startswith('L'):
            current_event.set_layer = int(action[1:])
        else:
            current_event.action = action


        input_state.queue_current_event()  # move to active list
        print("Event queued:", current_event.action)

    send_keys_num = 0
    for event in input_state.active_events:
        # if event.action in KeyCode:
        if isinstance(event.action, int):
            input_state.send_keys[send_keys_num] = event.action
            send_keys_num += 1
        if event.modifier <0:
            # print("sent modifier:", event.modifier)
            input_state.send_keys[send_keys_num] = event.modifier
            send_keys_num += 1
    for n in range(send_keys_num, len(input_state.send_keys)):
        input_state.send_keys[n] = 0

    # Send keys to the hid keyboard interface
    # print("Send keys:", input_state.send_keys, 'Num active events:', len(input_state.active_events))
    # send_keys_view = memoryview(input_state.send_keys)[:send_keys_num]
    send_keys_view = input_state.send_keys[:send_keys_num]
    result = keeb.send_keys(send_keys_view, timeout_ms=100)
    print(list(send_keys_view), result)
    # result = keeb.send_keys(input_state.send_keys[:send_keys_num], timeout_ms=100)
    if not result:
        print("Failed to send keys:", input_state.send_keys[:send_keys_num])
    # print("Send keys result:", result)


def main():
    '''Main program loop...'''
    # global INPUT_STATE
    global INPUTS

    print("Get shapes of all inputs to build state shaps...")
    state_num_keys = 0

    input_state = InputState()
    new = []
    for im in INPUTS:
        im_obj = im.InputModule(input_state, DEBUG_PRINT)
        new.append(im_obj)
        print("  * Input module:", im.__name__)
        im_keys_num = im_obj.get_num_keys()
        print('    ', im.__name__, im_keys_num)
        state_num_keys += im_keys_num
    INPUTS = new
    print("  * State total keys:", state_num_keys)

    print("Allocating events...")
    events = [KeyboardEvent() for _ in range(9)]
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
    next_debug_t = next_t
    while True:
        if ticks_diff(next_debug_t, ticks_us()) <= 0:
            next_debug_t = ticks_add(ticks_us(), DEBUG_INTERVAL)
            print("Debug info:")
            print("  * Active events:", len(input_state.active_events))
            print("  * Idle events:", len(input_state.idle_events))
            print("  * Current event:", input_state.current_event)
            print("  * Buttons:", input_state.buttons)
            print("  * Mouse enable:", input_state.mouse_enable)
            print("  * Mouse x/y:", input_state.mouse_x, input_state.mouse_y)
            print("  * Wheel:", input_state.wheel)
            print()
            mem_info()
        tick(input_state)
        next_t = ticks_add(next_t, PERIOD_US)
        while ticks_diff(next_t, ticks_us()) > 0:
            pass


if __name__ == "__main__":
    
    # Your main code logic here
    main()
