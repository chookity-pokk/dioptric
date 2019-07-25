# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 11:24:37 2019

This file plots the center frequency for the nv13_2019_06_10 vs the splitting.

@author: Aedan
"""
# %%
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy

# %%
def fit_eq(f, offset, amp):
    return offset + amp * f**(2)

# %%

splitting_list = [23.1, 28.0, 29.4, 29.8, 51.9, 72.4, 112.9, 164.1]

cent_freq = [2.84045, 2.8396, 2.8409, 2.8396, 2.84335, 2.8444, 2.85125, 2.86775 ]


fit_params, cov_arr = curve_fit(fit_eq, splitting_list, cent_freq, 
                                p0 = (2.7, 0.1))

splitting_linspace = numpy.linspace(splitting_list[0], splitting_list[-1], 1000)


fig, ax = plt.subplots(1, 1, figsize=(10, 8))
ax.plot(splitting_list, cent_freq, 'bo', label = 'data')
ax.plot(splitting_linspace, fit_eq(splitting_linspace, *fit_params), 'r', label = 'fit')

text = '\n'.join((r'$f_0 + A_0 f^{2}$',
                  r'$f_0 = $' + '%.2f'%(fit_params[0]) + ' GHz',
                  r'$A_0 = $' + '%.4f'%(fit_params[1] * 10**6) + ' kHz'
#                  ,r'$a = $' + '%.2f'%(fit_params[2])
                  ))


props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax.text(0.75, 0.40, text, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)
    
#print(fit_params[1])

ax.set_xlabel('Splitting (MHz)')
ax.set_ylabel('Center Frequency (GHz)')
ax.set_title('Center frequency shift vs splitting, nv13_2019_06_10')
ax.legend()