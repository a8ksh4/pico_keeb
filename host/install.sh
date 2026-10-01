#!/bin/sh
# Installs the tallcan-serial systemd user service, which logs the keyboard
# Pico's serial output from boot.  Run as your normal user (not with sudo); it
# asks for sudo only for the steps that need it.  Safe to re-run to update.
#
#   Status:   systemctl --user status tallcan-serial
#   Log:      tail -f ~/.local/state/tallcan/serial.log
#   Stop:     systemctl --user stop tallcan-serial   (e.g. to use pyboard.py)
#   Remove:   systemctl --user disable --now tallcan-serial
set -e
cd "$(dirname "$0")"

if [ "$(id -u)" = 0 ]; then
    echo "Run this as your normal user, not root." >&2
    exit 1
fi

# pyserial (pyboard.py needs it too)
if ! python3 -c 'import serial' 2>/dev/null; then
    if command -v apt-get >/dev/null; then
        echo "Installing pyserial..."
        sudo apt-get install -y python3-serial
    else
        echo "Please install pyserial for python3, then re-run this." >&2
        exit 1
    fi
fi

# Access to /dev/ttyACM*
NEED_REBOOT=
if ! id -nG | grep -qw dialout; then
    echo "Adding $USER to the dialout group for serial port access..."
    sudo usermod -aG dialout "$USER"
    NEED_REBOOT=1
fi

install -Dm755 tallcan_serial_log.py "$HOME/.local/bin/tallcan-serial-log"
install -Dm644 tallcan-serial.service "$HOME/.config/systemd/user/tallcan-serial.service"

# Start user services at boot, without having to log in.
if [ "$(loginctl show-user "$USER" -p Linger --value 2>/dev/null)" != yes ]; then
    echo "Enabling lingering so the service starts at boot..."
    sudo loginctl enable-linger "$USER"
fi

systemctl --user daemon-reload
systemctl --user enable tallcan-serial.service
systemctl --user restart tallcan-serial.service

echo
echo "Installed.  Log: ~/.local/state/tallcan/serial.log"
if [ -n "$NEED_REBOOT" ]; then
    echo "Reboot so the dialout group applies to the service."
fi
