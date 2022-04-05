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


def get_seq(pulse_streamer, config, args):
    
    # Unpack the args
    readout, state, laser_name, laser_power, apd_index = args
    
    state = States(state)
    pulser_wiring = config['Wiring']['PulseStreamer']
    sig_gen_name = config['Microwaves']['sig_gen_{}'.format(state.name)]
    uwave_delay = config['Microwaves'][sig_gen_name]['delay']
    laser_delay = config['Optics'][laser_name]['delay']
    meas_buffer = config['CommonDurations']['cw_meas_buffer']
    transient = 0

    readout = numpy.int64(readout)
    front_buffer = max(uwave_delay, laser_delay)
    period = front_buffer + 2 * (transient + readout + meas_buffer)

    # Get what we need out of the wiring dictionary
    pulser_do_daq_clock = pulser_wiring['do_sample_clock']
    pulser_do_apd_gate = pulser_wiring['do_apd_{}_gate'.format(apd_index)]
    sig_gen_gate_chan_name = 'do_{}_gate'.format(sig_gen_name)
    pulser_do_sig_gen_gate = pulser_wiring[sig_gen_gate_chan_name]
#    laser_chan = pulser_wiring['do_{}_dm'.format(laser_name)]

    seq = Sequence()

#    train = [(period-200, LOW), (100, HIGH), (100, LOW)]
    train = [(front_buffer, LOW), 
             (transient, LOW), (readout, LOW), (100, HIGH), (meas_buffer, LOW),
             (transient, LOW), (readout, LOW), (100, HIGH), (meas_buffer, LOW)]
    seq.setDigital(pulser_do_daq_clock, train)

    # Ungate the APD channel for the readouts
    train = [(front_buffer, LOW), 
             (transient, LOW), (readout, HIGH), (100, LOW), (meas_buffer, LOW),
             (transient, LOW), (readout, HIGH), (100, LOW), (meas_buffer, LOW)]
    seq.setDigital(pulser_do_apd_gate, train)

    # Uwave should be on for the first measurement and off for the second
    train = [(front_buffer-uwave_delay, LOW), 
             (transient, LOW), (readout, LOW), (100, LOW), (meas_buffer, LOW),
             (transient, LOW), (readout, HIGH), (100, LOW), (meas_buffer+uwave_delay, LOW)]
    seq.setDigital(pulser_do_sig_gen_gate, train)

    train = [(period, HIGH)]
    tool_belt.process_laser_seq(pulse_streamer, seq, config, 
                                laser_name, laser_power, train)

    final = OutputState([], 0.0, 0.0)
    return seq, final, [period]


if __name__ == '__main__':
    config = tool_belt.get_config_dict()
    args = [10000000.0, 3, 'cobolt_515', None, 0]
    seq, final, ret_vals = get_seq(None, config, args)
    seq.plot()
