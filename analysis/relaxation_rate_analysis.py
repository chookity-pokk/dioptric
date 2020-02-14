# -*- coding: utf-8 -*-
"""
Created on Wed Sep 4 14:52:43 2019

This analysis script will plot and evaluate the omega and gamma rates for the
modified rate equations [(0,0) - (0,1) and (1,1) - (1,-1)] for the complete
data set. It calculates a standard error of each data point based on the
statistics over the number of runs. With the standard error on each point, the
subtracted data is then fit to a single exponential. From the (0,0) - (0,1)
exponential, we extact 3*Omega from the exponent, along with the standard
error on omega from the covariance of the fit.

From the (1,1) - (1,-1) exponential, we extract (2*gamma + Omega). Using the
Omega we just found, we calculate gamma and the associated standard error
from the covariance of the fit.

-User can specify if the offset should be a free parameter or if it should be
  set to 0. All our analysis of rates has been done without offset as a free
  param.

-If a value for omega and the omega uncertainty is passed, file will just
  evaluate gamma (t=with the omega provided).


@author: agardill
"""

# %% Imports

import numpy
from scipy import exp
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os

import utils.tool_belt as tool_belt
from utils.tool_belt import States

# %% Constants

manual_offset_gamma = 0.0
# %% Functions

# The exponential function without an offset
def exp_eq_omega(t, rate, amp):
    return  amp * exp(- rate * t)

def exp_eq_gamma(t, rate, amp):
    return  amp * exp(- rate * t) + manual_offset_gamma

# The exponential function with an offset
def exp_eq_offset(t, rate, amp, offset):
    return  offset + amp * exp(- rate * t)

# A function to collect folders in mass analysis
def get_folder_list(keyword):
    path = 'E:/Shared drives/Kolkowitz Lab Group/nvdata/t1_double_quantum'

    folders = []

    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for folder in d:
                if keyword in folder:
                    folders.append(folder)

    return folders

# This function sorts the data from one folder of an experiment and passes it
# into main
def get_data_lists(folder_name):
    # Get the file list from this folder
    file_list = tool_belt.get_file_list(folder_name, '.txt')

    # Define booleans to be used later in putting data into arrays in the
    # correct order. This was mainly put in place for older data where we
    # took measurements in an inconsistent way (unlike we are now)
    zero_zero_bool = False
    zero_plus_bool = False
    plus_plus_bool = False
    plus_minus_bool = False

    # Initially create empty lists, so that if no data is recieved, a list is
    # still returned from this function
    zero_zero_counts = []
    zero_zero_ste = []
    zero_plus_counts = []
    zero_plus_ste = []
    zero_zero_time = []
    plus_plus_counts = []
    plus_plus_ste = []
    plus_minus_counts = []
    plus_minus_ste = []
    plus_plus_time = []

    # Unpack the data

    # Unpack the data and sort into arrays. This allows multiple measurements of
    # the same type to be correctly sorted into one array
    for file in file_list:
        data = tool_belt.get_raw_data(folder_name, file[:-4])
        try:

            init_state_name = data['init_state']
            read_state_name = data['read_state']

            # older files still used 1,-1,0 convention. This will allow old
            # and new files to be evaluated
            if init_state_name == 1 or init_state_name == -1 or  \
                                    init_state_name == 0:
                high_state_name = 1
                low_state_name = -1
                zero_state_name = 0
            else:
                high_state_name = States.HIGH.name
                low_state_name = States.LOW.name
                zero_state_name = States.ZERO.name
            relaxation_time_range = numpy.array(data['relaxation_time_range'])
            num_steps = data['num_steps']

            num_runs = data['num_runs']
            sig_counts  = numpy.array(data['sig_counts'])
            ref_counts = numpy.array(data['ref_counts'])

            # Calculate time arrays in us
            min_relaxation_time, max_relaxation_time = \
                                        relaxation_time_range / 10**6
            time_array = numpy.linspace(min_relaxation_time,
                                        max_relaxation_time, num=num_steps)

            # Calculate the average signal counts over the runs, and st. error
