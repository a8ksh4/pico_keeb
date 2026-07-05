#!/bin/sh


for F in input_*.py; do
	pyboard.py -f cp $F :
done
#pyboard.py main.py

