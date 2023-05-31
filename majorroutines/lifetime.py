# -*- coding: utf-8 -*-
"""
This is a program to record the lifetime (right now, specifically of the Er
implanted materials fro mVictor brar's group).

It takes the same structure as a standard t1 measurement. We shine 532 nm
light, wait some time, and then read out the counts WITHOUT shining 532 nm
light.

Adding a variable 'filter' to pass into the function to signify what filter
was used to take the measurement (2/20/2020)

Created on Mon Nov 11 12:49:55 2019

@author: agardill
"""

# %% Imports


import utils.tool_belt as tool_belt
import majorroutines.optimize as optimize
import numpy
import os
import time
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import json
import labrad
import csv


# %% Functions


def process_raw_buffer(new_tags, new_channels,
                       current_tags, current_channels,
                       gate_open_channel, gate_close_channel):

    # The processing here will be bin_size agnostic

    # Tack the new data onto the leftover data (leftovers are necessary if
    # the last read contained a gate open without a matching gate close)
    current_tags.extend(new_tags)
    current_channels.extend(new_channels)
    current_channels_array = numpy.array(current_channels)

    # Find gate open clicks
    result = numpy.nonzero(current_channels_array == gate_open_channel)
    gate_open_click_inds = result[0].tolist()

    # Find gate close clicks
    result = numpy.nonzero(current_channels_array == gate_close_channel)
    gate_close_click_inds = result[0].tolist()

    new_processed_tags = []

    # Loop over the number of closes we have since there are guaranteed to
    # be opens
    num_closed_samples = len(gate_close_click_inds)
    for list_ind in range(num_closed_samples):

        gate_open_click_ind = gate_open_click_inds[list_ind]
        gate_close_click_ind = gate_close_click_inds[list_ind]

        # Extract all the counts between these two indices as a single sample
        rep = current_tags[gate_open_click_ind+1:
                                    gate_close_click_ind]
        rep = numpy.array(rep, dtype=numpy.int64)
        # Make relative to gate open
        rep -= current_tags[gate_open_click_ind]
        new_processed_tags.extend(rep.astype(int).tolist())

    # Clear processed tags
    if len(gate_close_click_inds) > 0:
        leftover_start = gate_close_click_inds[-1]
        del current_tags[0: leftover_start+1]
        del current_channels[0: leftover_start+1]

    return new_processed_tags, num_closed_samples


# %% Main


def main(nv_sig, apd_indices, readout_time_range,
         num_reps, num_runs, num_bins,  polarization_time = None):

    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig, apd_indices, readout_time_range,
                      num_reps, num_runs, num_bins, polarization_time)


def main_with_cxn(cxn, nv_sig, apd_indices, readout_time_range,
                  num_reps, num_runs, num_bins,  polarization_time = None):

    if len(apd_indices) > 1:
        msg = 'Currently lifetime only supports single APDs!!'
        raise NotImplementedError(msg)

    tool_belt.reset_cfm(cxn)

    # %% Define the times to be used in the sequence

    laser_tag = "initialize"
    laser_key = "{}_laser".format(laser_tag)
    init_laser_name = nv_sig[laser_key]
    init_laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)
    if polarization_time:
        nv_sig["{}_dur".format(laser_tag)] = polarization_time
        
    initialization_dur = nv_sig["{}_dur".format(laser_tag)]
    
    
    # In ns
#    polarization_time = 25 * 10**3
    start_readout_time = int(readout_time_range[0])
    end_readout_time = int(readout_time_range[1])

    if end_readout_time < polarization_time:
        end_readout_time = polarization_time

    calc_readout_time = end_readout_time - start_readout_time