#            print(sig_counts)
            avg_sig_counts = numpy.average(sig_counts[::], axis=0)
            ste_sig_counts = numpy.std(sig_counts[::], axis=0, ddof = 1) / numpy.sqrt(num_runs)

            # Assume reference is constant and can be approximated to one value
            avg_ref = numpy.average(ref_counts[::])

            # Divide signal by reference to get normalized counts and st error
            norm_avg_sig = avg_sig_counts / avg_ref
            norm_avg_sig_ste = ste_sig_counts / avg_ref



            # Check to see which data set the file is for, and append the data
            # to the corresponding array
            if init_state_name == zero_state_name and \
                                read_state_name == zero_state_name:
                # Check to see if data has already been added to a list for
                #this experiment. If it hasn't, then create arrays of the data.
                if zero_zero_bool == False:
                    zero_zero_counts = norm_avg_sig
                    zero_zero_ste = norm_avg_sig_ste
                    zero_zero_time = time_array

                    zero_zero_ref_max_time = max_relaxation_time
                    zero_zero_bool = True
                # If data has already been sorted for this experiment, then check
                # to see if this current data is the shorter or longer measurement,
                # and either append before or after the prexisting data
                else:

                    if max_relaxation_time > zero_zero_ref_max_time:
                        zero_zero_counts = numpy.concatenate((zero_zero_counts,
                                                        norm_avg_sig))
                        zero_zero_ste = numpy.concatenate((zero_zero_ste,
                                                        norm_avg_sig_ste))
                        zero_zero_time = numpy.concatenate((zero_zero_time, time_array))

                    elif max_relaxation_time < zero_zero_ref_max_time:
                        zero_zero_counts = numpy.concatenate((norm_avg_sig,
                                              zero_zero_counts))
                        zero_zero_ste = numpy.concatenate((norm_avg_sig_ste,
                                              zero_zero_ste))
                        zero_zero_time = numpy.concatenate((time_array, zero_zero_time))

            # MCC
            if init_state_name == zero_state_name and \
                                read_state_name == low_state_name:
                if zero_plus_bool == False:
                    zero_plus_counts = norm_avg_sig
                    zero_plus_ste = norm_avg_sig_ste
                    zero_plus_time = time_array

                    zero_plus_ref_max_time = max_relaxation_time
                    zero_plus_bool = True
                else:

                    if max_relaxation_time > zero_plus_ref_max_time:
                        zero_plus_counts = numpy.concatenate((zero_plus_counts,
                                                        norm_avg_sig))
                        zero_plus_ste = numpy.concatenate((zero_plus_ste,
                                                        norm_avg_sig_ste))

                        zero_plus_time = numpy.concatenate((zero_plus_time, time_array))

                    elif max_relaxation_time < zero_plus_ref_max_time:
                        zero_plus_counts = numpy.concatenate((norm_avg_sig,
                                              zero_plus_counts))
                        zero_plus_ste = numpy.concatenate((norm_avg_sig_ste,
                                              zero_plus_ste))

                        zero_plus_time = numpy.concatenate(time_array, zero_plus_time)


            if init_state_name == high_state_name and \
                                read_state_name == high_state_name:
                if plus_plus_bool == False:
                    plus_plus_counts = norm_avg_sig
                    plus_plus_ste = norm_avg_sig_ste
                    plus_plus_time = time_array

                    plus_plus_ref_max_time = max_relaxation_time
                    plus_plus_bool = True
                else:

                    if max_relaxation_time > plus_plus_ref_max_time:
                        plus_plus_counts = numpy.concatenate((plus_plus_counts,
                                                        norm_avg_sig))
                        plus_plus_ste = numpy.concatenate((plus_plus_ste,
                                                        norm_avg_sig_ste))
                        plus_plus_time = numpy.concatenate((plus_plus_time, time_array))

                    elif max_relaxation_time < plus_plus_ref_max_time:
                        plus_plus_counts = numpy.concatenate((norm_avg_sig,
                                                          plus_plus_counts))
                        plus_plus_ste = numpy.concatenate((norm_avg_sig_ste,
                                                          plus_plus_ste))
                        plus_plus_time = numpy.concatenate((time_array, plus_plus_time))

            if init_state_name == high_state_name and \
                                read_state_name == low_state_name:
                # We will want to put the MHz splitting in the file metadata
                uwave_freq_init = data['uwave_freq_init']
                uwave_freq_read = data['uwave_freq_read']

                if plus_minus_bool == False:
                    plus_minus_counts = norm_avg_sig
                    plus_minus_ste = norm_avg_sig_ste
                    plus_minus_time = time_array

                    plus_minus_ref_max_time = max_relaxation_time
                    plus_minus_bool = True
                else:

                    if max_relaxation_time > plus_minus_ref_max_time:
                        plus_minus_counts = numpy.concatenate((plus_minus_counts,
                                                        norm_avg_sig))
                        plus_minus_ste = numpy.concatenate((plus_minus_ste,
                                                        norm_avg_sig_ste))
                        plus_minus_time = numpy.concatenate((plus_minus_time, time_array))


                    elif max_relaxation_time < plus_minus_ref_max_time:
                        plus_minus_counts = numpy.concatenate((norm_avg_sig,
                                              plus_minus_counts))
                        plus_minus_ste = numpy.concatenate((norm_avg_sig_ste,
                                              plus_minus_ste))
                        plus_minus_time = numpy.concatenate((time_array, plus_minus_time))


                splitting_MHz = abs(uwave_freq_init - uwave_freq_read) * 10**3

        except Exception:
            print('Skipping {}'.format(str(file)))
            continue

    omega_exp_list = [zero_zero_counts, zero_zero_ste, \
                      zero_plus_counts, zero_plus_ste, \
                      zero_zero_time]
    gamma_exp_list = [plus_plus_counts, plus_plus_ste,  \
                      plus_minus_counts, plus_minus_ste, \
                      plus_plus_time]
    return omega_exp_list, gamma_exp_list, num_runs, splitting_MHz
