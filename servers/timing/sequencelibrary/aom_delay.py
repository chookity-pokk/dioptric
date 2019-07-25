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
    
    durations = args[0:2]
    durations = [numpy.int64(el) for el in durations]
    delay, readout = durations[0:2]
    
    apd_index = args[2]
    do_apd_gate = pulser_wiring['do_apd_{}_gate'.format(apd_index)]
    do_aom = pulser_wiring['do_532_aom']
    
    period = 6 * readout

    seq = Sequence()

    # The readout windows are what everything else is relative to so keep
    # these fixed
    train = [(readout, LOW), (readout, HIGH), (readout, LOW)]
    train.extend([(readout, LOW), (readout, HIGH), (readout, LOW)])
    seq.setDigital(do_apd_gate, train)

    # Vary the position of the first readout AOM high and leave the AOM high
    # for the duration of the reference experiment so that the actual delay
    # doesn't matter
    readout_on_5 = readout // 5
    readout_rem = readout - readout_on_5
    train = [(readout-delay, LOW)]
    train.extend([(readout_on_5, HIGH)])
    train.extend([(readout_rem, LOW), (readout+delay, LOW)])
    train.extend([(3*readout, HIGH)])
    seq.setDigital(do_aom, train)

    final_digital = [pulser_wiring['do_532_aom'],
                     pulser_wiring['do_sample_clock']]
    final = OutputState(final_digital, 0.0, 0.0)
    return seq, final, [period]


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # The whole point of defining sequences in their own files is so that we
    # can run the file to plot the sequence for debugging and analysis. We'll
    # go through that here.

    # Set up a dummy pulser wiring dictionary
    pulser_wiring = {'do_apd_0_gate': 0, 'do_532_aom': 1, 'do_sample_clock': 2}

    # Set up a dummy args list
    args = [0, 2000, 0]

    # get_seq returns the sequence and an arbitrary list to pass back to the
    # client. We just want the sequence.
    seq = get_seq(pulser_wiring, args)[0]

    # Plot the sequence
    seq.plot()
