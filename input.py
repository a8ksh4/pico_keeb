'''Input module that can be extended by all other input modules.'''

from array import array


class MouseScaler:
    '''Turns the mouse movement the input modules add up each tick into a
    mouse report delta.  It averages the last 2 ** SMOOTH_BITS ticks to smooth
    out sensor noise, then divides by 2 ** SCALE_SHIFT.  The remainder lost to
    the division is carried to the next tick, so slow movements still add up,
    and it doesn't drift toward negative (>> rounds down).
    Only allocates at init.'''
    SCALE_SHIFT = 4      # speed: 1 = 1/2, 2 = 1/4, 3 = 1/8, 4 = 1/16, ...
    SMOOTH_BITS = 2      # average over 4 ticks (40 ms at 100 Hz)

    def __init__(self):
        n = 1 << self.SMOOTH_BITS
        self._mask = n - 1
        self._shift = self.SCALE_SHIFT + self.SMOOTH_BITS
        self._buf_x = array('i', [0] * n)
        self._buf_y = array('i', [0] * n)
        self._i = 0
        self._sum_x = 0
        self._sum_y = 0
        self._rem_x = 0
        self._rem_y = 0
        self._clear = True

    def reset(self):
        '''Clears the smoothing history, e.g. when the mouse is disabled, so
        old movement doesn't leak into the next time it's enabled.'''
        if self._clear:
            return
        for n in range(self._mask + 1):
            self._buf_x[n] = 0
            self._buf_y[n] = 0
        self._sum_x = 0
        self._sum_y = 0
        self._rem_x = 0
        self._rem_y = 0
        self._clear = True

    def scale(self, state):
        '''Replaces state.mouse_x/y with the smoothed, scaled delta, which
        is within the -127..127 a mouse report allows.  Call it every tick
        while the mouse is enabled, even with no movement, so the average
        settles back to 0.'''
        self._clear = False
        i = self._i
        # Running sums of the last n ticks.  The sum is n * the average, so
        # the average's division folds into the shift.
        x = state.mouse_x
        self._sum_x += x - self._buf_x[i]
        self._buf_x[i] = x
        y = state.mouse_y
        self._sum_y += y - self._buf_y[i]
        self._buf_y[i] = y
        self._i = (i + 1) & self._mask

        shift = self._shift
        x = self._sum_x + self._rem_x
        y = self._sum_y + self._rem_y
        dx = x >> shift
        dy = y >> shift
        self._rem_x = x - (dx << shift)
        self._rem_y = y - (dy << shift)

        if dx < -127:
            dx = -127
        elif dx > 127:
            dx = 127
        if dy < -127:
            dy = -127
        elif dy > 127:
            dy = 127
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
