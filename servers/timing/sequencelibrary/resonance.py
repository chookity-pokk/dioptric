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
    readout, uwave_switch_delay, apd_indices = args
    
    num_steps = 1
    readout = numpy.int64(readout)
    readout = numpy.int64(readout)
    uwave_switch_delay = numpy.int64(uwave_switch_delay)
    clock_pulse = numpy.int64(100)
    period = readout + clock_pulse + uwave_switch_delay

    # Get what we need out of the wiring dictionary
    pulser_do_daq_clock = pulser_wiring['do_daq_clock']
    pulser_do_apd_gate = pulser_wiring['do_apd_gate_{}'.format(apd_indices)]
    pulser_do_uwave = pulser_wiring['do_uwave_gate_0']
    pulser_do_aom = pulser_wiring['do_aom']
    pulser_do_uwave_clock = pulser_wiring['do_uwave-clock']

    seq = Sequence()

    # Collect two samples
#    train = [(readout, LOW), (clock_pulse, HIGH),
#             (uwave_switch_delay, LOW),
#            (readout, LOW), (clock_pulse, HIGH)]
#    seq.setDigital(pulser_do_daq_clock, train)
    
     #Ungate the APD channel for the readouts
#    train = [(readout, HIGH), (clock_pulse, LOW),
#            (uwave_switch_delay, LOW),
#            (readout, HIGH), (clock_pulse, LOW)]
#    seq.setDigital(pulser_do_apd_gate, train)

#    # Uwave should be on for the first measurement and off for the second
#    train = [(readout, LOW), (clock_pulse, LOW),
#             (uwave_switch_delay, HIGH),
#             (readout, HIGH), (clock_pulse, LOW)]
#    seq.setDigital(pulser_do_uwave, train)
    
    # The AOM should always be on

    train = [(period*num_steps*2, HIGH)]
    seq.setDigital(pulser_do_aom, train)

    #Analog genetrator sequence; smoothly change the voltages => frequencies
    #over time 
    train = []
    
#    for i in range(num_steps):
#        train.append((readout*2 + clock_pulse + uwave_switch_delay,(-1)+i*(2/(num_steps))))
#        train.append((clock_pulse,(-1)+i*(2/(num_steps))))            
#        train.append((uwave_switch_delay, (-1)+(i+1)*(2/(num_steps))))
#    seq.setAnalog(0,train)

    #uwave sequence 
    train = []

    for i in range(num_steps*2):
        if i%2 == 0:
            train.append((readout, LOW)) 
            train.append((clock_pulse, LOW))
            train.append((uwave_switch_delay, HIGH))
        elif i%2 != 0:
            train.append((readout, HIGH)) 
            train.append((clock_pulse, LOW))
            train.append((uwave_switch_delay, LOW))
    seq.setDigital(pulser_do_uwave,train)
    
    #apd gate sequence
    train = []

    for i in range(num_steps*2):
        if i%2 == 0:
            train.append((readout, HIGH)) 
            train.append((clock_pulse, LOW))
            train.append((uwave_switch_delay, LOW))
        elif i%2 != 0:
            train.append((readout, HIGH)) 
            train.append((clock_pulse, LOW))
            train.append((uwave_switch_delay, LOW)) 
    seq.setDigital(pulser_do_apd_gate, train)
    
    #pulser samplying clock sequence
    train = []

    for i in range(num_steps*2):
        if i%2 == 0:
            train.append((readout, LOW)) 
            train.append((clock_pulse, HIGH))
            train.append((uwave_switch_delay, LOW))
        elif i%2 != 0:
            train.append((readout, LOW)) 
            train.append((clock_pulse, HIGH))
            train.append((uwave_switch_delay, LOW)) 
    seq.setDigital(pulser_do_daq_clock, train)
   
    #set the uwave clock sequence
    train = []
    train.append((readout, LOW)) 
    train.append((uwave_switch_delay, LOW))
    train.append((readout, LOW)) 
    train.append((clock_pulse, HIGH))
    train.append((uwave_switch_delay, LOW)) 
    seq.setDigital(pulser_do_uwave_clock, train)

    return seq, [period]


if __name__ == '__main__':
    wiring = {'do_daq_clock': 0,
              'do_apd_gate_0': 1,
              'do_aom': 2,
              'do_uwave_gate_0': 3,
              'do_uwave-clock':4}

    args = [10 * 10**6, 1* 10**6, 0 ]

    seq,ret_val = get_seq(wiring, args)
    seq.plot()
