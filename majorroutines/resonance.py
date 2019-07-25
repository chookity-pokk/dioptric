# -*- coding: utf-8 -*-
"""
Electron spin resonance routine. Scans the microwave frequency, taking counts
at each point.

Created on Thu Apr 11 15:39:23 2019

@author: mccambria
"""


# %% Imports


import utils.tool_belt as tool_belt
import majorroutines.optimize as optimize
import numpy
import os
import matplotlib.pyplot as plt
import labrad


# %% Main


def main(nv_sig, apd_indices, freq_center, freq_range,
         num_steps, num_runs, uwave_power):

    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig, apd_indices, freq_center, freq_range,
                      num_steps, num_runs, uwave_power)

def main_with_cxn(cxn, nv_sig, apd_indices, freq_center, freq_range,
                  num_steps, num_runs, uwave_power):

    # %% Initial calculations and setup
    
    tool_belt.reset_cfm(cxn)

    # Set up for the pulser - we can't load the sequence yet until after 
    # optimize runs since optimize loads its own sequence
    shared_parameters = tool_belt.get_shared_parameters_dict(cxn)
    readout = shared_parameters['continuous_readout_dur']
    readout_sec = readout / (10**9)
    uwave_switch_delay = 1 * 10**6  # 1 ms to switch frequencies
    seq_args = [readout, uwave_switch_delay, apd_indices[0]]
    seq_args_string = tool_belt.encode_seq_args(seq_args)

    file_name = os.path.basename(__file__)

    # Calculate the frequencies we need to set
    half_freq_range = freq_range / 2
    freq_low = freq_center - half_freq_range
    freq_high = freq_center + half_freq_range
    freqs = numpy.linspace(freq_low, freq_high, num_steps)

    # Set up our data structure, an array of NaNs that we'll fill
    # incrementally. NaNs are ignored by matplotlib, which is why they're
    # useful for us here.
    counts = numpy.empty(num_steps)
    counts[:] = numpy.nan

    # Set up our data structure, an array of NaNs that we'll fill
    # incrementally. NaNs are ignored by matplotlib, which is why they're
    # useful for us here.
    # We define 2D arrays, with the horizontal dimension for the frequency and
    # the veritical dimension for the index of the run.
    ref_counts = numpy.empty([num_runs, num_steps])
    ref_counts[:] = numpy.nan
    sig_counts = numpy.copy(ref_counts)
        
    # %% Make some lists and variables to save at the end
    
#    passed_coords = coords
    
    opti_coords_list = []
