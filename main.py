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
from machine import I2C, Pin
import gyro

while True:
    gyro.print_gyro()
    gyro.print_adxl()
    gyro.print_hmc()
    time.sleep(1)
