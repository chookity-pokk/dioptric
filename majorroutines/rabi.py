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

# %% Main


def main(cxn, nv_sig, nd_filter, apd_indices,
         uwave_freq, uwave_power, uwave_time_range, do_uwave_gate_number,
         num_steps, num_reps, num_runs, name='untitled'):

    # %% Get the starting time of the function

    startFunctionTime = time.time()

    # %% Initial calculations and setup
    
    # Set which signal generator to use. 0 is the tektronix, 1 is HP
    do_uwave_gate = do_uwave_gate_number
    
    if do_uwave_gate == 0:
        do_uwave_gen = 'Tektronix'
    elif do_uwave_gate == 1:
        do_uwave_gen = 'HP'
    
    # Sequence prep (times are in ns)
    polarization_time = 3 * 10**3
    reference_time = 1 * 10**3
    signal_wait_time = 1 * 10**3
    reference_wait_time = 2 * 10**3
    background_wait_time = 1 * 10**3
    aom_delay_time = 750
    gate_time = 450
    uwave_delay= 40  # Delay between pulse and microwave gate open
    file_name = os.path.basename(__file__)

    # Array of times to sweep through
    # Must be ints since the pulse streamer only works with int64s
    min_uwave_time = uwave_time_range[0]
    max_uwave_time = uwave_time_range[1]
    taus = numpy.linspace(min_uwave_time, max_uwave_time,
                          num=num_steps, dtype=numpy.int32)

    # Set up our data structure, an array of NaNs that we'll fill
    # incrementally. NaNs are ignored by matplotlib, which is why they're
    # useful for us here.
    # We define 2D arrays, with the horizontal dimension for the frequency and
    # the veritical dimension for the index of the run.
    sig_counts = numpy.empty([num_runs, num_steps], dtype=numpy.uint32)
    sig_counts[:] = numpy.nan
    ref_counts = numpy.copy(sig_counts)
    # norm_avg_sig = numpy.empty([num_runs, num_steps])
    
    # %% Make some lists and variables to save at the end
    
    opti_coords_list = []
    
    # Create a list of indices to step through the taus. This will be shuffled
    tau_ind_list = list(range(0, num_steps))

    # %% Set up the microwaves

    cxn.microwave_signal_generator.set_freq(uwave_freq)
    cxn.microwave_signal_generator.set_amp(uwave_power)
    cxn.microwave_signal_generator.uwave_on()

    # %% Collect the data

    # Start 'Press enter to stop...'
    tool_belt.init_safe_stop()

    for run_ind in range(num_runs):

        print('Run index: {}'. format(run_ind))
        
        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break
        
        # Optimize
        opti_coords = optimize.main(cxn, nv_sig, nd_filter, apd_indices)
        opti_coords_list.append(opti_coords)

        # Load the APD
        cxn.apd_tagger.start_tag_stream(apd_indices)
        
        # Shuffle the list of indices to use for stepping through the taus
        shuffle(tau_ind_list)     
        
        for tau_ind in tau_ind_list:
#        for tau_ind in range(len(taus)):
#            print('Tau: {} ns'. format(taus[tau_ind]))
            # Break out of the while if the user says stop
            if tool_belt.safe_stop():
                break

            # Stream the sequence
            args = [taus[tau_ind], polarization_time, reference_time,
                    signal_wait_time, reference_wait_time,
                    background_wait_time, aom_delay_time, uwave_delay,
                    gate_time, max_uwave_time,
                    apd_indices[0], do_uwave_gate]
            cxn.pulse_streamer.stream_immediate(file_name, num_reps, args, 1)

            # Get the counts
            new_counts = cxn.apd_tagger.read_counter_separate_gates(1)
            
            sample_counts = new_counts[0]
            
            # signal counts are even - get every second element starting from 0
            sig_gate_counts = sample_counts[0::2]
            sig_counts[run_ind, tau_ind] = sum(sig_gate_counts)
            
            # ref counts are odd - sample_counts every second element starting from 1
            ref_gate_counts = sample_counts[1::2]  
            ref_counts[run_ind, tau_ind] = sum(ref_gate_counts)
            
        cxn.apd_tagger.stop_tag_stream()

    # %% Hardware clean up

    cxn.microwave_signal_generator.uwave_off()
    cxn.apd_tagger.stop_tag_stream()

    # %% Average the counts over the iterations

    avg_sig_counts = numpy.average(sig_counts, axis=0)
    avg_ref_counts = numpy.average(ref_counts, axis=0)

    # %% Calculate the Rabi data, signal / reference over different Tau

    norm_avg_sig = avg_sig_counts / avg_ref_counts

    # %% Fit the data and extract piPulse
    
    fit_func = tool_belt.cosexp

    # Estimated fit parameters
    offset = 0.90
    amplitude = 0.10
    frequency = 1/100
