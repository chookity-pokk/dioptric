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
    durations = []
    for ind in range(9):
        durations.append(numpy.int64(args[ind]))

    # Unpack the durations
    tau, polarization_time, reference_time, signal_wait_time, \
        reference_wait_time, background_wait_time, aom_delay_time, \
        gate_time, max_tau = durations

    # Get the APD indices
    apd_index = args[9]

    # Get what we need out of the wiring dictionary
    key = 'do_apd_gate_{}'.format(apd_index)
    pulser_do_apd_gate = pulser_wiring[key]
    pulser_do_uwave = pulser_wiring['do_uwave_gate_1']
    pulser_do_aom = pulser_wiring['do_aom']

    # %% Couple calculated values

    prep_time = polarization_time + signal_wait_time + \
        tau + signal_wait_time
    end_rest_time = max_tau - tau

    # The period is independent of the particular tau, but it must be long
    # enough to accomodate the longest tau
    period = aom_delay_time + polarization_time + reference_wait_time + \
        reference_wait_time + polarization_time + reference_wait_time + \
        reference_time + max_tau

    # %% Define the sequence

    seq = Sequence()
    
    

    # APD gating - first high is for signal, second high is for reference
    pre_duration = aom_delay_time + prep_time
    post_duration = reference_time - gate_time + \
        background_wait_time + end_rest_time
#    mid_duration = period - (pre_duration + (2 * gate_time) + post_duration)
    mid_duration = polarization_time + reference_wait_time - gate_time
    train = [(pre_duration, LOW),
             (gate_time, HIGH),
             (mid_duration, LOW),
             (gate_time, HIGH),
             (post_duration, LOW)]
    seq.setDigital(pulser_do_apd_gate, train)

    # # Ungate (high) the APD channel for the background
    # gateBackgroundTrain = [( AOMDelay + preparationTime + polarizationTime + referenceWaitTime + referenceTime + backgroundWaitTime, low),
    #                       (gateTime, high), (endRestTime - gateTime, low)]
    # pulserSequence.setDigital(pulserDODaqGate0, gateBackgroundTrain)

    # Pulse the laser with the AOM for polarization and readout
    train = [(polarization_time, HIGH),
             (signal_wait_time + tau + signal_wait_time, LOW),
             (polarization_time, HIGH),
             (reference_wait_time, LOW),
             (reference_time, HIGH),
             (background_wait_time + end_rest_time + aom_delay_time, LOW)]
    seq.setDigital(pulser_do_aom, train)

    # Pulse the microwave for tau
    pre_duration = aom_delay_time + polarization_time + signal_wait_time
    post_duration = signal_wait_time + polarization_time + \
        reference_wait_time + reference_time + \
        background_wait_time + end_rest_time
    train = [(pre_duration, LOW), (tau, HIGH), (post_duration, LOW)]
    seq.setDigital(pulser_do_uwave, train)

    return seq, [period]


if __name__ == '__main__':
    wiring = {'do_daq_clock': 0,
              'do_apd_gate_0': 5,
              'do_apd_gate_1': 5,
              'do_aom': 3,
              'do_uwave_gate_0': 4,
              'do_uwave_gate_1': 1}
    args = [120, 3000, 1000, 1000, 2000, 1000, 750, 450, 400, 0, 1]
    seq = get_seq(wiring, args)[0]
    seq.plot()
