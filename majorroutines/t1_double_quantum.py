# -*- coding: utf-8 -*-
"""
T1 measurement routine.

This version of t1 allows the the readout and measurement of all nine possible
combinations of the preparation and readout of the states in relaxation
measurements.

We write the +1 frequency to the Tektronix signal generator, 
and set the BNC signal generator to the -1 freq

To specify the preparation and readout states, pass into the function a list in
the form [preparation state, readout state]. That is passed in as
init_read_state.

Created on Wed Apr 24 15:01:04 2019

@author: agardill
"""

# %% Imports


import utils.tool_belt as tool_belt
import majorroutines.optimize as optimize
import numpy
import os
import time
from random import shuffle
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import json
import labrad


# %% Main


def main(nv_sig, apd_indices, uwave_freq_plus, uwave_freq_minus,
         uwave_power_plus, uwave_power_minus,
         uwave_pi_pulse_plus, uwave_pi_pulse_minus,
         relaxation_time_range, num_steps, num_reps, num_runs,
         init_read_list):

    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig, apd_indices,
                      uwave_freq_plus, uwave_freq_minus,
                      uwave_power_plus, uwave_power_minus,
                      uwave_pi_pulse_plus, uwave_pi_pulse_minus,
                      relaxation_time_range, num_steps, num_reps, num_runs,
                      init_read_list)


def main_with_cxn(cxn, nv_sig, apd_indices, uwave_freq_plus, uwave_freq_minus,
                  uwave_power_plus, uwave_power_minus,
                  uwave_pi_pulse_plus, uwave_pi_pulse_minus,
                  relaxation_time_range, num_steps, num_reps, num_runs,
                  init_read_list):

    tool_belt.reset_cfm(cxn)


    # %% Define the times to be used in the sequence
    
    shared_params = tool_belt.get_shared_parameters_dict(cxn)

    polarization_time = shared_params['polarization_dur']
    # time of illumination during which signal readout occurs
    signal_time = polarization_time
    # time of illumination during which reference readout occurs
    reference_time = polarization_time
    pre_uwave_exp_wait_time = shared_params['post_polarization_wait_dur']
    post_uwave_exp_wait_time = shared_params['pre_readout_wait_dur']
    # time between signal and reference without illumination
    sig_to_ref_wait_time = pre_uwave_exp_wait_time + post_uwave_exp_wait_time
    aom_delay_time = shared_params['532_aom_delay']
    rf_delay_time = shared_params['uwave_delay']
    gate_time = shared_params['pulsed_readout_dur']

    # %% Unpack the initial and read state

    init_state = init_read_list[0]
    read_state = init_read_list[1]

    # %% Setting initialize and readout states

    if init_state == 0:
        uwave_pi_pulse_init = 0
    elif init_state == 1:
        uwave_pi_pulse_init = round(uwave_pi_pulse_plus)
    elif init_state == -1:
        uwave_pi_pulse_init = round(uwave_pi_pulse_minus)

    if read_state == 0:
        uwave_pi_pulse_read = 0
    elif read_state == 1:
        uwave_pi_pulse_read =round(uwave_pi_pulse_plus)
    elif read_state == -1:
        uwave_pi_pulse_read = round(uwave_pi_pulse_minus)

    if init_state == 0:
        uwave_freq_init = 2.87
    if init_state == 1:
        uwave_freq_init = uwave_freq_plus
    if init_state == -1:
        uwave_freq_init = uwave_freq_minus


    if read_state == 0:
        uwave_freq_read = 2.87
    if read_state == 1:
        uwave_freq_read = uwave_freq_plus
    if read_state == -1:
        uwave_freq_read = uwave_freq_minus


    print('Initial pi pulse: {} ns'.format(uwave_pi_pulse_init))
    print('Initial frequency: {} GHz'.format(uwave_freq_init))
    print('Readout pi pulse: {} ns'.format(uwave_pi_pulse_read))
    print('Readout frequency: {} GHz'.format(uwave_freq_read))

    # %% Create the array of relaxation times

    # Array of times to sweep through
    # Must be ints since the pulse streamer only works with int64s

    min_relaxation_time = int( relaxation_time_range[0] )
    max_relaxation_time = int( relaxation_time_range[1] )

    taus = numpy.linspace(min_relaxation_time, max_relaxation_time,
                          num=num_steps, dtype=numpy.int32)

    # %% Fix the length of the sequence to account for odd amount of elements

    # Our sequence pairs the longest time with the shortest time, and steps
    # toward the middle. This means we only step through half of the length
    # of the time array.

    # That is a problem if the number of elements is odd. To fix this, we add
    # one to the length of the array. When this number is halfed and turned
    # into an integer, it will step through the middle element.

    if len(taus) % 2 == 0:
        half_length_taus = int( len(taus) / 2 )
    elif len(taus) % 2 == 1:
        half_length_taus = int( (len(taus) + 1) / 2 )

    # Then we must use this half length to calculate the list of integers to be
    # shuffled for each run

    tau_ind_list = list(range(0, half_length_taus))

    # %% Create data structure to save the counts

    # We create an array of NaNs that we'll fill
    # incrementally for the signal and reference counts.
    # NaNs are ignored by matplotlib, which is why they're useful for us here.
    # We define 2D arrays, with the horizontal dimension for the frequency and
    # the veritical dimension for the index of the run.

    sig_counts = numpy.empty([num_runs, num_steps], dtype=numpy.uint32)
    sig_counts[:] = numpy.nan
    ref_counts = numpy.copy(sig_counts)

    # %% Make some lists and variables to save at the end

    opti_coords_list = []
    tau_index_master_list = [[] for i in range(num_runs)]

    # %% Analyze the sequence

    # pulls the file of the sequence from serves/timing/sequencelibrary
    file_name = os.path.basename(__file__)

    seq_args = [min_relaxation_time, polarization_time, signal_time, reference_time,
                sig_to_ref_wait_time, pre_uwave_exp_wait_time,
                post_uwave_exp_wait_time, aom_delay_time, rf_delay_time,
                gate_time, uwave_pi_pulse_plus, uwave_pi_pulse_minus, max_relaxation_time,
                apd_indices[0], init_state, read_state]
    seq_args = [int(el) for el in seq_args]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    ret_vals = cxn.pulse_streamer.stream_load(file_name, seq_args_string)
    seq_time = ret_vals[0]

    # %% Ask user if they wish to run experiment based on run time

    seq_time_s = seq_time / (10**9)  # s
    expected_run_time = num_steps * num_reps * num_runs * seq_time_s / 2  # s
    expected_run_time_m = expected_run_time / 60 # m


