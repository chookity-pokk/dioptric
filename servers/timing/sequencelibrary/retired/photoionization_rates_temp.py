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
    readout_time, green_prep_time, red_prep_time, test_time, \
        yellow_laser_key, green_laser_key, red_laser_key, test_laser_key, \
         yellow_laser_power, green_laser_power, red_laser_power,  \
            apd_index = args

    readout_time = numpy.int64(readout_time)
    red_prep_time = numpy.int64(red_prep_time)
    green_prep_time = numpy.int64(green_prep_time)
    test_time = numpy.int64(test_time)
    
    
    # Get what we need out of the wiring dictionary
    pulser_wiring = config['Wiring']['PulseStreamer']
    pulser_do_daq_clock = pulser_wiring['do_sample_clock']
    pulser_do_apd_gate = pulser_wiring['do_apd_{}_gate'.format(apd_index)]
    
    wait_time = config['CommonDurations']['cw_meas_buffer']
    # wait_time = config['Positioning']['xy_small_response_delay']
    green_delay = 0#config['Optics'][yellow_laser_key]['delay']
    yellow_delay = 0#config['Optics'][green_laser_key]['delay']
    red_delay = 0#config['Optics'][red_laser_key]['delay']
    
    total_laser_delay = green_delay + yellow_delay + red_delay
    # Test period
    period =  total_laser_delay + (green_prep_time + test_time + readout_time + \
                           3 * wait_time) +  (red_prep_time + test_time + readout_time + \
                           3 * wait_time)
    
    seq = Sequence()

    # clock
    
    train = [(total_laser_delay + green_prep_time + test_time + 2*wait_time + readout_time + 100, LOW), 
             (100, HIGH),
             (red_prep_time + test_time  + 3*wait_time + readout_time - 100, LOW), 
             (100, HIGH), (wait_time - 100, LOW)]
    seq.setDigital(pulser_do_daq_clock, train)
    
    #collect photons for certain timewindow tR in APD
    train = [(total_laser_delay + green_prep_time + test_time + 2*wait_time, LOW), 
             (readout_time, HIGH),
             (red_prep_time + test_time  + 3*wait_time, LOW), 
             (readout_time, HIGH), (wait_time, LOW)]
    seq.setDigital(pulser_do_apd_gate, train)

    # laser pulses
    green_train = [(red_delay + yellow_delay, LOW),
         (green_prep_time, HIGH), (wait_time, LOW)]
    red_train = [(green_delay + yellow_delay + wait_time + green_prep_time, LOW)]
    yellow_train = [(red_delay + green_delay + wait_time + green_prep_time, LOW)]
    
    test_pulse_off = [(test_time, LOW)] 
    test_pulse_on =  [(test_time, HIGH)] 
    if test_laser_key == green_laser_key: # green
        green_train.extend(test_pulse_on) 
        red_train.extend(test_pulse_off) 
        yellow_train.extend(test_pulse_off)
    elif test_laser_key == red_laser_key: # red 
        green_train.extend(test_pulse_off)
        red_train.extend(test_pulse_on)
        yellow_train.extend(test_pulse_off)
    elif test_laser_key == yellow_laser_key: # yellow
        green_train.extend(test_pulse_off)
        red_train.extend(test_pulse_off) 
        yellow_train.extend(test_pulse_on)
    
    green_train.extend([(wait_time + readout_time + wait_time + red_prep_time + wait_time, LOW)])
    red_train.extend([(wait_time + readout_time + wait_time, LOW), (red_prep_time, HIGH), (wait_time, LOW)])
    yellow_train.extend([(wait_time, LOW), (readout_time, HIGH), (wait_time + red_prep_time + wait_time, LOW)])
    
    if test_laser_key == green_laser_key: # green
        green_train.extend(test_pulse_on) 
        red_train.extend(test_pulse_off) 
        yellow_train.extend(test_pulse_off)
    elif test_laser_key == red_laser_key: # red 
        green_train.extend(test_pulse_off)
        red_train.extend(test_pulse_on)
        yellow_train.extend(test_pulse_off)
    elif test_laser_key == yellow_laser_key: # yellow
        green_train.extend(test_pulse_off)
        red_train.extend(test_pulse_off) 
        yellow_train.extend(test_pulse_on)
        
    green_train.extend([(wait_time + readout_time + wait_time, LOW)])
    red_train.extend([(wait_time + readout_time + wait_time, LOW)])
    yellow_train.extend([(wait_time, LOW), (readout_time, HIGH), (wait_time, LOW)])
    
        
    tool_belt.process_laser_seq(pulse_streamer, seq, config,
                        green_laser_key, green_laser_power, green_train)
    tool_belt.process_laser_seq(pulse_streamer, seq, config,
                        red_laser_key, red_laser_power, red_train)
    tool_belt.process_laser_seq(pulse_streamer, seq, config,
                        yellow_laser_key, yellow_laser_power, yellow_train)
    

    
    # final_digital = [pulser_do_daq_clock]
    final_digital = []
    final = OutputState(final_digital, 0.0, 0.0)

    return seq, final, [period]


if __name__ == '__main__':
    config = tool_belt.get_config_dict()
            
    args = [10000, 1000,1000, 5000,
            'laserglow_589', 'cobolt_515', 'cobolt_638','cobolt_638', 
            0.5, None, None,  0]
    args = [1000.0, 1000.0, 1000.0, 1000, 
            'laserglow_589', 'cobolt_515', 'cobolt_638', 'cobolt_638', 
            0.12, None, None, 0]
    seq = get_seq(None, config, args)[0]
    seq.plot()