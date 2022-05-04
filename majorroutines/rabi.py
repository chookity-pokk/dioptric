# -*- coding: utf-8 -*-
"""
Rabi flopping routine. Sweeps the pulse duration of a fixed uwave frequency.

Created on Tue Apr 23 11:49:23 2019

@author: mccambria
"""


# %% Imports


import utils.tool_belt as tool_belt
import majorroutines.optimize as optimize
import numpy
import os
import time
import matplotlib.pyplot as plt
from random import shuffle
from scipy.optimize import curve_fit
import labrad


# %% Functions


def fit_data(uwave_time_range, num_steps, norm_avg_sig):

    # %% Set up

    min_uwave_time = uwave_time_range[0]
    max_uwave_time = uwave_time_range[1]
    taus, tau_step = numpy.linspace(min_uwave_time, max_uwave_time,
                            num=num_steps, dtype=numpy.int32, retstep=True)

    fit_func = tool_belt.cosexp_1_at_0

    # %% Estimated fit parameters

    offset = numpy.average(norm_avg_sig)
    decay = 1000

    # To estimate the frequency let's find the highest peak in the FFT
    transform = numpy.fft.rfft(norm_avg_sig)
    freqs = numpy.fft.rfftfreq(num_steps, d=tau_step)
    transform_mag = numpy.absolute(transform)
    # [1:] excludes frequency 0 (DC component)
    max_ind = numpy.argmax(transform_mag[1:])
    frequency = freqs[max_ind + 1]

    # %% Fit

    init_params = [offset, frequency, decay]

    try:
        popt, _ = curve_fit(fit_func, taus, norm_avg_sig,
                            p0=init_params)
    except Exception as e:
        print(e)
        popt = None

    return fit_func, popt

def create_fit_figure(uwave_time_range, uwave_freq, num_steps, norm_avg_sig,
                      fit_func, popt):

    min_uwave_time = uwave_time_range[0]
    max_uwave_time = uwave_time_range[1]
    taus = numpy.linspace(min_uwave_time, max_uwave_time,
                          num=num_steps, dtype=numpy.int32)
    linspaceTau = numpy.linspace(min_uwave_time, max_uwave_time, num=1000)

    fit_fig, ax = plt.subplots(figsize=(8.5, 8.5))
    ax.plot(taus, norm_avg_sig,'bo',label='data')
    ax.plot(linspaceTau, fit_func(linspaceTau, *popt), 'r-', label='fit')
    ax.set_xlabel('Microwave duration (ns)')
    ax.set_ylabel('Contrast (arb. units)')
    ax.set_title('Rabi Oscillation Of NV Center Electron Spin')
    ax.legend()
    text_freq = 'Resonant frequency:' + '%.3f'%(uwave_freq) + 'GHz'

    A_0 = 1- popt[0]

    text_popt = '\n'.join((r'$C + A_0 e^{-t/d} \mathrm{cos}(2 \pi \nu t + \phi)$',
                      r'$C = $' + '%.3f'%(popt[0]),
                      r'$A_0 = $' + '%.3f'%(A_0),
                      r'$\frac{1}{\nu} = $' + '%.1f'%(1/popt[1]) + ' ns',
                      r'$d = $' + '%i'%(popt[2]) + ' ' + r'$ ns$'))

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.55, 0.25, text_popt, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)
    ax.text(0.55, 0.3, text_freq, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)

    fit_fig.canvas.draw()
    fit_fig.set_tight_layout(True)
    fit_fig.canvas.flush_events()

    return fit_fig

def simulate(uwave_time_range, freq, resonant_freq, contrast,
             measured_rabi_period=None, resonant_rabi_period=None):

    if measured_rabi_period is None:
        resonant_rabi_freq = resonant_rabi_period**-1
        res_dev = freq - resonant_freq
        measured_rabi_freq = numpy.sqrt(res_dev**2 + resonant_rabi_freq**2)
        measured_rabi_period = measured_rabi_freq**-1
        print('measured_rabi_period: {} ns'.format(measured_rabi_period))
    elif resonant_rabi_period is None:
        measured_rabi_freq = measured_rabi_period**-1
        res_dev = freq-resonant_freq
        resonant_rabi_freq = numpy.sqrt(measured_rabi_freq**2 - res_dev**2)
        resonant_rabi_period = resonant_rabi_freq**-1
        print('resonant_rabi_period: {} ns'.format(resonant_rabi_period))
    else:
        raise RuntimeError('Pass either a measured_rabi_period or a ' \
                           'resonant_rabi_period, not both/neither.')

    min_uwave_time = uwave_time_range[0]
    max_uwave_time = uwave_time_range[1]
    smooth_taus = numpy.linspace(min_uwave_time, max_uwave_time,
                          num=1000, dtype=numpy.int32)
    amp = (resonant_rabi_freq / measured_rabi_freq)**2
    angle = measured_rabi_freq * 2 * numpy.pi * smooth_taus / 2
    prob = amp * (numpy.sin(angle))**2

    rel_counts = 1.0 - (contrast * prob)

    fig, ax = plt.subplots(figsize=(8.5, 8.5))
    ax.plot(smooth_taus, rel_counts)
    ax.set_xlabel('Tau (ns)')
    ax.set_ylabel('Contrast (arb. units)')

