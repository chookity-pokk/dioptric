# -*- coding: utf-8 -*-
"""Template for Pulse Streamer sequences. If you don't follow this template,
the pulse_streamer server won't be able to read your sequence."

Created on Sun Jun 16 11:22:40 2019

@author: mccambria
"""


# %% Imports


from pulsestreamer import Sequence
from pulsestreamer import OutputState
import numpy


# %% Constants


LOW = 0
HIGH = 1


# %% Functions


# %% Sequence definition


def get_seq(pulser_wiring, args):
    """This is called by the pulse_streamer server to get the sequence object
    based on the wiring (from the registry) and the args passed by the client.
    """

    seq = Sequence()
    
    period = numpy.int64(args[0])
    half_period = period // 2
    
    chan = pulser_wiring['do_arb_wave_trigger']
    train = [(half_period, HIGH),
             (half_period, LOW)]
    seq.setDigital(chan, train)
    
    chan = pulser_wiring['do_uwave_gate_0']
    train = [(period, HIGH)]
    seq.setDigital(chan, train)

    return seq, []


def get_final(pulser_wiring):
    """This is called along with get_seq to get the final output state that
    the Pulse Streamer will enter when sequence has finished running.
    """

    return OutputState([], 0.0, 0.0)


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # The whole point of defining sequences in their own files is so that we
    # can run the file to plot the sequence for debugging and analysis. We'll
    # go through that here.

    # Set up a dummy pulser wiring dictionary
    pulser_wiring = {'do_arb_wave_trigger': 6}

    # Set up a dummy args list
    args = [10**9]

    # get_seq returns the sequence and an arbitrary list to pass back to the
    # client. We just want the sequence.
    seq = get_seq(pulser_wiring, args)[0]

    # Plot the sequence
    seq.plot()