#    msg = 'Expected run time: {:.1f} minutes. ' \
#        'Enter \'y\' to continue: '.format(expected_run_time_m)
#    if input(msg) != 'y':
#        return


    print(' \nExpected run time: {:.1f} minutes. '.format(expected_run_time_m))
#    return
    
    # %% Get the starting time of the function, to be used to calculate run time

    startFunctionTime = time.time()
    start_timestamp = tool_belt.get_time_stamp()

    # %% Collect the data

    # Start 'Press enter to stop...'
    tool_belt.init_safe_stop()

    for run_ind in range(num_runs):

        print(' \nRun index: {}'.format(run_ind))

        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break

        # Optimize
        opti_coords = optimize.main_with_cxn(cxn, nv_sig, apd_indices)
        opti_coords_list.append(opti_coords)

        # Set up the microwaves
        # Tektronix controls +
        cxn.signal_generator_tsg4104a.set_freq(uwave_freq_plus)
        cxn.signal_generator_tsg4104a.set_amp(uwave_power_plus)
        cxn.signal_generator_tsg4104a.uwave_on()
        # Berkeley controls -
        cxn.signal_generator_bnc835.set_freq(uwave_freq_minus)
        cxn.signal_generator_bnc835.set_amp(uwave_power_minus)
        cxn.signal_generator_bnc835.uwave_on()

        # Load the APD
        cxn.apd_tagger.start_tag_stream(apd_indices)

        # Shuffle the list of tau indices so that it steps thru them randomly
        shuffle(tau_ind_list)

        for tau_ind in tau_ind_list:

            # 'Flip a coin' to determine which tau (long/shrt) is used first
            rand_boolean = numpy.random.randint(0, high=2)

            if rand_boolean == 1:
                tau_ind_first = tau_ind
                tau_ind_second = -tau_ind - 1
            elif rand_boolean == 0:
                tau_ind_first = -tau_ind - 1
                tau_ind_second = tau_ind

            # add the tau indexxes used to a list to save at the end
            tau_index_master_list[run_ind].append(tau_ind_first)
            tau_index_master_list[run_ind].append(tau_ind_second)


            # Break out of the while if the user says stop
            if tool_belt.safe_stop():
                break

            print(' \nFirst relaxation time: {}'.format(taus[tau_ind_first]))
            print('Second relaxation time: {}'.format(taus[tau_ind_second]))

            # Stream the sequence
            seq_args = [taus[tau_ind_first], polarization_time, signal_time, reference_time,
                        sig_to_ref_wait_time, pre_uwave_exp_wait_time,
                        post_uwave_exp_wait_time, aom_delay_time, rf_delay_time,
                        gate_time, uwave_pi_pulse_plus, uwave_pi_pulse_minus, taus[tau_ind_second],
                        apd_indices[0], init_state, read_state]
            seq_args = [int(el) for el in seq_args]
            seq_args_string = tool_belt.encode_seq_args(seq_args)
            cxn.pulse_streamer.stream_immediate(file_name, num_reps,
                                                seq_args_string)

            # Each sample is of the form [*(<sig_shrt>, <ref_shrt>, <sig_long>, <ref_long>)]
            # So we can sum on the values for similar index modulus 4 to
            # parse the returned list into what we want.
            new_counts = cxn.apd_tagger.read_counter_separate_gates(1)
            sample_counts = new_counts[0]

            sig_gate_counts = sample_counts[::4]
            sig_counts[run_ind, tau_ind] = sum(sig_gate_counts)

            count = sum(sample_counts[0::4])
            sig_counts[run_ind, tau_ind_first] = count
            print('First signal = ' + str(count))

            count = sum(sample_counts[1::4])
            ref_counts[run_ind, tau_ind_first] = count
            print('First Reference = ' + str(count))

            count = sum(sample_counts[2::4])
            sig_counts[run_ind, tau_ind_second] = count
            print('Second Signal = ' + str(count))

            count = sum(sample_counts[3::4])
            ref_counts[run_ind, tau_ind_second] = count
            print('Second Reference = ' + str(count))

        cxn.apd_tagger.stop_tag_stream()

        # %% Save the data we have incrementally for long measurements

        raw_data = {'start_timestamp': start_timestamp,
                    'init_state': int(init_state),
                    'read_state': int(read_state),
                    'nv_sig': nv_sig,
                    'nv_sig-units': tool_belt.get_nv_sig_units(),
                    'gate_time': gate_time,
                    'gate_time-units': 'ns',
                    'uwave_freq_init': uwave_freq_init,
                    'uwave_freq_init-units': 'GHz',
                    'uwave_freq_read': uwave_freq_read,
                    'uwave_freq_read-units': 'GHz',
                    'uwave_power_plus': uwave_power_plus,
                    'uwave_power_plus-units': 'dBm',
                    'uwave_power_minus': uwave_power_minus,
                    'uwave_power_minus-units': 'dBm',
                    'uwave_pi_pulse_init': uwave_pi_pulse_init,
                    'uwave_pi_pulse_init-units': 'ns',
                    'uwave_pi_pulse_read': uwave_pi_pulse_read,
                    'uwave_pi_pulse_read-units': 'ns',
                    'relaxation_time_range': relaxation_time_range,
                    'relaxation_time_range-units': 'ns',
                    'num_steps': num_steps,
                    'num_reps': num_reps,
                    'run_ind': run_ind,
                    'tau_index_master_list': tau_index_master_list,
                    'opti_coords_list': opti_coords_list,
                    'opti_coords_list-units': 'V',
                    'sig_counts': sig_counts.astype(int).tolist(),
                    'sig_counts-units': 'counts',
                    'ref_counts': ref_counts.astype(int).tolist(),
                    'ref_counts-units': 'counts'}

        # This will continuously be the same file path so we will overwrite
        # the existing file with the latest version
        file_path = tool_belt.get_file_path(__file__, start_timestamp,
                                            nv_sig['name'], 'incremental')
        tool_belt.save_raw_data(raw_data, file_path)

    # %% Hardware clean up

    tool_belt.reset_cfm(cxn)

    # %% Average the counts over the iterations

    avg_sig_counts = numpy.average(sig_counts, axis=0)
    avg_ref_counts = numpy.average(ref_counts, axis=0)

    # %% Calculate the t1 data, signal / reference over different relaxation times

    # Replace x/0=inf with 0
    try:
        norm_avg_sig = avg_sig_counts / avg_ref_counts
    except RuntimeWarning as e:
        print(e)
        inf_mask = numpy.isinf(norm_avg_sig)
        # Assign to 0 based on the passed conditional array
        norm_avg_sig[inf_mask] = 0

    # %% Plot the t1 signal

    raw_fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))

    ax = axes_pack[0]
    ax.plot(taus / 10**6, avg_sig_counts, 'r-', label = 'signal')
    ax.plot(taus / 10**6, avg_ref_counts, 'g-', label = 'reference')
    ax.set_xlabel('Relaxation time (ms)')
    ax.set_ylabel('Counts')
    ax.legend()

    ax = axes_pack[1]
    ax.plot(taus / 10**6, norm_avg_sig, 'b-')
    ax.set_title('T1 Measurement. Initial state: {}, readout state: {}'.format(init_state, read_state))
    ax.set_xlabel('Relaxation time (ms)')
    ax.set_ylabel('Contrast (arb. units)')

    raw_fig.canvas.draw()
    # fig.set_tight_layout(True)
    raw_fig.canvas.flush_events()

    # %% Save the data

    endFunctionTime = time.time()

    timeElapsed = endFunctionTime - startFunctionTime

    timestamp = tool_belt.get_time_stamp()

    raw_data = {'timestamp': timestamp,
            'timeElapsed': timeElapsed,
            'init_state': int(init_state),
            'read_state': int(read_state),
            'nv_sig': nv_sig,
            'nv_sig-units': tool_belt.get_nv_sig_units(),
            'gate_time': gate_time,
            'gate_time-units': 'ns',
            'uwave_freq_init': uwave_freq_init,
            'uwave_freq_init-units': 'GHz',
            'uwave_freq_read': uwave_freq_read,
            'uwave_freq_read-units': 'GHz',
            'uwave_power_plus': uwave_power_plus,
            'uwave_power_plus-units': 'dBm',
            'uwave_power_minus': uwave_power_minus,
            'uwave_power_minus-units': 'dBm',
            'uwave_pi_pulse_init': uwave_pi_pulse_init,
            'uwave_pi_pulse_init-units': 'ns',
            'uwave_pi_pulse_read': uwave_pi_pulse_read,
            'uwave_pi_pulse_read-units': 'ns',
            'relaxation_time_range': relaxation_time_range,
            'relaxation_time_range-units': 'ns',
            'num_steps': num_steps,
            'num_reps': num_reps,
            'num_runs': num_runs,
            'tau_index_master_list': tau_index_master_list,
            'opti_coords_list': opti_coords_list,
            'opti_coords_list-units': 'V',
            'sig_counts': sig_counts.astype(int).tolist(),
            'sig_counts-units': 'counts',
            'ref_counts': ref_counts.astype(int).tolist(),
            'ref_counts-units': 'counts',
            'norm_avg_sig': norm_avg_sig.astype(float).tolist(),
            'norm_avg_sig-units': 'arb'}

    file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
    tool_belt.save_figure(raw_fig, file_path)
    tool_belt.save_raw_data(raw_data, file_path)

