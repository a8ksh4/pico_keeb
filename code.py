
#from adafruit_hid.keyboard import Keyboard
#from adafruit_hid.keycode import Keycode
import Keys
import Devices
import keymap_simple as Keymap
import time
#import keymap_t9 as keymap
#KMAP = keymap.KMAP
#KEYS = keys.Keys()
#SCROLL_ENCODER = Keymap.SCROLL_ENCODER
#JOYSTICK_MOUSE = Keymap.JOYSTICK_MOUSE

# If a dual function key (layer if hold, key if tap), is held longer than this,
# then it is treated as a hold (layer change), not a key tap.
HOLD_TIME = .2
LOOP_STEP = .05 # 5 ms

def readLoop():
    global HOLD_TIME
    global LOOP_STEP
    kmap = Keymap.KMAP
    keys = Keys.Keys()
    buttons = [Devices.Button(p, HOLD_TIME) for p in Keymap.PINS]
    scroll_encoder = Devices.Encoder(Keymap.SCROLL_ENCODER)
    joystick_mouse = Devices.Joystick(Keymap.JOYSTICK_MOUSE)
    queue = [None for b in buttons]
    layer = ['BASE', ]
    pending = False

    while True:
        time.sleep(LOOP_STEP)
        for n, button in enumerate(buttons):
            keys.move_mouse()
            enc_state = scroll_encoder.getState()
            joy_stateg = joystick_mouse.getState()
            state = button.get_state()

            # Set the button hold/tap functions
            if state == 'new press':
                if pending:
                    if pending.hold in kmap.keys():
                        layer.append(pending.hold)
                    else:
                        keys.press(pending.hold)
                    pending.tap = False
                    pending = False

                current_layer = layer[-1]
                funcs = kmap[current_layer][n]
                if isinstance(funcs, str):
                    funcs = (funcs, False)
                print(funcs, state)
                button.tap, button.hold = funcs

            if 'continued' not in state:
                # FYI for button state transitions
                print(state, '- h:', button.hold, 't:', button.tap, button.pin)

            # Handle each state (change)
            if state == 'new press':
                if button.hold:
                    pending = button
                else:
                    keys.press(button.tap)

            elif state == 'continued press':
                pass

            elif state == 'new hold':
                if pending == button:
                    if button.hold in kmap.keys():
                        layer.append(button.hold)
                    else:
                        keys.press(button.hold) # e.g. alt, shift, etc.
                    button.tap = False
                    pending = False

            elif state == 'continued hold':
                pass

            elif state == 'new release':
                if pending == button:
                    pending = False
                    button.hold = False
                    keys.press(button.tap)

                elif button.hold:
                    print(button.hold, kmap.keys())
                    if button.hold in kmap.keys():
                        layer.remove(button.hold)
                    else:
                        keys.release(button.hold)
                        button.tap = False
                    button.hold = False

                else:
                    keys.release(button.tap)
                    button.tap = False

            else: # state == 'condinued_release'
                if button.tap:
                    print('continued release = tap release:', button.tap)
                    keys.release(button.tap)
                    button.tap = False


readLoop()
