# -*- coding: utf-8 -*-
"""CPMG dynamical decoupling routine.

Created on Sun Jun 16 11:38:17 2019

@author: mccambria
"""


# %% Imports


from utils import tool_belt
import time
import numpy
import os
from random import shuffle
from scipy.optimize import curve_fit


# %% Functions


def clean_up(cxn):

    cxn.microwave_signal_generator.uwave_off()
    cxn.apd_tagger.stop_tag_stream()
    cxn.pulse_streamer.force_final()


def stretch_exp(x, offset, amp, delay, beta):

    return offset + (amp * numpy.exp((x-delay)**beta))


# %% Figure functions


def create_raw_figure(precession_times, avg_sig_counts, ref_sig_counts
                      norm_avg_sig):

    # Get the figure and axes
    fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))

    # Signal and reference
    ax = axes_pack[0]
    ax.plot(taus, avg_sig_counts, 'r-', label='Signal')
    ax.plot(taus, avg_ref_counts, 'g-', label='Reference')
    ax.legend()
    ax.set_title('Counts Versus Free Precession Time')
    ax.set_xlabel(r'Free Precession Time ($\mu$s)')
    ax.set_ylabel('Counts')

    # Normalized
    ax = axes_pack[1]
    ax.plot(taus, norm_avg_sig, 'b-')
    ax.set_title('Normalized Signal Versus Free Precession Time')
    ax.set_xlabel(r'Free Precession Time ($\mu$s)')
    ax.set_ylabel('Contrast (arb. units)')

    # Draw
    fig.set_tight_layout(True)
    fig.canvas.draw()
    fig.canvas.flush_events()


def create_fit_figure(precession_times, norm_avg_sig, fit_params):

    # Get the figure and axis
    fig, axes_pack = plt.subplots(1, 1, figsize=(8.5, 8.5))
    ax = axes_pack[0]

    # Data
    ax.plot(taus, norm_avg_sig, 'bo', label='Data')

    # Fit
    smooth_precession_times = numpy.linspace(precession_times[0],
                                             precession_times[-1],
                                             1000)
    ax.plot(smooth_precession_times,
            stretch_exp(smooth_precession_times, *fit_params),
            'r-', label='Fit')

    # Labelling
    ax.legend()
    ax.set_title('Normalized Signal Versus Free Precession Time')
    ax.set_xlabel(r'Free Precession Time ($\mu$s)')
    ax.set_ylabel('Contrast (arb. units)')
    # text = '\n'.join((r'$C + A_0 e^{-t/d} \mathrm{cos}(2 \pi \nu t + \phi)$',
    #                   r'$C = $' + '%.3f'%(opti_params[0]),
    #                   r'$A_0 = $' + '%.3f'%(opti_params[1]),
    #                   r'$\frac{1}{\nu} = $' + '%.1f'%(rabi_period) + ' ns',
    #                   r'$d = $' + '%i'%(opti_params[3]) + ' ' + r'$ ns$'))
    # props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    # ax.text(0.55, 0.25, text, transform=ax.transAxes, fontsize=12,
    #         verticalalignment='top', bbox=props)

    # Draw
    fig.set_tight_layout(True)
    fig.canvas.draw()
    fig.canvas.flush_events()



# %% Main


def main(cxn, nv_sig, nd_filter, apd_indices,
         uwave_freq, uwave_power, pi_pulse,
         cpmg_n, precession_time_range,
         num_steps, num_reps, num_runs, name='untitled'):

    # %% Initial setup

    start_time = time.time()

    precession_times = numpy.linspace(precession_time_range[0],
                                      precession_time_range[1],
                                      num_steps)

    precession_time_inds = list(range(0, num_steps))

    opti_coords_list = []

    file_name = os.path.basename(__file__)

    sig_counts = numpy.zeros([num_runs, num_steps], dtype=numpy.int32)
    ref_counts = numpy.copy(sig_counts)

    # %% Microwave and modulation setup

    cxn.microwave_signal_generator.set_freq(uwave_freq)
    cxn.microwave_signal_generator.set_amp(uwave_power)
    cxn.microwave_signal_generator.load_iq()
    cxn.microwave_signal_generator.uwave_on()

    # %% Collect the data

    # 'Press enter to stop...'
    tool_belt.init_safe_stop()

    for run_ind in range(num_runs):

        if tool_belt.safe_stop():
            break

        # Shuffle the independent variable
        shuffle(precession_time_inds)

        # Optimize
        opti_coords = optimize.main(cxn, nv_sig, nd_filter, apd_indices)
        opti_coords_list.append(opti_coords)

        # Load the APD
        cxn.apd_tagger.start_tag_stream(apd_indices)

        for precession_time_ind in precession_time_inds:

            if tool_belt.safe_stop():
                break

            precession_time = precession_times[precession_time_ind]

            # Stream the sequence
            args = [taus[tau_ind], polarization_time, reference_time,
                    signal_wait_time, reference_wait_time,
                    background_wait_time, aom_delay_time,
                    gate_time, max_uwave_time,
                    apd_indices[0], uwave_source]
            cxn.pulse_streamer.stream_immediate(file_name, num_reps, args, 1)

            # Get the counts
            new_counts = cxn.apd_tagger.read_counter_separate_gates(1)
            sample_counts = new_counts[0]

            # sig counts are even - get every second element starting from 0
            sig_gate_counts = sample_counts[0::2]
            sig_counts[run_ind, precession_time_ind] = sum(sig_gate_counts)

            # ref counts are odd - get every second element starting from 1
            ref_gate_counts = sample_counts[1::2]
            ref_counts[run_ind, precession_time_ind] = sum(ref_gate_counts)

        cxn.apd_tagger.stop_tag_stream()

    # %% Process and display the data

    # Average and normalize
    avg_sig_counts = numpy.average(sig_counts, axis=0)
    avg_ref_counts = numpy.average(ref_counts, axis=0)
    norm_avg_sig = avg_sig_counts / avg_ref_counts

    # Extract fit
    offset = 0.8  # Constrast floor
    coeff = 0.2
    delay = 50.0  # Delay before decay in us
    beta = 0.5  # Stretching factor

    guess_params = [offset, coeff, delay, beta]

    try:
        fit_params, cov_arr = curve_fit(stretch_exp,
                                         precession_times, norm_avg_sig,
                                         p0=guess_params)
    except Exception:
        print('Fit failed')
        fit_params = None

    # Create figures
    raw_fig = create_raw_figure()
    if fit_params is not None:
        fit_fig = create_fit_figure()


    # %% Wrap up

    clean_up(cxn)

    end_time = time.time()

    # Set up the raw data dictionary
    raw_data = {}

    # Save the data and the figures from this run
    tool_belt.save_data(name, raw_data, raw_fig, fit_fig)


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # You should at least be able to recreate a data set's figures when you
    # run a file so we'll do that as an example here

    # Get the data
    file_name = ''  # eg '2019-06-07_14-20-27_ayrton12'
    data = tool_belt.get_raw_data(__file__, file_name)

    # Replot
    create_raw_figure()
    create_fit_figure()