# %% Main

def main(folder_name, omega = None, omega_ste = None, doPlot = False, offset = True):

    # Get the file list from the folder
    omega_exp_list, gamma_exp_list, \
                num_runs, splitting_MHz  = get_data_lists(folder_name)

    # %% Fit the data

    if doPlot:
        fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8))
        fig.set_tight_layout(True)

    omega_fit_failed = False
    gamma_fit_failed = False

    # If omega value is passed into the function, skip the omega fitting.
    if omega is not None and omega_ste is not None:
        omega_opti_params = numpy.array([None])
        zero_relaxation_counts = numpy.array([None])
        zero_relaxation_ste = numpy.array([None])
        zero_zero_time = numpy.array([None])
    else:
        #Fit to the (0,0) - (0,1) data to find Omega

        zero_zero_counts = omega_exp_list[0]
        zero_zero_ste = omega_exp_list[1]
        zero_plus_counts = omega_exp_list[2]
        zero_plus_ste = omega_exp_list[3]
        zero_zero_time = omega_exp_list[4]

        zero_relaxation_counts =  zero_zero_counts - zero_plus_counts
        zero_relaxation_ste = numpy.sqrt(zero_zero_ste**2 + zero_plus_ste**2)

        init_params_list = [1.0, 0.4]

        try:
            if offset:
                init_params_list.append(0)
                init_params = tuple(init_params_list)
                omega_opti_params, cov_arr = curve_fit(exp_eq_offset, zero_zero_time,
                                             zero_relaxation_counts, p0 = init_params,
                                             sigma = zero_relaxation_ste,
                                             absolute_sigma=True)

            else:
                init_params = tuple(init_params_list)
                omega_opti_params, cov_arr = curve_fit(exp_eq_omega, zero_zero_time,
                                             zero_relaxation_counts, p0 = init_params,
                                             sigma = zero_relaxation_ste,
                                             absolute_sigma=True)

        except Exception:

            omega_fit_failed = True

            if doPlot:
                ax = axes_pack[0]
                ax.errorbar(zero_zero_time, zero_relaxation_counts,
                            yerr = zero_relaxation_ste,
                            label = 'data', fmt = 'o', color = 'blue')
                ax.set_xlabel('Relaxation time (ms)')
                ax.set_ylabel('Normalized signal Counts')
                ax.set_title('(0,0) - (0,-1)')
                ax.legend()

        if not omega_fit_failed:
            # Calculate omega nad its ste
            omega = omega_opti_params[0] / 3.0
            omega_ste = numpy.sqrt(cov_arr[0,0]) / 3.0

            print('Omega: {} +/- {} kHz'.format('%.3f'%omega,
                      '%.3f'%omega_ste))
            # Plotting the data
            if doPlot:
                zero_time_linspace = numpy.linspace(0, zero_zero_time[-1], num=1000)
                ax = axes_pack[0]
                ax.errorbar(zero_zero_time, zero_relaxation_counts,
                            yerr = zero_relaxation_ste,
                            label = 'data', fmt = 'o', color = 'blue')
                if offset:
                    ax.plot(zero_time_linspace,
                        exp_eq_offset(zero_time_linspace, *omega_opti_params),
                        'r', label = 'fit')
                else:
                    ax.plot(zero_time_linspace,
                        exp_eq_omega(zero_time_linspace, *omega_opti_params),
                        'r', label = 'fit')
                ax.set_xlabel('Relaxation time (ms)')
                ax.set_ylabel('Normalized signal Counts')
                ax.set_title('(0,0) - (0,-1)')  # MCC
                # ax.set_title('(0,0) - (0,+1)')
                ax.legend()
                text = r'$\Omega = $ {} $\pm$ {} kHz'.format('%.3f'%omega,
                      '%.3f'%omega_ste)

                props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
                ax.text(0.55, 0.9, text, transform=ax.transAxes, fontsize=12,
                        verticalalignment='top', bbox=props)

    # %% Fit to the (1,1) - (1,-1) data to find Gamma, only if Omega waas able
    # to fit

    plus_plus_counts = gamma_exp_list[0]
    plus_plus_ste = gamma_exp_list[1]
    plus_minus_counts = gamma_exp_list[2]
    plus_minus_ste = gamma_exp_list[3]
    plus_plus_time = gamma_exp_list[4]

    # Define the counts for the plus relaxation equation
    plus_relaxation_counts =  plus_plus_counts - plus_minus_counts
    plus_relaxation_ste = numpy.sqrt(plus_plus_ste**2 + plus_minus_ste**2)

    init_params_list = [2*omega, 0.40]
    try:
        if offset:

            init_params_list.append(0)
            init_params = tuple(init_params_list)
            gamma_opti_params, cov_arr = curve_fit(exp_eq_offset,
                             plus_plus_time, plus_relaxation_counts,
                             p0 = init_params, sigma = plus_relaxation_ste,
                             absolute_sigma=True)


        else:
            init_params = tuple(init_params_list)
            gamma_opti_params, cov_arr = curve_fit(exp_eq_gamma,
                             plus_plus_time, plus_relaxation_counts,
                             p0 = init_params, sigma = plus_relaxation_ste,
                             absolute_sigma=True)

    except Exception:
        gamma_fit_failed = True

        if doPlot:
            ax = axes_pack[1]
            ax.errorbar(plus_plus_time, plus_relaxation_counts,
                    yerr = plus_relaxation_ste,
                    label = 'data', fmt = 'o', color = 'blue')
            ax.set_xlabel('Relaxation time (ms)')
            ax.set_ylabel('Normalized signal Counts')
            ax.set_title('(-1,-1) - (-1,+1)')

    if not gamma_fit_failed:

        # Calculate gamma and its ste
        gamma = (gamma_opti_params[0] - omega)/ 2.0
        gamma_ste = 0.5 * numpy.sqrt(cov_arr[0,0]+omega_ste**2)

        print('Gamma: {} +/- {} kHz'.format('%.3f'%gamma,
                  '%.3f'%gamma_ste))

        # Plotting
        if doPlot:
            plus_time_linspace = numpy.linspace(0, plus_plus_time[-1], num=1000)
            ax = axes_pack[1]
            ax.errorbar(plus_plus_time, plus_relaxation_counts,
                    yerr = plus_relaxation_ste,
                    label = 'data', fmt = 'o', color = 'blue')
            if offset:
                ax.plot(plus_time_linspace,
                    exp_eq_offset(plus_time_linspace, *gamma_opti_params),
                    'r', label = 'fit')
            else:
                ax.plot(plus_time_linspace,
                    exp_eq_gamma(plus_time_linspace, *gamma_opti_params),
                    'r', label = 'fit')
            ax.set_xlabel('Relaxation time (ms)')
            ax.set_ylabel('Normalized signal Counts')
            ax.set_title('(-1,-1) - (-1,+1)')
            ax.legend()
            text = r'$\gamma = $ {} $\pm$ {} kHz'.format('%.3f'%gamma,
                  '%.3f'%gamma_ste)
