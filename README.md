# pico_keeb
A pi pico keyboard firmware.

What Works:
* All standard keys
* Customizable pin mapping.
* Customizable key layouts using key names in adafruit Keycode package. https://github.com/adafruit/Adafruit_CircuitPython_HID/blob/main/adafruit_hid/keycode.py
* Layers
* Dual function hold/tap keys
* Direct key to pin wiring (no matrix scanning yet)
* Mouse emulation

What Needs to be done:
* Remove requirement for 'tap' key to be defined for layer keys.  Right now all layer keys are dual function.
* Add keymap validation at startup.  Make sure all given keycodes are valid and all given layers exist in keymap.
* Add pin scanning for matrix wiring.
* Add OLED output for general status messages, etc.
* Also intending to add T9 style predictive typing support. Curious if a fully functional ~15% keyboard can be practical for linux command line and programming operation.

## How To Use
Check out the repo to your pi pico.
Copy the layout_simple.py and modify it to suit your needs.  The example is a 4x4 pad some weird stuff.  
Change the 'import layout_simple as layout' line at the top of code.py to correspond with the name of your layout file.
Open bug reports and feature requests, or pull requests if you add features or fix stuff.

I was looking for a project to work on for experiende with Circuit Pytnon and the Pi Pico.  This one gets bonus points because it's an opportunity to explore machine learning!
