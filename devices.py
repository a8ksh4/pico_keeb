# Write your code here :-)
import board
import rotaryio
import time
import analogio
from digitalio import DigitalInOut, Direction, Pull

class Encoder():
    def __init__(self, pins):
        #   print('endoder pins:', pins)
        self.pin_a, self.pin_b = pins
        self.encoder = rotaryio.IncrementalEncoder(self.pin_b, self.pin_a)
        self.last_position = None

    def getState(self):
        position = self.encoder.position
        if self.last_position is None:
            self.last_position = position
        elif self.last_position > position:
            return 'DOWN'
        elif self.last_position < position:
            return 'UP'


class Joystick():
    def __init__(self, pins):
        self.pin_a, self.pin_b = pins
        self.x_axis = analogio.AnalogIn(self.pin_a)
        self.y_axis = analogio.AnalogIn(self.pin_b)

        self.pot_min = 0.00
        self.pot_max = 3.29
        self.step = (self.pot_max - self.pot_min) / 20.0

    def get_voltage(self, pin):
        return (pin.value * 3.3) / 65536

    def steps(self, axis):
        """ Maps the potentiometer voltage range to 0-20 """
        return round((axis - self.pot_min) / self.step)

    def getState(self):
        x = self.get_voltage(self.x_axis)
        y = self.get_voltage(self.y_axis)

        #steps(x) > 11.0:

class Button():
    '''Keep track of which button is inactive, tapped, or held.'''
    def __init__(self, pin, hold_time): #, keymap):
        self.hold_time = hold_time
        self.pin = pin
        self.io = DigitalInOut(pin)
        self.io.direction = Direction.INPUT
        self.io.pull = Pull.UP
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

