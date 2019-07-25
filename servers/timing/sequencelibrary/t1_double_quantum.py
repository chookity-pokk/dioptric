# -*- coding: utf-8 -*-
"""
Created on Sat May  4 08:34:08 2019

@author: Aedan
"""

from pulsestreamer import Sequence
from pulsestreamer import OutputState
import numpy

LOW = 0
HIGH = 1


def get_seq(pulser_wiring, args):

    # %% Parse wiring and args

    # The first 11 args are ns durations and we need them as int64s
    durations = []
    for ind in range(13):
        durations.append(numpy.int64(args[ind]))

    # Unpack the durations
    tau_shrt, polarization_time, signal_time, reference_time,  \
            sig_to_ref_wait_time, pre_uwave_exp_wait_time,  \
            post_uwave_exp_wait_time, aom_delay_time, rf_delay_time,  \
            gate_time, pi_pulse_plus, pi_pulse_minus, tau_long = durations

    # Get the APD indices
    apd_index = args[13]

    # Specify the initial and readout states
    init_state = args[14]
    read_state = args[15]

    pulser_do_apd_gate = pulser_wiring['do_apd_{}_gate'.format(apd_index)]

    pulser_do_uwave_plus = pulser_wiring['do_uwave_gate_0']
    pulser_do_uwave_minus = pulser_wiring['do_uwave_gate_1']

    if init_state == 1:
        init_pi_plus = pi_pulse_plus
        init_pi_minus = 0
    elif init_state == -1:
        init_pi_plus = 0
        init_pi_minus = pi_pulse_minus
    else:
        init_pi_plus = 0
        init_pi_minus = 0

    if read_state == 1:
        read_pi_plus = pi_pulse_plus
        read_pi_minus = 0
    elif read_state == -1:
        read_pi_plus = 0
        read_pi_minus = pi_pulse_minus
    else:
        read_pi_plus = 0
        read_pi_minus = 0

    # specify the sig gen to give the initial state
#    if init_state == 1:
#        pulser_do_uwave_init = pulser_wiring['do_uwave_gate_0']
#    elif init_state == -1:
#        pulser_do_uwave_init = pulser_wiring['do_uwave_gate_1']
#
#    # specify the sig gen to give the readout state
#    if read_state == 1:
#        pulser_do_uwave_read = pulser_wiring['do_uwave_gate_0']
#    elif read_state == -1:
#        pulser_do_uwave_read = pulser_wiring['do_uwave_gate_1']
#
#    # as a special case, for measuring (-1, -1), we can try initializing with
#    # the one sig gen and read out with the other
##    if init_state == -1 and read_state == -1:
##        pulser_do_uwave_init = pulser_wiring['do_uwave_gate_0']
##        pulser_do_uwave_read = pulser_wiring['do_uwave_gate_1']
#
#    # I thing including 0 states will still work, but I don't see us using this
#    # script to really measure that.
#    if init_state == 0:
#        pulser_do_uwave_init = pulser_wiring['do_uwave_gate_0']
#    if read_state == 0:
#        pulser_do_uwave_read = pulser_wiring['do_uwave_gate_0']

    pulser_do_aom = pulser_wiring['do_532_aom']

    # %% Write the microwave sequence to be used.

    # In t1, the sequence is just a pi pulse, wait for a relaxation time, then
    # then a second pi pulse

    # I define both the time of this experiment, which is useful for the AOM
    # and gate sequences to dictate the time for them to be LOW
    # And I define the actual uwave experiement to be plugged into the rf
    # sequence. I hope that this formatting works.

    # With future protocols--ramsey, spin echo, etc--it will be easy to use
    # this format of sequence building and just change this secion of the file

    uwave_experiment_shrt = init_pi_plus +init_pi_minus + tau_shrt + read_pi_plus +read_pi_minus

#    uwave_experiment_seq_shrt = [(pi_pulse_init, HIGH), (tau_shrt, LOW),
#                                     (pi_pulse_read, HIGH)]

    uwave_experiment_long = init_pi_plus +init_pi_minus + tau_long + read_pi_plus +read_pi_minus

