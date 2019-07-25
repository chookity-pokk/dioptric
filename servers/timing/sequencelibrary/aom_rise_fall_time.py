# -*- coding: utf-8 -*-
"""
Created on Mon Jun 3 11:49:23 2019

@author: gardill
"""

from pulsestreamer import Sequence
from pulsestreamer import OutputState
import numpy

def get_seq(pulser_wiring, args):

    # %% Parse wiring and args

    # Get the aom name
    aom_state = args[0]
    
    durations = []
    for ind in (1,2):
        durations.append(numpy.int64(args[ind]))
 
    # Unpack the durations
    aom_on_time, aom_off_time = durations
    
    # Define the period
    period = aom_on_time + aom_off_time
    
    #%% Based on the aom to use, set up the sequence
    
    seq = Sequence()
    
    if aom_state == 0:
        LOW = 0
        HIGH = 1
        
        pulser_do_aom_driver = pulser_wiring['do_532_aom']
       
        train = [(aom_on_time, HIGH), (aom_off_time, LOW)]
        seq.setDigital(pulser_do_aom_driver, train)

    if aom_state == 1:
        
        LOW = args[3]
        HIGH = args[4]
        
        pulser_ao_aom_driver = pulser_wiring['ao_589_aom']
        
        train = [(aom_on_time, HIGH), (aom_off_time, LOW)]
        seq.setAnalog(pulser_ao_aom_driver, train)
        
    if aom_state == 2:
        
        LOW = args[3]
        HIGH = args[4]
        
        pulser_ao_aom_driver = pulser_wiring['ao_638_aom']
        
        train = [(aom_on_time, HIGH), (aom_off_time, LOW)]
        seq.setAnalog(pulser_ao_aom_driver, train)

    final_digital = [pulser_wiring['do_532_aom'],
                     pulser_wiring['do_sample_clock']]
    final = OutputState(final_digital, 0.0, 0.0)

    return seq, final, [period]

    # %% Define the sequence




if __name__ == '__main__':
    wiring = {'do_daq_clock': 0,
              'do_apd_gate_0': 1,
              'do_apd_gate_1': 2,
              'do_aom': 3,
              'do_uwave_gate_0': 4,
              'do_uwave_gate_1': 5,
              'ao_638_aom': 0,
              'ao_589_aom': 1}
    args = ['638_aom', 100, 100, 0, 1]
    seq = get_seq(wiring, args)[0]
    seq.plot()   
