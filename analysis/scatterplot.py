# -*- coding: utf-8 -*-
"""
Simple scatter plotting script

Created on Fri May 31 10:38:04 2019

@author: mccambria
"""

import matplotlib.pyplot as plt
import numpy
from scipy.optimize import curve_fit

# %% Fitting functions

def AbsCos(angle, offset, amp, phase):
    return offset + abs(amp * numpy.cos(angle * numpy.pi / 180 + phase * numpy.pi / 180))

def AbsCosNoOff(angle, amp, phase):
    return abs(amp * numpy.cos(angle * numpy.pi / 180 + phase * numpy.pi / 180))

# %% Scatter raw data

angles = [100, 120, 140, 60, 80]
splittings = [108, 95, 72, 82, 101]

fig, ax = plt.subplots()

ax.set_title('ESR splitting versus magnet angle')

ax.set_xlabel('Angle (deg)')
ax.set_ylabel('Splitting (MHz)')

ax.scatter(angles, splittings, c='r')

# %% Fitting

offset = 0
amp = 230
phase = 90

#popt, pcov = curve_fit(AbsCos, angles, splittings, 
#                       p0=[offset, amp, phase])

popt, pcov = curve_fit(AbsCosNoOff, angles, splittings, 
                       p0=[amp, phase])

print(popt)

x_vals = numpy.linspace(0, 360, 1000)
#y_vals = AbsCos(x_vals, *popt)
y_vals = AbsCosNoOff(x_vals, *popt)

ax.plot(x_vals, y_vals)
