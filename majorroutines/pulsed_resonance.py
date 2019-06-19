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
import matplotlib.pyplot as plt


# %% Main


def main(cxn, nv_sig, nd_filter, apd_indices, freq_center, freq_range,
         num_steps, num_reps, num_runs, uwave_power, pi_pulse,
         name='untitled'):

    # %% Initial calculations and setup

    # Calculate the frequencies we need to set
    half_freq_range = freq_range / 2
    freq_low = freq_center - half_freq_range
    freq_high = freq_center + half_freq_range
    freqs = numpy.linspace(freq_low, freq_high, num_steps)

    # Set up our data structure, an array of NaNs that we'll fill
    # incrementally. NaNs are ignored by matplotlib, which is why they're
    # useful for us here.
    # We define 2D arrays, with the horizontal dimension for the frequency and
    # the veritical dimension for the index of the run.
    ref_counts = numpy.empty([num_runs, num_steps])
    ref_counts[:] = numpy.nan
    sig_counts = numpy.copy(ref_counts)
    
    # Define some times for the sequence (in ns)
    polarization_time = 3 * 10**3
    reference_time = 1 * 10**3
    signal_wait_time = 1 * 10**3
    reference_wait_time = 2 * 10**3
    background_wait_time = 1 * 10**3
    aom_delay_time = 750
    readout = 450
    readout_sec = readout // (10**9)
    uwave_delay = 40  # Delay between pulse and microwave gate open
    sequence_args = [pi_pulse, polarization_time, reference_time,
                    signal_wait_time, reference_wait_time,
                    background_wait_time, aom_delay_time, uwave_delay,
                    readout, pi_pulse,
                    apd_indices[0], 0]
    
    opti_coords_list = []

    # %% Collect the data

    # Start 'Press enter to stop...'
    tool_belt.init_safe_stop()

    for run_ind in range(num_runs):
        print('Run index: {}'. format(run_ind))

        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break
        
        # Optimize and save the coords we found
        opti_coords = optimize.main(cxn, nv_sig, nd_filter, apd_indices)
        opti_coords_list.append(opti_coords)
        
        # Load the pulse streamer (must happen after optimize since optimize
        # loads its own sequence)
        cxn.pulse_streamer.stream_load('rabi.py', sequence_args, 1)

        # Start the tagger stream
        cxn.apd_tagger.start_tag_stream(apd_indices)

        # Take a sample and increment the frequency
        for step_ind in range(num_steps):

            # Break out of the while if the user says stop
            if tool_belt.safe_stop():
                break

            cxn.microwave_signal_generator.set_freq(freqs[step_ind])

            # If this is the first sample then we have to enable the signal
            if (run_ind == 0) and (step_ind == 0):
                cxn.microwave_signal_generator.set_amp(uwave_power)
                cxn.microwave_signal_generator.uwave_on()

            # Start the timing stream
            cxn.pulse_streamer.stream_start(num_reps)

            # Get the counts
            new_counts = cxn.apd_tagger.read_counter_separate_gates(1)
            print(new_counts)
            
            sample_counts = new_counts[0]
            
            # signal counts are even - get every second element starting from 0
            sig_gate_counts = sample_counts[0::2]
            sig_counts[run_ind, step_ind] = sum(sig_gate_counts)
            
            # ref counts are odd - sample_counts every second element starting from 1
            ref_gate_counts = sample_counts[1::2]
            ref_counts[run_ind, step_ind] = sum(ref_gate_counts)

        cxn.apd_tagger.stop_tag_stream()

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

    cxn.microwave_signal_generator.uwave_off()
    cxn.apd_tagger.stop_tag_stream()

    timestamp = tool_belt.get_time_stamp()

    rawData = {'timestamp': timestamp,
               'name': name,
               'nv_sig': nv_sig,
               'nv_sig-units': tool_belt.get_nv_sig_units(),
               'nv_sig-format': tool_belt.get_nv_sig_format(),
               'opti_coords_list': opti_coords_list,
               'opti_coords_list-units': 'V',
               'nd_filter': nd_filter,
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
               'uwave_delay': uwave_delay,
               'uwave_delay-units': 'ns',
               'sig_counts': sig_counts.astype(int).tolist(),
               'sig_counts-units': 'counts',
               'ref_counts': ref_counts.astype(int).tolist(),
               'ref_counts-units': 'counts',
               'norm_avg_sig': norm_avg_sig.astype(float).tolist(),
               'norm_avg_sig-units': 'arb'}

    filePath = tool_belt.get_file_path(__file__, timestamp, name)
    tool_belt.save_figure(fig, filePath)
    tool_belt.save_raw_data(rawData, filePath)
