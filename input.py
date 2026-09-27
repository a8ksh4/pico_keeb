'''Input module that can be extended by all other input modules.'''

def scale_mouse_movement(state):
    '''https://github.com/micropython/micropython-lib/blob/master/micropython/usb/usb-device-mouse/usb/device/mouse.py
    The mouse movement has to be -127 <= delta <= 127, so we scale
    state.mouse_x and mouse_y in place using boolean operations.
    Floats would involve memory allocation, so boolean stuff is better,
    and scaling in place avoids allocating a tuple to return.'''
    # Scale to 1/2:
    dx = state.mouse_x >> 1
    dy = state.mouse_y >> 1
    # Scale to 1/4:
    # dx = dx >> 1
    # dy = dy >> 1
    # Scale to 3/8:
    # dx = dx * 96 >> 8  # 96 / 256 = 0.375
    # dy = dy * 96 >> 8
    if dx < 0:
        dx = max(-127, dx)
    if dx > 0:
        dx = min(dx, 127)
    if dy < 0:
        dy = max(-127, dy)
    if dy > 0:
        dy = min(127, dy)

    state.mouse_x = dx
    state.mouse_y = dy


class InputModule:
    '''Base class for input modules.  Each input module should inherit from this
    and implement the get_num_keys, init, and update_state methods.'''
    def __init__(self, input_state, debug_print=False):
        self.state = input_state
        self.keys_bits_offset = 0
        self.state_machine_num = None
        self.debug_print = debug_print

    def print(self, *args, **kwargs):
        '''Prints debug information if debug_print is True.
        Calling this allocates (the *args tuple, **kwargs dict and any string
        formatting) even when debug_print is False, so guard calls from
        update_state with `if self.debug_print:`.'''
        if self.debug_print:
            print(*args, **kwargs)

    def get_num_keys(self):
        '''Returns the number of keys this module handles.'''
        raise NotImplementedError

    def init(self, keys_bits_offset, state_machine_num=None):
        '''Initializes the input module.  This is called once at startup.'''
        self.keys_bits_offset = keys_bits_offset
        self.state_machine_num = state_machine_num

    def set_key_state(self, key_offset, value):
        '''This sets value in the state.buttons bytearray at the 
        sum position of the modules's external offset plus the 
        internal key key offset. This needs to work for offsets
        that place the bit we're modifying into the middle of
        up to 32 bits of the state.buttons bytearray.'''
        total_offset = self.keys_bits_offset + key_offset
        self.state.buttons = (self.state.buttons & ~(1 << total_offset)) | (value << total_offset)

    def update_state(self):
        '''Updates the internal state based on the current input values.  
        Valid behaviors here include updating self.state.mouse_x,  mouse_y, 
        mouse_enable, wheel, and calling set_keys_bits_offset to update
        the state.buttons bytefield.  This function is called every tick by
        the main loop. Try not to do anything that will cauce memory allocation
        from here.'''
        raise NotImplementedError

class TestInputState:
    '''Stand-in for main.InputState so modules can be tested on their own.
    main.py can't be on the pico during development because the board will
    try to run it at boot, so the fields the input modules use live here.'''
    def __init__(self):
        self.buttons = 0
        self.wheel = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_enable = 0

    def clear_deltas(self):
        self.wheel = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_enable = 0


def run_test(module_class, report, delay=0.5, debug_print=False):
    '''Runs module_class forever, calling report(state, module) each tick.
    Unless debug_print is on (debug printing allocates), the heap is locked
    around each update_state call, so any allocation raises a MemoryError
    pointing at the offending line.'''
    from time import sleep
    import micropython

    state = TestInputState()
    module = module_class(state, debug_print)
    print("Num keys:", module.get_num_keys())
    module.init(0, 0)
    module.update_state()  # the first tick is allowed to allocate
    while True:
        state.clear_deltas()
        if not debug_print:
            micropython.heap_lock()
        try:
            module.update_state()
        finally:
            if not debug_print:
                micropython.heap_unlock()
        report(state, module)
        sleep(delay)
