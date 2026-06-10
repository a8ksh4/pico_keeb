#!/bin/sh

for F in gyro.py stick.py; do  # main.py; do
	pyboard.py -f cp $F :
done
pyboard.py main.py