#            ax.set_xlim([-0.001, 0.05])

            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.55, 0.90, text, transform=ax.transAxes, fontsize=12,
                    verticalalignment='top', bbox=props)
    if doPlot:
        fig.canvas.draw()
        fig.canvas.flush_events()

        # Saving the data

        data_dir='E:/Shared drives/Kolkowitz Lab Group/nvdata'

        time_stamp = tool_belt.get_time_stamp()
        raw_data = {'time_stamp': time_stamp,
                    'splitting_MHz': splitting_MHz,
                    'splitting_MHz-units': 'MHz',
#                    'offset_free_param?': offset,
                    'manual_offset_gamma': manual_offset_gamma,
                    'omega': omega,
                    'omega-units': 'kHz',
                    'omega_ste': omega_ste,
                    'omega_ste-units': 'khz',
                    'gamma': gamma,
                    'gamma-units': 'kHz',
                    'gamma_ste': gamma_ste,
                    'gamma_ste-units': 'khz',
                    'zero_relaxation_counts': zero_relaxation_counts.tolist(),
                    'zero_relaxation_counts-units': 'counts',
                    'zero_relaxation_ste': zero_relaxation_ste.tolist(),
                    'zero_relaxation_ste-units': 'counts',
                    'zero_zero_time': zero_zero_time.tolist(),
                    'zero_zero_time-units': 'ms',
                    'plus_relaxation_counts': plus_relaxation_counts.tolist(),
                    'plus_relaxation_counts-units': 'counts',
                    'plus_relaxation_ste': plus_relaxation_ste.tolist(),
                    'plus_relaxation_ste-units': 'counts',
                    'plus_plus_time': plus_plus_time.tolist(),
                    'plus_plus_time-units': 'ms',
                    'omega_opti_params': omega_opti_params.tolist(),
                    'gamma_opti_params': gamma_opti_params.tolist(),
                    }

        file_name = '{}MHz_splitting_rate_analysis'.format(round(splitting_MHz))
        file_path = '{}/{}/{}'.format(data_dir, folder_name, file_name)
        tool_belt.save_raw_data(raw_data, file_path)
        tool_belt.save_figure(fig, file_path)

        return gamma, gamma_ste
# %% Run the file

if __name__ == '__main__':

    path = 't1_double_quantum/paper_data/bulk_dq/'
    folder = 'johnson-nv3_2020_02_04-121MHz-1deg'
    path += folder

    gamma, ste = main(path, omega=None, omega_ste=None,
                      doPlot=True, offset=False)
