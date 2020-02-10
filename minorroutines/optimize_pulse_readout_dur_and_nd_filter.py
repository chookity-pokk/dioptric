# -*- coding: utf-8 -*-
"""
Allows the readout time to be changed, and calculates the signal and noise with
a measurement. The signal is based on the difference of the high (uwave off) 
and low (uwave on) signal, and taken as the average fo multiple runs. The noise 
is based on the standard deviation of those multiple measurements.

Created on Tue Apr 23 11:49:23 2019

@author: gardill
"""


# %% Imports


import utils.tool_belt as tool_belt
import majorroutines.optimize as optimize
import numpy
import os
import time
import labrad
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from random import shuffle
from utils.tool_belt import States


# %%


def parabola(t, offset, amplitude, parameter):
    return offset + amplitude * (t - parameter)**2  

def fit_parabola(parameter_list, snr_list, init_guess_list):
    
    popt,pcov = curve_fit(parabola, parameter_list, snr_list,
                          p0=init_guess_list) 
    
    return popt
    
def raw_plot(num_steps ,avg_sig_counts, avg_ref_counts ,norm_avg_sig):
        raw_fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))
    
        ax = axes_pack[0]
        ax.plot(list(range(0, num_steps)), avg_sig_counts, 'r-')
        ax.plot(list(range(0, num_steps)), avg_ref_counts, 'g-')
        ax.set_xlabel('num_run')
        ax.set_ylabel('Counts')
    
        ax = axes_pack[1]
        ax.plot(list(range(0, num_steps)), norm_avg_sig, 'b-')
        ax.set_title('Normalized Signal With Varying Microwave Duration')
        ax.set_xlabel('num_run')
        ax.set_ylabel('Normalized contrast')
    
        raw_fig.canvas.draw()
        # fig.set_tight_layout(True)
        raw_fig.canvas.flush_events()
        
        return raw_fig
        
# %% Main, this allows any one of the inputs to be varied, like the readout
#    time or the nd_filter

def snr_measurement(nv_sig, readout_time, nd_filter, num_steps, num_reps, num_runs, 
                             do_plot, save_raw_data):

    with labrad.connect() as cxn:
        sig_to_noise_ratio = snr_measurement_with_cxn(cxn, nv_sig, readout_time, nd_filter,
                      num_steps, num_reps, num_runs, do_plot, save_raw_data)
        
        return sig_to_noise_ratio
def snr_measurement_with_cxn(cxn, nv_sig, readout_time, nd_filter,
                 num_steps, num_reps, num_runs,
                 do_plot = False, save_raw_data = False):
    

    # %% Get the starting time of the function

    startFunctionTime = time.time()

    # %% Initial calculations and setup
    
    apd_indices = [0]
    
    # Assume the low state
#    state = States.LOW
    state = States.HIGH
    
    shared_params = tool_belt.get_shared_parameters_dict(cxn)
    
    # Define some times (in ns)
    polarization_dur = 5 * 10**3
    exp_dur = 5 * 10**3
    aom_delay = shared_params['532_aom_delay']
    uwave_delay = shared_params['uwave_delay']
    pi_pulse = round(nv_sig['rabi_{}'.format(state.name)] / 2)
    
    # The two parameters we currently alter
    readout_time = int(readout_time)
    
    file_name = os.path.basename(__file__)

    # Set up our data structure, an array of NaNs that we'll fill
    # incrementally. NaNs are ignored by matplotlib, which is why they're
    # useful for us here.
    # We define 2D arrays, with the horizontal dimension for the frequency and
    # the veritical dimension for the index of the run.
    sig_counts = numpy.empty([num_runs, num_steps], dtype=numpy.uint32)
    sig_counts[:] = numpy.nan
    ref_counts = numpy.copy(sig_counts)
    
    # %% Make some lists and variables to save at the end
    
    opti_coords_list = []
    
    # Create a list of indices to step through the taus. This will be shuffled
    ind_list = list(range(0, num_steps))

    # %% Collect the data

    for run_ind in range(num_runs):

