# -*- coding: utf-8 -*-
"""
Plot the counts obtained by moving the AOM on time so that we can
determine the delay of the AOM relative to the APD gating.

Created on Fri Jul 12 13:53:45 2019

@author: mccambria
"""


# %% Imports


import labrad
import utils.tool_belt as tool_belt
import majorroutines.optimize as optimize
from random import shuffle
import numpy
import matplotlib.pyplot as plt


# %% Functions


def measure_delay(cxn, nv_sig, readout, apd_indices,
              delay_range, num_steps, num_reps, seq_file,
              sig_gen=None, uwave_freq=None, uwave_power=None,
              rabi_period=None, aom_delay=None):
    
    taus = numpy.linspace(delay_range[0], delay_range[1],
                          num_steps, dtype=numpy.int32)
    tau_ind_list = list(range(num_steps))
    shuffle(tau_ind_list)
    
    sig_counts = numpy.empty(num_steps, dtype=numpy.uint32)
    sig_counts[:] = numpy.nan
    ref_counts = numpy.copy(sig_counts)
    
    optimize.main_with_cxn(cxn, nv_sig, apd_indices)
    
    tool_belt.reset_cfm(cxn)
    # Turn on the microwaves for determining microwave delay
    if seq_file == 'uwave_delay.py':
        if sig_gen == 'tsg4104a':
            cxn.signal_generator_tsg4104a.set_freq(uwave_freq)
            cxn.signal_generator_tsg4104a.set_amp(uwave_power)
            cxn.signal_generator_tsg4104a.uwave_on()
        elif sig_gen == 'bnc835':
            cxn.signal_generator_bnc835.set_freq(uwave_freq)
            cxn.signal_generator_bnc835.set_amp(uwave_power)
            cxn.signal_generator_bnc835.uwave_on()
    cxn.apd_tagger.start_tag_stream(apd_indices)  
    
    tool_belt.init_safe_stop()
    
    for tau_ind in tau_ind_list:
        
        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break
        
        tau = taus[tau_ind]
        if seq_file == 'aom_delay.py':
            seq_args = [tau, readout, apd_indices[0]]
        elif seq_file == 'uwave_delay.py':
            seq_args = [tau, readout, apd_indices[0]]
        seq_args = [int(el) for el in seq_args]
        seq_args_string = tool_belt.encode_seq_args(seq_args)
        cxn.pulse_streamer.stream_immediate(seq_file, num_reps,
                                            seq_args_string)
        
        new_counts = cxn.apd_tagger.read_counter_separate_gates(1)
        sample_counts = new_counts[0]
        sig_counts[tau_ind] = sum(sample_counts[0::2])
        ref_counts[tau_ind] = sum(sample_counts[1::2])
            
    cxn.apd_tagger.stop_tag_stream()
    tool_belt.reset_cfm(cxn)
    
    # kcps
#    sig_count_rates = (sig_counts / (num_reps * 1000)) / (readout / (10**9))
#    ref_count_rates = (ref_counts / (num_reps * 1000)) / (readout / (10**9))
    norm_avg_sig = sig_counts / ref_counts

    fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))
    ax = axes_pack[0]
    ax.plot(taus, sig_counts, 'r-', label = 'signal')
    ax.plot(taus, ref_counts, 'g-', label = 'reference')
    ax.set_title('Counts vs Delay Time')
    ax.set_xlabel('Delay time (ns)')
    ax.set_ylabel('Count rate (kcps)')
    ax = axes_pack[1]
    ax.plot(taus, norm_avg_sig, 'b-')
    ax.set_title('Contrast vs Delay Time')
    ax.set_xlabel('Delay time (ns)')
    ax.set_ylabel('Contrast (arb. units)')
    fig.canvas.draw()
    fig.set_tight_layout(True)
    fig.canvas.flush_events()
    
    timestamp = tool_belt.get_time_stamp()
    raw_data = {'timestamp': timestamp,
            'sequence': seq_file,
            'nv_sig': nv_sig,
            'nv_sig-units': tool_belt.get_nv_sig_units(),
            'readout': readout,
            'readout-units': 'ns',
            'delay_range': delay_range,
            'delay_range-units': 'ns',
            'num_steps': num_steps,
            'num_reps': num_reps,
            'sig_counts': sig_counts.astype(int).tolist(),
            'sig_counts-units': 'counts',
            'ref_counts': ref_counts.astype(int).tolist(),
            'ref_counts-units': 'counts',
            'norm_avg_sig': norm_avg_sig.astype(float).tolist(),
            'norm_avg_sig-units': 'arb'}
    
    file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
    tool_belt.save_figure(fig, file_path)
    tool_belt.save_raw_data(raw_data, file_path)


# %% Mains


def aom_delay(cxn, nv_sig, readout, apd_indices,
              delay_range, num_steps, num_reps):
    
    seq_file = 'aom_delay.py'
    
    measure_delay(cxn, nv_sig, readout, apd_indices,
              delay_range, num_steps, num_reps, seq_file)

def uwave_delay(cxn, nv_sig, readout, apd_indices,
              sig_gen, uwave_freq, uwave_power, rabi_period, aom_delay,
              delay_range, num_steps, num_reps):
    
    seq_file = 'uwave_delay.py'
    
    measure_delay(cxn, nv_sig, readout, apd_indices,
              delay_range, num_steps, num_reps, seq_file,
              sig_gen, uwave_freq, uwave_power, rabi_period, aom_delay)


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here
    sample_name = 'johnson1'
    nv0_2019_06_27 = {'coords': [-0.148, -0.340, 5.46], 'nd_filter': 'nd_0.5',
                      'expected_count_rate': 47, 'magnet_angle': 41.8,
                      'name': sample_name}
    apd_indices = [0]
    num_reps = 10**5
    readout = 2000
    nv_sig = nv0_2019_06_27

    # aom_delay
    delay_range = [900, 1500]
    num_steps = 51
    with labrad.connect() as cxn:
        aom_delay(cxn, nv_sig, readout, apd_indices,
                  delay_range, num_steps, num_reps)

    # uwave_delay
#    delay_range = [0, 100]
#    num_steps = 21
#    sig_gen = 'tsg4104a'
#    uwave_freq = 2.8587  
#    uwave_power = 9
#    rabi_period = 144.4
#    aom_delay = 1000
#    with labrad.connect() as cxn:
#        uwave_delay(cxn, nv_sig, nd_filter, readout, apd_indices,
#              sig_gen, uwave_freq, uwave_power, rabi_period, aom_delay,
#              delay_range, num_steps, num_reps, name)
