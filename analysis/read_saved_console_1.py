# -*- coding: utf-8 -*-
"""

Another attempt at reading in this data from the iPython console. 


Created on Sat Jul 20 19:10:06 2019

@author: Aedan
"""
# %% Imports

import numpy
import json
import matplotlib.pyplot as plt
import utils.tool_belt as tool_belt


# %% Define some variables

# Get the file
directory_path = 'E:/Shared drives/Kolkowitz Lab Group/iPython_console/'
file_name = '2019-07-18_ipython.txt'
#file_name = 'test.txt'
file = open(directory_path + file_name, 'r')


# Define the num_runs and _num_steps
#num_runs = 2
#num_steps = 3
num_runs = 29
num_steps = 101

# Create some temperorary lists to save the raw data in
time = []
signal = []
reference = []

# %% Parse
# Extract the numbers from the txt file
for line in file:
    if line[0:10] == 'Run index:':
        temp = line.split(':')
    
    if line[0:22] == 'First relaxation time:':
        temp = line.split(':')
        time.append(int(temp[1]))
        
    if line[0:23] == 'Second relaxation time:':
        temp = line.split(':')
        time.append(int(temp[1]))
    
    if line[0:12] == 'First signal':
        temp = line.split('=')
        signal.append(int(temp[1]))
        
    if line[0:15] == 'First Reference':
        temp = line.split('=')
        reference.append(int(temp[1]))
        
    if line[0:13] == 'Second Signal':
        temp = line.split('=')
        signal.append(int(temp[1]))
        
    if line[0:16] == 'Second Reference':
        temp = line.split('=')
        reference.append(int(temp[1]))

# Zip the data together
data_list = list(zip(time, signal, reference))

# %% Sort

data = []

# sort the data based on the times, and in each run
for ind in range(num_runs):
    i = ind * (num_steps  + 1)
#    data_list[i:i+num_steps] = sorted(data_list[i:i+num_steps], key=lambda t: t[0])
    data.append(sorted(data_list[i:i+num_steps+1], key=lambda t: t[0]))

# %% Seperate the data and average
# Define lists to keep the taus, and averaged sig and ref counts
taus = []
avg_sig_counts = []
avg_ref_counts = []

# Average all the signal and referene counts
#step through each time point
for step_ind in range(num_steps+1):

    signal_at_tau_list = []
    reference_at_tau_list = []

    # for each time point, add all the signal and reference counts to a list and average
    for run_ind in range(num_runs):
        signal_at_tau_list.append(data[run_ind][step_ind][1])
        reference_at_tau_list.append(data[run_ind][step_ind][2])
    
    # Now average those counts at one point together
    avg_sig_counts.append(numpy.average(signal_at_tau_list))
    avg_ref_counts.append(numpy.average(reference_at_tau_list))
    taus.append(data[0][step_ind][0])
    
# delete one of the double middle times
avg_sig_counts = numpy.delete(avg_sig_counts, 50)
avg_ref_counts = numpy.delete(avg_ref_counts, 50)
taus = numpy.delete(taus, 50)
    
# Normalize the data
try:
    norm_avg_sig = numpy.array(avg_sig_counts) / numpy.array(avg_ref_counts)
except RuntimeWarning as e:
    print(e)
    inf_mask = numpy.isinf(norm_avg_sig)
    # Assign to 0 based on the passed conditional array
    norm_avg_sig[inf_mask] = 0
    
# %% Plot the data

raw_fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))

ax = axes_pack[0]
ax.plot(numpy.array(taus) / 10**3, avg_sig_counts, 'r-', label = 'signal')
ax.plot(numpy.array(taus) / 10**3, avg_ref_counts, 'g-', label = 'reference')
ax.set_xlabel('\u03C4 (us)')  # tau = \u03C4 in unicode
ax.set_ylabel('Counts')
ax.legend()

ax = axes_pack[1]
ax.plot(numpy.array(taus) / 10**3, norm_avg_sig, 'b-')
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
            'data': data,
            'avg_sig_counts': avg_sig_counts.tolist(),
            'avg_sig_counts-units': 'counts',
            'avg_ref_counts': avg_ref_counts.tolist(),
            'avg_ref_counts-units': 'counts',
            'norm_avg_sig': norm_avg_sig.astype(float).tolist(),
            'norm_avg_sig-units': 'arb'}
    
with open(directory_path + 'attempt2.txt', 'w') as file:
        json.dump(raw_data, file, indent=2)
        
raw_fig.savefig(directory_path + 'attempt2.svg')


