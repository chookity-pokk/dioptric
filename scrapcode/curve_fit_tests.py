# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 17:53:37 2019

@author: mccambria
"""

import numpy
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

def line(t, a, b):
    return a + (b * t)

def line_d_a(t, a, b):
    return 1 + (0 * t)

def line_d_b(t, a, b):
    return t

def exp_dec(t, rate, amp):
    return amp * numpy.exp(-rate * t)

def exp_dec_d_rate(t, rate, amp):
    return (-t) * amp * numpy.exp(-rate * t)

def exp_dec_d_amp(t, rate, amp):
    return numpy.exp(-rate * t)

def exp_dec_offset(t, rate, amp, offset):
    return offset + (amp * numpy.exp(-rate * t))

t = numpy.linspace(0, 10, 6)
y_vals = [9, 6, 4, 3, 2, 1.5]
sigmas = [2, 1, 1, 0.5, 1, 0.5]

# plt.plot(t, y_vals)
# plt.errorbar(t, y_vals, yerr=sigmas, linestyle='None')

# fit_func = line
fit_func = exp_dec

popt, pcov = curve_fit(fit_func, t, y_vals)
# popt, pcov = curve_fit(fit_func, t, y_vals, sigma=sigmas, absolute_sigma=True)
print(pcov)

# Get the chi squared
residuals = y_vals - fit_func(t, *popt)
chi_squared = sum((residuals) ** 2)  # without sigmas
# chi_squared = chisq = sum((residuals / sigmas) ** 2)  # with sigmas
reduced_chi_squared = chi_squared / (len(t) - 2)  # chi squared per degree of freedom

# Compute summed jacobian
summed_jacobian = numpy.empty((2,2))
# summed_jacobian[0,0] = sum(line_d_a(t, *popt) * line_d_a(t, *popt))
# summed_jacobian[0,1] = sum(line_d_a(t, *popt) * line_d_b(t, *popt))
# summed_jacobian[1,0] = sum(line_d_b(t, *popt) * line_d_a(t, *popt))
# summed_jacobian[1,1] = sum(line_d_b(t, *popt) * line_d_b(t, *popt))
summed_jacobian[0,0] = sum(exp_dec_d_rate(t, *popt) * exp_dec_d_rate(t, *popt))
summed_jacobian[0,1] = sum(exp_dec_d_rate(t, *popt) * exp_dec_d_amp(t, *popt))
summed_jacobian[1,0] = sum(exp_dec_d_amp(t, *popt) * exp_dec_d_rate(t, *popt))
summed_jacobian[1,1] = sum(exp_dec_d_amp(t, *popt) * exp_dec_d_amp(t, *popt))

# Manually calculate the covariances to check what scipy is really doing
# Where f is the fit_func and pi is the ith fit param, the covariances are:
# cov = reduced_chi_squared * summed_jacobian^-1
print(reduced_chi_squared * numpy.linalg.inv(summed_jacobian))

smooth_t = numpy.linspace(0, 10, 1000)
# plt.plot(smooth_t, fit_func(smooth_t, *popt))
