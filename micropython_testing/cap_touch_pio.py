"""
Capacitive touch measurement using RP2040 PIO (MicroPython).

The PIO program charges the cap pin HIGH, switches to input, then counts
(by decrementing X from 0xFFFFFFFF) for as long as the pin stays HIGH.
When the pin falls LOW, it pushes the remaining X to the FIFO.

A longer discharge (pin stays high longer) => smaller X => larger
"count" after we invert it in Python. Larger count == touched.

Wiring assumption (same RC topology as the original time_pulse_us version):
the cap pin is driven high to charge, then released to input and bleeds
toward low through the external resistor / finger capacitance. Touching
adds capacitance, so it takes longer to fall -> higher count.

If your hardware bleeds the *other* direction, flip the jmp(pin) sense
(see NOTE in the asm) and charge low instead.
"""

import rp2
from machine import Pin
import time

# ---- Configuration ---------------------------------------------------------

CAP_PIN_NUM = 22          # GPIO the sensor pad is on
SM_FREQ = 1_000_000       # PIO state machine clock (Hz). 1 MHz = 1 count/us-ish
CAP_THRESHOLD = 10000      # set by calibrate(); placeholder default

COUNT_MAX = 0xFFFFFFFF     # X starts here and decrements


# ---- PIO program -----------------------------------------------------------

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def cap_measure():
    wrap_target()

    # --- charge phase: drive pin high ---
    set(pindirs, 1)               # pin = output
    set(pins, 1)                  # drive high to charge
    nop()                  [31]   # let it charge (tune if needed)
    nop()                  [31]

    # --- discharge / measure phase ---
    set(pindirs, 0)               # release: pin = input, starts falling
    mov(x, invert(null))          # x = 0xFFFFFFFF

    label("loop")
    jmp(pin, "still_high")        # pin HIGH -> keep counting
    jmp("done")                   # pin LOW  -> finished
    # NOTE: to invert sense (cap charges low / bleeds high), swap the two
    # lines above: jmp(pin, "done") then jmp("still_high").

    label("still_high")
    jmp(x_dec, "loop")            # x-- ; loop while x != 0
    # if x underflows we just fall through to done (saturated)

    label("done")
    mov(isr, x)                   # report remaining X
    push(noblock)                 # don't stall if FIFO full
    wrap()


# ---- Driver ----------------------------------------------------------------

class CapTouch:
    def __init__(self, pin_num=CAP_PIN_NUM, sm_id=0, freq=SM_FREQ,
                 threshold=CAP_THRESHOLD):
        self.pin = Pin(pin_num, Pin.OUT, value=0)
        self.threshold = threshold
        self.sm = rp2.StateMachine(
            sm_id, cap_measure,
            freq=freq,
            set_base=self.pin,
            jmp_pin=self.pin,     # <-- critical: jmp(pin) reads THIS pin
        )
        self.sm.active(1)

    def _drain(self):
        """Discard any stale FIFO entries."""
        while self.sm.rx_fifo():
            self.sm.get()

    def read_raw(self, samples=4):
        """
        Return averaged count. Larger == longer discharge == touched.
        Drains stale samples first, then collects fresh ones.
        """
        self._drain()
        counts = []
        for _ in range(samples):
            x = self.sm.get()                 # blocks for one fresh sample
            counts.append(COUNT_MAX - x)      # invert: bigger = longer
        return sum(counts) // len(counts)

    def touched(self, samples=4):
        return self.read_raw(samples) > self.threshold

    def calibrate(self, seconds=5, margin=0.4):
        """
        Interactive calibration.
        Phase 1: don't touch (baseline). Phase 2: hold touch.
        Sets self.threshold between the two and returns (open_avg, touch_avg).
        """
        def _sample_window(label):
            print(label)
            time.sleep(1)
            vals = []
            t_end = time.ticks_add(time.ticks_ms(), seconds * 1000)
            while time.ticks_diff(t_end, time.ticks_ms()) > 0:
                vals.append(self.read_raw())
                time.sleep_ms(50)
            return min(vals), sum(vals) // len(vals), max(vals)

        o_min, o_avg, o_max = _sample_window(
            "Calibrating: DO NOT touch the sensor...")
        print("  open  min/avg/max =", o_min, o_avg, o_max)

        t_min, t_avg, t_max = _sample_window(
            "Calibrating: HOLD your finger on the sensor...")
        print("  touch min/avg/max =", t_min, t_avg, t_max)

        # threshold = baseline + margin of the gap
        gap = t_min - o_max
        if gap <= 0:
            print("WARNING: open and touched ranges overlap; "
                  "check wiring / charge timing.")
        self.threshold = o_max + int(max(gap, 1) * margin)
        print("  -> threshold set to", self.threshold)
        return o_avg, t_avg


# ---- Demo ------------------------------------------------------------------

def demo():
    cap = CapTouch()
    cap.calibrate()
    print("Running. Ctrl-C to stop.")
    try:
        while True:
            raw = cap.read_raw()
            state = "touched" if raw > cap.threshold else "open"
            print("Cap state:", state, raw)
            time.sleep_ms(150)
    except KeyboardInterrupt:
        cap.sm.active(0)
        print("stopped")


if __name__ == "__main__":
    demo()