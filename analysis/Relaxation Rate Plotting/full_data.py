# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 14:36:23 2019

This file plots the relaxation rate data collected for the nv1_2019_05_10.

The data is input manually, and plotted on a loglog plot with error bars along
the y-axis. A 1/f**2 line is also fit to the gamma rates to show the behavior.

@author: Aedan
"""

'''
nv1_2019_05_10

files used:
    
    
2019-06-14_09-48-56_116.0_MHz_splitting_rate_analysis

'''
# %%
def fit_eq(f, amp):
    return amp*f**(-2)

# %%

import matplotlib.pyplot as plt
from scipy import asarray as ar, exp
from scipy.optimize import curve_fit
import numpy

# nv1_2019_05_10
nv1_splitting_list = [19.8, 28, 30, 32.7, 51.8, 97.8, 116]
nv1_omega_avg_list = [1.3, 1.7, 1.62, 1.48, 2.3, 1.8, 1.18]
nv1_omega_error_list = [0.2, 0.4, 0, 0.09, 0.4, 0.2, 0.13]
nv1_gamma_avg_list = [136, 68, 37, 50, 13.0, 3.5, 4.6]
nv1_gamma_error_list = [10, 7, 6, 3, 0.6, 0.2, 0.3]

# nv2_2019_04_30
nv2_splitting_list = [29.1, 44.8, 56.2, 56.9, 69.8, 85.1, 101.6]
nv2_omega_avg_list = [0.37, 0.52, 0.33, 0.41, 0.33, 0.32, 0.27]
nv2_omega_error_list = [0.06, 0.11, 0.07, 0.06, 0.06, 0.04, 0.04]
nv2_gamma_avg_list = [20.8, 7.2, 3.9, 3.9, 2.46, 2.9, 1.6]
nv2_gamma_error_list = [0.9, 0.3, 0.2, 0.2, 0.14, 0.2, 0.2]

# nv13_2019_06_10
nv13_splitting_list = [23.1, 28.0, 29.4, 29.8, 51.9, 72.4, 112.9, 164.1]
nv13_omega_avg_list = [0.42, 0.9, 1.2, 0.9, 1.2, 0.8, 1.4, 1.2]
nv13_omega_error_list = [0.12, 0.4, 0.2, 0.4, 0.6, 0.4, 0.3, 0.2]
nv13_gamma_avg_list = [90, 58, 74, 25, 30, 22, 13, 5.8]
nv13_gamma_error_list = [30, 8, 16, 5, 5, 3, 3, 0.5]

# nv0_2019_06_06
nv0_splitting_list = [48.1]
nv0_omega_avg_list = [0.45]
nv0_omega_error_list = [0.14]
nv0_gamma_avg_list = [17.5]
nv0_gamma_error_list = [0.7]

# nv4_2019_06_06
nv4_splitting_list = [28.5]
nv4_omega_avg_list = [1.4]
nv4_omega_error_list = [0.3]
nv4_gamma_avg_list = [201]
nv4_gamma_error_list = [16]

fig, ax = plt.subplots(1, 1, figsize=(8, 6))

#ax.errorbar(splitting_list, omega_avg_list, yerr = omega_error_list)
ax.set_xscale("log", nonposx='clip')
ax.set_yscale("log", nonposy='clip')
ax.errorbar(nv1_splitting_list, nv1_gamma_avg_list, yerr = nv1_gamma_error_list, 
            label = 'nv1_2019_05_10', fmt='o', color='blue')
#ax.errorbar(nv1_splitting_list, nv1_omega_avg_list, yerr = nv1_omega_error_list, 
#            label = 'nv1 Omega', fmt='o', color='red')

ax.errorbar(nv2_splitting_list, nv2_gamma_avg_list, yerr = nv2_gamma_error_list, 
            label = 'nv2_2019_04_30', fmt='o', color='orange')
#ax.errorbar(nv2_splitting_list, nv2_omega_avg_list, yerr = nv2_omega_error_list, 
#            label = 'nv2 Omega', fmt='o', color='orange')

ax.errorbar(nv13_splitting_list, nv13_gamma_avg_list, yerr = nv13_gamma_error_list, 
            label = 'nv13_2019_06_10', fmt='o', color='red')
#ax.errorbar(nv13_splitting_list, nv13_omega_avg_list, yerr = nv13_omega_error_list, 
#            label = 'nv13 Omega', fmt='o', color='red')

ax.errorbar(nv0_splitting_list, nv0_gamma_avg_list, yerr = nv0_gamma_error_list, 
            label = 'nv0_2019_06_06', fmt='o', color='green')
#ax.errorbar(nv0_splitting_list, nv0_omega_avg_list, yerr = nv0_omega_error_list, 
#            label = 'nv0 Omega', fmt='o', color='red')

ax.errorbar(nv4_splitting_list, nv4_gamma_avg_list, yerr = nv4_gamma_error_list, 
            label = 'nv4_2019_06_06', fmt='o', color='purple')
#ax.errorbar(nv4_splitting_list, nv4_omega_avg_list, yerr = nv4_omega_error_list, 
#            label = 'nv4 Omega', fmt='o', color='red')

ax.grid()

#SMALL_SIZE = 8
#MEDIUM_SIZE = 10
#BIGGER_SIZE = 12
#
#plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
#plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
#plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
#plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
#plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
#plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
#plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

ax.set_xlabel('Splitting (MHz)')
ax.set_ylabel('Relaxation Rate (kHz)')
ax.set_title('Double quantum relaxation rates')
ax.legend()

fig.canvas.draw()
fig.canvas.flush_events()
