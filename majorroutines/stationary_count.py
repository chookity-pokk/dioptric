# -*- coding: utf-8 -*-
"""
Sit on the passed coordinates and take counts.

Created on Fri Apr 12 09:25:24 2019

@author: mccambria
"""


# %% Imports


import utils.tool_belt as tool_belt
import numpy
import matplotlib.pyplot as plt
import time
import labrad

import majorroutines.optimize as optimize


# %% Functions


def update_line_plot(new_samples, num_read_so_far, *args):

    fig, samples, write_pos, readout_sec, total_num_samples = args


    num_samples = numpy.count_nonzero(~numpy.isnan(samples))
    num_new_samples = len(new_samples)

    # If we're going to overflow, just shift everything over and drop the
    # earliest samples
    overflow = (num_samples + num_new_samples) - total_num_samples
    if overflow > 0:
        num_nans = max(total_num_samples - num_samples, 0)
        samples[::] = numpy.append(samples[num_new_samples-num_nans:
                                           total_num_samples-num_nans],
                                   new_samples)
    else:
        cur_write_pos = write_pos[0]
        new_write_pos = cur_write_pos + num_new_samples
        samples[cur_write_pos: new_write_pos] = new_samples
        write_pos[0] = new_write_pos


    # Update the figure in k counts per sec
    tool_belt.update_line_plot_figure(fig, (samples / (10**3 * readout_sec)))


# %% Main


def main(nv_sig, run_time, apd_indices, disable_opt=None):

    with labrad.connect() as cxn:
        average, st_dev = main_with_cxn(cxn, nv_sig, run_time, apd_indices, disable_opt)

    return average, st_dev

def main_with_cxn(cxn, nv_sig, run_time, apd_indices, disable_opt=None):

    # %% Some initial setup

    if disable_opt is not None:
        nv_sig["disable_opt"] = disable_opt

#    tool_belt.reset_cfm(cxn)

    readout = nv_sig['imaging_readout_dur']
    readout_sec = readout / 10**9

    # %% Optimize and set the coordinates

    optimize.main_with_cxn(cxn, nv_sig, apd_indices)
#    coords = nv_sig['coords']
#    drift = tool_belt.get_drift()
#    adj_coords = []
#    for i in range(3):
#        adj_coords.append(coords[i] + drift[i])
#    tool_belt.set_xyz(cxn, adj_coords)

    # %% Set up the imaging laser

    laser_key = 'imaging_laser'
    readout_laser = nv_sig[laser_key]
    tool_belt.set_filter(cxn, nv_sig, laser_key)
    readout_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)

    # %% Load the PulseStreamer


    seq_args = [0, readout, apd_indices[0], readout_laser, readout_power]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    ret_vals = cxn.pulse_streamer.stream_load('simple_readout.py',
                                              seq_args_string)
    period = ret_vals[0]

    total_num_samples = int(run_time / period)

    # %% Set up the APD

    apd_server = tool_belt.get_apd_server(cxn)
    apd_server_name = tool_belt.get_registry_entry(cxn, "apd_server", ["", "Config", "Counter"])
    if apd_server_name == 'apd_tagger':
        apd_server.start_tag_stream(apd_indices)
    elif apd_server_name == 'apd_daq':
        apd_server.load_stream_reader(apd_indices[0], period,  total_num_samples)
        
    # %% Initialize the figure

    samples = numpy.empty(total_num_samples)
    samples.fill(numpy.nan)  # Only floats support NaN
    write_pos = [0]  # This is a list because we need a mutable variable

    # Set up the line plot
    x_vals = numpy.arange(total_num_samples) + 1
    x_vals = x_vals / (10**9) * period   # Elapsed time in s

    fig = tool_belt.create_line_plot_figure(samples, x_vals)
    # fig = tool_belt.create_line_plot_figure(samples)

    # Set labels
    axes = fig.get_axes()
    ax = axes[0]
    ax.set_title('Stationary Counts')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('kcps')

    # Maximize the window
    fig_manager = plt.get_current_fig_manager()
    fig_manager.window.showMaximized()

    # Args to pass to update_line_plot
    args = fig, samples, write_pos, readout_sec, total_num_samples

    # %% Collect the data

    cxn.pulse_streamer.stream_start(-1)

    # timeout_duration = ((period*(10**-9)) * total_num_samples) + 10
    # timeout_inst = time.time() + timeout_duration

    num_read_so_far = 0

    tool_belt.init_safe_stop()

    while True:

        # if time.time() > timeout_inst:
        #     break

        if tool_belt.safe_stop():
            break

        # Read the samples and update the image
        try:
            new_samples = apd_server.read_counter_simple() #this function should work for using daq or timetagger
        except Exception:
        #if using a daq for counting, the read_counter_simple stops after 
        #the set number of samples is read, and then the info about the 
        #stream is removed. So we need to laod the stream again for continuous reading
            apd_server.load_stream_reader(apd_indices[0], period,  total_num_samples)
            new_samples = apd_server.read_counter_simple()
            
        # Read the samples and update the image
        num_new_samples = len(new_samples)
        if num_new_samples > 0:
            update_line_plot(new_samples, num_read_so_far, *args)
            num_read_so_far += num_new_samples

    # %% Clean up and report the data

#    tool_belt.reset_cfm(cxn)

    # Replace x/0=inf with 0
    try:
        average = numpy.mean(samples[0:write_pos[0]]) / (10**3 * readout_sec)
        print('average: {}'.format(average))
    except RuntimeWarning as e:
        print(e)
        inf_mask = numpy.isinf(average)
        # Assign to 0 based on the passed conditional array
        average[inf_mask] = 0

    try:
        st_dev = numpy.std(samples[0:write_pos[0]]) / (10**3 * readout_sec)
        print('st_dev: {}'.format(st_dev))
    except RuntimeWarning as e:
        print(e)
        inf_mask = numpy.isinf(st_dev)
        # Assign to 0 based on the passed conditional array
        st_dev[inf_mask] = 0

    return average, st_dev
