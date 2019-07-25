# -*- coding: utf-8 -*-
"""Automatically optimize the magnet angle by recording the splittings
at various magnet orientations.

Created on Sun Jun 16 11:38:17 2019

@author: mccambria
"""


# %% Imports


import utils.tool_belt as tool_belt
import labrad
import matplotlib.pyplot as plt
import numpy
from scipy.optimize import curve_fit
import majorroutines.pulsed_resonance as pulsed_resonance
from random import shuffle
import copy


# %% Figure functions


def create_fit_figure(splittings, angles, fit_func, popt):
    fig, ax = plt.subplots(figsize=(8.5, 8.5))

    ax.set_title('ESR Splitting Versus Magnet Angle')
    ax.set_xlabel('Angle (deg)')
    ax.set_ylabel('Splitting (GHz)')
    ax.scatter(angles, splittings, c='r')

    x_vals = numpy.linspace(0, 180, 1000)
    y_vals = fit_func(x_vals, *popt)
    ax.plot(x_vals, y_vals)

    fig.canvas.draw()
    fig.set_tight_layout(True)
    fig.canvas.flush_events()
    
    return fig


# %% Other functions


def clean_up(cxn):

    tool_belt.reset_cfm()

def save_data(name, raw_data, figs):
    """Save the raw data to a txt file as a json object. Save the figures as
    svgs.
    """

    time_stamp = tool_belt.get_time_stamp()

    file_path = tool_belt.get_file_path(__file__, time_stamp, name)

    tool_belt.save_raw_data(raw_data, file_path)

    for fig in figs:
        tool_belt.save_figure(fig, file_path)

def AbsCos(angle, offset, amp, phase):
    return offset + abs(amp * numpy.cos(angle * numpy.pi / 180 + phase * numpy.pi / 180))

def AbsCosNoOff(angle, amp, phase):
    return abs(amp * numpy.cos(angle * numpy.pi / 180 + phase * numpy.pi / 180))


# %% Main


def main(nv_sig, apd_indices, angle_range, num_angle_steps,
         freq_center, freq_range,
         num_freq_steps, num_freq_reps, num_freq_runs,
         uwave_power, uwave_pulse_dur):
    """When you run the file, we'll call into main, which should contain the
    body of the routine.
    """

    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig, apd_indices, angle_range, num_angle_steps,
                      freq_center, freq_range,
                      num_freq_steps, num_freq_reps, num_freq_runs,
                      uwave_power, uwave_pulse_dur)
    
def main_with_cxn(cxn, nv_sig, apd_indices, angle_range, num_angle_steps,
                  freq_center, freq_range,
                  num_freq_steps, num_freq_reps, num_freq_runs,
                  uwave_power, uwave_pulse_dur):

    # %% Initial set up here
    
    angles = numpy.linspace(angle_range[0], angle_range[1], num_angle_steps)
    angle_inds = numpy.linspace(0, num_angle_steps-1, num_angle_steps, dtype=int)
    shuffle(angle_inds)
    resonances = numpy.empty((num_angle_steps, 2))  # Expect 2 resonances
    resonances[:] = numpy.nan
    splittings = numpy.empty(num_angle_steps)
    splittings[:] = numpy.nan
    
    # %% Collect the data
    
    nv_sig_copy = copy.deepcopy(nv_sig)
    pesr = pulsed_resonance.main_with_cxn
    
    for ind in angle_inds:
        
        angle = angles[ind]
        nv_sig_copy['magnet_angle'] = angle
        
        angle_resonances = pesr(cxn, nv_sig_copy, apd_indices,
                                freq_center, freq_range,
                                num_freq_steps, num_freq_reps, num_freq_runs,
                                uwave_power, uwave_pulse_dur)
        resonances[ind, :] = angle_resonances
        # Check if all the returned values are truthy (no Nones)
        if all(angle_resonances):
            splittings[ind] = (angle_resonances[1] - angle_resonances[0]) * 1000
            
    # %% Analyze the data
    
    fit_func = AbsCosNoOff
    amp = 200
    phase = 0
    guess_params = [amp, phase]
    # Check if we have any undefined splittings
    if any(numpy.isnan(splittings)):
        opti_angle = None
        fig = None
    else:
        popt, pcov = curve_fit(fit_func, angles, splittings, p0=guess_params)
        # Find the angle at the peak within [0, 360]
        opti_angle = (-popt[1]) % 360 
        fig = create_fit_figure(splittings, angles, fit_func, popt)

    # %% Wrap up

    if opti_angle is not None:
        cxn.rotation_stage_ell18k.set_angle(opti_angle)
        print('Optimized angle: {}'.format(opti_angle))

    # Set up the raw data dictionary
    raw_data = {'nv_sig': nv_sig,
                'nv_sig-units': tool_belt.get_nv_sig_units(),
                'apd_indices': apd_indices,
                'angle_range': angle_range,
                'angle_range-units': 'deg',
                'num_angle_steps': num_angle_steps,
                'freq_center': freq_center,
                'freq_center-units': 'GHz',
                'freq_range': freq_range,
                'freq_range-units': 'GHz',
                'num_freq_steps': num_freq_steps,
                'num_freq_runs': num_freq_runs,
                'uwave_power': uwave_power,
                'uwave_power-units': 'dBm',
                'resonances': resonances.tolist(),
                'resonances-units': 'GHz',
                'splittings': splittings.tolist(),
                'splittings-units': 'MHz',
                'opti_angle': opti_angle,
                'opti_angle-units': 'deg'}

    # Save the data and the figures from this run
    if fig is not None:
        save_data(nv_sig['name'], raw_data, [fig])


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # You should at least be able to recreate a data set's figures when you
    # run a file so we'll do that as an example here

    # Get the data
    
#    file_name = ''  # eg '2019-06-07_14-20-27_ayrton12.txt'
#    data = tool_belt.get_raw_data(__file__, file_name)
    splittings = [170, 140, 80, 201, 223, 30]
    angles = [0.0, 90.0, 150.0, 60.0, 30.0, 120.0]
    
    fit_func = AbsCosNoOff
    amp = 200
    phase = 0
    guess_params = [amp, phase]
    popt, pcov = curve_fit(fit_func, angles, splittings, p0=guess_params)
    # Find the angle at the peak within [0, 360]
    opti_angle = (-popt[1]) % 360
    print(opti_angle)
        
    # Replot
    create_fit_figure(splittings, angles, fit_func, popt)
