import time
import board
from digitalio import DigitalInOut, Direction, Pull
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# https://www.instructables.com/Raspberry-Pi-Pico-With-I2C-Oled-Display-and-Circui/
import busio
import displayio
import adafruit_displayio_ssd1306

displayio.release_displays()
i2c = busio.I2C (scl=board.GP1, sda=board.GP0)
display_bus = displayio.I2CDisplay(i2c, device_address=60)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

led = DigitalInOut(board.GP25)
led.direction = Direction.OUTPUT

pins = [
    board.GP2,
    board.GP3,
    board.GP4,
    board.GP5,
    board.GP6,
    board.GP7,
    board.GP8,
    board.GP9,
    board.GP10,
    board.GP11,
    board.GP12,
    board.GP13,
    board.GP14,
    board.GP15,
    board.GP16,
    board.GP17,
]

switches = []
for pin in pins:
    switch = DigitalInOut(pin)
    switch.direction = Direction.INPUT
    switch.pull = Pull.UP
    switches.append(switch)

print('Hello World Foo!')
kbd = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)

keymap = {
    (0): (KEY, [Keycode.ZERO]),
    (1): (KEY, [Keycode.ONE]),
    (2): (KEY, [Keycode.THREE]),
    (3): (KEY, [Keycode.FOUR]),
    (4): (KEY, [Keycode.FIVE]),
}


while True:
    for n, switch in enumerate(switches):
        if not switch.value:
            print('switch:', n)

            try:
                if keymap[button][0] == KEY:
                        kbd.press(*keymap[button][1])
                    else:
                        cc.send(keymap[button][1])
                except ValueError:  # deals w six key limit
                    pass
                switch_state[button] = 1
            for c in range(n):
                led.value = True
                time.sleep(.1)
                led.value = False
                time.sleep(.1)
    #print('end iter')
    time.sleep(1)


print("Done!")
