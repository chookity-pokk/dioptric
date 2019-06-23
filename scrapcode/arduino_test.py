# -*- coding: utf-8 -*-
"""
Created on Sat Jun 22 23:00:37 2019

@author: Matt
"""

import serial

# Connect to the USB port and wait until the Arduino completes setup
arduino = serial.Serial('COM3', 9600, timeout=5)
print(arduino.read_until(b'#'))

try:
    arduino.write(b'FILTER3#')
except Exception as ex:
    print(ex)
finally:
    arduino.close()
