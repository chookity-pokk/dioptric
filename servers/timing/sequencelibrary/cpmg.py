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
from constants import UwaveSource


# %% Functions


# %% Sequence definition


def get_seq(pulser_wiring, args):

    # Unpack durations, which need to be numpy.int64s
    durations = args[0:10]
    durations = [numpy.in64(el) for el in durations]
    polarization_dur, precession_dur, pi_pulse_dur, readout_dur, \
        ref_wait_dur, aom_delay_dur, uwave_delay_dur = durations

    pi_on_two_pulse_dur = pi_pulse_dur //

    # Calculate tau for an ideal pulse of zero duration, then account for its
    # actual nonzero duration
    tau = precession_dur // (2 * cpmg_n)  # T = 2 N tau
    tau_nonzero_pulse_dur = tau - (pi_on_two_pulse_dur)

    # Use tau to redefine precession_dur so we avoid any rounding errors
    precession_dur = 2 * cpmg_n * tau

    # The final args specify the number of pi pulses and the APD to use
    cpmg_n, apd_index = args[10:]

    LOW = DigitalLevel.LOW
    HIGH = DigitalLevel.HIGH

    seq = Sequence()

    # Shine the laser for polarization/readout
    chan = pulser_wiring['do_aom']
    train = [(polarization_dur, HIGH),
             (pi_on_two_pulse_dur + precession_dur + pi_on_two_pulse_dur, LOW),
             (polarization_dur, HIGH),
             (ref_wait_dur, LOW),
             (polarization_dur, HIGH)]
    seq.setDigital(chan, train)

    # Read out our signal and reference
    chan = pulser_wiring['do_apd_gate_{}'.format(apd_index)]
    train = [(polarization_dur, LOW),
             (pi_on_two_pulse_dur + precession_dur + pi_on_two_pulse_dur, LOW),
             (readout_dur, HIGH),
             (polarization_dur - readout_dur, LOW),
             (ref_wait_dur, LOW),
             (readout_dur, HIGH),
             (polarization_dur - readout_dur, LOW)]
    seq.setDigital(chan, train)

    # Apply microwaves
    chan = pulser_wiring['do_uwave_gate_{}'.format(UwaveSource.TEKTRONIX)]
    train = [(polarization_dur, LOW),
             (pi_on_two_pulse_dur, HIGH)]
    cpmg_chunk = [(tau_nonzero_pulse_dur, LOW),
                  (pi_pulse_dur, HIGH),
                  (tau_nonzero_pulse_dur, LOW)]
    train.append(cpmg_n * cpmg_chunk)
    tain.append([(pi_on_two_pulse_dur, HIGH),
                 (polarization_dur, LOW),
                 (ref_wait_dur, LOW),
                 (polarization_dur, LOW)])
    seq.setDigital(chan, train)

    # Trigger the IQ waveform on the arbitrary waveform generator
    # The first HIGH sets the phase for the first pi_on_two_pulse.
    # The second HIGH sets the phase for the pi_pulses.
    # The third HIGH sets the phase for the second pi_on_two_pulse.
    # This means the IQ sequence should look like this:
    # i = [1.0, 0.0, 1.0]
    # q = [0.0, 1.0, 0.0]
    # so that we stay in sync with the pulse sequence.
    chan = pulser_wiring['do_arb_wave_trigger']
    train = [(100, HIGH),
             (- 100 + polarization_dur + pi_on_two_pulse_dur, LOW),
             (100, HIGH),
             (- 100 + precession_dur, LOW)
             (100, HIGH)
             (- 100 + pi_on_two_pulse_dur + polarization_dur + \
              ref_wait_dur + polarization_dur, LOW)]
    seq.setDigital(chan, train)

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
