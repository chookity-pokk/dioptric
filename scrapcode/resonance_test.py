#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 11:26:41 2019

@author: yanfeili
"""


import numpy
from pulsestreamer import OutputState
from pulsestreamer import PulseStreamer as Pulser 
import labrad

    
expected_freqs = [2.85, 2.852, 2.854, 2.856, 2.858, 
                  2.86, 2.862, 2.864, 2.866, 2.868, 2.87, 2.872, 2.874, 
                  2.876, 2.878, 2.88, 2.882, 2.884, 2.886, 2.888, 2.89]
    
num_steps = 21
freq_center = 2.87  # GHz
fm_dev = 0.020  # GHz
uwave_power = 5.0  # dBm

freq_low = freq_center - fm_dev
freq_high = freq_center + fm_dev
expected_freqs = numpy.linspace(freq_low, freq_high, num_steps).tolist()

print(expected_freqs)

ao_voltages = numpy.linspace(-1.0, +1.0, num_steps).tolist()

print(ao_voltages)
        
pulser = Pulser('128.104.160.11')

with labrad.connect() as cxn:
    cxn.microwave_signal_generator.set_amp(uwave_power)
    cxn.microwave_signal_generator.set_freq(freq_center)
    cxn.microwave_signal_generator.load_fm(fm_dev)
    cxn.microwave_signal_generator.uwave_on()
    
    for step_ind in range(num_steps):
#        cxn.microwave_signal_generator.set_freq(expected_freqs[step_ind])
        state = OutputState([4], ao_voltages[step_ind], 0.0)
        pulser.constant(state)
        if input('Enter nothing to continue or "q" to quit: ') == 'q':
            break
            
    cxn.microwave_signal_generator.mod_off()
    cxn.microwave_signal_generator.uwave_off()
    state = OutputState([], 0.0, 0.0)
    pulser.constant(state)
