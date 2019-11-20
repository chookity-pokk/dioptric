# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 16:19:44 2019

@author: mccambria
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
    readout, uwave_switch_delay, apd_index, state_value = args
    
    readout = numpy.int64(readout)
    readout = numpy.int64(readout)
    uwave_switch_delay = numpy.int64(uwave_switch_delay)
    clock_pulse = numpy.int64(100)
    clock_buffer = 3 * clock_pulse
    period = readout + clock_pulse + uwave_switch_delay + readout + clock_pulse

    # Get what we need out of the wiring dictionary
    pulser_do_daq_clock = pulser_wiring['do_sample_clock']
    pulser_do_apd_gate = pulser_wiring['do_apd_{}_gate'.format(apd_index)]
    pulser_do_aom = pulser_wiring['do_532_aom']
    
    sig_gen_name = tool_belt.get_signal_generator_name(States(state_value))
    sig_gen_gate_chan_name = 'do_{}_gate'.format(sig_gen_name)
    pulser_do_sig_gen_gate = pulser_wiring[sig_gen_gate_chan_name]

    seq = Sequence()

    # Collect two samples
    train = [(readout + clock_pulse, LOW),
             (clock_pulse, HIGH),
             (clock_pulse, LOW),
             (uwave_switch_delay + readout + clock_pulse, LOW),
             (clock_pulse, HIGH),
             (clock_pulse, LOW)]
    seq.setDigital(pulser_do_daq_clock, train)
    
    # Ungate the APD channel for the readouts
    train = [(readout, HIGH), (clock_buffer, LOW),
             (uwave_switch_delay, LOW),
             (readout, HIGH), (clock_buffer, LOW)]
    seq.setDigital(pulser_do_apd_gate, train)

    # Uwave should be on for the first measurement and off for the second
    train = [(readout, LOW), (clock_buffer, LOW),
             (uwave_switch_delay, HIGH),
             (readout, HIGH), (clock_buffer, LOW)]
    seq.setDigital(pulser_do_sig_gen_gate, train)

    # The AOM should always be on
    train = [(period, HIGH)]
    seq.setDigital(pulser_do_aom, train)

    final_digital = [pulser_wiring['do_532_aom']]
    final = OutputState(final_digital, 0.0, 0.0)
    return seq, final, [period]


if __name__ == '__main__':
    wiring = {'do_sample_clock': 0,
              'do_apd_0_gate': 1,
              'do_532_aom': 2,
              'do_signal_generator_tsg4104a_gate': 3}
    args = [10 * 10**6, 0, 0, States.LOW]
    seq, final, ret_vals = get_seq(wiring, args)
    seq.plot()