#        print('Run index: {}'. format(run_ind))
        
        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break
        
        # Optimize
        opti_coords_list.append(optimize.main(nv_sig, apd_indices))
        
        # After optimizing, change the filter to the nd_filter passed
        cxn.filter_slider_ell9k.set_filter(nd_filter)
        time.sleep(0.5)
        
        sig_gen_cxn = tool_belt.get_signal_generator_cxn(cxn, state)
        sig_gen_cxn.set_freq(nv_sig['resonance_{}'.format(state.name)])
        sig_gen_cxn.set_amp(nv_sig['uwave_power_{}'.format(state.name)])
        sig_gen_cxn.uwave_on()

        # Load the APD stream
        cxn.apd_tagger.start_tag_stream(apd_indices)
        
        # Shuffle the list of indices to use for stepping through the taus
        shuffle(ind_list)     
        
        for ind in ind_list:

            # Break out of the while if the user says stop
            if tool_belt.safe_stop():
                break 

            # Stream the sequence
            # polarization_dur, exp_dur, aom_delay, uwave_delay, 
            # readout_dur, pi_pulse, apd_index, uwave_gate_index
            seq_args = [polarization_dur, exp_dur, aom_delay, uwave_delay, 
                    readout_time, pi_pulse, apd_indices[0], state.value]
            seq_args = [int(el) for el in seq_args]
            seq_args_string = tool_belt.encode_seq_args(seq_args)            
            
            cxn.pulse_streamer.stream_immediate(file_name, num_reps, seq_args_string)

            # Get the counts
            new_counts = cxn.apd_tagger.read_counter_separate_gates(1)
            
            sample_counts = new_counts[0]
            
            # signal counts are even - get every second element starting from 0
            sig_gate_counts = sample_counts[0::2]
            sig_counts[run_ind, ind] = sum(sig_gate_counts)
            
            # ref counts are odd - sample_counts every second element starting from 1
            ref_gate_counts = sample_counts[1::2]  
            ref_counts[run_ind, ind] = sum(ref_gate_counts)
    
        tool_belt.reset_cfm(cxn)

    # %% Average the counts over the iterations

    avg_sig_counts = numpy.average(sig_counts, axis=0)
    avg_ref_counts = numpy.average(ref_counts, axis=0)

    # %% Calculate the statistics of the run

    norm_avg_sig = avg_ref_counts - avg_sig_counts
    
    sig_stat = numpy.average(norm_avg_sig)
    
    st_dev_stat = numpy.std(norm_avg_sig)
    
    sig_to_noise_ratio = sig_stat / st_dev_stat

    print('Readout Time: {} ns \nSignal: {:.3f} \nNoise: {:.3f} \nSNR: {:.1f}\n '.format(readout_time, \
          sig_stat, st_dev_stat, sig_to_noise_ratio))
    
    # %% Plot the counts
    if do_plot:
        
        raw_fig = raw_plot(num_steps, avg_sig_counts, avg_ref_counts, norm_avg_sig)

    # %% Save the data
    if save_raw_data:
        
        endFunctionTime = time.time()
    
        timeElapsed = endFunctionTime - startFunctionTime
    
        timestamp = tool_belt.get_time_stamp()
    
        raw_data = {'timestamp': timestamp,
                    'timeElapsed': timeElapsed,
                    'nv_sig': nv_sig,
                    'nv_sig-units': tool_belt.get_nv_sig_units(),
                    'readout_time': readout_time,
                    'readout_time-unit': 'ns',
                    'sig_stat': sig_stat,
                    'st_dev_stat': st_dev_stat,
                    'sig_to_noise_ratio': sig_to_noise_ratio,
                    'nv_sig': nv_sig,
                    'opti_coords_list': opti_coords_list,
                    'coords-units': 'V',
                    'nd_filter_used': nd_filter,
                    'state': state,
                    'num_steps': num_steps,
                    'num_reps': num_reps,
                    'num_runs': num_runs,
                    'sig_counts': sig_counts.astype(int).tolist(),
                    'sig_counts-units': 'counts',
                    'ref_counts': ref_counts.astype(int).tolist(),
                    'ref_counts-units': 'counts',
                    'norm_avg_sig': norm_avg_sig.astype(float).tolist(),
                    'norm_avg_sig-units': 'arb'}
    
        file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
        tool_belt.save_figure(raw_fig, file_path)
        tool_belt.save_raw_data(raw_data, file_path)
    
    return sig_to_noise_ratio

# %%
    
def optimize_readout(nv_sig, readout_range, num_readout_steps, nd_filter):
    
    # don't plot or save each individual raw data of the snr
    do_plot = False
    save_raw_data = False
    
    num_steps = 51
    num_reps = 10**5
