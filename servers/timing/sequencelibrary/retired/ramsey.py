# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 9:33:00 2019

@author: mccambria
"""

from pulsestreamer import Sequence
import numpy

LOW = 0
HIGH = 1


def get_seq(pulser_wiring, args):
    
    # %% Parse wiring and args
    
    # The first 11 args are ns durations and we need them as int64s
    durations = []
    for ind in range(12):
        durations.append(numpy.int64(args[ind]))        
        
    # Unpack the durations
    tau_frst, polarization_time, signal_time, reference_time,  \
            sig_to_ref_wait_time, pre_uwave_exp_wait_time,  \
            post_uwave_exp_wait_time, aom_delay_time, rf_delay_time,  \
            gate_time, uwave_pi_half_pulse, tau_scnd = durations
        
    # Get the APD index (if more than one APD is to be used, then they must
    # share a gate channel)
    apd_index = args[13]

    # Get what we need out of the wiring dictionary
    key = 'do_apd_gate_{}'.format(apd_index)
    pulser_do_apd_gate = pulser_wiring[key]
    do_uwave_gate = 0
    if do_uwave_gate == 0:
        pulser_do_uwave = pulser_wiring['do_uwave_gate_0']
    if do_uwave_gate == 1:
        pulser_do_uwave = pulser_wiring['do_uwave_gate_1']
    pulser_do_aom = pulser_wiring['do_aom']
    
    # %% Write the microwave sequence to be used.
    
    uwave_experiment_frst = uwave_pi_half_pulse + tau_frst + uwave_pi_half_pulse
    
    uwave_experiment_seq_frst = [(uwave_pi_half_pulse, HIGH), (tau_frst, LOW), 
                                     (uwave_pi_half_pulse, HIGH)]
    
    uwave_experiment_scnd = uwave_pi_half_pulse + tau_scnd + uwave_pi_half_pulse
    
    uwave_experiment_seq_scnd = [(uwave_pi_half_pulse, HIGH), (tau_scnd, LOW), 
                                     (uwave_pi_half_pulse, HIGH)]

    # %% Calculate total period. This is the same for any pair of taus
        
    # The period is independent of the particular tau, but it must be long
    # enough to accomodate the longest tau
    period = aom_delay_time + rf_delay_time + polarization_time + \
        pre_uwave_exp_wait_time + uwave_experiment_frst + post_uwave_exp_wait_time + \
        signal_time + sig_to_ref_wait_time + reference_time + pre_uwave_exp_wait_time + \
        uwave_experiment_scnd + post_uwave_exp_wait_time + \
        signal_time + sig_to_ref_wait_time + reference_time
        
    # %% Define the sequence

    seq = Sequence()
    
    # APD gate
    pre_duration = prep_time
    frst_sig_to_frst_ref = signal_time + sig_to_ref_wait_time - gate_time
    frst_ref_to_scnd_sig = up_to_scnd_gates - (prep_time + signal_time + sig_to_ref_wait_time + gate_time)
    scnd_sig_to_scnd_ref = signal_time + sig_to_ref_wait_time - gate_time
    post_duration = reference_time - gate_time
    train = [(pre_duration, LOW),
             (gate_time, HIGH),
             (frst_sig_to_frst_ref, LOW),
             (gate_time, HIGH),
             (frst_ref_to_scnd_sig, LOW),
             (gate_time, HIGH),
             (scnd_sig_to_scnd_ref, LOW),
             (gate_time, HIGH),
             (post_duration, LOW)]
    seq.setDigital(pulser_do_apd_gate, train)

    # Pulse the laser with the AOM for polarization and readout
    train = [(rf_delay_time + polarization_time, HIGH),
             (pre_uwave_exp_wait_time + uwave_experiment_frst + post_uwave_exp_wait_time, LOW),
             (signal_time, HIGH),
             (sig_to_ref_wait_time, LOW),
             (reference_time, HIGH),
             (pre_uwave_exp_wait_time + uwave_experiment_scnd + post_uwave_exp_wait_time, LOW),
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
    train.extend(uwave_experiment_seq_frst)
    train.extend([(mid_duration, LOW)])
    train.extend(uwave_experiment_seq_scnd)
    train.extend([(post_duration, LOW)])
    seq.setDigital(pulser_do_uwave, train)
    
    return seq, [period]
    
if __name__ == '__main__':
    wiring = {'do_apd_gate_0': 0,
              'do_aom': 2,
              'do_uwave_gate': 3}

    args = [2000, 3000, 3000, 3000, 2000, 1000, 1000, 0, 0, 300, 55, 88000, 0]
    seq, ret_vals = get_seq(wiring, args)
    seq.plot()    
        