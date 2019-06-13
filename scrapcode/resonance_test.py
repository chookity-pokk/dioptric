#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 11:26:41 2019

@author: yanfeili
"""


import numpy
from pulsestreamer import Sequence
from pulsestreamer import OutputState
from pulsestreamer import PulseStreamer as Pulser 

def main(cxn, freq_center, freq_range, num_steps, num_runs, uwave_power, name='untitled'):
    readout = 100 * 10**6  # 0.1 s
    #readout_sec = readout / (10**9)
    uwave_switch_delay = 100 * 10**6  # 0.1 s to open the gate
    num_steps = 50
    sequence_args = [readout, uwave_switch_delay, apd_index, num_steps]
    
    half_freq_range = freq_range / 2
    freq_low = freq_center - half_freq_range
    freq_high = freq_center + half_freq_range
    freqs = numpy.linspace(freq_low, freq_high, num_steps)
#%%
    cxn.microwave_signal_generator.uwave_on()
    cxn.microwave_signal_generator.set_amp(uwave_power)
    for run_ind in range(num_runs):
        state = OutputState([],freqs(run_ind),0.0)
        Pulser.constant(state)
        input('Press enter to continue')
        