# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 17:11:03 2019

@author: mccambria
"""


# %% Imports


import json
import numpy
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import utils.tool_belt as tool_belt


# %% Input parameters


folder_dir = 'E:\\Shared drives\\Kolkowitz Lab Group\\nvdata\\rabi\\'
file_name = '2019-06-27_18-04-33_johnson1.txt'

# Estimated fit parameters
offset = 0.92
amplitude = 0.08
frequency = 1/250
decay = 1000


# %% Run the file


with open('{}{}'.format(folder_dir, file_name)) as file:
    data = json.load(file)
    norm_avg_sig = data['norm_avg_sig']
    uwave_time_range = data['uwave_time_range']
    min_uwave_time = uwave_time_range[0]
    max_uwave_time = uwave_time_range[1]
    num_steps = data['num_steps']
    
taus = numpy.linspace(min_uwave_time, max_uwave_time,
                      num=num_steps, dtype=numpy.int32)

fit_func = tool_belt.cosexp

#    init_params = [offset, amplitude, frequency, phase, decay]
init_params = [offset, amplitude, frequency, decay]

try:
    opti_params, cov_arr = curve_fit(fit_func, taus, norm_avg_sig,
                                     p0=init_params)
    print(init_params)
    print(opti_params)
except Exception:
    print('Rabi fit failed - using guess parameters.')
    opti_params = init_params

rabi_period = 1 / opti_params[2]
    
linspaceTau = numpy.linspace(min_uwave_time, max_uwave_time, num=1000)

fit_fig, ax = plt.subplots(1, 1, figsize=(10, 8))
ax.plot(taus, norm_avg_sig,'bo',label='data')
ax.plot(linspaceTau, fit_func(linspaceTau, *opti_params), 'r-', label='fit')
ax.set_xlabel('Microwave duration (ns)')
ax.set_ylabel('Contrast (arb. units)')
ax.set_title('Rabi Oscillation Of NV Center Electron Spin')
ax.legend()
text = '\n'.join((r'$C + A_0 e^{-t/d} \mathrm{cos}(2 \pi \nu t + \phi)$',
                  r'$C = $' + '%.3f'%(opti_params[0]),
                  r'$A_0 = $' + '%.3f'%(opti_params[1]),
                  r'$\frac{1}{\nu} = $' + '%.1f'%(rabi_period) + ' ns',
                  r'$d = $' + '%i'%(opti_params[3]) + ' ' + r'$ ns$'))
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax.text(0.55, 0.25, text, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)

fit_fig.canvas.draw()
# fig.set_tight_layout(True)
fit_fig.canvas.flush_events()
