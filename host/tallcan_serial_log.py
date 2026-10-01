#!/usr/bin/env python3
'''Keeps a serial connection to the tallcan keyboard's Pico open and logs
everything it prints.  Run by the tallcan-serial systemd user service (see
install.sh).

It only ever reads, so it never interrupts main.py on the Pico.  It opens the
port exclusively, so pyboard.py / mpremote fail with "port busy" rather than
both programs silently splitting the output.  Stop the service while using
them:  systemctl --user stop tallcan-serial

Log:      ~/.local/state/tallcan/serial.log (rotated)
Battery:  ~/.local/state/tallcan/battery    (latest BATTERY line, see below)
Port:     the first /dev/serial/by-id/*MicroPython*, else /dev/ttyACM0, or set
          TALLCAN_SERIAL=/dev/...
'''

import glob
import logging
import logging.handlers
import os
import sys
import time

import serial  # pyserial, already needed by pyboard.py

STATE_DIR = os.path.expanduser('~/.local/state/tallcan')
LOG_FILE = os.path.join(STATE_DIR, 'serial.log')
BATTERY_FILE = os.path.join(STATE_DIR, 'battery')
RETRY_SECONDS = 2


def find_port():
    '''Returns the Pico's serial device, or None if it isn't plugged in.'''
    port = os.environ.get('TALLCAN_SERIAL')
    if port:
        return port if os.path.exists(port) else None
    by_id = sorted(glob.glob('/dev/serial/by-id/*MicroPython*'))
    if by_id:
        return by_id[0]
    return '/dev/ttyACM0' if os.path.exists('/dev/ttyACM0') else None


def handle_battery(text):
    '''Placeholder for battery reporting.  main.py on the Pico prints
    "BATTERY <millivolts>" when BATTERY_ADC_PIN is set.  For now this just
    keeps the latest reading in BATTERY_FILE, for a status bar or similar to
    read.  TODO: low battery warning, shutdown, etc.'''
    millivolts = text.split()[1]
    tmp = BATTERY_FILE + '.tmp'
    with open(tmp, 'w') as f:
        f.write(millivolts + '\n')
    os.replace(tmp, BATTERY_FILE)


def log_port(port, log):
    '''Logs lines from the port until it disconnects.'''
    with serial.Serial(port, 115200, timeout=1, exclusive=True) as ser:
        log.info('--- connected to %s', port)
        pending = b''
        while True:
            # readline() can return a partial line on timeout, so keep it
            # until the rest arrives.
            pending += ser.readline()
            if not pending.endswith(b'\n'):
                continue
            text = pending.decode('utf-8', 'replace').rstrip('\r\n')
            pending = b''
            log.info('%s', text)
            if text.startswith('BATTERY '):
                try:
                    handle_battery(text)
                except (IndexError, OSError) as e:
                    log.warning('--- bad battery line %r: %s', text, e)


def main():
    os.makedirs(STATE_DIR, exist_ok=True)
    log = logging.getLogger('tallcan')
    log.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    log.addHandler(handler)
    # Connection messages also go to the journal (journalctl --user -u tallcan-serial)
    status = logging.StreamHandler(sys.stdout)
    status.addFilter(lambda record: record.getMessage().startswith('---'))
    log.addHandler(status)

    waiting = False
    while True:
        port = find_port()
        if port is None:
            if not waiting:
                log.info('--- waiting for the Pico to be plugged in')
                waiting = True
            time.sleep(RETRY_SECONDS)
            continue
        waiting = False
        try:
            log_port(port, log)
        except (serial.SerialException, OSError) as e:
            log.info('--- disconnected from %s: %s', port, e)
            time.sleep(RETRY_SECONDS)


if __name__ == '__main__':
    main()