# def simulate_split(uwave_time_range, freq,
#                    res_freq_low, res_freq_high, contrast, rabi_period):

#     rabi_freq = rabi_period**-1

#     min_uwave_time = uwave_time_range[0]
#     max_uwave_time = uwave_time_range[1]
#     smooth_taus = numpy.linspace(min_uwave_time, max_uwave_time,
#                           num=1000, dtype=numpy.int32)

#     omega = numpy.sqrt((freq-res_freq)**2 + rabi_freq**2)
#     amp = (rabi_freq / omega)**2
#     angle = omega * 2 * numpy.pi * smooth_taus / 2
#     prob = amp * (numpy.sin(angle))**2

#     rel_counts = 1.0 - (contrast * prob)

#     fig, ax = plt.subplots(figsize=(8.5, 8.5))
#     ax.plot(smooth_taus, rel_counts)
#     ax.set_xlabel('Tau (ns)')
#     ax.set_ylabel('Contrast (arb. units)')


# %% Main


def main(nv_sig, apd_indices, uwave_time_range, state,
         num_steps, num_reps, num_runs, opti_nv_sig = None):

    with labrad.connect() as cxn:
        rabi_per, sig_counts, ref_counts = main_with_cxn(cxn, nv_sig, 
                                         apd_indices, uwave_time_range, state,
                                         num_steps, num_reps, num_runs, opti_nv_sig)

        return rabi_per


def main_with_cxn(cxn, nv_sig, apd_indices, uwave_time_range, state,
                  num_steps, num_reps, num_runs, opti_nv_sig = None):

    tool_belt.reset_cfm(cxn)

    # %% Get the starting time of the function, to be used to calculate run time

    startFunctionTime = time.time()
    start_timestamp = tool_belt.get_time_stamp()

    # %% Initial calculations and setup

    uwave_freq = nv_sig['resonance_{}'.format(state.name)]
    uwave_power = nv_sig['uwave_power_{}'.format(state.name)]
    
    laser_key = 'spin_laser'
    laser_name = nv_sig[laser_key]
    tool_belt.set_filter(cxn, nv_sig, laser_key)
    laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)

    polarization_time = nv_sig['spin_pol_dur']
    readout = nv_sig['spin_readout_dur']
    readout_sec = readout / (10**9)

    # Array of times to sweep through
    # Must be ints since the pulse streamer only works with int64s
    min_uwave_time = uwave_time_range[0]
    max_uwave_time = uwave_time_range[1]
    taus = numpy.linspace(min_uwave_time, max_uwave_time,
                          num=num_steps, dtype=numpy.int32)

    # Analyze the sequence
    num_reps = int(num_reps)
    file_name = os.path.basename(__file__)
    seq_args = [taus[0], polarization_time,
                readout, max_uwave_time, apd_indices[0], 
                state.value, laser_name, laser_power]
#    for arg in seq_args:
#        print(type(arg))
#    print(seq_args)
#    return
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    cxn.pulse_streamer.stream_load(file_name, seq_args_string)

    # Set up our data structure, an array of NaNs that we'll fill
    # incrementally. NaNs are ignored by matplotlib, which is why they're
    # useful for us here.
    # We define 2D arrays, with the horizontal dimension for the frequency and
    # the veritical dimension for the index of the run.
    sig_counts = numpy.empty([num_runs, num_steps], dtype=numpy.float32)
    sig_counts[:] = numpy.nan
    ref_counts = numpy.copy(sig_counts)
    # norm_avg_sig = numpy.empty([num_runs, num_steps])

    # %% Make some lists and variables to save at the end

    opti_coords_list = []
    tau_index_master_list = [[] for i in range(num_runs)]

    # Create a list of indices to step through the taus. This will be shuffled
    tau_ind_list = list(range(0, num_steps))

    # %% Collect the data

    # Start 'Press enter to stop...'
    tool_belt.init_safe_stop()
    for run_ind in range(num_runs):

        print('Run index: {}'. format(run_ind))

        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break

        # Optimize and save the coords we found
        if opti_nv_sig:
            opti_coords = optimize.main_with_cxn(cxn, opti_nv_sig, apd_indices)
            drift = tool_belt.get_drift()
            adj_coords = nv_sig['coords'] + numpy.array(drift)
            tool_belt.set_xyz(cxn, adj_coords)
        else:
            opti_coords = optimize.main_with_cxn(cxn, nv_sig, apd_indices)
        opti_coords_list.append(opti_coords)
            
        tool_belt.set_filter(cxn, nv_sig, "spin_laser")
        laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)

        # Apply the microwaves
        sig_gen_cxn = tool_belt.get_signal_generator_cxn(cxn, state)
        sig_gen_cxn.set_freq(uwave_freq)
        sig_gen_cxn.set_amp(uwave_power)
        # sig_gen_cxn.load_iq()
        sig_gen_cxn.uwave_on()
        # cxn.arbitrary_waveform_generator.iq_switch()

        # TEST for split resonance