#    num_reps = 10**3
    num_runs = 1
    
    # Create an empty list to fill with snr
    snr_list = []
    
    # make a linspace for the various readout times to test
    readout_time_list = numpy.linspace(readout_range[0], readout_range[-1], 
                                           num=num_readout_steps).astype(int)
    
    
    # Step thru the readout times and take a snr measurement
    for readout_ind_time in readout_time_list:
        
        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break
        
        readout_time = readout_ind_time
    
        snr_value = snr_measurement(nv_sig, readout_time, nd_filter,
                 num_steps, num_reps, num_runs, do_plot, save_raw_data)
        
        snr_list.append(snr_value)
        
        
    # Prepare the plot:
    snr_fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    ax.plot(readout_time_list, snr_list, 'ro', label = 'data')
    ax.set_xlabel('Readout time (ns)')
    ax.set_ylabel('Signal-to-noise ratio') 
    ax.set_title('Optimize readout window at {}'.format(nd_filter))
    
    # Fit the data to a parabola
    offset = 130
    amplitude = 10
    readout_time_guess = numpy.average(readout_range)   

    init_guess_list = [offset, amplitude, readout_time_guess]
    try:
        popt = fit_parabola(readout_time_list, snr_list, init_guess_list)
        
        # If the fit works, plot the fitted curve
        linspace_time = numpy.linspace(readout_range[0], readout_range[-1], num=1000)
        ax.plot(linspace_time, parabola(linspace_time,*popt), 'b-', label = 'fit')
        
        text = ('Optimal readout time = {:.1f} ns'.format(popt[2]))
    
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        ax.text(0.70, 0.05, text, transform=ax.transAxes, fontsize=12,
                                verticalalignment="top", bbox=props)
        
    except Exception as e:
        # Just print the error if the fit failed
        print(e)
    
    # Plot the figure
    ax.legend() 
    snr_fig.canvas.draw()
    snr_fig.canvas.flush_events()
    
    # Save the data
    timestamp = tool_belt.get_time_stamp()
    snr_data = {'timestamp': timestamp,
                'nv_sig': nv_sig,
                'nv_sig-units': tool_belt.get_nv_sig_units(), 
                'num_steps': num_steps,
                'num_reps': num_reps,
                'num_runs': num_runs,
                'snr_list': snr_list,
                'readout_time_list': readout_time_list.tolist(),
                'nd_filter': nd_filter}
    
    file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
    tool_belt.save_figure(snr_fig, file_path)
    tool_belt.save_raw_data(snr_data, file_path)
    
        
# %%
    
def main(nv_sig):
    # Step through the nd filters and find the optimized gate time in each one.
    
#    nd_filter_list = ['nd_0', 'nd_0.5', 'nd_1.0', 'nd_1.5']
    nd_filter_list = ['nd_0.5']
#    nd_filter_list = ['nd_1.0', 'nd_1.5']
    
    # Start 'Press enter to stop...'
    tool_belt.init_safe_stop()
    
    # Step thru the nd_filters and take snr over range of readout times
    for nd_filter_ind in range(len(nd_filter_list)):
        
        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break
        
        nd_filter = nd_filter_list[nd_filter_ind]
        
        if nd_filter == 'nd_0':
            readout_range = [50, 400]
            num_readout_steps = 8
        elif nd_filter == 'nd_0.5':
            readout_range = [200, 600]
            num_readout_steps = 9
        elif nd_filter == 'nd_1.0':
            readout_range = [250, 600]
            num_readout_steps = 8
        elif nd_filter == 'nd_1.5':
            readout_range = [250, 600]
            num_readout_steps = 8
        
        print('nd filter set to {}'.format(nd_filter))
        
        optimize_readout(nv_sig, readout_range, num_readout_steps, nd_filter)
    
# %%
    
if __name__ == '__main__':

    # Define the nv_sig to be used
    sample_name = 'johnson'
    nv3_2020_02_04 = { 'coords': [0.054, -0.046, 4.80],
            'name': '{}-nv3_2020_02_04'.format(sample_name),
            'expected_count_rate': 375, 'nd_filter': 'nd_0.5',
            'pulsed_readout_dur': 375, 'magnet_angle': 0.0,
            'resonance_LOW': 2.699, 'rabi_LOW':  94.8, 'uwave_power_LOW': 9.0,
            'resonance_HIGH': 2.9312, 'rabi_HIGH': 147.7, 'uwave_power_HIGH': 10.0}
    
    ### MAIN ###
    main(nv3_2020_02_04)
    
    # The individual functions in this file
#    snr_measurement(nv_sig, 320, 'nd_1.5', 51, 10**5, 1, True, True)
#    optimize_readout(nv_sig, readout_range, num_readout_steps, 'nd_1.5')

# %%
    do_plot = False
    if do_plot:
        
        snr_list = [
                ]
        
        readout_time_list = [
                ]
        
        init_guess_list = [10, 10, 450]
        
        popt = fit_parabola(readout_time_list, snr_list, init_guess_list)
        
        snr_fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        ax.plot(readout_time_list, snr_list, 'ro', label = 'data')
        ax.set_xlabel('Readout time (ns)')
        ax.set_ylabel('Signal-to-noise ratio') 
        ax.set_title('Optimize readout window at {}'.format('nd_1.5'))
        linspace_time = numpy.linspace(200, 600, num=1000)
        ax.plot(linspace_time, parabola(linspace_time,*popt), 'b-', label = 'fit')
        
        text = ('Optimal readout time = {:.1f} ns'.format(popt[2]))
    
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        ax.text(0.70, 0.05, text, transform=ax.transAxes, fontsize=12,
                                verticalalignment="top", bbox=props)
        ax.legend() 
        snr_fig.canvas.draw()
        snr_fig.canvas.flush_events()
    
# %%
    if tool_belt.check_safe_stop_alive():
        print("\n\nRoutine complete. Press enter to exit.")
        tool_belt.poll_safe_stop()
