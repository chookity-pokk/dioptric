# -*- coding: utf-8 -*-
"""
Ramsey measruement.

This routine puts polarizes the nv state into 0, then applies a pi/2 pulse to
put the state into a superposition between the 0 and + or - 1 state. The state
then evolves for a time, tau, of free precesion, and then a second pi/s pulse
is applied. The amount of population in 0 is read out by collecting the
fluorescence during a readout.

It then takes a fast fourier transform of the time data to attempt to extract
the frequencies in the ramsey experiment. If the funtion can't determine the
peaks in the fft, then a detuning is used.

Lastly, this file curve_fits the data to a triple sum of cosines using the
found frequencies.

Created on Wed Apr 24 15:01:04 2019

@author: agardill
"""

# %% Imports


import utils.tool_belt as tool_belt
import majorroutines.optimize as optimize
import numpy
import time
import matplotlib.pyplot as plt
from random import shuffle
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
import labrad


# %% Main


def main(nv_sig, apd_indices, uwave_freq, detuning,
         uwave_power, rabi_period, precession_time_range,
         num_steps, num_reps, num_runs):

    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig, apd_indices, uwave_freq, detuning,
                      uwave_power, rabi_period, precession_time_range,
                      num_steps, num_reps, num_runs)

def main_with_cxn(cxn, nv_sig, apd_indices, uwave_freq, detuning,
                  uwave_power, rabi_period, precession_time_range,
                  num_steps, num_reps, num_runs):

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

    # Convert pi_pulse to integer
    uwave_pi_half_pulse = round(rabi_period / 4)

    # Detune the pi/2 pulse frequency
    uwave_freq_detuned = uwave_freq + detuning / 10**3

    seq_file_name = 't1_double_quantum.py'

    # %% Create the array of relaxation times

    # Array of times to sweep through
    # Must be ints since the pulse streamer only works with int64s

    min_precession_time = int(precession_time_range[0])
    max_precession_time = int(precession_time_range[1])

    taus = numpy.linspace(min_precession_time, max_precession_time,
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
#
#    save_tau_list = numpy.array([num_runs, len(taus)])

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

    # We can simply reuse t1_double_quantum for this if we pass a pi/2 pulse
    # instead of a pi pulse and use the same states for init/readout
    seq_args = [min_precession_time, polarization_time, signal_time, reference_time,
                sig_to_ref_wait_time, pre_uwave_exp_wait_time,
                post_uwave_exp_wait_time, aom_delay_time, rf_delay_time,
                gate_time, uwave_pi_half_pulse, 0,
                max_precession_time, apd_indices[0], 1, 1]
    seq_args = [int(el) for el in seq_args]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    ret_vals = cxn.pulse_streamer.stream_load(seq_file_name, seq_args_string)
    seq_time = ret_vals[0]
#    print(sequence_args)
#    print(seq_time)

    # %% Let the user know how long this will take

    seq_time_s = seq_time / (10**9)  # s
    expected_run_time = num_steps * num_reps * num_runs * seq_time_s / 2  # s
    expected_run_time_m = expected_run_time / 60 # s

    print(' \nExpected run time: {:.1f} minutes. '.format(expected_run_time_m))

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

        # Set up the microwaves - just use the Tektronix
        cxn.signal_generator_tsg4104a.set_freq(uwave_freq_detuned)
        cxn.signal_generator_tsg4104a.set_amp(uwave_power)
        cxn.signal_generator_tsg4104a.uwave_on()

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

            seq_args = [taus[tau_ind_first], polarization_time, signal_time, reference_time,
                            sig_to_ref_wait_time, pre_uwave_exp_wait_time,
                            post_uwave_exp_wait_time, aom_delay_time, rf_delay_time,
                            gate_time, uwave_pi_half_pulse, 0,
                            taus[tau_ind_second], apd_indices[0], 1, 1]
            seq_args = [int(el) for el in seq_args]
            seq_args_string = tool_belt.encode_seq_args(seq_args)
            cxn.pulse_streamer.stream_immediate(seq_file_name, num_reps, seq_args_string)

            # Each sample is of the form [*(<sig_shrt>, <ref_shrt>, <sig_long>, <ref_long>)]
            # So we can sum on the values for similar index modulus 4 to
            # parse the returned list into what we want.
            new_counts = cxn.apd_tagger.read_counter_separate_gates(1)
            sample_counts = new_counts[0]

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
                'nv_sig': nv_sig,
                'nv_sig-units': tool_belt.get_nv_sig_units(),
                'gate_time': gate_time,
                'gate_time-units': 'ns',
                'uwave_freq': uwave_freq,
                'uwave_freq-units': 'GHz',
                'detuning': detuning,
                'detuning-units': 'MHz',
                'uwave_power': uwave_power,
                'uwave_power-units': 'dBm',
                'rabi_period': rabi_period,
                'rabi_period-units': 'ns',
                'uwave_pi_half_pulse': uwave_pi_half_pulse,
                'uwave_pi_half_pulse-units': 'ns',
                'precession_time_range': precession_time_range,
                'precession_time_range-units': 'ns',
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

    # %% Calculate the ramsey data, signal / reference over different
    # relaxation times

    # Replace x/0=inf with 0
    try:
        norm_avg_sig = avg_sig_counts / avg_ref_counts
    except RuntimeWarning as e:
        print(e)
        inf_mask = numpy.isinf(norm_avg_sig)
        # Assign to 0 based on the passed conditional array
        norm_avg_sig[inf_mask] = 0

    # %% Plot the signal

    raw_fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))

    ax = axes_pack[0]
    ax.plot(taus / 10**3, avg_sig_counts, 'r-', label = 'signal')
    ax.plot(taus / 10**3, avg_ref_counts, 'g-', label = 'reference')
    ax.set_xlabel('Precession time (us)')
    ax.set_ylabel('Counts')
    ax.legend()

    ax = axes_pack[1]
    ax.plot(taus / 10**3, norm_avg_sig, 'b-')
    ax.set_title('Ramsey Measurement')
    ax.set_xlabel('Precession time (us)')
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
            'nv_sig': nv_sig,
            'nv_sig-units': tool_belt.get_nv_sig_units(),
            'gate_time': gate_time,
            'gate_time-units': 'ns',
            'uwave_freq': uwave_freq,
            'uwave_freq-units': 'GHz',
            'detuning': detuning,
            'detuning-units': 'MHz',
            'uwave_power': uwave_power,
            'uwave_power-units': 'dBm',
            'rabi_period': rabi_period,
            'rabi_period-units': 'ns',
            'uwave_pi_half_pulse': uwave_pi_half_pulse,
            'uwave_pi_half_pulse-units': 'ns',
            'precession_time_range': precession_time_range,
            'precession_time_range-units': 'ns',
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


