# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 09:52:43 2019

This analysis script will take a set of T1 experiments and fit the fucntions
defined in the Myer's paper ((0,0) - (0,1) and (1,1) - (1,-1)) to extract a 
value for Omega nad Gamma. 

Additionally, this fucntion allows the user to pass in a variable to define the
number of bins to seperate the data into. We can split the data up into bins
based on the num_runs. This allows us to see the data does not significantly 
changes over the course of the experiment.

@author: Aedan
"""

# %% Imports

import numpy
from scipy import asarray as ar, exp
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

import utils.tool_belt as tool_belt

# %% Constants

data_folder = 't1_double_quantum'

# %% Functions

# The functions we will fit the data to

def zero_relaxation_eq(t, omega, amp, offset):
    return offset + amp * exp(-3 * omega * t)

    
def plus_relaxation_eq(t, gamma, omega, amp, offset):
    return offset + amp * exp(-(omega + gamma * 2) * t)

# %% Main
    
def main(folder_name, num_bins, doPlot = False, save_data = True):
    
    print('Number of bins: {}'.format(num_bins))

    # Get the file list from this folder
    file_list = tool_belt.get_file_list(data_folder, '.txt', folder_name)

    # Get the number of runs to create the empty arrays from the last file in 
    # the list. This requires all the relaxation measurements to have the same
    # num_runs
    for file in file_list:
        data = tool_belt.get_raw_data(data_folder, file[:-4], folder_name)

        try:
            num_runs_set = data['num_runs']
        except Exception:
            continue
        
    bin_size = int(num_runs_set / num_bins)
        
    # Define booleans to be used later in putting data into usable arrays
    zero_zero_bool = False
    zero_plus_bool = False
    plus_plus_bool = False
    plus_minus_bool = False
    
    omega_fit_failed_list = []
    gamma_fit_failed_list = []
    
    # Create lists to store the omega and gamma rates
    omega_rate_list = []
    omega_amp_list = []
    omega_offset_list = []
    gamma_rate_list = []
    gamma_amp_list = []
    gamma_offset_list = []
    
    # %% Unpack the data
    
    # Unpack the data and sort into arrays. This allows multiple experiments of 
    # the same type (ie (1,-1)) to be correctly sorted into one array
    for file in file_list:
        data = tool_belt.get_raw_data(data_folder, file[:-4], folder_name)
        try:
                
            init_state = data['init_state']
            read_state = data['read_state']
            
            sig_counts = numpy.array(data['sig_counts'])
            ref_counts = numpy.array(data['ref_counts'])
            
            relaxation_time_range = numpy.array(data['relaxation_time_range'])
            # time is in microseconds
            min_relaxation_time, max_relaxation_time = relaxation_time_range / 10**6
            num_steps = data['num_steps']
            num_runs = data['num_runs']

            time_array = numpy.linspace(min_relaxation_time, 
                                        max_relaxation_time, num=num_steps) 
            
            
            # Check that the num_runs is consistent. If not, raise an error
            if num_runs_set != num_runs:
                print('Error, num_runs not consistent in file {}'.format(file))
                break
            
            # Check to see which data set the file is for, and append the data
            # to the corresponding array
            if init_state == 0 and read_state == 0:
                # Check to see if data has already been taken of this experiment
                # If it hasn't, then create arrays of the data.
                if zero_zero_bool == False:
                    zero_zero_sig_counts = sig_counts
                    zero_zero_ref_counts = ref_counts
                    zero_zero_time = time_array
                    
                    zero_zero_ref_max_time = max_relaxation_time
                    zero_zero_bool = True
                # If data has already been taken for this experiment, then check
                # to see if this current data is the shorter or longer measurement,
                # and either append before or after the prexisting data
                else:
                    
                    if max_relaxation_time > zero_zero_ref_max_time:
                        zero_zero_sig_counts = numpy.concatenate((zero_zero_sig_counts, 
                                                        sig_counts), axis = 1)
                        zero_zero_ref_counts = numpy.concatenate((zero_zero_ref_counts, 
                                                        ref_counts), axis = 1)
                        zero_zero_time = numpy.concatenate((zero_zero_time, time_array))
                        
                    elif max_relaxation_time < zero_zero_ref_max_time:
                        zero_zero_sig_counts = numpy.concatenate((sig_counts, 
                                              zero_zero_sig_counts), axis = 1)
                        zero_zero_ref_counts = numpy.concatenate((ref_counts, 
                                              zero_zero_ref_counts), axis = 1)
                        zero_zero_time = numpy.concatenate((time_array, zero_zero_time))
                
            if init_state == 0 and read_state == 1:
                # Check to see if data has already been taken of this experiment
                # If it hasn't, then create arrays of the data.
                if zero_plus_bool == False:
                    zero_plus_sig_counts = sig_counts
                    zero_plus_ref_counts = ref_counts
                    
                    zero_plus_ref_max_time = max_relaxation_time
                    zero_plus_bool = True
                # If data has already been taken for this experiment, then check
                # to see if this current data is the shorter or longer measurement,
                # and either append before or after the prexisting data
                else:
                    
                    if max_relaxation_time > zero_plus_ref_max_time:
                        zero_plus_sig_counts = numpy.concatenate((zero_plus_sig_counts, 
                                                        sig_counts), axis = 1)
                        zero_plus_ref_counts = numpy.concatenate((zero_plus_ref_counts, 
                                                        ref_counts), axis = 1)
                        
                    elif max_relaxation_time < zero_plus_ref_max_time:
                        zero_plus_sig_counts = numpy.concatenate((sig_counts, 
                                              zero_plus_sig_counts), axis = 1)
                        zero_plus_ref_counts = numpy.concatenate((ref_counts, 
                                              zero_plus_ref_counts), axis = 1)

            if init_state == 1 and read_state == 1:              
                # Check to see if data has already been taken of this experiment
                # If it hasn't, then create arrays of the data.
                if plus_plus_bool == False:
                    plus_plus_sig_counts = sig_counts
                    plus_plus_ref_counts = ref_counts
                    plus_plus_time = time_array
                    
                    plus_plus_ref_max_time = max_relaxation_time
                    plus_plus_bool = True
                # If data has already been taken for this experiment, then check
                # to see if this current data is the shorter or longer measurement,
                # and either append before or after the prexisting data
                else:
                    
                    if max_relaxation_time > plus_plus_ref_max_time:
                        plus_plus_sig_counts = numpy.concatenate((plus_plus_sig_counts, 
                                                        sig_counts), axis = 1)
                        plus_plus_ref_counts = numpy.concatenate((plus_plus_ref_counts, 
                                                        ref_counts), axis = 1)
                        plus_plus_time = numpy.concatenate((plus_plus_time, time_array))
                        
                    elif max_relaxation_time < plus_plus_ref_max_time:
                        plus_plus_sig_counts = numpy.concatenate((sig_counts, 
                                                          plus_plus_sig_counts), axis = 1)
                        plus_plus_ref_counts = numpy.concatenate((ref_counts, 
                                                          plus_plus_ref_counts), axis = 1)
                        plus_plus_time = numpy.concatenate((time_array, plus_plus_time))
                
            if init_state == 1 and read_state == -1:
                # We will want to put the MHz splitting in the file metadata
                uwave_freq_init = data['uwave_freq_init']
                uwave_freq_read = data['uwave_freq_read']
                
                # Check to see if data has already been taken of this experiment
                # If it hasn't, then create arrays of the data.
                if plus_minus_bool == False:
                    plus_minus_sig_counts = sig_counts
                    plus_minus_ref_counts = ref_counts
                    
                    plus_minus_ref_max_time = max_relaxation_time
                    plus_minus_bool = True
                # If data has already been taken for this experiment, then check
                # to see if this current data is the shorter or longer measurement,
                # and either append before or after the prexisting data
                else:
                    
                    if max_relaxation_time > plus_minus_ref_max_time:
                        plus_minus_sig_counts = numpy.concatenate((plus_minus_sig_counts, 
                                                        sig_counts), axis = 1)
                        plus_minus_ref_counts = numpy.concatenate((plus_minus_ref_counts, 
                                                        ref_counts), axis = 1)
                        
                    elif max_relaxation_time < plus_minus_ref_max_time:
                        plus_minus_sig_counts = numpy.concatenate((sig_counts, 
                                              plus_minus_sig_counts), axis = 1)
                        plus_minus_ref_counts = numpy.concatenate((ref_counts, 
                                              plus_minus_ref_counts), axis = 1)
                
                splitting_MHz = abs(uwave_freq_init - uwave_freq_read) * 10**3
                
        except Exception:
            continue
    
    # Some error handeling if the count arras don't match up            
    if len(zero_zero_sig_counts) != len(zero_plus_sig_counts): 
                    
         print('Error: length of zero_zero_sig_counts and zero_plus_sig_counts do not match')
       
    if len(plus_plus_sig_counts) != len(plus_minus_sig_counts):
        print('Error: length of plus_plus_sig_counts and plus_minus_sig_counts do not match')
    
    # %% Fit the data based on the bin size
        
    i = 0
    
    # For any number of bins except the maximum amount, we want to slice the
    # arrays from [i:i+bin_size-1]. However, this doesn't work for the maximum
    # amount of bins, when the bin_size is 1. In that case, we do want to take
    # slices [i:i+bin_size]
    if num_bins == num_runs:
        slice_size = bin_size
    else:
        slice_size = bin_size - 1
    
    while i < (num_runs):
        if doPlot:
            fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8))
        
        #Fit to the (0,0) - (0,1) data to find Omega
        zero_zero_avg_sig_counts =  \
            numpy.average(zero_zero_sig_counts[i:i+slice_size, ::], axis=0)
        zero_zero_avg_ref_counts =  \
            numpy.average(zero_zero_ref_counts[i:i+slice_size, ::], axis=0)
        
        zero_zero_norm_avg_sig = zero_zero_avg_sig_counts / zero_zero_avg_ref_counts
               
        zero_plus_avg_sig_counts = \
            numpy.average(zero_plus_sig_counts[i:i+slice_size, ::], axis=0)
        zero_plus_avg_ref_counts = \
            numpy.average(zero_plus_ref_counts[i:i+slice_size, ::], axis=0)
        
        zero_plus_norm_avg_sig = zero_plus_avg_sig_counts / zero_plus_avg_ref_counts 
    
        # Define the counts for the zero relaxation equation
        zero_relaxation_counts =  zero_zero_norm_avg_sig - zero_plus_norm_avg_sig
        
        omega_fit_failed = False
        gamma_fit_failed = False
    
        try:

            init_params = (0.33, 0.4, 0)
            opti_params, cov_arr = curve_fit(zero_relaxation_eq, zero_zero_time,
                                         zero_relaxation_counts, p0 = init_params)
           
        except Exception:
            
            omega_fit_failed = True
            omega_fit_failed_list.append(omega_fit_failed)
            
            if doPlot:
                ax = axes_pack[0]
                ax.plot(zero_zero_time, zero_relaxation_counts, 'bo', label = 'data')
                ax.set_xlabel('Relaxation time (ms)')
                ax.set_ylabel('Normalized signal Counts')
                ax.set_title('(0,0) - (0,+1)')
                ax.legend()

        if not omega_fit_failed:
            omega_fit_failed_list.append(omega_fit_failed)
            
            omega_rate_list.append(opti_params[0])
            omega_amp_list.append(opti_params[1])
            omega_offset_list.append(opti_params[2])
            
            omega = opti_params[0]
            omega_unc= cov_arr[0,0]
        
            # Plotting the data
            if doPlot:
                zero_time_linspace = numpy.linspace(0, zero_zero_time[-1], num=1000)
                ax = axes_pack[0]
                ax.plot(zero_zero_time, zero_relaxation_counts, 'bo', label = 'data')
                ax.plot(zero_time_linspace, 
                        zero_relaxation_eq(zero_time_linspace, *opti_params), 
                        'r', label = 'fit') 
                ax.set_xlabel('Relaxation time (ms)')
                ax.set_ylabel('Normalized signal Counts')
                ax.set_title('(0,0) - (0,+1)')
                ax.legend()
                text = r'$\Omega = $ {} kHz'.format('%.2f'%opti_params[0])
    
                props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
                ax.text(0.55, 0.95, text, transform=ax.transAxes, fontsize=12,
                        verticalalignment='top', bbox=props)

# %% Fit to the (1,1) - (1,-1) data to find Gamma, only if Omega waas able
# to fit
        
        plus_plus_avg_sig_counts = \
            numpy.average(plus_plus_sig_counts[i:i+slice_size, ::], axis=0)
        plus_plus_avg_ref_counts = \
            numpy.average(plus_plus_ref_counts[i:i+slice_size, ::], axis=0)
        
        plus_plus_norm_avg_sig = plus_plus_avg_sig_counts / plus_plus_avg_ref_counts
               
        plus_minus_avg_sig_counts = \
            numpy.average(plus_minus_sig_counts[i:i+slice_size, ::], axis=0)
        plus_minus_avg_ref_counts = \
            numpy.average(plus_minus_ref_counts[i:i+slice_size, ::], axis=0)
        
        plus_minus_norm_avg_sig = plus_minus_avg_sig_counts / plus_minus_avg_ref_counts
        
        # Define the counts for the plus relaxation equation
        plus_relaxation_counts =  plus_plus_norm_avg_sig - plus_minus_norm_avg_sig
        
        # If omega failed, we can't fit gamma to this data, so we will set the
        # gamma fail to True and just plot the points
        if omega_fit_failed:
            gamma_fit_failed = True
            gamma_fit_failed_list.append(gamma_fit_failed)
            
            if doPlot:
                ax = axes_pack[1]
                ax.plot(plus_plus_time, plus_relaxation_counts, 'bo')
                ax.set_xlabel('Relaxation time (ms)')
                ax.set_ylabel('Normalized signal Counts')
                ax.set_title('(+1,+1) - (+1,-1)')
                
        else:
            # we will use the omega found to fit to, and add bounds to the 
            # omega param given by +/- the covariance of the fit.
            
            omega_max = omega + omega_unc
            omega_min = omega - omega_unc
            try:
                init_params = (100, omega, 0.40, 0)
                bound_params = ((-numpy.inf, omega_min, -numpy.inf, -numpy.inf),
                          (numpy.inf, omega_max, numpy.inf, numpy.inf))
                opti_params, cov_arr = curve_fit(plus_relaxation_eq, 
                                 plus_plus_time, plus_relaxation_counts, 
                                 p0 = init_params, bounds = bound_params)
    
            except Exception:
                gamma_fit_failed = True
                gamma_fit_failed_list.append(gamma_fit_failed)
                
                if doPlot:
                    ax = axes_pack[1]
                    ax.plot(plus_plus_time, plus_relaxation_counts, 'bo')
                    ax.set_xlabel('Relaxation time (ms)')
                    ax.set_ylabel('Normalized signal Counts')
                    ax.set_title('(+1,+1) - (+1,-1)')
                
            if not gamma_fit_failed:
                gamma_fit_failed_list.append(gamma_fit_failed)
                
                gamma_rate_list.append(opti_params[0])
                gamma_amp_list.append(opti_params[1])
                gamma_offset_list.append(opti_params[2])
            
           
                # Plotting
                if doPlot:
                    plus_time_linspace = numpy.linspace(0, plus_plus_time[-1], num=1000)
                    ax = axes_pack[1]
                    ax.plot(plus_plus_time, plus_relaxation_counts, 'bo')
                    ax.plot(plus_time_linspace, 
                            plus_relaxation_eq(plus_time_linspace, *opti_params), 
                            'r', label = 'fit')   
#                    ax.set_xlim(0,0.1)
                    ax.set_xlabel('Relaxation time (ms)')
                    ax.set_ylabel('Normalized signal Counts')
                    ax.set_title('(+1,+1) - (+1,-1)')
                    ax.legend()
                    text = r'$\gamma = $ {} kHz'.format('%.2f'%opti_params[0])
        
                    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
                    ax.text(0.55, 0.95, text, transform=ax.transAxes, fontsize=12,
                            verticalalignment='top', bbox=props)
            if doPlot:
                fig.canvas.draw()
                fig.canvas.flush_events()
                    
        # Advance_ the index
        i = i + bin_size
    
    omega_average = numpy.average(omega_rate_list)
    omega_stdev = numpy.std(omega_rate_list)
    
    gamma_average = numpy.average(gamma_rate_list)
    gamma_stdev = numpy.std(gamma_rate_list)
    
#    print('Omega list: {} \nGamma list: {}'.format(omega_rate_list, gamma_rate_list))
    
# %% Saving data
    
    if save_data: 
        time_stamp = tool_belt.get_time_stamp()
        raw_data = {'time_stamp': time_stamp,
                    'level_splitting': splitting_MHz,
                    'level_splitting-units': 'MHz',
                    'num_runs': num_runs,
                    'num_bins': num_bins,
                    'bin_size': bin_size,
                    'omega_fit_failed_list': omega_fit_failed_list,
                    'gamma_fit_failed_list': gamma_fit_failed_list,
                    'omega_average': omega_average,
                    'omega_average-units': 'kHz',
                    'omega_stdev': omega_stdev,
                    'omega_stdev-units': 'kHz',
                    'gamma_average': gamma_average,
                    'gamma_average-units': 'kHz',
                    'gamma_stdev': gamma_stdev,
                    'gamma_stdev-units': 'kHz',
                    'omega_rate_list': omega_rate_list,
                    'omega_rate_list-units': 'kHz',
                    'omega_amp_list': omega_rate_list,
                    'omega_amp_list-units': 'arb',
                    'omega_offset_list': omega_offset_list,
                    'omega_offset_list-units': 'arb',
                    'gamma_rate_list': gamma_rate_list,
                    'gamma_rate_list-units': 'kHz',
                    'gamma_amp_list': gamma_rate_list,
                    'gamma_amp_list-units': 'arb',
                    'gamma_offset_list': gamma_offset_list,
                    'gamma_offset_list-units': 'arb'}
        
        data_dir='E:/Shared drives/Kolkowitz Lab Group/nvdata'
        
        file_name = str('%.1f'%splitting_MHz) + '_MHz_splitting_' + str(num_bins) + '_bins' 
        file_path = '{}/{}/{}/{}'.format(data_dir, data_folder, folder_name, 
                                                         file_name)
    
        tool_belt.save_raw_data(raw_data, file_path)

    return omega_average, omega_stdev, gamma_average, gamma_stdev, \
                  splitting_MHz, omega_fit_failed_list, gamma_fit_failed_list
                  
# %% Run the file
                  
if __name__ == '__main__':
    
    folder = 'nv13_2019_06_10_113MHz'
    
    main(folder, 1, True, True)

