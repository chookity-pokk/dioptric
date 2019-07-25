# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 11:48:33 2019

@author: mccambria
"""

import utils.tool_belt as tool_belt
import numpy
import matplotlib.pyplot as plt

data = tool_belt.get_raw_data('ramsey', '2019-07-12_18-29-39_johnson1', 'branch_ramsey2')

sig_counts = data['sig_counts']
ref_counts = data['ref_counts']
avg_sig_counts = numpy.average(sig_counts, axis=0)
avg_ref_counts = numpy.average(ref_counts, axis=0)
#avg_ref = numpy.average(avg_ref_counts)
norm_avg_sig = data['norm_avg_sig']
#norm_avg_sig = avg_sig_counts / numpy.average(avg_ref_counts)  # single-valued reference
num_steps = data['num_steps']
precession_time_range = data['precession_time_range']
min_tau = precession_time_range[0]
max_tau = precession_time_range[1]
taus = numpy.linspace(min_tau, max_tau, num_steps)

# Fake
#min_tau = precession_time_range[0]
#max_tau = precession_time_range[1]
#max_tau *= 2
#num_steps = 101

time_step = (max_tau - min_tau) / (num_steps - 1)
time_step /= 1000  # to us

transform = numpy.fft.rfft(ref_counts[0])
window = max_tau - min_tau
freqs = numpy.fft.rfftfreq(num_steps, d=time_step)

transform_mag = numpy.absolute(transform)

raw_fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))
ax = axes_pack[0]
ax.plot(taus / 10**3, avg_sig_counts, 'r-', label = 'signal')
ax.plot(taus / 10**3, avg_ref_counts, 'g-', label = 'reference')
ax.set_xlabel('Precession time (us)')
ax.set_ylabel('Counts')
ax.legend()
ax = axes_pack[1]
ax.plot(taus / 10**3, norm_avg_sig, 'b-')
ax.set_title('Ramsey Measurement')
ax.set_xlabel('Precession time (us)')
ax.set_ylabel('Contrast (arb. units)')
raw_fig.canvas.draw()
# fig.set_tight_layout(True)
raw_fig.canvas.flush_events()


fig, ax= plt.subplots(1, 1, figsize=(10, 8))
fig.set_tight_layout(True)
ax.plot(freqs[1:], transform_mag[1:])  # [1:] excludes frequency 0 (DC component)
ax.set_xlabel('Frequency (MHz)')
ax.set_ylabel('FFT magnitude')
ax.set_title('Ramsey FFT')