# %% Fitting the data

    # Create an empty array for the frequency arrays
    FreqParams = numpy.empty([3])

    # Perform the fft
    time_step = (max_precession_time - min_precession_time) / (num_steps - 1)

    transform = numpy.fft.rfft(norm_avg_sig)
#    window = max_precession_time - min_precession_time
    freqs = numpy.fft.rfftfreq(num_steps, d=time_step)
    transform_mag = numpy.absolute(transform)

    # Plot the fft
    fig_fft, ax= plt.subplots(1, 1, figsize=(10, 8))
    ax.plot(freqs[1:], transform_mag[1:])  # [1:] excludes frequency 0 (DC component)
    ax.set_xlabel('Frequency (MHz)')
    ax.set_ylabel('FFT magnitude')
    ax.set_title('Ramsey FFT')
    fig_fft.canvas.draw()
    fig_fft.canvas.flush_events()

    # Save the fft figure
    tool_belt.save_figure(fig_fft, file_path + '_fft')

    # Guess the peaks in the fft. There are parameters that can be used to make
    # this more efficient
    freq_guesses_ind = find_peaks(transform_mag[1:]
                                  , prominence = 0.5
#                                  , height = 0.8
#                                  , distance = 2.2 / freq_step
                                  )

#    print(freq_guesses_ind[0])

    # Check to see if there are three peaks. If not, try the detuning passed in
    if len(freq_guesses_ind[0]) != 3:
        print('Number of frequencies found: {}'.format(len(freq_guesses_ind[0])))
#        detuning = 3 # MHz

        FreqParams[0] = detuning - 2.2
        FreqParams[1] = detuning
        FreqParams[2] = detuning + 2.2
    else:
        FreqParams[0] = freqs[freq_guesses_ind[0][0]]
        FreqParams[1] = freqs[freq_guesses_ind[0][1]]
        FreqParams[2] = freqs[freq_guesses_ind[0][2]]


    # Guess the other params for fitting
    amp_1 = 0.3
    amp_2 = amp_1
    amp_3 = amp_1
    decay = 1
    offset = 1

    guess_params = (offset, decay, amp_1, FreqParams[0],
                        amp_2, FreqParams[1],
                        amp_3, FreqParams[2])

    # Try the fit to a sum of three cosines

    try:
        popt,pcov = curve_fit(tool_belt.cosine_sum, taus, norm_avg_sig,
                      p0=guess_params)
    except Exception:
        print('Something went wrong!')
        popt = guess_params

    taus_linspace = numpy.linspace(min_precession_time, max_precession_time,
                          num=1000)

    fig_fit, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.plot(taus, norm_avg_sig,'b',label='data')
    ax.plot(taus_linspace, tool_belt.cosine_sum(taus_linspace,*popt),'r',label='fit')
    ax.set_xlabel('Free precesion time (us)')
    ax.set_ylabel('Contrast (arb. units)')
    ax.legend()
    text1 = "\n".join((r'$C + e^{-t/d} [a_1 \mathrm{cos}(2 \pi \nu_1 t) + a_2 \mathrm{cos}(2 \pi \nu_2 t) + a_3 \mathrm{cos}(2 \pi \nu_3 t)]$',
                       r'$d = $' + '%.2f'%(popt[1]) + ' us',
                       r'$\nu_1 = $' + '%.2f'%(popt[3]) + ' MHz',
                       r'$\nu_2 = $' + '%.2f'%(popt[5]) + ' MHz',
                       r'$\nu_3 = $' + '%.2f'%(popt[7]) + ' MHz'
                       ))
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)

    ax.text(0.40, 0.25, text1, transform=ax.transAxes, fontsize=12,
                            verticalalignment="top", bbox=props)



# %% Plot the data itself and the fitted curve

    fig_fit.canvas.draw()
#    fig.set_tight_layout(True)
    fig_fit.canvas.flush_events()

    # Save the file in the same file directory
    tool_belt.save_figure(fig_fit, file_path + '_fit')
