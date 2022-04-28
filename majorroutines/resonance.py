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
import labrad
from utils.tool_belt import States
from majorroutines import pulsed_resonance 
from random import shuffle


# %% Main


def main(nv_sig, apd_indices, freq_center, freq_range,
         num_steps, num_runs, uwave_power, state=States.LOW, opti_nv_sig = None):

    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig, apd_indices, freq_center, freq_range,
                      num_steps, num_runs, uwave_power, state, opti_nv_sig)

def main_with_cxn(cxn, nv_sig, apd_indices, freq_center, freq_range,
                  num_steps, num_runs, uwave_power, state=States.LOW, opti_nv_sig = None):

    # %% Initial calculations and setup

#    tool_belt.reset_cfm(cxn)
    
    # Set up the laser
    laser_key = 'spin_laser'
    laser_name = nv_sig[laser_key]
    laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)

    # Since this is CW we need the imaging readout rather than the spin 
    # readout typically used for state detection
    readout = nv_sig['imaging_readout_dur']  
    readout_sec = readout / (10**9)
    
    file_name = 'resonance.py'
    seq_args = [readout, state.value, laser_name, laser_power, apd_indices[0]]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    # print(seq_args)
    # return

    # Calculate the frequencies we need to set
    half_freq_range = freq_range / 2
    freq_low = freq_center - half_freq_range
    freq_high = freq_center + half_freq_range
    freqs = numpy.linspace(freq_low, freq_high, num_steps)
    freq_ind_list = list(range(num_steps))
    freq_ind_master_list = []

    # Set up our data structure, an array of NaNs that we'll fill
    # incrementally. NaNs are ignored by matplotlib, which is why they're
    # useful for us here.
    # counts = numpy.empty(num_steps)
    # counts[:] = numpy.nan

    # Set up our data structure, an array of NaNs that we'll fill
    # incrementally. NaNs are ignored by matplotlib, which is why they're
    # useful for us here.
    # We define 2D arrays, with the horizontal dimension for the frequency and
    # the veritical dimension for the index of the run.
    ref_counts = numpy.empty([num_runs, num_steps])
    ref_counts[:] = numpy.nan
    sig_counts = numpy.copy(ref_counts)

    opti_coords_list = []

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
        if opti_nv_sig:
            opti_coords = optimize.main_with_cxn(cxn, opti_nv_sig, apd_indices)
            drift = tool_belt.get_drift()
            adj_coords = nv_sig['coords'] + numpy.array(drift)
            tool_belt.set_xyz(cxn, adj_coords)
        else:
            opti_coords = optimize.main_with_cxn(cxn, nv_sig, apd_indices)
        opti_coords_list.append(opti_coords)
        
        # Laser setup
        tool_belt.set_filter(cxn, nv_sig, laser_key)
        laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)
        # Start the laser now to get rid of transient effects
        tool_belt.laser_on(cxn, laser_name, laser_power)
    
        sig_gen_cxn = tool_belt.get_signal_generator_cxn(cxn, state)
        sig_gen_cxn.set_amp(uwave_power)
        sig_gen_cxn.uwave_on()
        
        #load the pulse streamer
        ret_vals= cxn.pulse_streamer.stream_load(file_name, seq_args_string)
        period = ret_vals[0]
        
        # Load the APD task with two samples for each frequency step
        apd_server = tool_belt.get_apd_server(cxn)
        apd_server_name = tool_belt.get_registry_entry(cxn, "apd_server", ["", "Config", "Counter"])
        if apd_server_name == 'apd_tagger':
            apd_server.start_tag_stream(apd_indices)
        elif apd_server_name == 'apd_daq':
            apd_server.load_stream_reader(apd_indices[0], period,  2*num_steps)#put the total number of samples you expect for this run
        
        # Shuffle the list of frequency indices so that we step through
        # them randomly
        shuffle(freq_ind_list)
        freq_ind_master_list.append(freq_ind_list)

        # Take a sample and increment the frequency
        for step_ind in range(num_steps):

            # Break out of the while if the user says stop
            if tool_belt.safe_stop():
                break
            freq_ind = freq_ind_list[step_ind]
            # print(freqs[freq_ind])
            sig_gen_cxn.set_freq(freqs[freq_ind])

            # Start the timing stream
            apd_server.clear_buffer()
            cxn.pulse_streamer.stream_start() 

            # Read the counts using parity to distinguish signal vs ref
#            new_counts = apd_server.read_counter_simple(2)
#            print(new_counts)
            
            new_counts = apd_server.read_counter_separate_gates(2) #originally 1