#        sig_gen_cxn = cxn.signal_generator_bnc835
#        sig_gen_cxn.set_freq(uwave_freq + 0.008)
#        sig_gen_cxn.set_amp(uwave_power)
#        sig_gen_cxn.uwave_on()
        
    
        seq_args = [taus[0], polarization_time,
                    readout, max_uwave_time, apd_indices[0], 
                    state.value, laser_name, laser_power]
        seq_args_string = tool_belt.encode_seq_args(seq_args)
        ret_vals = cxn.pulse_streamer.stream_load(
            "rabi.py", seq_args_string
        )
        period = ret_vals[0]
                
        # Start the tagger stream 
        apd_server = tool_belt.get_apd_server(cxn)
        apd_server_name = tool_belt.get_registry_entry(cxn, "apd_server", ["", "Config", "Counter"])

        if apd_server_name == 'apd_tagger':
            apd_server.start_tag_stream(apd_indices)
            n_apd_samples = 1
        elif apd_server_name == 'apd_daq':
            apd_server.load_stream_reader(apd_indices[0], period,  int(2*num_reps*num_steps))#put the total number of samples you expect for this run
            n_apd_samples = int(2*num_reps)
        

        # Shuffle the list of indices to use for stepping through the taus
        shuffle(tau_ind_list)

#        start_time = time.time()
        for tau_ind in tau_ind_list:
#        for tau_ind in range(len(taus)):
#            print('Tau: {} ns'. format(taus[tau_ind]))
            # Break out of the while if the user says stop
            if tool_belt.safe_stop():
                break
#            print(taus[tau_ind])
            # add the tau indexxes used to a list to save at the end
            tau_index_master_list[run_ind].append(tau_ind)
            # Stream the sequence
            seq_args = [taus[tau_ind], polarization_time,
                        readout, max_uwave_time, apd_indices[0], 
                        state.value, laser_name, laser_power]
            seq_args_string = tool_belt.encode_seq_args(seq_args)
            # Clear the tagger buffer of any excess counts
            apd_server.clear_buffer()
            cxn.pulse_streamer.stream_immediate(file_name, num_reps,
                                                seq_args_string)

            # Get the counts
            new_counts = apd_server.read_counter_separate_gates(n_apd_samples)
#            print(new_counts)

            sample_counts = new_counts[0]

            # signal counts are even - get every second element starting from 0
            sig_gate_counts = sample_counts[0::2]
            sig_counts[run_ind, tau_ind] = sum(sig_gate_counts)
#            print('Sig counts: {}'.format(sum(sig_gate_counts)))

            # ref counts are odd - sample_counts every second element starting from 1
            ref_gate_counts = sample_counts[1::2]
            ref_counts[run_ind, tau_ind] = sum(ref_gate_counts)
#            print('Ref counts: {}'.format(sum(ref_gate_counts)))

#            run_time = time.time()
#            run_elapsed_time = run_time - start_time
#            start_time = run_time
#            print('Tau: {} ns'.format(taus[tau_ind]))
#            print('Elapsed time {}'.format(run_elapsed_time))
        apd_server.stop_tag_stream()

        # %% Save the data we have incrementally for long measurements

        raw_data = {'start_timestamp': start_timestamp,
                    'nv_sig': nv_sig,
                    'nv_sig-units': tool_belt.get_nv_sig_units(),
                    'uwave_freq': uwave_freq,
                    'uwave_freq-units': 'GHz',
                    'uwave_power': uwave_power,
                    'uwave_power-units': 'dBm',
                    'uwave_time_range': uwave_time_range,
                    'uwave_time_range-units': 'ns',
                    'state': state.name,
                    'num_steps': num_steps,
                    'num_reps': num_reps,
                    'num_runs': num_runs,
                    'tau_index_master_list':tau_index_master_list,
                    'opti_coords_list': opti_coords_list,
                    'opti_coords_list-units': 'V',
                    'sig_counts': sig_counts.astype(int).tolist(),
                    'sig_counts-units': 'counts',
                    'ref_counts': ref_counts.astype(int).tolist(),
                    'ref_counts-units': 'counts'}

        # This will continuously be the same file path so we will overwrite
        # the existing file with the latest version
