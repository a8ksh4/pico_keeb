# pico_keeb
A small keyboard firmware!  It was originally written in CircuitPython and was
a buggy monolitic implementatino.  It's currently being rewritten in micropython
and hopefully made to work reliably with a big feature list... even if still
totally monolithic.  It is really modular in the input modules.

Notes:
* https://github.com/micropython/micropython-lib/tree/master/micropython/usb
* mpremote.py connect /dev/ttyACM0 mip install usb-device-keyboard
* mpremote.py connect /dev/ttyACM0 mip install usb-device-mouse
* mpremote.py connect /dev/ttyACM0 mip install usb-device-hid
* mpremote.py connect /dev/ttyACM0 mip install usb-device-cdc


What Works:
* All standard keys
* Customizable pin mapping.
* Layers
* Dual function hold/tap keys
* Chording
* Mouse emulation
* Analog joystick mouse and accelerometer fine mouse movement.
* Encoder wheels
* WIP allignment with QMK key names.
* Only memory churn when debug mode is off is print statements driving battery reporting to serial.

What Needs to be done and features want-list:
* Input stick pio module needs tuning changed away from rolling avg to static value as mouse jenks out if you hover over it for a few seconds and mis-caliwrate it.
* Nice things for making this easy for other people to use.
* Artsio keymap example.
* Fix mouse wheel behavior for encoder wheel.
* Gamepad emulation and 'game mode' layer enabled with chording disabled for minimum latency.
* Add keymap validation at startup.  Make sure all given keycodes are valid and all given layers exist in keymap.
* Also intending to add T9 style predictive typing support. Curious if a fully functional ~15% keyboard can be practical for linux command line and programming operation.

** Voltage Checking -> pin high/low or i2c reporting
** Hall sensor read -> pin high/low

## How To Use
Check out the repo to your pi pico.
Copy the layout_simple.py and modify it to suit your needs.  The example is a 4x4 pad some weird stuff.  

Change the 'import layout_simple as layout' line at the top of code.py to correspond with the name of your layout file.
Open bug reports and feature requests, or pull requests if you add features or fix stuff.

I was looking for a project to work on for experiende with Circuit Pytnon and the Pi Pico.  This one gets bonus points because it's an opportunity to explore machine learning!


## Test Hardware
<img src="/images/4x4_pico.jpg" alt="Poco Macro Pad" width="200"/>
<img src="/images/4x4_pico_wiring.jpg" alt="Pico Macro Pad Wiring" width="200"/>
