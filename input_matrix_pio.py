'''This is a standard pick_keeb input module with init() and
update_state() functions to handle keyboard matrix scanning
using pio. '''

from input import InputModule
from machine import Pin
import rp2


@rp2.asm_pio(set_init=(rp2.PIO.OUT_LOW,) * 4, fifo_join=rp2.PIO.JOIN_RX)
def  matrix_monitor():
    '''PIO program to matrix scan a 4 row x 5 col keyboard (could use two
    instances for each half of a larger keyboard) and push any state changes to
    the rx fifo.
    We drive the row pins high one at a time and shift the state of the
    (pulled down) column pins into the ISR.  Rows are scanned last to first
    so that row 0 ends up in the lowest bits after the left shifts.
    If the scan differs from the last one, we push it to the fifo.'''
    mov(y, invert(null))  # impossible last state so the first scan is pushed

    label("loop")
    mov(isr, null)

    set(pins, 0b1000)  [3]  # delay lets the column pins settle
    in_(pins, 5)
    set(pins, 0b0100)  [3]
    in_(pins, 5)
    set(pins, 0b0010)  [3]
    in_(pins, 5)
    set(pins, 0b0001)  [3]
    in_(pins, 5)

    mov(x, isr)
    jmp(x_not_y, "state_changed")
    jmp("loop")

    label("state_changed")
    mov(y, x)
    push(noblock)  # push still has the scan in the isr

    jmp("loop")


class InputModule(InputModule):
    '''This is a standard pick_keeb input module with init() and
    update_state() functions to handle keyboard matrix scanning
    using pio. '''
    def __init__(self, input_state, debug_print=False):
        super().__init__(input_state, debug_print)

        # Rows are driven, cols are read (diodes row -> col), same as input_matrix.
        # The pio program needs both pin groups to be consecutive gpios, but
        # the order listed here sets the key bit order: bit = row * 5 + col_index
        self.ROWS = [8, 9, 10, 11]
        self.COLS = [16, 17, 18, 20, 19]

        self.ROW_BASE = min(self.ROWS)
        self.COL_BASE = min(self.COLS)
        self.OUT_PINS = [Pin(n, Pin.OUT) for n in range(self.ROW_BASE, self.ROW_BASE + len(self.ROWS))]
        self.IN_PINS = [Pin(n, Pin.IN, Pin.PULL_DOWN) for n in range(self.COL_BASE, self.COL_BASE + len(self.COLS))]

        self.NUM_KEYS = len(self.ROWS) * len(self.COLS)
        self.KEYS_MASK = (1 << self.NUM_KEYS) - 1

        # The pio scan has bits in gpio order.  REMAP[bit] is the scan bit that
        # holds key bit n, so we can reorder to match self.ROWS/self.COLS.
        remap = []
        for row in self.ROWS:
            for col in self.COLS:
                remap.append((row - self.ROW_BASE) * len(self.COLS) + (col - self.COL_BASE))
        self.REMAP = bytes(remap)

        self.SM_FREQ = 1_000_000
        self.SM = None

        # The PIO only pushes on change, so hold the latest scan between ticks.
        self.LAST_SCAN = 0

    def get_num_keys(self):
        '''Tells the main program how many keys this module handles
        so the main program knows how much memory to allocate for it.'''
        return self.NUM_KEYS

    def init(self, keys_bits_offset, state_machine_num=None):
        '''Init is a standard function for pico_keeb input modules that
        we use to store a referenc to the global InputState oject so
        any inputs can be recorded in it each tick without any allocation.
        We also can perform any needed module initialization here, like
        pio state machines as well as other hardware setup.'''
        super().init(keys_bits_offset, state_machine_num)
        if state_machine_num is None:
            print("Did you update PIO_MAP in main.py with a state machine numbers?")
        self.SM = rp2.StateMachine(state_machine_num, matrix_monitor,
                                   freq=self.SM_FREQ,
                                   in_base=self.IN_PINS[0],
                                   set_base=self.OUT_PINS[0])
        self.SM.active(1)

    def remap_scan(self, scan):
        '''Reorders the gpio ordered pio scan into key bit order.'''
        keys = 0
        for n in range(self.NUM_KEYS):
            keys |= ((scan >> self.REMAP[n]) & 1) << n
        return keys

    def update_state(self):
        '''update_state is a standard function in input modules.
        Drains the pio fifo, keeping only the latest matrix scan, and writes
        its bits into state.buttons at this module's offset.
        TODO: If we have bouncing issues, we may need to add some debouncing logic
                here.  Rather than drop older states, we could track history or something.'''
        while self.SM.rx_fifo():
            scan = self.SM.get() & self.KEYS_MASK  # nuke all but latest update
            self.LAST_SCAN = self.remap_scan(scan)
            if self.debug_print:
                self.print("matrix state: {0:020b}".format(self.LAST_SCAN))

        offset = self.keys_bits_offset
        self.state.buttons = (self.state.buttons & ~(self.KEYS_MASK << offset)) \
            | (self.LAST_SCAN << offset)


if __name__ == "__main__":
    from input import run_test
    run_test(InputModule,
             lambda state, module: print("{0:020b}".format(state.buttons)),
             delay=1)