#            print(new_counts)
            sample_counts = new_counts[0]
            ref_gate_counts = sample_counts[0::2]
            ref_counts[run_ind, freq_ind]  = sum(ref_gate_counts)

            sig_gate_counts = sample_counts[1::2]
            sig_counts[run_ind, freq_ind] = sum(sig_gate_counts)


        apd_server.stop_tag_stream()
        sig_gen_cxn.uwave_off()
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
                   'freq_ind_master_list': freq_ind_master_list,
                   'uwave_power': uwave_power,
                   'uwave_power-units': 'dBm',
                   'readout': readout,
                   'readout-units': 'ns',
                   'sig_counts': sig_counts.astype(int).tolist(),
                   'sig_counts-units': 'counts',
                   'ref_counts': ref_counts.astype(int).tolist(),
                   'ref_counts-units': 'counts'}

        # This will continuously be the same file path so we will overwrite
        # the existing file with the latest version
#        file_path = tool_belt.get_file_path(__file__, start_timestamp,
#                                            nv_sig['name'], 'incremental')
#        tool_belt.save_raw_data(rawData, file_path)

    # %% Process and plot the data

    ret_vals = pulsed_resonance.process_counts(ref_counts, sig_counts, num_runs)
    avg_ref_counts, avg_sig_counts, norm_avg_sig, ste_ref_counts, ste_sig_counts, norm_avg_sig_ste = ret_vals
    
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

#    tool_belt.reset_cfm(cxn)

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
               'freq_ind_master_list': freq_ind_master_list,
               'uwave_power': uwave_power,
               'uwave_power-units': 'dBm',
               'readout': readout,
               'readout-units': 'ns',
               'sig_counts': sig_counts.astype(int).tolist(),
               'sig_counts-units': 'counts',
               'ref_counts': ref_counts.astype(int).tolist(),
               'ref_counts-units': 'counts',
               'norm_avg_sig': norm_avg_sig.astype(float).tolist(),
               'norm_avg_sig-units': 'arb',
#               'norm_avg_sig_ste': norm_avg_sig_ste.astype(float).tolist(),
#               'norm_avg_sig_ste-units': 'arb',
               }

    name = nv_sig['name']
#    filePath = tool_belt.get_file_path(__file__, timestamp, name)
#    tool_belt.save_figure(fig, filePath)
#    tool_belt.save_raw_data(rawData, filePath)

    # Use the pulsed_resonance fitting functions
#    fit_func, popt, pcov = pulsed_resonance.fit_resonance(freq_range, freq_center,
#                                  num_steps, norm_avg_sig, norm_avg_sig_ste, ref_counts)
#    fit_fig = None
#    if (fit_func is not None) and (popt is not None):
#        fit_fig = pulsed_resonance.create_fit_figure(freq_range, freq_center,
#                                     num_steps, norm_avg_sig, fit_func, popt)
#    filePath = tool_belt.get_file_path(__file__, timestamp, name + '-fit')
#    if fit_fig is not None:
#        tool_belt.save_figure(fit_fig, filePath)
#
#    if fit_func == pulsed_resonance.single_gaussian_dip:
#        print('Single resonance at {:.4f} GHz'.format(popt[2]))
#        print('\n')
#        return popt[2], None
#    elif fit_func == pulsed_resonance.double_gaussian_dip:
#        print('Resonances at {:.4f} GHz and {:.4f} GHz'.format(popt[2], popt[5]))
#        print('Splitting of {:d} MHz'.format(int((popt[5] - popt[2]) * 1000)))
#        print('\n')
#        return popt[2], popt[5]
#    else:
#        print('No resonances found')
#        print('\n')
#        return None, None

# %%

if __name__ == '__main__':

    file = '2021_08_27-00_25_11-hopper-search'
    file_path = "pc_hahn/branch_KPZ101-z-control/resonance/2021_08"
    data = tool_belt.get_raw_data(file, file_path)

    freq_center = data['freq_center']
    freq_range = data['freq_range']
    num_steps = data['num_steps']
    num_runs = data['num_runs']
    ref_counts = data['ref_counts']
    sig_counts = data['sig_counts']
    print(len(ref_counts))
    ret_vals = pulsed_resonance.process_counts(ref_counts, sig_counts, num_runs)
    avg_ref_counts, avg_sig_counts, norm_avg_sig, ste_ref_counts, ste_sig_counts, norm_avg_sig_ste = ret_vals
    # norm_avg_sig_ste = None
    

    fit_func, popt, pcov = pulsed_resonance.fit_resonance(freq_range, freq_center, num_steps,
                                         norm_avg_sig, norm_avg_sig_ste, ref_counts)

    # fit_func, popt, pcov = fit_resonance(freq_range, freq_center, num_steps,
    #                                norm_avg_sig, ref_counts)

    pulsed_resonance.create_fit_figure(freq_range, freq_center, num_steps,
                      norm_avg_sig, fit_func, popt)
    
