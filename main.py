'''Micropython test code for hid keyboard and mouse.
We'll have a few components enabled here:
* buttons reading for keyboard events
* joystick reading for mouse
* capacitive touch sensor
* encoder wheel for mouse wheel
* read gyro/ accelerometer to augment mouse movement ITG3205 ADXL345 HMC5883L combo board

I2C devices for the gyro board are:
* 68 is ITG2305 gyro
* 1e or 53 is ADXL345 accelerometer
* 1e or 53 is HMC5883L
'''

import time
from machine import Pin
import gyro
import stick
import usb.device
from usb.device.keyboard import KeyboardInterface, KeyCode, LEDCode

KEY_TO_PRESS = KeyCode.A
PRESS_TOGGLE = True
kb = KeyboardInterface()
usb.device.get().init(kb, builtin_driver=True)

while True:
    gyro.print_gyro()
    gyro.print_adxl()
    gyro.print_hmc()
    stick.print_position()
    # This works, commenting out because it's disruptive
    # kb.send_keys([KeyCode.A])
    # kb.send_keys([])
    time.sleep(1)
