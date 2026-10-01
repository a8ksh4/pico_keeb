'''main function!'''

# disable pylint import error:
# pylint: disable=import-error

import machine
machine.freq(200_000_000)  # Set the CPU frequency to 200 MHz

import gc
import array
import input_encoder_pio
import input_stick_pio
import input_matrix_pio
import input_adxl
from input import MouseScaler

import keymap_tallcan as KEYMAP
LOOKUP = KEYMAP.LOOKUP
# Kinds of special actions in the lookup table (see keymap_utils.py).
from keymap_utils import MO, DF, MS_BTN, MS_MOVE

# import pyb
# pyb.usb_mode("VCP+HID", hid=pyb.hid_keyboard)
import usb.device
from usb.device.mouse import MouseInterface
from usb.device.keyboard import KeyboardInterface, KeyCode, LEDCode

from time import sleep, ticks_us, ticks_add, ticks_diff

from micropython import const, mem_info, heap_lock, heap_unlock

INPUTS = [input_encoder_pio, input_stick_pio,
          input_matrix_pio, input_adxl]
# If pio machines are too many instructions, different
# clocks, ..., they need to be on separate pio blocks.
PIO_MAP = [0, 4, 2, None]

PERIOD_MS = 10  # 100Hz
# PERIOD_MS = 1  # 1kHz
PERIOD_US = PERIOD_MS * 1000
# PERIOD_US = 500   # 0.5 kHz
# PERIOD_US = 1000  # 1 kHz

# PERIOD_US = 1_000_000  # 1 Hz
DEBUG_INTERVAL = 30_000_000  # 30 seconds
DEBUG_PRINT = True
# Lock the heap around each tick, so anything that allocates raises a
# MemoryError at the offending line.  For development only: it crashes the
# keyboard on the first allocation, and must be off when DEBUG_PRINT is on.
HEAP_LOCK_TICK = False

# Battery voltage, printed as "BATTERY <millivolts>" for the host's serial
# logger (host/tallcan_serial_log.py).  Placeholder until it's wired up: set
# BATTERY_ADC_PIN to an ADC pin (GPIO 28 is free) and BATTERY_DIVIDER to the
# voltage divider ratio (battery volts / pin volts).
BATTERY_ADC_PIN = None
BATTERY_DIVIDER = 2
BATTERY_INTERVAL = 60_000_000  # 60 seconds

NUM_EVENTS = 9  # max simultaneous events (keys / chords held)

# Returned by lookups for key combinations not in the keymap.  A module level
# constant, so a new tuple isn't built for every lookup.
_NO_ACTION = (None, None, None, None, None, 0, 0)

# Mouse keys (MS_UP, ...) move the pointer this many pixels per tick.
MOUSE_KEY_SPEED = 4  # 400 px/s at 100 Hz



class KeyboardEvent:
    '''We pre-allocate a few of these at start and use them to associate
    key presses with actions.  We  call cleanup when the event is done.'''
    def __init__(self):
        self.active = False  # True once queued, until recycled
        self.seq = 0         # queue order, the newest active layer wins
        self.set_layer = None
        self.buttons = 0
        self.modifier = 0
        self.is_held = False
        self.start_time = None
        self.oneshot = False
        self.action = None

    def cleanup(self):
        '''Resets the event for reuse.'''
        self.active = False
        self.seq = 0
        self.set_layer = None
        self.buttons = 0
        self.modifier = 0
        self.start_time = None
        self.is_held = False
        self.oneshot = False
        self.action = None


