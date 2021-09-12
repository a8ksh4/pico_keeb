# Write your code here :-)
import board
import time
from digitalio import DigitalInOut, Direction, Pull

class Button():
    '''Keep track of which button is inactive, tapped, or held.'''
    def __init__(self, pin): #, keymap):
        self.pin = pin
        self.io = DigitalInOut(pin)
        self.io.direction = Direction.INPUT
        self.io.pull = Pull.UP
        self.is_pressed = False   # state tracking
        self.was_pressed = False  # state tracking
        self.ptime = 0            # what time it was pressed
        self.hold = False
        self.tap = False

    def poll(self):
        ms = time.monotonic()
        cur_pressed = not self.io.value
        #print(cur_pressed)
        if not cur_pressed and not self.is_pressed: # not pressed and wasn't pressed
            self.was_pressed = False
        elif not cur_pressed and self.is_pressed: # not pressed but was pressed
            self.was_pressed = True
            self.is_pressed = False
            #self.ptime = None
        elif cur_pressed and not self.is_pressed: # newly pressed
            self.is_pressed = True
            self.was_pressed = False
            self.ptime = ms
        else:                    # continues to be pressed
            self.was_pressed = True

    #def is_pressed(self):
    #    return self.is_pressed

    #def was_pressed(self):
    #    return self.was_pressed

    def duration(self):
        return time.monotonic() - self.ptime

    def get_state(self):
        self.poll()
        if self.is_pressed and not self.was_pressed:
            return 'new press'
        elif self.is_pressed and self.was_pressed:
            return 'continued press'
        elif not self.is_pressed and self.was_pressed:
            return 'new release'
        else: #if not self.is_pressed and not self.was_pressed:
            return 'continued release'



