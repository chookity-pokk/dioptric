# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 20:03:36 2019

@author: mccambria
"""

import numpy

def read_counter(channels, leftover_channels=[]):

    channels = numpy.array(channels)

    stream_apd_indices = [0]
    tagger_di_clock = 1
    tagger_di_gate = {0: 2}
    tagger_di_apd = {0: 3}

    # Find clock clicks (sample breaks)
    result = numpy.nonzero(channels == tagger_di_clock)
    clock_click_inds = result[0].tolist()

    previous_sample_end_ind = None
    sample_end_ind = None

    # Counts will be a list of lists - the first dimension will divide
    # samples and the second will divide gatings within samples
    return_counts = []

    for clock_click_ind in clock_click_inds:

        # Clock clicks end samples, so they should be included with the
        # sample itself
        sample_end_ind = clock_click_ind + 1

        if previous_sample_end_ind is None:
            sample_channels = leftover_channels
            sample_channels.extend(channels[0: sample_end_ind])
        else:
            sample_channels = channels[previous_sample_end_ind:
                sample_end_ind]
            
        # Make sure we've got arrays or else comparison won't produce
        # the boolean array we're looking for when we find gate clicks
        sample_channels = numpy.array(sample_channels)
        
        sample_counts = []
        
        # Loop through the APDs
        for apd_index in stream_apd_indices:
            
            apd_channel = tagger_di_apd[apd_index]
            gate_open_channel = tagger_di_gate[apd_index]
            gate_close_channel = -gate_open_channel
        
            # Find gate open clicks
            result = numpy.nonzero(sample_channels == gate_open_channel)
            gate_open_click_inds = result[0].tolist()

            # Find gate close clicks
            # Gate close channel is negative of gate open channel,
            # signifying the falling edge
            result = numpy.nonzero(sample_channels == gate_close_channel)
            gate_close_click_inds = result[0].tolist()

            # The number of APD clicks is simply the number of items in the
            # buffer between gate open and gate close clicks
            channel_counts = []
            
            for ind in range(len(gate_open_click_inds)):
                gate_open_click_ind = gate_open_click_inds[ind]
                gate_close_click_ind = gate_close_click_inds[ind]
                gate_window = sample_channels[gate_open_click_ind:
                    gate_close_click_ind]
                gate_window = gate_window.tolist()
                gate_count = gate_window.count(apd_channel)
                channel_counts.append(gate_count)
                
            sample_counts.append(channel_counts)

        return_counts.append(sample_counts)
        previous_sample_end_ind = sample_end_ind
    
    if sample_end_ind is None:
        # No samples were clocked - add everything to leftovers
        leftover_channels.extend(channels.tolist())
    else:
        # Reset leftovers from the last sample clock
        leftover_channels = channels[sample_end_ind:].tolist()

    return return_counts, leftover_channels

if __name__ == '__main__':

    # channels = [3, 3, 3,
    #             2, -2,
    #             3, 3, 3,
    #             2, 3, 3, -2,
    #             3, 3,
    #             1,
    #             3, 3, 3,
    #             2, 3, -2,
    #             2, 3, -2,
    #             2, 3, 3, 3, -2,
    #             1,
    #             2, 3, -2,
    #             2, 3, -2,
    #             2, 3, 3, 3, -2,
    #             3, 3,
    #             1]

    channels = [3, 3, 3,
                2, -2,
                3, 3, 3,
                2, 3, 3, -2,
                3, 3,
                3, 3, 3,
                2, 3, -2,
                2, 3, -2,
                2, 3, 3, 3, -2,
                2, 3, -2,
                2, 3, -2,
                2, 3, 3, 3, -2,
                3, 3]
    print(read_counter(channels))
    counts, leftover_channels = read_counter(channels)

    channels = [1, 3, 3, 3,
                2, -2,
                3, 3, 3,
                2, 3, 3, -2,
                3, 3,
                1,
                3, 3, 3,
                2, 3, -2,
                2, 3, -2,
                2, 3, 3, 3, -2,
                3, 3,
                1]
    
    print(read_counter(channels, leftover_channels))
