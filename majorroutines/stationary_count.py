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

    fig, samples, write_pos, readout_sec = args

    # Write to the samples array
    cur_write_pos = write_pos[0]
    new_write_pos = cur_write_pos + len(new_samples)
    samples[cur_write_pos: new_write_pos] = new_samples
    write_pos[0] = new_write_pos

    # Update the figure in k counts per sec
    tool_belt.update_line_plot_figure(fig, (samples * 10**-3) / readout_sec)


# %% Main


def main(nv_sig, run_time, apd_indices, continuous=False):

    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig, run_time, apd_indices, continuous)

def main_with_cxn(cxn, nv_sig, run_time, apd_indices, continuous=False):

    # %% Some initial setup
    
    tool_belt.reset_cfm(cxn)

    shared_parameters = tool_belt.get_shared_parameters_dict(cxn)
    readout = shared_parameters['continuous_readout_dur']
    readout_sec = readout / 10**9

    # %% Optimize

    optimize.main_with_cxn(cxn, nv_sig, apd_indices)

    # %% Load the PulseStreamer

    seq_args = [0, readout, apd_indices[0]]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    ret_vals = cxn.pulse_streamer.stream_load('simple_readout.py',
                                              seq_args_string)
    period = ret_vals[0]

    total_num_samples = int(run_time / period)

    # %% Set up the APD

    cxn.apd_tagger.start_tag_stream(apd_indices)

    # %% Initialize the figure

    samples = numpy.empty(total_num_samples)
    samples.fill(numpy.nan)  # Only floats support NaN
    write_pos = [0]  # This is a list because we need a mutable variable

    # Set up the line plot
#    x_vals = numpy.arange(totalNumSamples) + 1
#    x_vals *= period / (10**9)  # Elapsed time in s
#    fig = tool_belt.create_line_plot_figure(samples, x_vals)
    fig = tool_belt.create_line_plot_figure(samples)

    # Set labels
    axes = fig.get_axes()
    ax = axes[0]
    ax.set_title('Stationary Counts')
    ax.set_xlabel('Elapsed time (s)')
    ax.set_ylabel('kcts/sec')

    # Maximize the window
    fig_manager = plt.get_current_fig_manager()
    fig_manager.window.showMaximized()

    # Args to pass to update_line_plot
    args = fig, samples, write_pos, readout_sec

    # %% Collect the data

    cxn.pulse_streamer.stream_start(total_num_samples)

    timeout_duration = ((period*(10**-9)) * total_num_samples) + 10
    timeout_inst = time.time() + timeout_duration

    num_read_so_far = 0

    tool_belt.init_safe_stop()

    while num_read_so_far < total_num_samples:

        if time.time() > timeout_inst:
            break

        if tool_belt.safe_stop():
            break

        # Read the samples and update the image
        new_samples = cxn.apd_tagger.read_counter_simple()
        num_new_samples = len(new_samples)
        if num_new_samples > 0:
            update_line_plot(new_samples, num_read_so_far, *args)
            num_read_so_far += num_new_samples

    # %% Clean up and report the data
    
    tool_belt.reset_cfm(cxn)
    
    # Replace x/0=inf with 0
    try:
        average = numpy.mean(samples[0:write_pos[0]]) / (10**3 * readout_sec)
    except RuntimeWarning as e:
        print(e)
        inf_mask = numpy.isinf(average)
        # Assign to 0 based on the passed conditional array
        average[inf_mask] = 0
        
    try:
        st_dev = numpy.std(samples[0:write_pos[0]]) / (10**3 * readout_sec)
    except RuntimeWarning as e:
        print(e)
        inf_mask = numpy.isinf(st_dev)
        # Assign to 0 based on the passed conditional array
        st_dev[inf_mask] = 0

    return average, st_dev
