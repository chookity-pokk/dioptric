#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 20:40:44 2020

A sequence to do G/T/Y and R/T/Y, where T isG, R, or Y. This starts the 
NV in either NV- or NV0, then applies a pusle for some duration and then 
checks the final charge state.

Updated 11/17/21

@author: agardill
"""

from pulsestreamer import Sequence
from pulsestreamer import OutputState
import utils.tool_belt as tool_belt
import numpy

LOW = 0
HIGH = 1

def get_seq(pulse_streamer, config, args):

    # Unpack the args
    readout_time, prep_time, test_time, \
        readout_laser_key,  prep_laser_key, test_laser_key, \
         readout_laser_power, prep_laser_power, test_laser_power,  \
            apd_index = args

    readout_time = numpy.int64(readout_time)
    prep_time = numpy.int64(prep_time)
    test_time = numpy.int64(test_time)
    
    
    # Get what we need out of the wiring dictionary
    pulser_wiring = config['Wiring']['PulseStreamer']
    pulser_do_daq_clock = pulser_wiring['do_sample_clock']
    pulser_do_apd_gate = pulser_wiring['do_apd_{}_gate'.format(apd_index)]
    
    wait_time = config['CommonDurations']['cw_meas_buffer']
    galvo_move_time = config['Positioning']['xy_small_response_delay']
    readout_delay = config['Optics'][readout_laser_key]['delay']
    prep_delay = config['Optics'][prep_laser_key]['delay']
    test_delay = config['Optics'][test_laser_key]['delay']
    
    if prep_laser_key == test_laser_key:
        total_laser_delay = readout_delay + prep_delay
    else:
        total_laser_delay = readout_delay + prep_delay + test_delay
    # Test period
    period =  galvo_move_time + total_laser_delay + (prep_time + test_time + readout_time + \
                           3 * wait_time)
    
    seq = Sequence()


    #collect photons for certain timewindow tR in APD
    train = [(galvo_move_time + total_laser_delay + prep_time + test_time + 2*wait_time, LOW), 
             (readout_time, HIGH), (100, LOW)]
    seq.setDigital(pulser_do_apd_gate, train)


    train = [(galvo_move_time + total_laser_delay + prep_time + test_time + 2*wait_time +readout_time, LOW), 
             (100, HIGH),(100,LOW)]
    seq.setDigital(pulser_do_daq_clock, train)
    
    # laser pulses
    readout_train = [(galvo_move_time + total_laser_delay - readout_delay + wait_time + prep_time + test_time + wait_time, LOW),
                     (readout_time, HIGH),(100, LOW)]
    
    tool_belt.process_laser_seq(pulse_streamer, seq, config,
                        readout_laser_key, readout_laser_power, readout_train)
    
    if prep_laser_key == test_laser_key:
        prep_test_train = [(galvo_move_time + total_laser_delay - prep_delay , LOW),
         (prep_time, HIGH), (wait_time, LOW), (test_time, HIGH), (wait_time + readout_time, LOW)]
    
        tool_belt.process_laser_seq(pulse_streamer, seq, config,
                            prep_laser_key, prep_laser_power, prep_test_train)
    else:
        prep_train = [(galvo_move_time + total_laser_delay - prep_delay , LOW),
         (prep_time, HIGH), (wait_time + test_time + wait_time + readout_time, LOW)]
        test_train = [(galvo_move_time + total_laser_delay - test_delay  + prep_time + wait_time, LOW),
         (test_time, HIGH), (wait_time + readout_time, LOW)]
        
        tool_belt.process_laser_seq(pulse_streamer, seq, config,
                            prep_laser_key, prep_laser_power, prep_train)
        tool_belt.process_laser_seq(pulse_streamer, seq, config,
                            test_laser_key, test_laser_power, test_train)
    
    
    final_digital = []
    final = OutputState(final_digital, 0.0, 0.0)

    return seq, final, [period]


if __name__ == '__main__':
    config = tool_belt.get_config_dict()
            
    args = [10000, 1000,5000,
            'laserglow_589', 'cobolt_515', 'cobolt_638',
            0.5, None, None,  0]
    args = [1000.0, 1000.0, 0, 'laserglow_589', 'cobolt_515', 'cobolt_638', 0.12, None, 120, 0]
    seq = get_seq(None, config, args)[0]
    seq.plot()