'''Input module that can be extended by all other input modules.'''

def scale_mouse_movement(dx, dy):
    '''https://github.com/micropython/micropython-lib/blob/master/micropython/usb/usb-device-mouse/usb/device/mouse.py
    The mouse movement has to be -127 <= delta <= 127, so we scale it using boolean operations.
    Floats would involve memory allocation, so boolean stuff is better.'''
    # Scale to 1/2:
    dx = dx >> 1
    dy = dy >> 1
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

    return dx, dy


class InputModule:
    '''Base class for input modules.  Each input module should inherit from this
    and implement the get_num_keys, init, and update_state methods.'''
    def __init__(self, input_state):
        self.state = input_state
        self.keys_bits_offset = 0
        self.state_machine_num = None

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