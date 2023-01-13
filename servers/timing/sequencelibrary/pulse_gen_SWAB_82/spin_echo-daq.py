# -*- coding: utf-8 -*-
"""
Created on Sat May  4 08:34:08 2019

@author: Aedan
"""

from pulsestreamer import Sequence
from pulsestreamer import OutputState
import numpy
import utils.tool_belt as tool_belt
from utils.tool_belt import States

LOW = 0
HIGH = 1


def get_seq(pulse_streamer, config, args):

    # %% Parse wiring and args

    # The first 11 args are ns durations and we need them as int64s
    durations = []
    for ind in range(6):
        durations.append(numpy.int64(args[ind]))

    # Unpack the durations
    tau_shrt, polarization_time, gate_time, pi_pulse, pi_on_2_pulse, tau_long = durations

    # Get the APD indices
    apd_index, state, laser_name, laser_power = args[6:10]
    state = States(state)
        
    # time of illumination during which signal readout occurs
    signal_time = polarization_time
    # time of illumination during which reference readout occurs
    reference_time = polarization_time
    pre_uwave_exp_wait_time = config['CommonDurations']['uwave_buffer']
    post_uwave_exp_wait_time = config['CommonDurations']['uwave_buffer']
    # time between signal and reference without illumination
    sig_to_ref_wait_time_base = pre_uwave_exp_wait_time + post_uwave_exp_wait_time