#    readout_time = polarization_time + int(readout_time)
#    inter_exp_wait_time = 500  # time between experiments



    # %% Analyze the sequence

    # pulls the file of the sequence from serves/timing/sequencelibrary
    file_name = os.path.basename(__file__)
    seq_args = [start_readout_time, end_readout_time, initialization_dur,
                init_laser_name, init_laser_power, apd_indices[0]]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    ret_vals = cxn.pulse_streamer.stream_load(file_name, seq_args_string)
    seq_time = ret_vals[0]

    # %% Report the expected run time

    seq_time_s = seq_time / (10**9)  # s
    expected_run_time = num_runs * (num_reps *  seq_time_s + 1)  # s
    expected_run_time_m = expected_run_time / 60 # m
    print(' \nExpected run time: {:.1f} minutes. '.format(expected_run_time_m))
#    return

    # %% Bit more setup

    # Record the start time
    startFunctionTime = time.time()
    start_timestamp = tool_belt.get_time_stamp()

    opti_coords_list = []

    # %% Set the filters
    
    tool_belt.set_filter(cxn, nv_sig, laser_key)
    tool_belt.set_filter(cxn, nv_sig, 'collection')

    # %% Collect the data

    processed_tags = []

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


        # Expose the stream
        cxn.apd_tagger.start_tag_stream(apd_indices, apd_indices, False)

        # Find the gate channel
        # The order of channel_mapping is APD, APD gate open, APD gate close
        channel_mapping = cxn.apd_tagger.get_channel_mapping()
        gate_open_channel = channel_mapping[1]
        gate_close_channel = channel_mapping[2]

        # Stream the sequence
        # seq_args = [start_readout_time, end_readout_time, polarization_time,
        #         aom_delay_time, apd_indices[0]]
        # seq_args = [int(el) for el in seq_args]
        seq_args_string = tool_belt.encode_seq_args(seq_args)

        cxn.pulse_streamer.stream_immediate(file_name, int(num_reps),
                                            seq_args_string)

        # Initialize state
        current_tags = []
        current_channels = []
        num_processed_reps = 0

        while num_processed_reps < num_reps:

            # Break out of the while if the user says stop
            if tool_belt.safe_stop():
                break

            new_tags, new_channels = cxn.apd_tagger.read_tag_stream()
            new_tags = numpy.array(new_tags, dtype=numpy.int64)

            ret_vals = process_raw_buffer(new_tags, new_channels,
                                   current_tags, current_channels,
                                   gate_open_channel, gate_close_channel)
            new_processed_tags, num_new_processed_reps = ret_vals
            # MCC test
            if num_new_processed_reps > 750000:
                print('Processed {} reps out of 10^6 max'.format(num_new_processed_reps))
                print('Tell Matt that the time tagger is too slow!')

            num_processed_reps += num_new_processed_reps

            processed_tags.extend(new_processed_tags)


        cxn.apd_tagger.stop_tag_stream()

        # %% Save the data we have incrementally for long measurements

        raw_data = {'start_timestamp': start_timestamp,
                    'nv_sig': nv_sig,
                    'nv_sig-units': tool_belt.get_nv_sig_units(),
                    # 'filter': filter,
                    # 'reference_measurement?': reference,
                    'start_readout_time': start_readout_time,
                    'start_readout_time-units': 'ns',
                    'end_readout_time': end_readout_time,
                    'end_readout_time-units': 'ns',
                    'calc_readout_time': calc_readout_time,
                    'calc_readout_time-units': 'ns',
                    'num_reps': num_reps,
                    'num_runs': num_runs,
                    'run_ind': run_ind,
                    'num_bins': num_bins,
                    'opti_coords_list': opti_coords_list,
                    'opti_coords_list-units': 'V',
                    'processed_tags': processed_tags,
                    'processed_tags-units': 'ps',
                    }

        # This will continuously be the same file path so we will overwrite
        # the existing file with the latest version
        file_path = tool_belt.get_file_path(__file__, start_timestamp,
                                            nv_sig['name'], 'incremental')
        tool_belt.save_raw_data(raw_data, file_path)

    # %% Hardware clean up

    tool_belt.reset_cfm(cxn)

    # %% Bin the data

    readout_time_ps = 1000*calc_readout_time