class InputState:
    '''An instance of this is passed to the input modules to track state.'''
    def __init__(self, ):
        self.buttons = 0            # accumulated key presses as a bitfield
        self.wheel = 0              # accumulated detents this tick
        self.mouse_x = 0            # fixed-point, e.g. 1/256 px units
        self.mouse_y = 0
        self.mouse_enable = 0
        self.mouse_scaler = MouseScaler()  # smoothing and speed
        self.mouse_key_buttons = 0  # mouse buttons held by mouse keys
        self.default_layer = 0      # set by DF(n)
        self.mouse = MouseInterface()
        self.keyboard = KeyboardInterface()
        # A fixed pool of events.  Events are marked active rather than moved
        # between lists, since list append/pop/remove can reallocate.
        self.events = tuple(KeyboardEvent() for _ in range(NUM_EVENTS))
        self.event_seq = 0
        self.current_event = None  # the current event being processed
        # Each event can send a key and a modifier.
        # hid send_keys can pass up to six regular keys,
        # and puts shift ctrl alt gui in the modifyer byte,
        # but we pass them as regular keys.
        self.send_keys = array.array('b', [0] * (2 * NUM_EVENTS))
        # send_keys reads every item it's given, so it gets a view of just the
        # used ones.  Slicing a memoryview allocates, so make them all now.
        send_keys_mv = memoryview(self.send_keys)
        self.send_keys_views = tuple(send_keys_mv[:n]
                                     for n in range(len(self.send_keys) + 1))

    def clear_deltas(self):
        '''After each tick, we clear these values.'''
        self.wheel = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_enable = 0

    def ensure_current_event(self):
        '''Make sure we have an event object to work on.  Returns False if
        all events are in use.'''
        if self.current_event is None:
            for event in self.events:
                if not event.active:
                    self.current_event = event
                    break
        return self.current_event is not None

    def queue_current_event(self):
        '''Marks the current event active and clears it.'''
        event = self.current_event
        event.active = True
        self.event_seq += 1
        event.seq = self.event_seq
        self.current_event = None

    def recycle_event(self, event):
        '''Recycles an event back to the idle pool.'''
        event.cleanup()
        if self.current_event is event:
            self.current_event = None


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
    if input_state.mouse_enable:
        input_state.mouse_scaler.scale(input_state)
        # Small movements can scale to 0 until the remainders add up.
        if input_state.mouse_x or input_state.mouse_y:
            mouse.move_by(input_state.mouse_x, input_state.mouse_y)
    else:
        input_state.mouse_scaler.reset()

    # The newest active event that sets a layer wins.
    current_layer = input_state.default_layer
    layer_seq = 0
    for event in input_state.events:
        if event.active and event.set_layer is not None and event.seq > layer_seq:
            current_layer = event.set_layer
            layer_seq = event.seq

    # remove buttons that are part of an active event
    buttons = input_state.buttons
    for event in input_state.events:
        if event.active:
            buttons &= ~event.buttons
    # print(input_state.buttons, '->', buttons)

    # recycle completed events back to the idle pool
    for event in input_state.events:
        if event.active and not (event.buttons & input_state.buttons):
            if DEBUG_PRINT:
                print("Recycling event:", event.action)
                mem_info()
            input_state.recycle_event(event)

    if not input_state.ensure_current_event():
        # Every event is in use, so new presses wait until one is released.
        send_keys(input_state, keeb)
        send_mouse_keys(input_state, mouse)
        return
    current_event = input_state.current_event

    ########
    # New event block
    ########


    current_time = ticks_us()
    tap_action, hold_action, in_chord, \
        tap_oneshot, hold_oneshot, \
        tap_modifier, hold_modifier = LOOKUP[current_layer].get(current_event.buttons, _NO_ACTION)
    hold_reqd = hold_action is not None or in_chord
    any_pressed = current_event.buttons != 0

    if current_event.start_time is not None:
        held_time = ticks_diff(current_time, current_event.start_time)
        current_event.is_held = held_time > KEYMAP.HOLD_TIME_US

    # any new buttons pressed / any of the event's buttons released
    new_pressed = (current_event.buttons & buttons) != buttons
    new_released = (current_event.buttons & buttons) != current_event.buttons
    joined_chord = False
    new_unjoinable = False

    if not buttons and not current_event.buttons:
        pass

    # Starting event
    elif buttons and not current_event.buttons:
        if buttons not in LOOKUP[current_layer]:
            # Keys pressed together that aren't a chord (or part of one),
            # like two mouse keys, get an event each, one per tick, lowest
            # bit first.
            buttons &= -buttons
        current_event.buttons = buttons
        if DEBUG_PRINT:
            print("Event starting:", current_event.buttons, current_event.modifier, 'Layer:', current_layer)
        current_event.start_time = current_time

    elif new_pressed:  # and buttons and current_event.buttons
        combo = current_event.buttons | buttons
        if in_chord and combo in LOOKUP[current_layer]:
            # The new keys make (part of) a chord with this event, so they
            # join it.  The lookup above is now stale, so we wait for the next
            # tick to process it.
            current_event.buttons = combo
            joined_chord = True
        else:
            # The new keys can't join this event, so it's done waiting and
            # the new keys will start their own event.
            new_unjoinable = True

    # Check for event processing needed
    process_current_event = False
    if joined_chord:
        pass
    elif not hold_reqd:
        if any_pressed:
            process_current_event = True
    else:  # hold_reqq!
        if new_released or new_unjoinable:
            assert(any_pressed)
            process_current_event = True
        elif current_event.is_held:  # hold time exceeded
            assert(any_pressed)
            process_current_event = True

    if process_current_event:
        # Check what actions the current event maps to:
        if DEBUG_PRINT:
            print("Tap Action/Mod:", tap_action, tap_modifier)
            print("Hold Action/Mod, in_chord:", hold_action, hold_modifier, in_chord)
        # Hold if held past the hold time, or if another key was pressed
        # meanwhile (like QMK's HOLD_ON_OTHER_KEY_PRESS), so LT(1, ...) then
        # a layer 1 key works.  Without a hold action, like a chord key, it's
        # a tap.
        if (current_event.is_held or new_unjoinable) and hold_action is not None:
            action = hold_action
            oneshot = hold_oneshot
            modifier = hold_modifier
        else:  # Tap
            action = tap_action
            oneshot = tap_oneshot
            modifier = tap_modifier

        current_event.oneshot = oneshot
        current_event.modifier = modifier

        kind = action & 0xFF00 if action is not None else 0
        if kind == MO:
            current_event.set_layer = action & 0xFF
        elif kind == DF:
            input_state.default_layer = action & 0xFF
        else:
            current_event.action = action  # key, modifier or mouse key

        input_state.queue_current_event()  # move to active list
        if DEBUG_PRINT:
            print("Event queued:", current_event.action)

    send_keys(input_state, keeb)
    send_mouse_keys(input_state, mouse)


