#!/bin/sh

for F in gyro.py stick.py stick_pio.py matrix.py encoder_pio.py encoder.py; do  # main.py; do
	pyboard.py -f cp $F :
done
#pyboard.py main.py

