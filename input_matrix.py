
def init(pio_machine_num):
    '''Init is a standard function for input modules that 
    can perform any needede initialization.  Probably this
    is on ly needed to assign unique state machine nums.'''
    global SM
    SM = rp2.StateMachine(pio_machine_num, encoder_monitor, 
                          freq=SM_FREQ, 
                          in_base=0)
    SM.active(1)


def get_state():
    '''get_state is a standard function in inupt modules.
    It returns a dict with keys a list of states of any buttons/keys,
    and 'wheel' a list of movement directions.'''
    clicked = not PIN_BUTTON.value()
    state = {'keys': [clicked],
             'wheel': []}
    while SM.rx_fifo():
        state = SM.get() & 0b11  # get the last two bits for A and B
        if PREV is None:
            PREV = state
            continue
        if (PREV, state) in UP_STATES:
            state['wheel'].append('up')
        else:
            state['wheel'].append('down')
    return state