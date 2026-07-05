'''This is a standard pick_keeb input module with init() and 
get_state() functions to handle keyboard matrix scanning
using pio. '''

from machine import Pin
import rp2


IN_PIN_NUMS = [8, 9, 10, 11]
OUT_PIN_NUMS = [16, 17, 18, 19, 20]
# IN_PIN_NUMS = [16, 17, 18, 19, 20]
# OUT_PIN_NUMS = [8, 9, 10, 11]

IN_PINS = [Pin(n, Pin.IN, Pin.PULL_UP) for n in IN_PIN_NUMS]
OUT_PINS = [Pin(n, Pin.OUT) for n in OUT_PIN_NUMS]

# SM_FREQ = 1_000_000
SM_FREQ = 2000


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, fifo_join=rp2.PIO.JOIN_RX)
def  matrix_monitor():
    '''PIO program to matrix scan a keyboard with up to 32 keys (could use two
    instances for each half of a larger keyboard) and push any state changes to
    the ouotput fifo.
    We step through the output pins one at a time and shift
    the state of the input pins to the OSR.
    Then we push the osr to the fifo and start over.'''
    mov(y, invert(null))

    label("loop")
    mov(osr, null)
    mov(isr, null)

    # in_(null, 12)  # Padd the isr for total 32 bits after 4x5 matrix scan
    set(pins, 0x00001)
    in_(pins, 5)
    set(pins, 0x00010)
    in_(pins, 5)
    set(pins, 0x00100)
    in_(pins, 5)
    set(pins, 0x01000)
    in_(pins, 5)
    # set(pins, 0x10000)
    # in_(pins, 4)

    mov(x, isr)
    jmp(x_not_y, "state_changed")
    jmp("loop")

    label("state_changed")
    mov(y, x)
    mov(osr, y)
    push(noblock)

    jmp("loop")


def init(pio_machine_num):
    '''Init is a standard function for input modules that 
    can perform any needede initialization.  Probably this
    is on ly needed to assign unique state machine nums.'''
    global SM
    SM = rp2.StateMachine(pio_machine_num, matrix_monitor,
                          freq=SM_FREQ,
                          in_base=IN_PINS[0],
                          set_base=OUT_PINS[0])
    SM.active(1)


def get_state():
    '''get_state is a standard function in inupt modules.
    It returns a dict with keys a list of boolean states of any buttons/keys
    In this case, we have 20 relevant keys from the 4x5 matrix, so
    we'll return a list of 20 booleans in the dict.
    TODO: If we have bouncing issues, we may need to add some debouncing logic
            here.  Rather than drop older states, we could track history or something.'''
    state = 0
    while SM.rx_fifo():
        state = SM.get() # nuke all but latest update
        print("matrix state: {0:020b}".format(state))
    keys = [bool(state & (1 << n)) for n in range(20)]
    state = {'keys': keys}
    return state


if __name__ == "__main__":
    from time import sleep
    init(0)
    while True:
        changes = get_state()
        print(changes)
        sleep(1)
