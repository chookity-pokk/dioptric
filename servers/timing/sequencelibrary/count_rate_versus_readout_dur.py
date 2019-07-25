# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 17:39:27 2019

@author: mccambria
"""

from pulsestreamer import Sequence
from pulsestreamer import OutputState
import numpy

LOW = 0
HIGH = 1


def get_seq(pulser_wiring, args):

    # %% Parse wiring and args

    # The first 9 args are ns durations and we need them as int64s
    durations = args[0:4]
    durations = [numpy.int64(el) for el in durations]

    # Unpack the durations
    polarization_dur, reference_wait_dur, gate_dur, aom_delay = durations
    
    # Buffer turning off the AOM so that we're sure the AOM was fully on for
    # the duration of the gate. This also separates the gate falling edge from
    # the clock rising edge - if these are simultaneous the tagger can get
    # confused
    aom_switch_buffer_dur = 100

    # Get the APD indices
    apd_index = args[4]

    # Get what we need out of the wiring dictionary
    key = 'do_apd_{}_gate'.format(apd_index)
    pulser_do_apd_gate = pulser_wiring[key]
    pulser_do_aom = pulser_wiring['do_532_aom']

    # %% Couple calculated values

    # The period is independent of the particular tau, but it must be long
    # enough to accomodate the longest tau
    period = aom_delay + polarization_dur + reference_wait_dur + gate_dur

    # %% Define the sequence

    seq = Sequence()

    # APD gating
    train = [(aom_delay + polarization_dur + reference_wait_dur, LOW),
             (gate_dur, HIGH),
             (aom_switch_buffer_dur, LOW)]
    seq.setDigital(pulser_do_apd_gate, train)

    # AOM
#    train = [(polarization_dur, HIGH),
#             (reference_wait_dur, LOW),
#             (gate_dur + aom_switch_buffer_dur, HIGH),
#             (aom_delay, LOW)]
    train = [(period, HIGH)]  # Always on to completely negate transient brightness
    seq.setDigital(pulser_do_aom, train)

    final_digital = [pulser_wiring['do_532_aom'],
                     pulser_wiring['do_sample_clock']]
    final = OutputState(final_digital, 0.0, 0.0)
    return seq, final, [period]


if __name__ == '__main__':
    wiring = {'do_532_aom': 0, 'do_apd_0_gate': 1}
    args = [3 * 10**3, 2 * 10**3, 320, 0, 0]
    seq = get_seq(wiring, args)[0]
    seq.plot()
