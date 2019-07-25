# -*- coding: utf-8 -*-
"""Template for scripts that should be run directly from the files themselves
(as opposed to from the control panel, for example).

Created on Sun Jun 16 11:22:40 2019

@author: mccambria
"""


# %% Imports


from pathlib import Path
import numpy
import matplotlib.pyplot as plt


# %% Constants


# %% Functions


# %% Main


def main(file_name):
    """When you run the file, we'll call into main, which should contain the
    body of the script.
    """
    
    data_dir = Path('C:/Users/kolkowitz/Desktop/iPython_console/')
    file_name_ext = '{}.txt'.format(file_name)
    file_path = data_dir / file_name_ext
    with open(file_path) as file:
        console = file.read()
        
    # Build taus
    taus = []
    runs = console.split('Run index: ')
    runs = runs[1:]  # Ignore the experiment header
    num_runs = len(runs) - 1  # Skip the unfinished run
    first_run = runs[0]
    exps = first_run.split('First relaxation time: ')
    exps = exps[1:]  # ignore the run header
    num_exps = len(exps)
    for exp in exps:
        first_time = exp.split('\n\n')[0]
        taus.append(first_time)
        second_time = exp.split('Second relaxation time: ')[1].split('\n\n')[0]
        if second_time != first_time:
            taus.append(second_time)
    taus = numpy.array(taus, dtype=numpy.int32)
    taus = numpy.sort(taus)
    num_steps = len(taus)
#    print(taus)
#    return
    
    # Build the data structures
    sig_counts = numpy.empty([num_runs, num_steps], dtype=numpy.uint32)
    sig_counts[:] = numpy.nan
    ref_counts = numpy.copy(sig_counts)
    sig_counts_time = numpy.empty([num_runs * (2 * num_exps)], dtype=numpy.uint32)
    sig_counts_time[:] = numpy.nan
    ref_counts_time = numpy.copy(sig_counts_time)
    
    for run_ind in range(num_runs):
        run = runs[run_ind]
        exps = run.split('First relaxation time: ')
        exps = exps[1:]  # Ignore the run header
        for exp_ind in range(num_exps):
            
            exp = exps[exp_ind]
            
            first_time = numpy.int32(exp.split('\n\n')[0])
            first_time_ind = numpy.where(taus==first_time)[0]
            
            first_sig = exp.split('First signal = ')[1].split('\n\n')[0]
            sig_counts[run_ind, first_time_ind] = first_sig
            time_ind = (run_ind * 2 * num_exps) + (2 * exp_ind)
            sig_counts_time[time_ind] = first_sig
            first_ref = exp.split('First Reference = ')[1].split('\n\n')[0]
            ref_counts[run_ind, first_time_ind] = first_ref
            ref_counts_time[time_ind] = first_ref
            
            second_time = numpy.int32(exp.split('Second relaxation time: ')[1].split('\n\n')[0])
            second_time_ind = numpy.where(taus==second_time)[0]
            
            second_sig = exp.split('Second Signal = ')[1].split('\n\n')[0]
            sig_counts[run_ind, second_time_ind] = second_sig
            time_ind += 1
            sig_counts_time[time_ind] = second_sig
            second_ref = exp.split('Second Reference = ')[1].split('\n\n')[0]
            ref_counts[run_ind, second_time_ind] = second_ref
            ref_counts_time[time_ind] = second_ref
    
    # %% Plotting
    
    std = numpy.std(ref_counts_time)
    print(std)
    avg = numpy.average(ref_counts_time)
    print(avg)
    print(std / avg)
    
    plot_ref = True
    if plot_ref:
        x_low = 0
        x_high = 511
        fig, ax = plt.subplots(figsize=(8.5, 8.5))
        ax.plot(ref_counts_time[x_low: x_high], 'g-', label = 'reference')
        ax.set_xlabel('Time index')  # tau = \u03C4 in unicode
        ax.set_ylabel('Counts')
        ax.legend()
        run_lines = numpy.array(range(num_runs)) * 102
        for line in run_lines:
            if x_low < line < x_high:
                ax.axvline(line - x_low)
        fig.canvas.draw()
        fig.set_tight_layout(True)
        fig.canvas.flush_events()
    else:
        avg_sig_counts = numpy.average(sig_counts, axis=0)
        avg_ref_counts = numpy.average(ref_counts, axis=0)
        try:
            norm_avg_sig = avg_sig_counts / avg_ref_counts
        except RuntimeWarning as e:
            print(e)
            inf_mask = numpy.isinf(norm_avg_sig)
            # Assign to 0 based on the passed conditional array
            norm_avg_sig[inf_mask] = 0
        
        fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))
    
        ax = axes_pack[0]
        ax.plot(taus / 10**3, avg_sig_counts, 'r-', label = 'signal')
        ax.plot(taus / 10**3, avg_ref_counts, 'g-', label = 'reference')
        ax.set_xlabel('\u03C4 (us)')  # tau = \u03C4 in unicode
        ax.set_ylabel('Counts')
        ax.legend()
    
        ax = axes_pack[1]
        ax.plot(taus / 10**3, norm_avg_sig, 'b-')
        ax.set_title('Spin Echo Measurement')
        ax.set_xlabel('\u03C4 (us)')
        ax.set_ylabel('Contrast (arb. units)')
    
        fig.canvas.draw()
        fig.set_tight_layout(True)
        fig.canvas.flush_events()
    

# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here
    file_name = '2019-07-23_ipython'
    
    # Run the script
    main(file_name)
