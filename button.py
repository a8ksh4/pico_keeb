# Write your code here :-)
import board
import time
from digitalio import DigitalInOut, Direction, Pull

class Button():
    '''Keep track of which button is inactive, tapped, or held.'''
    def __init__(self, pin, hold_time): #, keymap):
        self.hold_time = hold_time
        self.pin = pin
        self.io = DigitalInOut(pin)
        self.io.direction = Direction.INPUT
        self.io.pull = Pull.UP
        #self.is_pressed = False   # state tracking
        #self.was_pressed = False  # state tracking
        self.state = 'continued release'
        self.ptime = 0            # what time it was pressed
        self.hold = False
        self.tap = False


    def get_state(self):
        ms = time.monotonic()
        cur_pressed = not self.io.value

        if self.state in ('new press', 'continued press'):
            if cur_pressed:
                if ms - self.ptime > self.hold_time:
                    self.state = 'new hold'
                else:
                    self.state = 'continued press'
            else:
                self.state = 'new release'

        elif self.state in ('new hold', 'continued hold'):
            if cur_pressed:
                self.state = 'continued hold'
            else:
                self.state = 'new release'

        elif self.state in ('new release', 'continued release'):
            if cur_pressed:
                self.state = 'new press'
                self.ptime = ms
            else:
                self.state = 'continued release'
            
        return self.state

