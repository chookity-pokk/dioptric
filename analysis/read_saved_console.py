# -*- coding: utf-8 -*-
"""

Parsing data from a txt file. This is made for a spin echo experiment that
ran into an error partway through the experiment. 

This file will go through that line in the saved iPython console and add the
data to their respective lists. It will then save that file and plot the data.

Currently for spin echo.

This could be expanded to be more useful outside of just this specific case.



Created on Fri Jul 19 15:44:48 2019

@author: gardill
"""

import numpy
import matplotlib.pyplot as plt
import json
import utils.tool_belt as tool_belt


# %% File to use

directory_path = 'E:/Shared drives/Kolkowitz Lab Group/iPython_console/'
file_name = '2019-07-18_ipython.txt'
file = open(directory_path + file_name, 'r')

# %% Create some lists to fill

num_runs = 29
num_steps = 101

#num_runs = 2
#num_steps = 4

data = numpy.empty([num_runs, num_steps+1, 3], dtype=numpy.uint32)
data[:] = numpy.nan

ind_first = 0
ind_sec = 1

for line in file:
    
    if line[0:10] == 'Run index:':
        cur_run_ind = int(line[11:13])
        ind_run = cur_run_ind
        
        #reset the indexes for counts for each run
        ind_first = 0
        ind_sec = 1
        
    if line[0:22] == 'First relaxation time:':
        first_rel_time = line[23:30]
        
        data[ind_run, ind_first, 0] = first_rel_time
        
    if line[0:23] == 'Second relaxation time:':
        second_rel_time = line[24:31]
        
        data[ind_run, ind_sec, 0] = second_rel_time
        
    if line[0:12] == 'First signal':
        frst_sig = line[15:21]
        
        data[ind_run, ind_first, 1] = frst_sig
        
    if line[0:15] == 'First Reference':
        frst_ref = line[18:23]
        
        data[ind_run, ind_first, 2] = frst_ref
        
        ind_first = ind_first + 2
        
    if line[0:13] == 'Second Signal':
        scnd_sig = line[16:22]
        
        data[ind_run, ind_sec, 1] = scnd_sig
        
    if line[0:16] == 'Second Reference':
        scnd_ref = line[19:24]
        
        data[ind_run, ind_sec, 2] = scnd_ref
        ind_sec = ind_sec + 2
        
#print(data)

# Sort the data based on the time
for ind in range(num_runs):
    data[ind] = numpy.array(sorted(data[ind], key=lambda x: x[0]))
#    print(data[ind])
#    print(len(data[ind]))
#    data[ind] = numpy.delete(data[ind], 0, axis = 0)
    
# Create lsits to put the data in
    
taus = []
sig_counts = numpy.empty([num_runs, num_steps+1], dtype=numpy.uint32)
sig_counts[:] = numpy.nan
ref_counts = numpy.copy(sig_counts)

# Put the taus in a list
for run_ind in range(num_runs):
    for step_ind in range(num_steps+1):
        sig_counts[run_ind][step_ind] = data[run_ind][step_ind][1]
#        print('{}, '.format(data[run_ind][step_ind][1]))
        ref_counts[run_ind][step_ind] = data[run_ind][step_ind][2]
        
        if run_ind == 0:
            taus.append(data[run_ind][step_ind][0])
            
#    print(' ')
    
#taus = numpy.array(taus)
taus = numpy.delete(taus, 50)
sig_counts = numpy.delete(sig_counts, 50, axis = 1)
ref_counts = numpy.delete(ref_counts, 50, axis = 1)

avg_sig_counts = numpy.average(sig_counts, axis=0)
avg_ref_counts = numpy.average(ref_counts, axis=0)

# delete the extra midpoint



#print(taus)
#print(sig_counts)
#for ind in range(101):
#    print(sig_counts[ind][:])
#print(avg_ref_counts)

try:
    norm_avg_sig = avg_sig_counts / avg_ref_counts
except RuntimeWarning as e:
    print(e)
    inf_mask = numpy.isinf(norm_avg_sig)
    # Assign to 0 based on the passed conditional array
    norm_avg_sig[inf_mask] = 0

# %% Plot the data

raw_fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))

ax = axes_pack[0]
ax.plot(taus / 10**3, avg_sig_counts, 'r-', label = 'signal')
ax.plot(taus / 10**3, avg_ref_counts, 'g-', label = 'reference')
ax.set_xlabel('\u03C4 (us)')  # tau = \u03C4 in unicode
ax.set_ylabel('Counts')
ax.legend()

ax = axes_pack[1]
ax.plot(taus / 10**3, norm_avg_sig, 'b-')
ax.set_title('Spin Echo Measurement')
ax.set_xlabel('Precession time (us)')
ax.set_ylabel('Contrast (arb. units)')

raw_fig.canvas.draw()
# fig.set_tight_layout(True)
raw_fig.canvas.flush_events()
    
# %% Save the data
    
nv_sig = {'coords': [-0.151, -0.338, 37.74], 'nd_filter': 'nd_0.5',
                      'expected_count_rate': 45, 'magnet_angle': 99.0,
                      'name': 'Johnson'}

raw_data = {
            'nv_sig': nv_sig,
            'nv_sig-units': tool_belt.get_nv_sig_units(),
            'uwave_freq': 2.8151,
            'uwave_freq-units': 'GHz',
            'uwave_power': 9,
            'uwave_power-units': 'dBm',
            'rabi_period': 128.0,
            'rabi_period-units': 'ns',
            'uwave_pi_pulse': round(128.0 / 2),
            'uwave_pi_pulse-units': 'ns',
            'uwave_pi_on_2_pulse': round(128.0 / 4),
            'uwave_pi_on_2_pulse-units': 'ns',
            'precession_time_range': [0, 100 * 10**3],
            'precession_time_range-units': 'ns',
            'taus': taus.tolist(),
            'taus-units': 'ns',
            'num_steps': num_steps,
            'num_reps': 1 * 10**5,
            'num_runs': num_runs,
            'sig_counts': sig_counts.astype(int).tolist(),
            'sig_counts-units': 'counts',
            'ref_counts': ref_counts.astype(int).tolist(),
            'ref_counts-units': 'counts',
            'norm_avg_sig': norm_avg_sig.astype(float).tolist(),
            'norm_avg_sig-units': 'arb'}
    
with open(directory_path + 'attempt1.txt', 'w') as file:
        json.dump(raw_data, file, indent=2)
        
raw_fig.savefig(directory_path + 'attempt1.svg')



        