#    start_readout_time_ps = 1000*start_readout_time
#    end_readout_time_ps = 1000*end_readout_time
    binned_samples, bin_edges = numpy.histogram(processed_tags, num_bins,
                                (0, readout_time_ps))
#    print(binned_samples)

    # Compute the centers of the bins
    bin_size = calc_readout_time / num_bins
    bin_center_offset = bin_size / 2
    bin_centers = numpy.linspace(start_readout_time, end_readout_time, num_bins) + bin_center_offset
#    print(bin_centers)

    # %% Plot

    fig, ax = plt.subplots(1, 1, figsize=(10, 8.5))

    bin_size = calc_readout_time / num_bins
    bin_size_s = bin_size / 1e9
    
    binned_samples_kcps = binned_samples / bin_size_s / 1e3 / num_reps / num_runs
    
    
    ax2 = ax.twinx()
    ax.plot(numpy.array(bin_centers)/10**3, binned_samples_kcps, 'r-')
    ax2.plot(numpy.array(bin_centers)/10**3, binned_samples, 'r-')
    
    ax.set_xlabel('X data')
    ax.set_ylabel('kcps', color='k')
    ax2.set_ylabel('total raw counts', color='k')

    ax.set_title('Lifetime')
    ax.set_xlabel('Time after illumination (us)')
    # ax.set_ylabel('kcps')

    fig.canvas.draw()
    fig.set_tight_layout(True)
    fig.canvas.flush_events()

    # %% Save the data

    endFunctionTime = time.time()
    time_elapsed = endFunctionTime - startFunctionTime
    timestamp = tool_belt.get_time_stamp()

    raw_data = {'timestamp': timestamp,
                'time_elapsed': time_elapsed,
                'nv_sig': nv_sig,
                'nv_sig-units': tool_belt.get_nv_sig_units(),
                # 'filter': filter,
                # 'reference_measurement?': reference,
                # 'voltage': voltage,
                'polarization_time': polarization_time,
                'polarization_time-units': 'ns',
                'start_readout_time': start_readout_time,
                'start_readout_time-units': 'ns',
                'end_readout_time': end_readout_time,
                'end_readout_time-units': 'ns',
                'calc_readout_time': calc_readout_time,
                'calc_readout_time-units': 'ns',
                'num_bins': num_bins,
                'num_reps': num_reps,
                'num_runs': num_runs,
                'opti_coords_list': opti_coords_list,
                'opti_coords_list-units': 'V',
                'binned_samples': binned_samples.tolist(),
                'bin_centers': bin_centers.tolist(),
                'processed_tags': processed_tags,
                'processed_tags-units': 'ps',
                }

    file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
    tool_belt.save_figure(fig, file_path)
    tool_belt.save_raw_data(raw_data, file_path)

# %%

def lifetime_json_to_csv(file, folder, nv_data_dir = 'E:/Shared drives/Kolkowitz Lab Group/nvdata'):
    

    data = tool_belt.get_raw_data(file, folder)
    # data = json.load(json_file)
    binned_samples = data['binned_samples']
    bin_centers = data['bin_centers']

    # Populate the data to save
    csv_data = []
    
    for bin_ind in range(len(bin_centers)):
        row = []
        row.append(bin_centers[bin_ind])
        row.append(binned_samples[bin_ind])
        csv_data.append(row)

    tool_belt.write_csv(csv_data, file, folder)
    
    
# %%

def decayExp(t, amplitude, decay):
    return amplitude * numpy.exp(- t / decay)

def dobule_decay(t, a1, d1, a2, d2):
    return decayExp(t, a1, d1) + decayExp(t, a2, d2)

# %% Fitting the data