#    sig_to_ref_wait_time_shrt = sig_to_ref_wait_time_base + 2*tau_shrt 
#    sig_to_ref_wait_time_long = sig_to_ref_wait_time_base + 2*tau_long
    sig_to_ref_wait_time_shrt = sig_to_ref_wait_time_base 
    sig_to_ref_wait_time_long = sig_to_ref_wait_time_base 
    aom_delay_time = config['Optics'][laser_name]['delay']
    sig_gen_name = config['Microwaves']['sig_gen_{}'.format(state.name)]
    rf_delay_time = config['Microwaves'][sig_gen_name]['delay']
    back_buffer = 200

    pulser_wiring = config['Wiring']['PulseGen']
    pulser_do_apd_gate = pulser_wiring['do_apd_{}_gate'.format(apd_index)]
    sig_gen_gate_chan_name = 'do_{}_gate'.format(sig_gen_name)
    pulser_do_sig_gen_gate = pulser_wiring[sig_gen_gate_chan_name]
    key = 'do_sample_clock'
    pulser_do_apd_clock = pulser_wiring[key]

    # %% Write the microwave sequence to be used.

    # In t1, the sequence is just a pi pulse, wait for a relaxation time, then
    # then a second pi pulse

    # I define both the time of this experiment, which is useful for the AOM
    # and gate sequences to dictate the time for them to be LOW
    # And I define the actual uwave experiement to be plugged into the rf
    # sequence. I hope that this formatting works.

    # With future protocols--ramsey, spin echo, etc--it will be easy to use
    # this format of sequence building and just change this section of the file

    uwave_experiment_shrt = pi_on_2_pulse + tau_shrt + pi_pulse + \
                            tau_shrt + pi_on_2_pulse
    uwave_experiment_long = pi_on_2_pulse + tau_long + pi_pulse + \
                            tau_long + pi_on_2_pulse

    # %% Couple calculated values

    prep_time = aom_delay_time + rf_delay_time + \
        polarization_time + pre_uwave_exp_wait_time + \
        uwave_experiment_shrt + post_uwave_exp_wait_time

    up_to_long_gates = prep_time + signal_time + sig_to_ref_wait_time_shrt + \
        reference_time + pre_uwave_exp_wait_time + \
        uwave_experiment_long + post_uwave_exp_wait_time

    # %% Calclate total period. This is fixed for each tau index

    # The period is independent of the particular tau, but it must be long
    # enough to accomodate the longest tau
    period = aom_delay_time + rf_delay_time + polarization_time + \
        pre_uwave_exp_wait_time + uwave_experiment_shrt + post_uwave_exp_wait_time + \
        signal_time + sig_to_ref_wait_time_shrt + reference_time + pre_uwave_exp_wait_time + \
        uwave_experiment_long + post_uwave_exp_wait_time + \
        signal_time + sig_to_ref_wait_time_long + reference_time

    # %% Define the sequence

    seq = Sequence()

    # APD gating
    pre_duration = prep_time
    short_sig_to_short_ref = signal_time + sig_to_ref_wait_time_shrt - gate_time
    short_ref_to_long_sig = up_to_long_gates - (prep_time + signal_time + sig_to_ref_wait_time_shrt + gate_time)
    long_sig_to_long_ref = signal_time + sig_to_ref_wait_time_long - gate_time
    post_duration = reference_time - gate_time + back_buffer
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
    
    #clock pulses
    pre_duration = prep_time
    short_sig_to_short_ref = signal_time + sig_to_ref_wait_time_shrt - gate_time
    short_ref_to_long_sig = up_to_long_gates - (prep_time + signal_time + sig_to_ref_wait_time_shrt + gate_time)
    long_sig_to_long_ref = signal_time + sig_to_ref_wait_time_long - gate_time
    post_duration = reference_time - gate_time + back_buffer
    train = [(pre_duration, LOW),
             (gate_time + 100, LOW),
             (100, HIGH),
             (short_sig_to_short_ref-200, LOW),
             (gate_time + 100, LOW),
             (100, HIGH),
             (short_ref_to_long_sig-200, LOW),
             (gate_time + 100, LOW),
             (100, HIGH),
             (long_sig_to_long_ref-200, LOW),
             (gate_time + 100, LOW),
             (100, HIGH),
             (post_duration-200, LOW)]
    seq.setDigital(pulser_do_apd_clock, train)

    # Laser
    train = [(rf_delay_time + polarization_time, HIGH),
             (pre_uwave_exp_wait_time + uwave_experiment_shrt + post_uwave_exp_wait_time, LOW),
             (signal_time, HIGH),
             (sig_to_ref_wait_time_shrt, LOW),
             (reference_time, HIGH),
             (pre_uwave_exp_wait_time + uwave_experiment_long + post_uwave_exp_wait_time, LOW),
             (signal_time, HIGH),
             (sig_to_ref_wait_time_long, LOW),
             (reference_time + aom_delay_time, HIGH),
             (back_buffer, LOW)]
    tool_belt.process_laser_seq(pulse_streamer, seq, config,
                                laser_name, laser_power, train)

    # Pulse the microwave for tau
    pre_duration = aom_delay_time + polarization_time + pre_uwave_exp_wait_time
    mid_duration = post_uwave_exp_wait_time + signal_time + sig_to_ref_wait_time_shrt + \
        reference_time + pre_uwave_exp_wait_time
    post_duration = post_uwave_exp_wait_time + signal_time + \
        sig_to_ref_wait_time_long + reference_time + rf_delay_time + back_buffer

    train = [(pre_duration, LOW)]
    train.extend([(pi_on_2_pulse, HIGH), (tau_shrt, LOW)])
    train.extend([(pi_pulse, HIGH)])
    train.extend([(tau_shrt, LOW), (pi_on_2_pulse, HIGH)])
    train.extend([(mid_duration, LOW)])
    train.extend([(pi_on_2_pulse, HIGH), (tau_long, LOW)])
    train.extend([(pi_pulse, HIGH)])
    train.extend([(tau_long, LOW), (pi_on_2_pulse, HIGH)])
    train.extend([(post_duration, LOW)])
    seq.setDigital(pulser_do_sig_gen_gate, train)

    final_digital = []
    final = OutputState(final_digital, 0.0, 0.0)
    return seq, final, [period]

if __name__ == '__main__':
    config = tool_belt.get_config_dict()
    seq_args = [400, 10000.0, 350, 87, 44, 120000, 0, 1, 'cobolt_515', None]
    seq, final, ret_vals = get_seq(None, config, seq_args)
    seq.plot()