def send_keys(input_state, keeb):
    '''Sends the keys and modifiers of all active events.'''
    send_keys_num = 0
    for event in input_state.events:
        if not event.active:
            continue
        # Keycodes are 0..0xFF and modifiers are negative, other actions are
        # handled elsewhere.
        action = event.action
        if action is not None and action < 0x100:
            input_state.send_keys[send_keys_num] = action
            send_keys_num += 1
        if event.modifier < 0:
            # print("sent modifier:", event.modifier)
            input_state.send_keys[send_keys_num] = event.modifier
            send_keys_num += 1

    # Send keys to the hid keyboard interface
    send_keys_view = input_state.send_keys_views[send_keys_num]
    result = keeb.send_keys(send_keys_view, timeout_ms=100)
    if not result and DEBUG_PRINT:
        print("Failed to send keys:", input_state.send_keys[:send_keys_num])


def send_mouse_keys(input_state, mouse):
    '''Sends mouse buttons and movement from active mouse key events.  This
    is separate from the analog mouse (stick, gyro) handled at the start of
    the tick, which goes through smoothing and scaling.'''
    buttons = 0
    dx = 0
    dy = 0
    for event in input_state.events:
        if not event.active or event.action is None:
            continue
        kind = event.action & 0xFF00
        arg = event.action & 0xFF
        if kind == MS_BTN:
            buttons |= 1 << arg
        elif kind == MS_MOVE:
            if arg == 0:
                dy -= MOUSE_KEY_SPEED
            elif arg == 1:
                dy += MOUSE_KEY_SPEED
            elif arg == 2:
                dx -= MOUSE_KEY_SPEED
            else:
                dx += MOUSE_KEY_SPEED

    # Each click_* sends a report, so only call them when a button changes.
    changed = buttons ^ input_state.mouse_key_buttons
    if changed:
        input_state.mouse_key_buttons = buttons
        if changed & 1:
            mouse.click_left(bool(buttons & 1))
        if changed & 2:
            mouse.click_right(bool(buttons & 2))
        if changed & 4:
            mouse.click_middle(bool(buttons & 4))
    if dx or dy:
        mouse.move_by(dx, dy)


def report_battery(adc):
    '''Prints the battery voltage for the host's serial logger.'''
    millivolts = adc.read_u16() * 3300 * BATTERY_DIVIDER // 65535
    print("BATTERY", millivolts)


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

    battery_adc = None
    if BATTERY_ADC_PIN is not None:
        battery_adc = machine.ADC(machine.Pin(BATTERY_ADC_PIN))

    print("Looping forever...")
    gc.collect()
    next_t = ticks_us()
    next_debug_t = next_t
    next_battery_t = next_t
    # Time left over after each tick, in us.  Integer math, since floats
    # allocate.  A negative min means a tick overran its period.
    slack_avg = 0
    slack_min = PERIOD_US
    while True:
        if ticks_diff(next_debug_t, ticks_us()) <= 0:
            next_debug_t = ticks_add(ticks_us(), DEBUG_INTERVAL)
            print("Tick slack avg/min (us):", slack_avg, slack_min)
            slack_min = PERIOD_US
            print("Debug info:")
            print("  * Active events:", sum(1 for e in input_state.events if e.active))
            print("  * Current event:", input_state.current_event)
            print("  * Buttons:", input_state.buttons)
            print("  * Mouse enable:", input_state.mouse_enable)
            print("  * Mouse x/y:", input_state.mouse_x, input_state.mouse_y)
            print("  * Wheel:", input_state.wheel)
            print()
            mem_info()
        if battery_adc and ticks_diff(next_battery_t, ticks_us()) <= 0:
            next_battery_t = ticks_add(ticks_us(), BATTERY_INTERVAL)
            report_battery(battery_adc)
        if HEAP_LOCK_TICK:
            heap_lock()
            try:
                tick(input_state)
            finally:
                heap_unlock()
        else:
            tick(input_state)
        next_t = ticks_add(next_t, PERIOD_US)
        slack = ticks_diff(next_t, ticks_us())
        slack_avg += (slack - slack_avg) >> 4
        if slack < slack_min:
            slack_min = slack
        while ticks_diff(next_t, ticks_us()) > 0:
            pass


if __name__ == "__main__":
    
    # Your main code logic here
    main()
