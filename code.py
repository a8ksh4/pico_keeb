
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
    #kmap = getKeymap()
    #keys = Keys()
    buttons = [Button.Button(p) for p in PINS]
    queue = [None for b in buttons]
    layer = ['BASE', ]

    while True:
        time.sleep(0.05)
        for n, button in enumerate(buttons):
            state = button.get_state()
            current_layer = layer[-1]

            # Set the button hold/tap functions

            if state == 'new press':
                funcs = KMAP[current_layer][n]
                # What does this button do?
                #if len(funcs) == 1:
                if isinstance(funcs, str):
                    funcs = (funcs, False)
                print(funcs)
                button.tap, button.hold = funcs

            if 'continued' not in state:
                print(state, 'hold:', button.hold, 'tap:', button.tap, button.duration(), button.pin)

            # Handle each state (change)w
            if state == 'new press':
                #print(KMAP.keys())
                if button.hold and button.hold in KMAP.keys():
                    layer.append(button.hold)
                elif button.hold:
                    KEYS.press(button.hold) # e.g. alt, shift, etc.wb;'

                else:
                    KEYS.press(button.tap)
            elif state == 'continued press':
                pass
            elif state == 'new release':
                if button.hold:
                    print(button.hold, KMAP.keys())
                    if button.hold in KMAP.keys():
                        layer.remove(button.hold)
                    else:
                        KEYS.release(button.hold)
                    if button.duration() < HOLD_TIME:
                        KEYS.press(button.tap)
                    else:
                        button.tap = False
                    button.hold = False
                else:
                    KEYS.release(button.tap)
                    button.tap = False
            else: # state == 'condinued_release':
                if button.tap:
                    KEYS.release(button.tap)
                    button.tap = False

readLoop()