#    optimization_success_list = []
    
    # %% Get the starting time of the function

    start_timestamp = tool_belt.get_time_stamp()

    # %% Collect the data

    # Start 'Press enter to stop...'
    tool_belt.init_safe_stop()

    for run_ind in range(num_runs):
        print('Run index: {}'. format(run_ind))

        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break
        
        # Optimize and save the coords we found
        opti_coords = optimize.main_with_cxn(cxn, nv_sig, apd_indices)
        opti_coords_list.append(opti_coords)

        # Load the APD task with two samples for each frequency step
        cxn.pulse_streamer.stream_load(file_name, seq_args_string)
        cxn.apd_tagger.start_tag_stream(apd_indices)

        # Take a sample and increment the frequency
        for step_ind in range(num_steps):

            # Break out of the while if the user says stop
            if tool_belt.safe_stop():
                break

            cxn.signal_generator_bnc835.set_freq(freqs[step_ind])
            cxn.signal_generator_bnc835.set_amp(uwave_power)
            cxn.signal_generator_bnc835.uwave_on()

            # Start the timing stream
            cxn.pulse_streamer.stream_start()

            new_counts = cxn.apd_tagger.read_counter_simple(2)
            if len(new_counts) != 2:
                raise RuntimeError('There should be exactly 2 samples per freq.')

            ref_counts[run_ind, step_ind] = new_counts[0]
            sig_counts[run_ind, step_ind] = new_counts[1]
            
        cxn.apd_tagger.stop_tag_stream()
        
        # %% Save the data we have incrementally for long measurements

        rawData = {'start_timestamp': start_timestamp,
                   'nv_sig': nv_sig,
                   'nv_sig-units': tool_belt.get_nv_sig_units(),
                   'opti_coords_list': opti_coords_list,
                   'opti_coords_list-units': 'V',
                   'freq_center': freq_center,
                   'freq_center-units': 'GHz',
                   'freq_range': freq_range,
                   'freq_range-units': 'GHz',
                   'num_steps': num_steps,
                   'num_runs': num_runs,
                   'uwave_power': uwave_power,
                   'uwave_power-units': 'dBm',
                   'readout': readout,
                   'readout-units': 'ns',
                   'uwave_switch_delay': uwave_switch_delay,
                   'uwave_switch_delay-units': 'ns',
                   'sig_counts': sig_counts.astype(int).tolist(),
                   'sig_counts-units': 'counts',
                   'ref_counts': ref_counts.astype(int).tolist(),
                   'ref_counts-units': 'counts'}

        # This will continuously be the same file path so we will overwrite
        # the existing file with the latest version
        file_path = tool_belt.get_file_path(__file__, start_timestamp,
                                            nv_sig['name'], 'incremental')
        tool_belt.save_raw_data(rawData, file_path)

    # %% Process and plot the data

    # Find the averages across runs
    avg_ref_counts = numpy.average(ref_counts, axis=0)
    avg_sig_counts = numpy.average(sig_counts, axis=0)
    norm_avg_sig = avg_sig_counts / avg_ref_counts

    # Convert to kilocounts per second
    kcps_uwave_off_avg = (avg_ref_counts / (10**3)) / readout_sec
    kcpsc_uwave_on_avg = (avg_sig_counts / (10**3)) / readout_sec

    # Create an image with 2 plots on one row, with a specified size
    # Then draw the canvas and flush all the previous plots from the canvas
    fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))

    # The first plot will display both the uwave_off and uwave_off counts
    ax = axes_pack[0]
    ax.plot(freqs, kcps_uwave_off_avg, 'r-', label = 'Reference')
    ax.plot(freqs, kcpsc_uwave_on_avg, 'g-', label = 'Signal')
    ax.set_title('Non-normalized Count Rate Versus Frequency')
    ax.set_xlabel('Frequency (GHz)')
    ax.set_ylabel('Count rate (kcps)')
    ax.legend()
    # The second plot will show their subtracted values
    ax = axes_pack[1]
    ax.plot(freqs, norm_avg_sig, 'b-')
    ax.set_title('Normalized Count Rate vs Frequency')
    ax.set_xlabel('Frequency (GHz)')
    ax.set_ylabel('Contrast (arb. units)')

    fig.canvas.draw()
    fig.tight_layout()
    fig.canvas.flush_events()

    # %% Clean up and save the data
    
    tool_belt.reset_cfm(cxn)

    timestamp = tool_belt.get_time_stamp()

    rawData = {'timestamp': timestamp,
               'nv_sig': nv_sig,
               'nv_sig-units': tool_belt.get_nv_sig_units(),
               'opti_coords_list': opti_coords_list,
               'opti_coords_list-units': 'V',
               'freq_center': freq_center,
               'freq_center-units': 'GHz',
               'freq_range': freq_range,
               'freq_range-units': 'GHz',
               'num_steps': num_steps,
               'num_runs': num_runs,
               'uwave_power': uwave_power,
               'uwave_power-units': 'dBm',
               'readout': readout,
               'readout-units': 'ns',
               'uwave_switch_delay': uwave_switch_delay,
               'uwave_switch_delay-units': 'ns',
               'sig_counts': sig_counts.astype(int).tolist(),
               'sig_counts-units': 'counts',
               'ref_counts': ref_counts.astype(int).tolist(),
               'ref_counts-units': 'counts',
               'norm_avg_sig': norm_avg_sig.astype(float).tolist(),
               'norm_avg_sig-units': 'arb'}

    filePath = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
    tool_belt.save_figure(fig, filePath)
    tool_belt.save_raw_data(rawData, filePath)
