#!/bin/sh


for F in input_*.py keymap_*.py; do
	pyboard.py -f cp $F :
done

echo "Run:"
echo "pyboard.py main.py"

