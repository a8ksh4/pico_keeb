"""
Capacitive touch measurement using RP2040 PIO (MicroPython).

The PIO program charges the cap pin HIGH, switches to input, then counts
for as long as the pin stays HIGH.  The pad has no external bleed resistor,
so the internal ~50k pull-down discharges it.  (Left floating, the pad picks
up 60 Hz hum through a finger and readings land on multiples of 16.6 ms.)

Touching adds capacitance, so it takes longer to fall -> higher count.

A single discharge only takes ~1us, so the state machine runs at the full
system clock (~72 counts at 200 MHz), and the PIO sums 32 discharges into
each push for resolution.
"""

import rp2
from machine import Pin, freq
import time

# ---- Configuration ---------------------------------------------------------

CAP_PIN_NUM = 22          # GPIO the sensor pad is on
SM_FREQ = freq()          # PIO state machine clock: the full system clock
CAP_THRESHOLD = 2400      # set by calibrate(); placeholder default


# ---- PIO program -----------------------------------------------------------

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, fifo_join=rp2.PIO.JOIN_RX)
def cap_measure():
    wrap_target()
    mov(x, invert(null))          # x = 0xFFFFFFFF, counts down across all 32
    set(y, 31)                    # 32 discharges per push

    # --- charge phase: drive pin high ---
    label("measure")
    set(pindirs, 1)               # pin = output
    set(pins, 1)           [31]   # drive high to charge
    nop()                  [31]

    # --- discharge / measure phase ---
    set(pindirs, 0)               # release: pull-down discharges the pad

    label("loop")
    jmp(pin, "still_high")        # pin HIGH -> keep counting
    jmp("done")                   # pin LOW  -> this discharge is done

    label("still_high")
    jmp(x_dec, "loop")            # x-- ; loop while x != 0

    label("done")
    jmp(y_dec, "measure")         # next discharge until 32 are summed
    mov(isr, invert(x))           # report the summed count
    push(noblock)                 # don't stall if FIFO full
    wrap()


# ---- Driver ----------------------------------------------------------------

class CapTouch:
    def __init__(self, pin_num=CAP_PIN_NUM, sm_id=0, freq=SM_FREQ,
                 threshold=CAP_THRESHOLD):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
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
        total = 0
        for _ in range(samples):
            total += self.sm.get()            # blocks for one fresh sample
        return total // samples

    def touched(self, samples=4):
        return self.read_raw(samples) > self.threshold

    def calibrate(self, seconds=5):
        """
        Interactive calibration.
        Phase 1: don't touch (baseline). Phase 2: hold touch.
        Sets self.threshold midway between the two medians and returns
        (open_median, touch_median).  Medians ignore the moments you were
        moving your finger on or off the pad.
        """
        def _sample_window(label):
            print(label)
            time.sleep(1)
            vals = []
            t_end = time.ticks_add(time.ticks_ms(), seconds * 1000)
            while time.ticks_diff(t_end, time.ticks_ms()) > 0:
                vals.append(self.read_raw())
                time.sleep_ms(50)
            vals.sort()
            return vals[0], vals[len(vals) // 2], vals[-1]

        o_min, o_med, o_max = _sample_window(
            "Calibrating: DO NOT touch the sensor...")
        print("  open  min/median/max =", o_min, o_med, o_max)

        t_min, t_med, t_max = _sample_window(
            "Calibrating: HOLD your finger on the sensor...")
        print("  touch min/median/max =", t_min, t_med, t_max)

        if t_med <= o_max:
            print("WARNING: touched median is within the open range; "
                  "check wiring / charge timing.")
        self.threshold = (o_med + t_med) // 2
        print("  touched / open = {:.2f}".format(t_med / o_med))
        print("  -> threshold set to", self.threshold)
        return o_med, t_med


# ---- Demo ------------------------------------------------------------------

def demo():
    cap = CapTouch()
    print("SM freq:", SM_FREQ)
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
