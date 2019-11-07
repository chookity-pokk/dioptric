#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 15:29:41 2019

@author: yanfeili
"""

from pulsestreamer import Sequence
from pulsestreamer import OutputState
import numpy
import utils.tool_belt as tool_belt
from utils.tool_belt import States

LOW = 0
HIGH = 1

def get_seq(pulser_wiring, args):

    # Unpack the args
    gate_time, polarize_time, ionize_time, buffer_time, aom_delay532, aom_delay589,aom_delay638, readout_time, apd_index, state_value = args
    
    
    polarize_time = numpy.int64(polarize_time)
    ionize_time = numpy.int64(ionize_time)

    readout_time = numpy.int64(readout_time)
    aom_delay532 = numpy.int64(aom_delay532)
    aom_delay589 = numpy.int64(aom_delay589)
    aom_delay638 = numpy.int64(aom_delay638)
    buffer_time = buffer_time + aom_delay638
    buffer_time= numpy.int64(buffer_time)
#    uwave_switch_delay = numpy.int64(uwave_switch_delay)
    clock_pulse = numpy.int64(100)
    clock_buffer = 3 * clock_pulse
    #SCC charge readout period
    period = 2*(polarize_time + ionize_time + buffer_time + readout_time) 
    # Get what we need out of the wiring dictionary
    pulser_do_daq_clock = pulser_wiring['do_sample_clock']
    pulser_do_apd_gate = pulser_wiring['do_apd_{}_gate'.format(apd_index)]
    pulser_do_aom532 = pulser_wiring['do_532_aom']
    pulser_do_aom638 = pulser_wiring['do_638_aom']
    pulser_do_aom589 = pulser_wiring['do_589_aom']
    
#    sig_gen_name = tool_belt.get_signal_generator_name(States(state_value))
#    sig_gen_gate_chan_name = 'do_{}_gate'.format(sig_gen_name)
#    pulser_do_sig_gen_gate = pulser_wiring['sig_gen_gate_chan_name']

    seq = Sequence()
    
#    #collect one sample for each run
#    train = [(polarize_time + ionize_time + buffer_time, LOW),
#             (clock_pulse, HIGH),
#             (clock_pulse, LOW),
#             (period/2 - (polarize_time + ionize_time + buffer_time + clock_pulse*2),LOW),
#             (polarize_time + ionize_time + buffer_time, LOW),
#             (clock_pulse, LOW),
#             (clock_pulse, LOW),
#             (period/2 - (polarize_time + ionize_time + buffer_time + clock_pulse*2),LOW)]
#    seq.setDigital(pulser_do_daq_clock, train)
    
    #collect photons for certain timewindow tR in APD
    train = [(polarize_time + ionize_time + buffer_time + aom_delay589, LOW),
             (gate_time, HIGH),
             (period/2 - (polarize_time + ionize_time + buffer_time + aom_delay589 + gate_time),LOW),
             (polarize_time + ionize_time + buffer_time + aom_delay589, LOW),
             (gate_time, HIGH),
             (period/2 - (polarize_time + ionize_time + buffer_time + gate_time + aom_delay589),LOW)]
    seq.setDigital(pulser_do_apd_gate, train)
    
    #polarize with 532
    train = [(polarize_time, HIGH),(aom_delay532, LOW),
             (period/2 - (polarize_time + aom_delay532), LOW),
             (polarize_time, HIGH),(aom_delay532, LOW),
             (period/2 - (polarize_time + aom_delay532), LOW)]
    seq.setDigital(pulser_do_aom532 , train)
    
    #ionize with 638 
    train = [(polarize_time + aom_delay532, LOW),
             (ionize_time, HIGH),
             (buffer_time + readout_time - aom_delay532, LOW),
             (polarize_time + aom_delay532, LOW),
             (ionize_time, LOW),
             (buffer_time + readout_time - aom_delay532, LOW)]
    seq.setDigital(pulser_do_aom638 , train)
    
    #readout with 589 
    train = [(polarize_time, LOW),
             (ionize_time, LOW),
             (buffer_time, LOW),
             (readout_time,HIGH),
             (polarize_time, LOW),
             (ionize_time, LOW),
             (buffer_time, LOW),
             (readout_time,HIGH)]
    seq.setDigital(pulser_do_aom589 , train)
    

#    final_digital = [pulser_wiring['do_532_aom']]
#    final = OutputState(final_digital, 0.0, 0.0)
    return seq,[period]


if __name__ == '__main__':
    wiring = {'do_daq_clock': 0,
              'do_apd_0_gate': 1,
              'do_532_aom': 2,
              'sig_gen_gate_chan_name': 3,
               'do_sample_clock':4,
               'do_589_aom': 5,
               'do_638_aom': 6}
    args = [2*10**6,2 * 10**6,10 * 10**6,1 * 10**6, 1*10**6,1*10**6,1*10**6, 10 * 10**6, 0, States.LOW]
    seq, ret_vals = get_seq(wiring, args)
    seq.plot()
