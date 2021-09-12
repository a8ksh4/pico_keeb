
#from adafruit_hid.keyboard import Keyboard
#from adafruit_hid.keycode import Keycode
import Keys
import Button
import keymap_simple as keymap
import time
#import keymap_t9 as keymap
KMAP = keymap.KMAP
PINS = keymap.PINS
KEYS = Keys.Keys()

# If a dual function key (layer if hold, key if tap), is held longer than this,
# then it is treated as a hold (layer change), not a key tap.
HOLD_TIME = .2
LOOP_STEP = .05 # 5 ms

def readLoop():
    global PINS
    global KMAP
    global HOLD_TIME
    #kmap = getKeymap()
    #keys = Keys()
    buttons = [Button.Button(p, HOLD_TIME) for p in PINS]
    queue = [None for b in buttons]
    layer = ['BASE', ]
    pending = False

    while True:
        time.sleep(0.05)
        for n, button in enumerate(buttons):
            state = button.get_state()

            # Set the button hold/tap functions
            if state == 'new press':
                if pending:
                    if pending.hold in KMAP.keys():
                        layer.append(pending.hold)
                    else:
                        KEYS.press(pending.hold)
                    pending.tap = False
                    pending = False

                current_layer = layer[-1]
                funcs = KMAP[current_layer][n]
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
                    KEYS.press(button.tap)

            elif state == 'continued press':
                pass

            elif state == 'new hold':
                if pending == button:
                    if button.hold in KMAP.keys():
                        layer.append(button.hold)
                    else:
                        KEYS.press(button.hold) # e.g. alt, shift, etc.
                    button.tap = False
                    pending = False

            elif state == 'continued hold':
                pass

            elif state == 'new release':
                if pending == button:
                    pending = False
                    button.hold = False
                    KEYS.press(button.tap)

                elif button.hold:
                    print(button.hold, KMAP.keys())
                    if button.hold in KMAP.keys():
                        layer.remove(button.hold)
                    else:
                        KEYS.release(button.hold)
                        button.tap = False
                    button.hold = False

                else:
                    KEYS.release(button.tap)
                    button.tap = False

            else: # state == 'condinued_release'
                if button.tap:
                    print('continued release = tap release:', button.tap)
                    KEYS.release(button.tap)
                    button.tap = False


readLoop()