#    phase = 0
    decay = 1000

#    init_params = [offset, amplitude, frequency, phase, decay]
    init_params = [offset, amplitude, frequency, decay]

    try:
        opti_params, cov_arr = curve_fit(fit_func, taus, norm_avg_sig,
                                         p0=init_params)
    except Exception:
        print('Rabi fit failed - using guess parameters.')
        opti_params = init_params

    rabi_period = 1 / opti_params[2]

    # %% Plot the Rabi signal

    raw_fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))

    ax = axes_pack[0]
    ax.plot(taus, avg_sig_counts, 'r-')
    ax.plot(taus, avg_ref_counts, 'g-')
    # ax.plot(tauArray, countsBackground, 'o-')
    ax.set_xlabel('rf time (ns)')
    ax.set_ylabel('Counts')

    ax = axes_pack[1]
    ax.plot(taus , norm_avg_sig, 'b-')
    ax.set_title('Normalized Signal With Varying Microwave Duration')
    ax.set_xlabel('Microwave duration (ns)')
    ax.set_ylabel('Contrast (arb. units)')

    raw_fig.canvas.draw()
    # fig.set_tight_layout(True)
    raw_fig.canvas.flush_events()

    # %% Plot the data itself and the fitted curve

    linspaceTau = numpy.linspace(min_uwave_time, max_uwave_time, num=1000)

    fit_fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.plot(taus, norm_avg_sig,'bo',label='data')
    ax.plot(linspaceTau, fit_func(linspaceTau, *opti_params), 'r-', label='fit')
    ax.set_xlabel('Microwave duration (ns)')
    ax.set_ylabel('Contrast (arb. units)')
    ax.set_title('Rabi Oscillation Of NV Center Electron Spin')
    ax.legend()
    text = '\n'.join((r'$C + A_0 e^{-t/d} \mathrm{cos}(2 \pi \nu t + \phi)$',
                      r'$C = $' + '%.3f'%(opti_params[0]),
                      r'$A_0 = $' + '%.3f'%(opti_params[1]),
                      r'$\frac{1}{\nu} = $' + '%.1f'%(rabi_period) + ' ns',
                      r'$d = $' + '%i'%(opti_params[3]) + ' ' + r'$ ns$'))


    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.55, 0.25, text, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)

    fit_fig.canvas.draw()
    # fig.set_tight_layout(True)
    fit_fig.canvas.flush_events()

    # %% Save the data

    endFunctionTime = time.time()

    timeElapsed = endFunctionTime - startFunctionTime

    timestamp = tool_belt.get_time_stamp()

    raw_data = {'timestamp': timestamp,
                'timeElapsed': timeElapsed,
                'timeElapsed-units': 's',
                'name': name,
                'nv_sig': nv_sig,
                'nv_sig-units': tool_belt.get_nv_sig_units(),
                'nv_sig-format': tool_belt.get_nv_sig_format(),
                'opti_coords_list': opti_coords_list,
                'opti_coords_list-units': 'V',
                'nd_filter': nd_filter,
                'uwave_freq': uwave_freq,
                'uwave_freq-units': 'GHz',
                'uwave_power': uwave_power,
                'uwave_power-units': 'dBm',
                'uwave_time_range': uwave_time_range,
                'uwave_time_range-units': 'ns',
                'do_uwave_gen': do_uwave_gen,
                'num_steps': num_steps,
                'num_reps': num_reps,
                'num_runs': num_runs,
                'sig_counts': sig_counts.astype(int).tolist(),
                'sig_counts-units': 'counts',
                'ref_counts': ref_counts.astype(int).tolist(),
                'ref_counts-units': 'counts',
                'norm_avg_sig': norm_avg_sig.astype(float).tolist(),
                'norm_avg_sig-units': 'arb'}

    file_path = tool_belt.get_file_path(__file__, timestamp, name)
    tool_belt.save_figure(raw_fig, file_path)
    tool_belt.save_figure(fit_fig, file_path + '_fit')
    tool_belt.save_raw_data(raw_data, file_path)

    # %% Return integer value for pi pulse

    return rabi_period // 2
