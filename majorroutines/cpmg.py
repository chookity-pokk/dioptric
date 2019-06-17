# -*- coding: utf-8 -*-
"""CPMG dynamical decoupling routine.

Created on Sun Jun 16 11:38:17 2019

@author: mccambria
"""


# %% Imports


import utils.tool_belt as tool_belt
import utils.constants as constants
import time
import numpy
import os
from random import shuffle


# %% Constants


# %% Functions


def clean_up(cxn):

    pass


def save_data(name, raw_data, figs):
    """Save the raw data to a txt file as a json object. Save the figures as
    svgs.
    """

    time_stamp = tool_belt.get_time_stamp()

    file_path = tool_belt.get_file_path(__file__, time_stamp, name)

    tool_belt.save_raw_data(rawData, file_path)

    for fig in figs:
        tool_belt.save_figure(fig, file_path)


# %% Figure functions


def create_raw_figure():

    pass


def update_raw_figure():

    pass


def create_fit_figure():

    pass


# %% Main


def main(cxn, nv_sig, nd_filter, apd_indices,
         uwave_freq, uwave_power, uwave_source,
         cpmg_n, precession_time_range,
         num_steps, num_reps, num_runs, name='untitled'):

    # %% Initial setup

    if uwave_source != constants.UwaveSource.TEKTRONIX:
        print('Only the Tektronix currently supports the modulation' \
              'necessary for CPMG.')
        return

    start_time = time.time()

    precession_times = numpy.linspace(precession_time_range[0],
                                      precession_time_range[1],
                                      num_steps)

    precession_time_inds = list(range(0, num_steps))

    opti_coords_list = []

    file_name = os.path.basename(__file__)
    sequence_args = [taus[0], polarization_time, reference_time,
                    signal_wait_time, reference_wait_time,
                    background_wait_time, aom_delay_time,
                    gate_time, max_uwave_time,
                    apd_indices[0], do_uwave_gate]
    cxn.pulse_streamer.stream_load(file_name, sequence_args, 1)

    # %% Microwave and modulation setup

    cxn.microwave_signal_generator.set_freq(uwave_freq)
    cxn.microwave_signal_generator.set_amp(uwave_power)
    cxn.microwave_signal_generator.load_iq()
    cxn.microwave_signal_generator.uwave_on()

    # %% Collect the data

    # 'Press enter to stop...'
    tool_belt.init_safe_stop()

    for run_ind in range(num_runs):

        # Break out of the loop if the user says stop
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

            precession_time = precession_times[precession_time_ind]




    # %% Wrap up

    clean_up(cxn)

    # Set up the raw data dictionary
    raw_data = {}

    # Save the data and the figures from this run
    save_data(name, raw_data, figs)


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
