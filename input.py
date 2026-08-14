'''Input module that can be extended by all other input modules.'''

class InputModule:
    '''Base class for input modules.  Each input module should inherit from this
    and implement the get_num_keys, init, and update_state methods.'''
    def __init__(self, input_state):
        self.state = input_state
        self.keys_external_offset = 0
        self.state_machine_num = None

    def get_num_keys(self):
        '''Returns the number of keys this module handles.'''
        raise NotImplementedError

    def init(self, keys_bytes_offset, state_machine_num=None):
        '''Initializes the input module.  This is called once at startup.'''
        self.keys_bytes_offset = keys_bytes_offset
        self.state_machine_num = state_machine_num

    def set_key_state(self, key_offset, value):
        '''This sets value in the state.keys bytearray at the 
        sum position of the modules's external offset plus the 
        internal key key offset. This needs to work for offsets
        that place the bit we're modifying into the middle of
        up to 32 bits of the state.keys bytearray.'''
        total_offset = self.keys_bytes_offset + key_offset
        self.state.keys = (self.state.keys & ~(1 << total_offset)) | (value << total_offset)

    def update_state(self):
        '''Updates the internal state based on the current input values.  
        Valid behaviors here include updating self.state.mouse_x,  mouse_y, 
        mouse_enable, wheel, and calling set_keys_bytes_offset to update
        the state.keys bytefield.  This function is called every tick by
        the main loop. Try not to do anything that will cauce memory allocation
        from here.'''
        raise NotImplementedError