# %%

def decayExp(t, offset, amplitude, decay):
    return offset + amplitude * numpy.exp(-decay * t)

# %% Fitting the data

def t1_exponential_decay(open_file_name, save_file_type):

    directory = 'E:/Team Drives/Kolkowitz Lab Group/nvdata/t1_measurement/'

    # Open the specified file
    with open(directory + open_file_name + '.txt') as json_file:

        # Load the data from the file
        data = json.load(json_file)
        countsT1 = data["norm_avg_sig"]
        relaxation_time_range = data["relaxation_time_range"]
        num_steps = data["num_steps"]
        spin = data["spin_measured?"]

    min_relaxation_time = relaxation_time_range[0]
    max_relaxation_time = relaxation_time_range[1]

    timeArray = numpy.linspace(min_relaxation_time, max_relaxation_time,
                              num=num_steps, dtype=numpy.int32)

    offset = 0.8
    amplitude = 0.1
    decay = 1/10000 # inverse ns

    popt,pcov = curve_fit(decayExp, timeArray, countsT1,
                              p0=[offset, amplitude, decay])

    decay_time = 1 / popt[2]

    first = timeArray[0]
    last = timeArray[len(timeArray)-1]
    linspaceTime = numpy.linspace(first, last, num=1000)


    fig, ax= plt.subplots(1, 1, figsize=(10, 8))
    ax.plot(timeArray / 10**6, countsT1,'bo',label='data')
    ax.plot(linspaceTime / 10**6, decayExp(linspaceTime,*popt),'r-',label='fit')
    ax.set_xlabel('Dark Time (ms)')
    ax.set_ylabel('Contrast (arb. units)')
    ax.set_title('T1 of ' + str(spin))
    ax.legend()

    text = "\n".join((r'$C + A_0 e^{-t / d}$',
                      r'$C = $' + '%.1f'%(popt[0]),
                      r'$A_0 = $' + '%.1f'%(popt[1]),
                      r'$d = $' + "%.3f"%(decay_time / 10**6) + " ms"))


    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
    ax.text(0.70, 0.95, text, transform=ax.transAxes, fontsize=12,
                            verticalalignment="top", bbox=props)

    fig.canvas.draw()
    fig.canvas.flush_events()

    fig.savefig(open_file_name + 'replot.' + save_file_type)
