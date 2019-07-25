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


'''
# %%
def fit_eq_alpha(f, amp, alpha):
    return amp*f**(-alpha)

# %%

import matplotlib.pyplot as plt
#from scipy import asarray as ar, exp
#from scipy.optimize import curve_fit
#import numpy

# The data
nv0_splitting_list = [23.9, 125.9, 128.1, 233.2]
nv0_omega_avg_list = [0.065, 0.057, 0.059, 0.046]
nv0_omega_error_list = [0.013, 0.010, 0.014, 0.008]
nv0_gamma_avg_list = [0.15, 0.139, 0.13, 0.13]
nv0_gamma_error_list = [0.03, 0.014, 0.02, 0.02]

# Try to fit the gamma to a 1/f^2

#fit_1_params, cov_arr = curve_fit(fit_eq_1, nv1_splitting_list, nv1_gamma_avg_list, 
#                                p0 = 100)
#
#fit_2_params, cov_arr = curve_fit(fit_eq_2, nv1_splitting_list, nv1_gamma_avg_list, 
#                                p0 = 100)
#
#fit_alpha_params, cov_arr = curve_fit(fit_eq_alpha, nv1_splitting_list, nv1_gamma_avg_list, 
#                                p0 = (100, 1))
#
#splitting_linspace = numpy.linspace(nv1_splitting_list[0], nv1_splitting_list[-1],
#                                    1000)


fig, ax = plt.subplots(1, 1, figsize=(10, 8))

#ax.errorbar(splitting_list, omega_avg_list, yerr = omega_error_list)

axis_font = {'size':'14'}

ax.set_xscale("log", nonposx='clip')
ax.set_yscale("log", nonposy='clip')
ax.errorbar(nv0_splitting_list, nv0_gamma_avg_list, yerr = nv0_gamma_error_list, 
            label = r'$\gamma$', fmt='o', color='blue')
ax.errorbar(nv0_splitting_list, nv0_omega_avg_list, yerr = nv0_omega_error_list, 
            label = r'$\Omega$', fmt='o', color='red')

#ax.plot(splitting_linspace, fit_eq_2(splitting_linspace, *fit_2_params), 
#            label = r'$f^{-2}$', color ='teal')
#ax.plot(splitting_linspace, fit_eq_1(splitting_linspace, *fit_1_params), 
#            label = r'$f^{-1}$', color = 'orange')

# %%

#ax.plot(splitting_linspace, fit_eq_alpha(splitting_linspace, *fit_alpha_params), 
#            label = r'$1/f^\alpha$')

#text = '\n'.join((r'$1/f^{\alpha}$ fit:',
#                  r'$\alpha = $' + '%.2f'%(fit_alpha_params[1])
#                  r'$A_0 = $' + '%.4f'%(fit_params[1] * 10**6) + ' kHz'
#                  ,r'$a = $' + '%.2f'%(fit_params[2])
#                  ))

#props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
#ax.text(0.85, 0.8, text, transform=ax.transAxes, fontsize=12,
#        verticalalignment='top', bbox=props)

# %%

ax.tick_params(which = 'both', length=6, width=2, colors='k',
                grid_alpha=0.7, labelsize = 18)

ax.tick_params(which = 'major', length=12, width=2)

ax.grid()

plt.xlabel('Splitting (MHz)', fontsize=18)
plt.ylabel('Relaxation Rate (kHz)', fontsize=18)
plt.title('Bulk Diamond, NV 0', fontsize=18)
ax.legend(fontsize=18)
