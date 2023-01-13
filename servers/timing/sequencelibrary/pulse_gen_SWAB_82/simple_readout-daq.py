# -*- coding: utf-8 -*-
"""
Created on Tue Apr  9 21:24:36 2019

@author: mccambria
"""

from pulsestreamer import Sequence
from pulsestreamer import OutputState
import utils.tool_belt as tool_belt
import numpy

LOW = 0
HIGH = 1


def get_seq(pulse_streamer, config, args):

    # Unpack the args
    delay, readout_time, laser_name, laser_power = args

    # Get what we need out of the wiring dictionary
    pulser_wiring = config['Wiring']['PulseGen']
    pulser_do_daq_clock = pulser_wiring['do_sample_clock']
    pulser_do_daq_gate = pulser_wiring['do_apd_gate']

    # Convert the 32 bit ints into 64 bit ints
    delay = numpy.int64(delay)
    readout_time = numpy.int64(readout_time)

    period = numpy.int64(delay + readout_time + 300)

#    tool_belt.check_laser_power(laser_name, laser_power)

    # Define the sequence
    seq = Sequence()

    # The clock signal will be high for 100 ns with buffers of 100 ns on
    # either side. During the buffers, everything should be low. The buffers
    # account for any timing jitters/delays and ensure that everything we
    # expect to be on one side of the clock signal is indeed on that side.
    train = [(period-200, LOW), (100, HIGH), (100, LOW)]
    seq.setDigital(pulser_do_daq_clock, train)

    train = [(delay, LOW), (readout_time, HIGH), (300, LOW)]
    seq.setDigital(pulser_do_daq_gate, train)

    train = [(period, HIGH)]
    tool_belt.process_laser_seq(pulse_streamer, seq, config, 
                                laser_name, laser_power, train)

    final_digital = []
    final = OutputState(final_digital, 0.0, 0.0)

    return seq, final, [period]


if __name__ == '__main__':
    config = tool_belt.get_config_dict()
    # args = [500000, 10000000.0, 0, "laserglow_532", None]
    args = [2000, 100000.0, 0, "cobolt_515", None]
#    seq_args_string = tool_belt.encode_seq_args(args)
    seq, ret_vals, period = get_seq(None, config, args)
    seq.plot()