def fit_decay(file_name, date_folder, sub_folder =None,bkgd_sig = []):
    fig, ax= plt.subplots(1, 1, figsize=(10, 8))

    directory = 'pc_rabi/branch_master/lifetime_v2/'

    folder_path = directory + date_folder
    if sub_folder:
       folder_path = folder_path + '/' + sub_folder 
       
    data = tool_belt.get_raw_data(file_name, folder_path)
    
    bin_centers = numpy.array(data['bin_centers'])
    binned_samples = numpy.array(data['binned_samples'])
    nv_sig = data['nv_sig']
    nv_name = nv_sig['name']
    timestamp = data['timestamp']
    
    if len(bkgd_sig) == len(binned_samples):
        binned_samples_sub = binned_samples - bkgd_sig
    else:
        binned_samples_sub = binned_samples
        
    nn = 15 # take an average of the beginning and end to calculate contrast
    one = numpy.average(binned_samples_sub[:nn])
    zero = numpy.average(binned_samples_sub[-nn:])
    norm_samples = (binned_samples_sub - zero) / (one - zero)
    
    #specific for this data set, choose the range of data to fit to
    start_ind =28
    print(bin_centers[start_ind] )
    # start_ind =29 
    # end_ind = 80
    end_ind = 40
    bin_centers_shift = bin_centers[start_ind:end_ind] - bin_centers[start_ind] 
    norm_samples_shift = norm_samples[start_ind:end_ind]
        
    ax.plot(numpy.array(bin_centers_shift), norm_samples_shift, 'bo', 
                label = 'data')
    
    centers_lin = numpy.linspace(bin_centers_shift[0], bin_centers_shift[-1], 100)
    # print(centers_lin)
    fit_func = lambda t, d: decayExp(t, 1, d)
    # fit_func = lambda t, a1, d1,a2, d2: dobule_decay(t, a1, d1, a2, d2)
    init_params = [10]
    popt, pcov = curve_fit(
        fit_func,
        bin_centers_shift,
        norm_samples_shift,
        # sigma=norm_avg_sig_ste,
        # absolute_sigma=True,
        p0=init_params,
        # bounds=(0, numpy.inf),
    )
    print('{} +/- {} ns'.format(popt[0], numpy.sqrt(pcov[0][0])))
    # print(popt)
    # print(popt)
    # print(pcov)
    ax.plot(
            centers_lin,
            fit_func(centers_lin, *popt),
            "r-",
            label="fit",
        ) 
    
    text_popt = '\n'.join((
                        r'y = exp(-t / d)',
                        r'd = ' + '%.2f'%(popt[0]) + ' +/- ' + '%.2f'%(numpy.sqrt(pcov[0][0])) + ' ns'
                        ))

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.1, 0.3, text_popt, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)
    
    
    
    ax.set_xlabel('Time after illumination, t (ns)')
    ax.set_ylabel('Normalized signal')
    ax.set_title('Lifetime for {}'.format(nv_name))
    ax.set_ylim([5e-4, 1.7])
    ax.set_yscale("log")
    ax.legend()
    
    filePath = tool_belt.get_file_path('lifetime_v2.py', timestamp, nv_name +'-fit')
    if sub_folder:
       filePath = tool_belt.get_file_path('lifetime_v2.py', timestamp, nv_name +'-fit', sub_folder)
       
    tool_belt.save_figure(fig, filePath)
    
    return popt

def replot(file_name, date_folder, sub_folder =None,semilog = False):
    fig, ax= plt.subplots(1, 1, figsize=(10, 8))

    directory = 'pc_rabi/branch_master/lifetime_v2/'

    folder_path = directory + date_folder
    if sub_folder:
       folder_path = folder_path + '/' + sub_folder 
       
    data = tool_belt.get_raw_data(file_name, folder_path)
    
    bin_centers = numpy.array(data['bin_centers'])
    binned_samples = numpy.array(data['binned_samples'])
    nv_sig = data['nv_sig']
    nv_name = nv_sig['name']
    timestamp = data['timestamp']
    
        
    ax.plot(numpy.array(bin_centers), binned_samples, 'bo', 
                label = 'data')
                
    ax.set_xlabel('Time (ns)')
    ax.set_ylabel('Signal')
    ax.set_title('Lifetime for {}'.format(nv_name))
    # ax.set_ylim([5e-4, 1.7])
    if semilog:
        ax.set_yscale("log")
    ax.legend()
    
    
