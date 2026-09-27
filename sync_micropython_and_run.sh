#!/bin/sh


for F in input*.py keymap_*.py main.py; do
	pyboard.py -f cp $F :
done

echo "Run:"
echo "pyboard.py main.py"

