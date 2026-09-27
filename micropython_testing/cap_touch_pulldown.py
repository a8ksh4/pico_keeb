"""
Capacitive touch diagnostic: does enabling the RP2040's internal pull-down on
the pad give stable readings, and at what state machine frequency?

With no bleed path the floating pad picked up ~60 Hz through a finger, and
readings landed on multiples of 16.6 ms.  A ~50k pull-down should discharge
the pad in about a microsecond instead, with touch adding capacitance
(larger count == touched).

For each pull setting and SM frequency, this collects samples without ever
blocking (a pad that never falls low just times out), and prints the counts
and the discharge time they represent.  Run it once not touching, once
touching; the script prompts for both.
"""

import rp2
from machine import Pin, freq
import time

CAP_PIN_NUM = 22
SAMPLES = 32
TIMEOUT_MS = 1500

PULLS = ((None, "none"), (Pin.PULL_DOWN, "down"))
FREQS = (1_000_000, 10_000_000, freq())


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, fifo_join=rp2.PIO.JOIN_RX)
def cap_measure():
    wrap_target()
    set(pindirs, 1)               # output
    set(pins, 1)                  # charge high
    nop()                  [31]
    nop()                  [31]
    set(pindirs, 0)               # release -> input, starts falling
    mov(x, invert(null))          # x = 0xFFFFFFFF
    label("loop")
    jmp(pin, "still_high")        # pin high -> keep counting
    jmp("done")                   # pin low  -> done
    label("still_high")
    jmp(x_dec, "loop")
    label("done")
    mov(isr, invert(x))           # push the count
    push(noblock)
    wrap()


def measure(pull, sm_freq):
    '''Returns a sorted list of counts, possibly empty on timeout.'''
    pin = Pin(CAP_PIN_NUM, Pin.IN, pull)
    sm = rp2.StateMachine(0, cap_measure, freq=sm_freq,
                          set_base=pin, jmp_pin=pin)
    sm.active(1)
    counts = []
    first = True
    t_end = time.ticks_add(time.ticks_ms(), TIMEOUT_MS)
    while len(counts) < SAMPLES and time.ticks_diff(t_end, time.ticks_ms()) > 0:
        if sm.rx_fifo():
            c = sm.get()
            if first:  # may have started mid-measurement
                first = False
                continue
            counts.append(c)
    sm.active(0)
    counts.sort()
    return counts


def sweep(label):
    print()
    print("=== " + label)
    print("pull  freq_hz      n   min      median   max      median_us")
    for pull, pull_name in PULLS:
        for sm_freq in FREQS:
            counts = measure(pull, sm_freq)
            if not counts:
                print("{:5} {:<12} 0   (timed out: pad never fell low)".format(
                    pull_name, sm_freq))
                continue
            med = counts[len(counts) // 2]
            # 2 PIO cycles per count
            us = med * 2 * 1_000_000 / sm_freq
            print("{:5} {:<12} {:<3} {:<8} {:<8} {:<8} {:.2f}".format(
                pull_name, sm_freq, len(counts), counts[0], med, counts[-1], us))


print("Cap touch diagnostic on GPIO", CAP_PIN_NUM, "- system clock", freq())
for label in ("NOT touching", "TOUCHING"):
    print()
    print("Get ready: " + label + " in 3 seconds...")
    time.sleep(3)
    sweep(label)
print()
print("done")
