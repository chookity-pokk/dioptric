# -*- coding: utf-8 -*-
"""Template for scripts that should be run directly from the files themselves
(as opposed to from the control panel, for example).

Created on Sun Jun 16 11:22:40 2019

@author: mccambria
"""


# %% Imports


import utils.tool_belt as tool_belt
import matplotlib.pyplot as plt
import numpy


# %% Constants


# %% Functions


# %% Main


def main(source_name, file_name):
    """When you run the file, we'll call into main, which should contain the
    body of the script.
    """

    raw_data = tool_belt.get_raw_data(source_name, file_name)
    
    num_steps = raw_data['num_steps']
    sig_counts = raw_data['sig_counts']
    ref_counts = raw_data['ref_counts']
    avg_sig_counts = numpy.average(sig_counts, axis=0)
    avg_ref_counts = numpy.average(ref_counts, axis=0)
    norm_avg_sig = raw_data['norm_avg_sig']
    

    raw_fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))

    ax = axes_pack[0]
    ax.plot(list(range(0, num_steps)), avg_sig_counts, 'r-')
    ax.plot(list(range(0, num_steps)), avg_ref_counts, 'g-')
    ax.set_xlabel('num_run')
    ax.set_ylabel('Counts')

    ax = axes_pack[1]
    ax.plot(list(range(0, num_steps)), norm_avg_sig, 'b-')
    ax.set_title('Normalized Signal With Varying Microwave Duration')
    ax.set_xlabel('num_run')
    ax.set_ylabel('Normalized contrast')

    raw_fig.canvas.draw()
    # fig.set_tight_layout(True)
    raw_fig.canvas.flush_events()
    
    


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here
    source_name = 'optimize_readout_window'
#    file_name = '2019-06-28_16-47-18_Johnson1'
    file_name = '2019-06-28_16-44-40_Johnson1'

    # Run the script
    main(source_name, file_name)
