# -*- coding: utf-8 -*-
"""
g(2) routine. For each event on one channel, calculates the deltas relative to
the events on the opposite channel and plots a histogram of the deltas. Here
the events are photon detections from the same source, but split over two
APDs. The splitting is necessary to compensate for the APD dead time, which
is typically significantly longer than the lifetime of the excited state we
are interested in.

Created on Wed Apr 24 17:33:26 2019

@author: mccambria
"""

# %% Imports


import utils.tool_belt as tool_belt
import numpy
import matplotlib.pyplot as plt
import time


# %% Functions


def process_raw_buffer(timestamps, apd_indices, buffer_size,
                       diff_window, afterpulse_window,
                       differences_append, apd_a_index, apd_b_index):

    indices_to_delete = []
    indices_to_delete_append = indices_to_delete.append

    # Throw out probable afterpulses
    for click_index in range(buffer_size):

        click_time = timestamps[click_index] #time when one click occurs

        # Determine the afterpulse channel
        click_channel = add_indices[click_index]

        # Calculate relevant differences
        next_index = click_index + 1 #mark the next click
        while next_index < buffer_size: 
            diff = timestamps[next_index] - click_time #the time difference between two clicks
            if diff > afterpulse_window: #jump out because the next click is a real photon 
                break
            if add_indices[next_index] == click_channel: #check if the click is on the same channel, if so, delete it
                indices_to_delete_append(next_index)
            next_index += 1

    timestamps = numpy.delete(timestamps, indices_to_delete) #keep unrepeated count

    # Calculate differences
    num_vals = timestamps.size #timestamps is an array/list 
    for click_index in range(num_vals):

        click_time = timestamps[click_index] #each index corresponding to the time when that click occurs

        # Determine the channel to take the difference with
        click_channel = apd_indices[click_index] 
        if click_channel == apd_a_index:#connect the click channel with the APD 
            diff_channel = apd_b_index
        else:
            diff_channel = apd_a_index

        # Calculate relevant differences
        next_index = click_index + 1
        while next_index < num_vals:  # Don't go past the buffer end
            # Stop taking differences past the diff window
            diff = timestamps[next_index] - click_time
            if diff > diff_window:
                break
            # Only record the diff between opposite chanels
            if apd_indices[next_index] == diff_channel:
                # Flip the sign for diffs relative to channel 2
                if click_channel == apd_b_index:
                    diff = -diff #used for calculation
                differences_append(int(diff))
            next_index += 1


# %% Main


def main(cxn, coords, nd_filter, run_time, diff_window,
         apd_a_index, apd_b_index, name='untitled'):

    # %% Initial calculations and setup
    
    afterpulse_window = 50 * 10**3
    sleep_time = 2

    # Set xyz and open the AOM
    tool_belt.set_xyz(cxn, coords)
    cxn.pulse_streamer.constant()

    num_tags = 0
    collection_index = 0

    apd_indices = [apd_a_index, apd_b_index]

    differences = []  # Create a list to hold the differences
    differences_append = differences.append  # Skip unnecessary lookup
    num_bins = int((2 * diff_window) / 1000) + 1  # 1 ns bins in ps

    # %% Collect the data

    start_time = time.time()
    print('Time remaining:')
    tool_belt.init_safe_stop()

    # Python does not have do-while loops so we will use something like
    # a while True
    cxn.apd_tagger.start_tag_stream(apd_indices)  # Expose an initial stream
    stop = False
    start_calc_time = start_time
    while not stop:

        # Wait until some data has filled
        now = time.time()
        calc_time_elapsed = now - start_calc_time
        time.sleep(max(sleep_time - calc_time_elapsed, 0))
        # Read the stream and convert from strings to int64s
        ret_vals = cxn.apd_tagger.read_tag_stream()
        buffer_timetags, buffer_apd_indices, buffer_size = ret_vals
        buffer_timetags = numpy.array(buffer_timetags, dtype=numpy.int64)

        # Check if we should stop
        time_remaining = (start_time + run_time)- time.time()
        if (time_remaining < 0) or tool_belt.safe_stop():
            stop = True
        else:
            print(int(time_remaining))

        # Process data
        start_calc_time = time.time()
        process_raw_buffer(buffer_timetags, buffer_apd_indices, buffer_size,
                           diff_window, afterpulse_window,
                           differences_append, apd_a_index, apd_b_index)

        # Create/update the histogram
        if collection_index == 0:
            fig, ax = plt.subplots()
            hist, bin_edges = numpy.histogram(differences, num_bins)
            bin_edges = bin_edges / 1000  # ps to ns
            bin_center_offset = (bin_edges[1] - bin_edges[0]) / 2
            bin_centers = bin_edges[0: num_bins] + bin_center_offset
            ax.plot(bin_centers, hist)
            ax.set_xlabel('Time (ns)')
            ax.set_ylabel('Differences')
            ax.set_title(r'$g^{(2)}(\tau)$')
            fig.set_tight_layout(True)
            fig.canvas.draw()
            fig.canvas.flush_events()
        elif collection_index > 1:
            hist, bin_edges = numpy.histogram(differences, num_bins)
            tool_belt.update_line_plot_figure(fig, hist)

        collection_index += 1
        num_tags += buffer_size
        
    cxn.apd_tagger.stop_tag_stream()

    # %% Save the data

    timestamp = tool_belt.get_time_stamp()

    raw_data = {'name': name,
                'timestamp': timestamp,
                'coords': coords,
                'coords-units': 'V',
                'nd_filter': nd_filter,
                'run_time': run_time,
                'run_time-units': 's',
                'diff_window': diff_window,
                'diff_window-units': 'ns',
                'num_bins': num_bins,
                'num_tags': num_tags,
                'differences': differences,
                'differences-units': 'ps'}

    filePath = tool_belt.get_file_path(__file__, timestamp, name)
    tool_belt.save_figure(fig, filePath)
    tool_belt.save_raw_data(raw_data, filePath)