#    uwave_experiment_seq_long = [(pi_pulse_init, HIGH), (tau_long, LOW),
#                                     (pi_pulse_read, HIGH)]

    # %% Couple calculated values

    prep_time = aom_delay_time + rf_delay_time + \
        polarization_time + pre_uwave_exp_wait_time + \
        uwave_experiment_shrt + post_uwave_exp_wait_time

    up_to_long_gates = prep_time + signal_time + sig_to_ref_wait_time + \
        reference_time + pre_uwave_exp_wait_time + \
        uwave_experiment_long + post_uwave_exp_wait_time

    # %% Calclate total period. This is fixed for each tau index

    # The period is independent of the particular tau, but it must be long
    # enough to accomodate the longest tau
    period = aom_delay_time + rf_delay_time + polarization_time + \
        pre_uwave_exp_wait_time + uwave_experiment_shrt + post_uwave_exp_wait_time + \
        signal_time + sig_to_ref_wait_time + reference_time + pre_uwave_exp_wait_time + \
        uwave_experiment_long + post_uwave_exp_wait_time + \
        signal_time + sig_to_ref_wait_time + reference_time

    # %% Define the sequence

    seq = Sequence()

    # APD gating
    pre_duration = prep_time
    short_sig_to_short_ref = signal_time + sig_to_ref_wait_time - gate_time
    short_ref_to_long_sig = up_to_long_gates - (prep_time + signal_time + sig_to_ref_wait_time + gate_time)
    long_sig_to_long_ref = signal_time + sig_to_ref_wait_time - gate_time
    post_duration = reference_time - gate_time
    train = [(pre_duration, LOW),
             (gate_time, HIGH),
             (short_sig_to_short_ref, LOW),
             (gate_time, HIGH),
             (short_ref_to_long_sig, LOW),
             (gate_time, HIGH),
             (long_sig_to_long_ref, LOW),
             (gate_time, HIGH),
             (post_duration, LOW)]
    seq.setDigital(pulser_do_apd_gate, train)

    # Pulse the laser with the AOM for polarization and readout
    train = [(rf_delay_time + polarization_time, HIGH),
             (pre_uwave_exp_wait_time + uwave_experiment_shrt + post_uwave_exp_wait_time, LOW),
             (signal_time, HIGH),
             (sig_to_ref_wait_time, LOW),
             (reference_time, HIGH),
             (pre_uwave_exp_wait_time + uwave_experiment_long + post_uwave_exp_wait_time, LOW),
             (signal_time, HIGH),
             (sig_to_ref_wait_time, LOW),
             (reference_time + aom_delay_time, HIGH)]
    seq.setDigital(pulser_do_aom, train)

    # Pulse the microwave for tau
    pre_duration = aom_delay_time + polarization_time + pre_uwave_exp_wait_time
    mid_duration = post_uwave_exp_wait_time + signal_time + sig_to_ref_wait_time + \
        reference_time + pre_uwave_exp_wait_time
    post_duration = post_uwave_exp_wait_time + signal_time + \
        sig_to_ref_wait_time + reference_time + rf_delay_time

    train = [(pre_duration, LOW)]
    train.extend([(init_pi_plus, HIGH), (tau_shrt + init_pi_minus, LOW), (read_pi_plus, HIGH)])
    train.extend([(read_pi_minus + mid_duration, LOW)])
    train.extend([(init_pi_plus, HIGH), (tau_long + init_pi_minus, LOW), (read_pi_plus, HIGH)])
    train.extend([(read_pi_minus + post_duration, LOW)])
    seq.setDigital(pulser_do_uwave_plus, train)

    train = [(pre_duration, LOW)]
    train.extend([(init_pi_minus, HIGH), (tau_shrt + init_pi_plus, LOW), (read_pi_minus, HIGH)])
    train.extend([(read_pi_plus + mid_duration, LOW)])
    train.extend([(init_pi_minus, HIGH), (tau_long + init_pi_plus, LOW), (read_pi_minus, HIGH)])
    train.extend([(read_pi_plus + post_duration, LOW)])
    seq.setDigital(pulser_do_uwave_minus, train)

#    if init_state == 1 and read_state == 1:
#        pulser_do_uwave = pulser_do_uwave_read
#        train = [(pre_duration, LOW)]
#        train.extend([(pi_pulse_init, HIGH), (tau_shrt, LOW), (pi_pulse_read, HIGH)])
#        train.extend([(mid_duration, LOW)])
#        train.extend([(pi_pulse_init, HIGH), (tau_long, LOW), (pi_pulse_read, HIGH)])
#        train.extend([(post_duration, LOW)])
#        seq.setDigital(pulser_do_uwave, train)
#
#    if init_state == -1 and read_state == -1:
#        pulser_do_uwave = pulser_do_uwave_read
#        train = [(pre_duration, LOW)]
#        train.extend([(pi_pulse_init, HIGH), (tau_shrt, LOW), (pi_pulse_read, HIGH)])
#        train.extend([(mid_duration, LOW)])
#        train.extend([(pi_pulse_init, HIGH), (tau_long, LOW), (pi_pulse_read, HIGH)])
#        train.extend([(post_duration, LOW)])
#        seq.setDigital(pulser_do_uwave, train)

    final_digital = [pulser_wiring['do_532_aom'],
                     pulser_wiring['do_sample_clock']]
    final = OutputState(final_digital, 0.0, 0.0)
    return seq, final, [period]

if __name__ == '__main__':
    wiring = {'do_sample_clock': 0,
              'do_apd_0_gate': 4,
              'do_532_aom': 1,
              'do_uwave_gate_0': 2,
              'do_uwave_gate_1': 3}

#    args = [32000, 3000, 3000, 3000, 2000, 1000, 1000,
#            750, 40, 450, 34, 48, 68000, 0, 1, -1]
#    args = [6240, 3000, 3000, 3000, 2000, 1000, 1000,
#            750, 40, 320, 36, 0, 1760, 0, 1, 1]
    # no delay
    args = [6240, 3000, 3000, 3000, 2000, 1000, 1000,
            0, 0, 320, 36, 0, 1760, 0, 1, 1]
    args = [0, 3000, 3000, 3000, 2000, 1000, 1000,
            0, 0, 320, 36, 0, 0, 0, 1, 1]
    seq, ret_vals = get_seq(wiring, args)
    seq.plot()
