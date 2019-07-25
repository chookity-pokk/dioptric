# -*- coding: utf-8 -*-
"""Template for scripts that should be run directly from the files themselves
(as opposed to from the control panel, for example).

Created on Sun Jun 16 11:22:40 2019

@author: mccambria
"""


# %% Imports


import utils.tool_belt as tool_belt
import numpy
import matplotlib.pyplot as plt


# %% Constants


# %% Functions


# %% Main


def main(data):
    """When you run the file, we'll call into main, which should contain the
    body of the script.
    """

    ref_counts = data['ref_counts']
    num_runs = data['num_runs']
    num_steps = data['num_steps']
    
    x_low = 3000
    x_high = 4000
    
    ref_counts = numpy.array(ref_counts)
    std = numpy.std(ref_counts)
    print(std)
    avg = numpy.average(ref_counts)
    print(avg)
    print(std / avg)
    
    tau_inds = data['tau_index_master_list']
    ref_counts = numpy.array(ref_counts)
    ref_counts_time = numpy.zeros(num_runs * num_steps)
    time_ind = 0
    for run_ind in range(num_runs):
        tau_ind_run = tau_inds[run_ind]
        tau_ind_run = numpy.array(tau_ind_run)
        tau_ind_run = tau_ind_run % num_steps  # Convert negative indices
        tau_ind_run_dedupe = []
        for tau_ind in tau_ind_run:
            if tau_ind not in tau_ind_run_dedupe:
                tau_ind_run_dedupe.append(tau_ind)
        for tau_ind in tau_ind_run_dedupe:
            ref_counts_time[time_ind] = ref_counts[run_ind, tau_ind]
            time_ind += 1
    
    fig, ax = plt.subplots(figsize=(8.5, 8.5))
    ax.plot(ref_counts_time[x_low: x_high], 'g-', label = 'reference')
    ax.set_xlabel('Time index')
    ax.set_ylabel('Counts')
    ax.legend()
    run_lines = numpy.array(range(num_runs)) * num_steps
    for line in run_lines:
#        ax.axvline(line)
        if x_low < line < x_high:
            ax.axvline(line - x_low)
    fig.canvas.draw()
    fig.set_tight_layout(True)
    fig.canvas.flush_events()


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here
#     Rabi
#    file_name = '2019-07-19_17-53-17_johnson1'  # 3.9% std, 1.7 kcps
#    file_name = '2019-07-19_17-57-43_johnson1'  # 8.8% std, 1.6 kcps
#    data = tool_belt.get_raw_data('rabi', file_name)
    
    # Spin echo
#    file_name = '2019-07-18_ipython'  # 2.8% std, 1.7 kcps, from console
#    file_name = '2019-07-18_21-09-10_johnson1'  # 5.3% std, 7.9 kcps
    file_name = '2019-07-23_06-14-54_johnson1'  # 
    data = tool_belt.get_raw_data('spin_echo', file_name)
#    data = tool_belt.get_raw_data('spin_echo', file_name, 'branch_ramsey3')

    # Run the script
    main(data)
