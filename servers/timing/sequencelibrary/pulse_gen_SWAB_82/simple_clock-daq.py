# -*- coding: utf-8 -*-
"""
Created on Thu Sep 2 10:24:36 2021

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
    delay = args

    # Get what we need out of the wiring dictionary
    pulser_wiring = config['Wiring']['PulseGen']
    pulser_do_daq_clock = pulser_wiring['do_sample_clock']

    # Convert the 32 bit ints into 64 bit ints
    delay = numpy.int64(delay)

    period = numpy.int64(delay + 100)

    # Define the sequence
    seq = Sequence()

    # The clock signal will be high for 100 ns with buffers of 100 ns on
    # either side. During the buffers, everything should be low. The buffers
    # account for any timing jitters/delays and ensure that everything we
    # expect to be on one side of the clock signal is indeed on that side.
    train = [(100, HIGH), (delay, LOW)]
    seq.setDigital(pulser_do_daq_clock, train)
    

    final_digital = []
    final = OutputState(final_digital, 0.0, 0.0)

    return seq, final, [period]


if __name__ == '__main__':
    config = tool_belt.get_config_dict()
    args = [5000]
#    seq_args_string = tool_belt.encode_seq_args(args)
    seq, ret_vals, period = get_seq(None, config, args)
    seq.plot()
