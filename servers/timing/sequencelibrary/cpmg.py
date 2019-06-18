# -*- coding: utf-8 -*-
"""Template for Pulse Streamer sequences. If you don't follow this template,
the pulse_streamer server won't be able to read your sequence."

Created on Sun Jun 16 11:22:40 2019

@author: mccambria
"""


# %% Imports


from pulsestreamer import Sequence
from pulsestreamer import OutputState
from constants import DigitalLevel


# %% Functions


# %% Sequence definition


def get_seq(pulser_wiring, args):

    # Unpack durations, which need to be numpy.int64s
    durations = args[0:10]
    durations = [numpy.in64(el) for el in durations]
    polarization_dur, precession_dur, pi_pulse_dur, readout_dur, \
        ref_wait_dur, aom_delay_dur, uwave_delay_dur = durations

    pi_on_two_pulse_dur = pi_pulse_dur // 2

    # The final args specify the number of pi pulses and the APD to use
    cpmg_n, apd_index = args[10:]

    seq = Sequence()

    # Shine the laser for polarization/readout
    chan = pulser_wiring['do_aom']
    train = [(polarization_dur, DigitalLevel.HIGH),
             (pi_on_two_pulse_dur + precession_dur + pi_on_two_pulse_dur, DigitalLevel.LOW),
             (polarization_dur, DigitalLevel.HIGH),
             (ref_wait_dur, DigitalLevel.LOW),
             (polarization_dur, DigitalLevel.HIGH)]
    seq.setDigital(chan, train)

    # Read out our signal and reference
    chan = pulser_wiring['do_apd_gate_{}'.format(apd_index)]
    train = [(polarization_dur, DigitalLevel.LOW),
             (pi_on_two_pulse_dur + precession_dur + pi_on_two_pulse_dur, DigitalLevel.LOW),
             (readout_dur, DigitalLevel.HIGH),
             (polarization_dur - readout_dur, DigitalLevel.LOW),
             (ref_wait_dur, DigitalLevel.LOW),
             (readout_dur, DigitalLevel.HIGH),
             (polarization_dur - readout_dur, DigitalLevel.LOW)]
    seq.setDigital(chan, train)

    # Apply microwaves
    chan = pulser_wiring['do_uwave_gate_0']
    train = [(),
             ]

    return seq, []


def get_final(pulser_wiring):

    return OutputState([pulser_wiring['do_daq_clock']], 0.0, 0.0)


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # The whole point of defining sequences in their own files is so that we
    # can run the file to plot the sequence for debugging and analysis. We'll
    # go through that here.

    # Set up a dummy pulser wiring dictionary
    pulser_wiring = {}

    # Set up a dummy args list
    args = []

    # get_seq returns the sequence and an arbitrary list to pass back to the
    # client. We just want the sequence.
    seq = get_seq(pulser_wiring, args)[0]

    # Plot the sequence
    seq.plot()
