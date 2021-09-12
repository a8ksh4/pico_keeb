
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

def foo(key):
    exec(f'code = Keycode.{key}', globals())
    #exec(f'code = Keycode.{key}', locals())

    return code

class Keys:
    def __init__(self):
        self.kbd = Keyboard(usb_hid.devices)
        self.codes = {}
        self.pressed = {}
        #ptime = {}
        print(dir(Keycode))
        #print(k for k in Keycode)
        for key in dir(Keycode):
            if key != key.upper() or key.startswith('_'):
                continue
            #exec(f'code = Keycode.{key}')
            code = foo(key)
            self.codes[key] = code
            self.pressed[key] = False
            #ptime[key] = Noness
        print(sorted(self.codes.items()))


    def toggle_shift(self):
        key = 'SHIFT'
        if self.pressed['SHIFT']:
            self.kbd.release(self.codes[key])
            self.pressed[key] = False
        else:
            self.kbd.press(self.codes[key])
            self.pressed[key] = True

    def press(self, key):
        if key.startswith('S_'):
            self.toggle_shift()
            key = '_'.join(key.split('_')[1:])
        if 'SHIFT' in key:
            self.toggle_shift()
        else:
            assert(not self.pressed[key])
            print(key, self.codes[key])
            self.kbd.press(self.codes[key])
            self.pressed[key] = True

    def release(self, key):
        if key.startswith('S_'):
            self.toggle_shift()
            key = '_'.join(key.split('_')[1:])
        if 'SHIFT' in key:
            self.toggle_shift()
        else:
            assert(self.pressed[key])
            self.kbd.release(self.codes[key])
            self.pressed[key] = False

    #def pressed(self, key):swb;waaadd
    #    return self.pressed[key]
