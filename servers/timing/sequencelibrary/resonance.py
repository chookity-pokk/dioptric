# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 16:19:44 2019

@author: mccambria
"""

from pulsestreamer import Sequence
import numpy

LOW = 0
HIGH = 1


def get_seq(pulser_wiring, args):

    # Unpack the args
    readout, uwave_switch_delay, num_steps, apd_index = args

    double_num_steps = 2 * num_steps
    readout = numpy.int64(readout)
    readout = numpy.int64(readout)
    uwave_switch_delay = numpy.int64(uwave_switch_delay)
    clock_pulse = numpy.int64(100)
    half_clock_pulse = clock_pulse // 2
    # Each ref/sig chunk is readout + clock_pulse long and there are
    # 2 chunks per step
    period = num_steps * (2 * (readout + clock_pulse))

    # Get what we need out of the wiring dictionary
    pulser_do_daq_clock = pulser_wiring['do_daq_clock']
    pulser_do_apd_gate = pulser_wiring['do_apd_gate_{}'.format(apd_index)]
    pulser_do_uwave = pulser_wiring['do_uwave_gate_0']
    pulser_do_aom = pulser_wiring['do_aom']
    pulser_do_uwave_clock = pulser_wiring['do_uwave_clock']

    seq = Sequence()

    # Microwave gating
    train = []
    for ind in range(double_num_steps):
        if ind % 2 == 0:  # Even
            train.append([readout + clock_pulse - uwave_switch_delay, LOW]) 
        else:  # Odd
            train.append([readout, HIGH]) 
            train.append([clock_pulse + uwave_switch_delay, LOW])
    seq.setDigital(pulser_do_uwave,train)
   
    # Microwave frequency switching clock
    train = []
    for ind in range(num_steps):
        train.append([readout, LOW])
        train.append([clock_pulse, LOW])
        train.append([readout, LOW])
        train.append([half_clock_pulse, LOW])
        train.append([half_clock_pulse, HIGH])
    seq.setDigital(pulser_do_uwave_clock, train)
    
    # APD gating
    train = []
    for ind in range(double_num_steps):
        train.append([readout, HIGH]) 
        train.append([clock_pulse, LOW])
    seq.setDigital(pulser_do_apd_gate, train)
    
    # Sample clock
    train = []
    for ind in range(double_num_steps):
        train.append([readout, LOW]) 
        train.append([half_clock_pulse, LOW])
        train.append([half_clock_pulse, HIGH])
    seq.setDigital(pulser_do_daq_clock, train)
    
    # AOM - open the whole time
    train = []
    train.append([period, HIGH])
    seq.setDigital(pulser_do_aom, train)

    return seq, [period]


if __name__ == '__main__':
    wiring = {'do_daq_clock': 0,
              'do_apd_gate_0': 1,
              'do_aom': 2,
              'do_uwave_gate_0': 3,
              'do_uwave_clock': 4}

    # readout, uwave_switch_delay, num_steps, apd_index
    args = [5000, 500, 2, 0]

    seq, ret_vals = get_seq(wiring, args)
    seq.plot()
