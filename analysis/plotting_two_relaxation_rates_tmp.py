# -*- coding: utf-8 -*-
"""
Created on Wed Jul  3 09:51:31 2019

@author: Aedan
"""

# %% Imports

import numpy
from scipy import exp
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

import utils.tool_belt as tool_belt

# %% Functions

# The exponential function used to fit the data

def exp_eq(t, rate, amp, offset):
    return offset + amp * exp(- rate * t)

# %%
    
time_linspace = numpy.linspace(0,10,1000)

# 23 MHz splitting, 
data = tool_belt.get_raw_data('t1_double_quantum', 
                              '22.9_MHz_splitting_1_bins_all_data', 
                              'nv0_2019_06_27_23MHz')

zero_relaxation_counts_23 = data['zero_relaxation_counts']
zero_zero_time_23 = data['zero_zero_time']
opti_params_23 = data['omega_opti_params']
    
# 228 MHz splitting, 
data = tool_belt.get_raw_data('t1_double_quantum', 
                              '228.0_MHz_splitting_1_bins_all_data', 
                              'nv0_2019_06_27_228MHz')

zero_relaxation_counts_228 = data['zero_relaxation_counts']
zero_zero_time_228 = data['zero_zero_time']
opti_params_228 = data['omega_opti_params']
    
fig, ax = plt.subplots(1, 1, figsize=(10, 8))

ax.plot(zero_zero_time_23, zero_relaxation_counts_23, 'bo', label = '23 MHz splitting data')
ax.plot(time_linspace,
                    exp_eq(time_linspace, *opti_params_23),
                    'teal', label = '23 MHz splitting fit')
ax.plot(zero_zero_time_228, zero_relaxation_counts_228, 'ro', label = '228 MHz splitting data')
ax.plot(time_linspace,
                    exp_eq(time_linspace, *opti_params_228),
                    'orange', label = '228 MHz splitting fit')
ax.set_xlabel('Relaxation time (ms)')
ax.set_ylabel('Normalized signal Counts')
ax.set_title('Comparing omega rate of bulk diamond at two splittings')
ax.legend()


