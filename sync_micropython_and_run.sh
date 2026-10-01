#!/bin/sh

# The serial logger service (host/install.sh) holds the port, so pause it
# while pyboard.py needs it.
LOGGER=
if systemctl --user is-active --quiet tallcan-serial 2>/dev/null; then
	LOGGER=1
	systemctl --user stop tallcan-serial
fi

for F in input*.py keymap_*.py main.py; do
	pyboard.py -f cp $F :
done

if [ -n "$LOGGER" ]; then
	echo "Serial logger stopped.  Start it again when done with the REPL:"
	echo "systemctl --user start tallcan-serial"
fi

echo "Run:"
echo "pyboard.py main.py"