# %%
if __name__ == '__main__':
    folder = 'pc_rabi/branch_master/lifetime_v2/2022_09'
    file = '2022_09_17-00_12_47-rubin-nv0_2022_09_16'
    
    file_bckg = '2022_09_14-12_39_05-rubin-no_nv'
    
    lifetime_json_to_csv(file, folder)
        
    # data = tool_belt.get_raw_data(file_bckg, folder)
    # bkgd= numpy.array(data['binned_samples'])
    # decay_list = []
    
    # file_list = tool_belt.get_file_list(
    #     'pc_rabi/branch_master/lifetime_v2/2022_09/2022_09_18',
    #     'txt',
    # )
    file_list = ['2022_09_13-17_07_24-rubin-nv1_2022_08_10.txt',
                 '2022_09_13-17_51_35-rubin-nv4_2022_08_10.txt',
                 '2022_09_13-18_17_53-rubin-nv5_2022_08_10.txt',
                 '2022_09_13-18_17_55-rubin-nv8_2022_08_10.txt',
                 '2022_09_13-19_10_05-rubin-nv10_2022_08_10.txt']
    
    for file_name in file_list:
        file = file_name[:-4]
        lifetime_json_to_csv(file, folder)
    
    # fit_decay('2022_09_22-13_48_04-rubin_al-no_nv', '2022_09' )
    # replot('2022_09_13-18_17_55-rubin-nv8_2022_08_10', '2022_09/incremental' ,semilog=True)
        # [d] = fit_decay(file, '2022_09', '2022_09_18', bkgd_sig = bkgd)
        # decay_list.append(d)
    
    # print(decay_list)
    
    # # decay_list = [19.059485988628694, 18.408959908485883, 18.55644393743853, 15.910078181399864, 13.08983621888649, 17.440854238724143, 19.30161420123414, 20.456542286541925, 15.912223911467104, 18.152678848095103, 14.313007642378626, 15.866427084210091, 16.72573476040746, 17.574747894434203, 17.513620268161343, 17.503002305697688, 16.656257218411735, 18.265675680041735, 16.79152908738018, 17.904080947608154, 19.433017398759024, 17.34069666788826, 19.841424506854693, 16.668763794591644, 17.13078827352994, 17.476590885736066, 16.86830852746903, 16.590796937894723, 16.013673974819014, 11.537271394243945, 19.084253795519004, 14.654132348217287, 17.46338812789775, 18.127077732677453, 14.448578102795235, 11.615328005874195, 15.54952874102039, 19.901513230609066, 18.32889038526471, 19.215021743145453, 19.786860442848795, 16.82717791950751, 20.276692444486795, 11.816717939596048, 16.87455264792951, 16.326218893577735, 20.284876689476707, 17.194885555367666, 17.287883285697095, 16.799133784460565, 17.55195383542611, 15.829957603452579, 15.275008538092347, 20.254799450822183, 17.315973777464702, 21.149714900343255, 13.385583837307996, 16.636295449014685, 18.964838435427424, 18.237687452278028, 16.717049274858894, 18.41685955207426, 18.435945938825476, 16.479269430502107, 19.521043461525338, 16.875025550498478, 17.573642129599666, 21.91975468229476, 23.90868882778355, 20.943797037806874, 17.79330452146329, 19.719794945954863, 16.71025220732571, 18.298791719421786, 18.546361840159932, 19.00512891239648, 17.224093709222057, 15.815145838866146]
    
    # occur, bin_edges = numpy.histogram(
    #     decay_list)
    # x_vals = bin_edges[:-1]
    
    
    # fig, ax= plt.subplots(1, 1, figsize=(8, 8))
    # ax.plot(
    #         x_vals,
    #         occur,
    #         "ko",
    #     ) 
    # ax.set_xlabel('Lifetime decay time, t (ns)')
    # ax.set_ylabel('Occurrences')
    # ax.set_title('Histogram of lifetime decay times')
        

    