#        file_path = tool_belt.get_file_path(__file__, start_timestamp,
#                                            nv_sig['name'], 'incremental')
#        tool_belt.save_raw_data(raw_data, file_path)

    # %% Average the counts over the iterations

    avg_sig_counts = numpy.average(sig_counts, axis=0)
    avg_ref_counts = numpy.average(ref_counts, axis=0)

    # %% Calculate the Rabi data, signal / reference over different Tau

    norm_avg_sig = avg_sig_counts / avg_ref_counts

    # %% Fit the data and extract piPulse

    fit_func, popt = fit_data(uwave_time_range, num_steps, norm_avg_sig)

    # %% Plot the Rabi signal

    raw_fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))

    ax = axes_pack[0]
    ax.plot(taus, avg_sig_counts, 'r-', label = 'signal')
    ax.plot(taus, avg_ref_counts, 'g-', label = 'refernece')
    # ax.plot(tauArray, countsBackground, 'o-')
    ax.set_xlabel('rf time (ns)')
    ax.set_ylabel('Counts')
    ax.legend()

    ax = axes_pack[1]
    ax.plot(taus , norm_avg_sig, 'b-')
    ax.set_title('Normalized Signal With Varying Microwave Duration')
    ax.set_xlabel('Microwave duration (ns)')
    ax.set_ylabel('Contrast (arb. units)')

    raw_fig.canvas.draw()
    raw_fig.set_tight_layout(True)
    raw_fig.canvas.flush_events()

    # %% Plot the data itself and the fitted curve

    fit_fig = None
    if (fit_func is not None) and (popt is not None):
        fit_fig = create_fit_figure(uwave_time_range, uwave_freq, num_steps,
                                    norm_avg_sig, fit_func, popt)
        rabi_period = 1/popt[1]
        print('Rabi period measured: {} ns\n'.format('%.1f'%rabi_period))

    # %% Clean up and save the data

    tool_belt.reset_cfm(cxn)

    endFunctionTime = time.time()

    timeElapsed = endFunctionTime - startFunctionTime

    timestamp = tool_belt.get_time_stamp()

    raw_data = {'timestamp': timestamp,
                'timeElapsed': timeElapsed,
                'timeElapsed-units': 's',
                'nv_sig': nv_sig,
                'nv_sig-units': tool_belt.get_nv_sig_units(),
                'uwave_freq': uwave_freq,
                'uwave_freq-units': 'GHz',
                'uwave_power': uwave_power,
                'uwave_power-units': 'dBm',
                'uwave_time_range': uwave_time_range,
                'uwave_time_range-units': 'ns',
                'state': state.name,
                'num_steps': num_steps,
                'num_reps': num_reps,
                'num_runs': num_runs,
                'tau_index_master_list':tau_index_master_list,
                'opti_coords_list': opti_coords_list,
                'opti_coords_list-units': 'V',
                'sig_counts': sig_counts.astype(int).tolist(),
                'sig_counts-units': 'counts',
                'ref_counts': ref_counts.astype(int).tolist(),
                'ref_counts-units': 'counts',
                'norm_avg_sig': norm_avg_sig.astype(float).tolist(),
                'norm_avg_sig-units': 'arb'}

#    file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
#    tool_belt.save_figure(raw_fig, file_path)
#    if fit_fig is not None:
#        tool_belt.save_figure(fit_fig, file_path + '-fit')
#    tool_belt.save_raw_data(raw_data, file_path)

    if (fit_func is not None) and (popt is not None):
        return rabi_period, sig_counts, ref_counts
    else:
        return None, sig_counts, ref_counts


# %% Run the file


if __name__ == '__main__':

    path = 'pc_hahn/branch_cryo-setup/rabi/2021_03'
    file = '2021_03_06-16_07_29-johnson-nv14_2021_02_26'
    data = tool_belt.get_raw_data(path, file)

    norm_avg_sig = data['norm_avg_sig']
    uwave_time_range = data['uwave_time_range']
    num_steps = data['num_steps']
    uwave_freq = data['uwave_freq']

    fit_func, popt = fit_data(uwave_time_range, num_steps, norm_avg_sig)
    if (fit_func is not None) and (popt is not None):
        create_fit_figure(uwave_time_range, uwave_freq, num_steps,
                          norm_avg_sig, fit_func, popt)

    # simulate([0,250], 2.8268, 2.8288, 0.43, measured_rabi_period=197)
