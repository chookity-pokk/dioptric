# -*- coding: utf-8 -*-
"""
This file contains functions to control the CFM. Just change the function call
in the main section at the bottom of this file and run the file. Shared or
frequently changed parameters are in the __main__ body and relatively static
parameters are in the function definitions.

Created on Sun Nov 25 14:00:28 2018

@author: mccambria
"""


# %% Imports

import labrad
import numpy
import utils.tool_belt as tool_belt
import majorroutines.image_sample as image_sample
import majorroutines.optimize as optimize
import majorroutines.stationary_count as stationary_count
import majorroutines.resonance as resonance
import majorroutines.pulsed_resonance as pulsed_resonance 
import majorroutines.rabi as rabi
import majorroutines.g2_measurement as g2_measurement
import majorroutines.t1_double_quantum as t1_double_quantum
import majorroutines.ramsey as ramsey
import minorroutines.set_drift_from_reference_image as set_drift_from_reference_image
import debug.test_major_routines as test_major_routines


# %% Minor Routines


def set_xyz(nv_sig):
    with labrad.connect() as cxn:
        tool_belt.set_xyz(cxn, nv_sig)


def set_xyz_zero():
    with labrad.connect() as cxn:
        tool_belt.set_xyz_zero(cxn)


# %% Major Routines


def do_image_sample(name, nv_sig, nd_filter, apd_indices):

    # Scan ranges

#    scan_range = 0.5
#    num_scan_steps = 150
#    num_scan_steps = 200

#    scan_range = 0.2
#    num_scan_steps = 60

    scan_range = 0.10
    num_scan_steps = 30

    with labrad.connect() as cxn:
        # For now we only support square scans so pass scan_range twice
        image_sample.main(cxn, nv_sig, nd_filter, scan_range, scan_range,
                          num_scan_steps, apd_indices, name=name)


def do_optimize(name, nv_sig, nd_filter, apd_indices):

    with labrad.connect() as cxn:
        optimize.main(cxn, nv_sig, nd_filter, apd_indices, name,
                      set_to_opti_coords=False,
                      save_data=True, plot_data=True)


def do_optimize_list(name, nv_sig_list, nd_filter, apd_indices):

    with labrad.connect() as cxn:
        optimize.optimize_list(cxn, nv_sig_list, nd_filter, apd_indices,
                               name, set_to_opti_coords=False,
                               save_data=True, plot_data=False)


def do_stationary_count(name, nv_sig, nd_filter, apd_indices):

    # In nanoseconds
    run_time = 60 * 10**9
    readout = 100 * 10**6

    with labrad.connect() as cxn:
        stationary_count.main(cxn, nv_sig, nd_filter, run_time, readout, apd_indices,
                              name=name)


def do_g2_measurement(name, nv_sig, nd_filter, apd_a_index, apd_b_index):

    # Run times are in seconds
#    run_time = 2
#    run_time = 30
#    run_time = 60 * 3
#    run_time = 60 * 5
    run_time = 60 * 10
#    run_time = 60 * 20

    diff_window = 150  # ns

    with labrad.connect() as cxn:
        g2_measurement.main(cxn, nv_sig, nd_filter, run_time, diff_window,
                            apd_a_index, apd_b_index, name=name)


def do_resonance(name, nv_sig, nd_filter, apd_indices, freq_center=2.87, freq_range=0.2):

    num_steps = 101
    num_runs = 1
    uwave_power = -13.0  # -13.0 with a 1.5 ND is a good starting point
#    uwave_power = -11.0
#    uwave_power = -10.0

    with labrad.connect() as cxn:
        resonance.main(cxn, nv_sig, nd_filter, apd_indices, freq_center, freq_range,
                               num_steps, num_runs, uwave_power, name=name)


def do_pulsed_resonance(name, nv_sig, nd_filter, apd_indices,
                        freq_center=2.87, freq_range=0.2):

    num_steps = 101
    num_runs = 4
    uwave_power = 9.0  # 9.0 is the highest reasonable value, accounting for saturation

    with labrad.connect() as cxn:
        pulsed_resonance.main(cxn, nv_sig, nd_filter, apd_indices,
                              freq_center, freq_range, num_steps, num_runs,
                              uwave_power, name=name)

def do_rabi(name, nv_sig, nd_filter, apd_indices,
            uwave_freq, do_uwave_gate_number):

    uwave_power = 9.0  # 9.0 is the highest reasonable value, accounting for saturation
    uwave_time_range = [0, 500]
#    uwave_time_range = [0, 300]
    num_steps = 51

    num_reps = 10**5

#    num_runs = 1
#    num_runs = 2
    num_runs = 4
#    num_runs = 6

    with labrad.connect() as cxn:
        rabi.main(cxn, nv_sig, nd_filter, apd_indices,
                  uwave_freq, uwave_power, uwave_time_range,
                  do_uwave_gate_number,
                  num_steps, num_reps, num_runs, name=name)


def do_t1_double_quantum(name, nv_sig, nd_filter, apd_indices,
                         uwave_freq_plus, uwave_freq_minus,
                         uwave_pi_pulse_plus, uwave_pi_pulse_minus,
                         relaxation_time_range, num_steps, num_reps,
                         init_read_list):

    uwave_power = 9
#    num_runs = 80  # This'll double the expected duration listed below!!
    num_runs = 40
#    num_runs = 20  # This'll halve the expected duration listed below
#    num_runs = 1  # Pick this one for the best noise to signal ratio

    with labrad.connect() as cxn:
        t1_double_quantum.main(cxn, nv_sig, nd_filter, apd_indices,
                     uwave_freq_plus, uwave_freq_minus, uwave_power,
                     uwave_pi_pulse_plus, uwave_pi_pulse_minus,
                     relaxation_time_range, num_steps, num_reps, num_runs,
                     init_read_list, name)


def do_ramsey_measurement(name, nv_sig, nd_filter,
                      sig_shrt_apd_index, ref_shrt_apd_index,
                      sig_long_apd_index, ref_long_apd_index):

    uwave_power = 9
    uwave_freq = 2.852
    uwave_pi_half_pulse = 32
    precession_time_range = [0, 1 * 10**3]

    num_steps = 21
    num_reps = 10**5
    num_runs = 3


    with labrad.connect() as cxn:
            ramsey.main(cxn, nv_sig, nd_filter, sig_shrt_apd_index, ref_shrt_apd_index,
                        sig_long_apd_index, ref_long_apd_index,
                        uwave_freq, uwave_power, uwave_pi_half_pulse, precession_time_range,
                        num_steps, num_reps, num_runs,
                        name)


def do_sample_nvs(name, nv_sig_list, nd_filter, apd_indices):

    # g2 parameters
    run_time = 60 * 5
    diff_window = 150 * 10**3  # 150 ns in ps

    # ESR parameters
    num_steps = 101
    num_runs = 5
    uwave_power = -13.0  # -13.0 with a 1.5 ND is a good starting point

    for nv_sig in nv_sig_list:

        with labrad.connect() as cxn:
            g2_zero = g2_measurement.main(cxn, nv_sig, nd_filter, run_time,
                                          diff_window, apd_indices[0],
                                          apd_indices[1], name=name)
            if g2_zero < 0.5:
                resonance.main(cxn, nv_sig, nd_filter, apd_indices, 2.87, 0.1,
                               num_steps, num_runs, uwave_power, name=name)


def do_set_drift_from_reference_image(nv_sig, nd_filter, apd_indices):

    ref_file_name = '2019-06-10_15-22-25_ayrton12'  # 60 x 60

    with labrad.connect() as cxn:
        set_drift_from_reference_image.main(cxn, ref_file_name, nv_sig, nd_filter, apd_indices)


def do_test_major_routines(name, nv_sig, nd_filter, apd_indices):
    """Run this whenver you make a significant code change. It'll make sure
    you didn't break anything in the major routines.
    """

    test_major_routines.main(name, nv_sig, nd_filter, apd_indices)


# %% Script Code


# Functions only run when called. Since this part of the script is not in a
# function, it will run when the script is run.
# __name__ will only be __main__ if we're running the file as a program.
# The below pattern enables us to import this file as a module without
# running it as a program.
if __name__ == '__main__':

    # %% General

    name = 'ayrton12'  # Sample name

#    nd_filter = 2.0
    nd_filter = 1.5
#    nd_filter = 1.0

    apd_indices = [0]
#    apd_indices = [0, 1]

    # %% NV sigs

#    z_voltage = 50.3
#    z_voltage = 50.8  # 6/12 3:41
    z_voltage = 50.5  # 6/12 17:27 before starting T1

    # ND 1.5
    background_count_rate = 3
    nv_sig_list = [
               [-0.142, 0.501, z_voltage, 53, background_count_rate],
               [-0.133, 0.420, z_voltage, 45, background_count_rate],
               [-0.141, 0.269, z_voltage, 92, background_count_rate],
               [-0.224, 0.070, z_voltage, 49, background_count_rate],
               [-0.234, 0.123, z_voltage, 83, background_count_rate],
               [-0.236, 0.163, z_voltage, 78, background_count_rate],
               [-0.269, 0.184, z_voltage, 40, background_count_rate],
               [-0.306, 0.160, z_voltage, 64, background_count_rate],
               [-0.269, 0.184, z_voltage, 40, background_count_rate],
               [-0.287, 0.260, z_voltage, 66, background_count_rate],
               [-0.308, 0.270, z_voltage, 30, background_count_rate],
               [-0.335, 0.280, z_voltage, 74, background_count_rate],
               [-0.324, 0.325, z_voltage, 90, background_count_rate],
               [-0.379, 0.280, z_voltage, 43, background_count_rate],
               [-0.388, 0.294, z_voltage, 31, background_count_rate],
               [-0.389, 0.264, z_voltage, 85, background_count_rate],
               [-0.375, 0.183, z_voltage, 45, background_count_rate],
               [-0.416, 0.398, z_voltage, 35, background_count_rate],
               [-0.397, 0.383, z_voltage, 100, background_count_rate],
               [-0.397, 0.337, z_voltage, 85, background_count_rate],
               [-0.456, 0.152, z_voltage, 63, background_count_rate],
               [-0.415, 0.398, z_voltage, 33, background_count_rate],
               [-0.393, 0.484, z_voltage, 60, background_count_rate]]

    # Before 6/13
#    nv13_2019_06_10 = nv_sig_list[13]
#    nv13_2019_06_10 = [-0.373, 0.279, z_voltage, 44, background_count_rate]  # 6/12 3:41
#    nv13_2019_06_10 = [-0.376, 0.280, 51.1, 40, background_count_rate]  # 6/12 4:29
#    nv13_2019_06_10 = [-0.379, 0.278, 50.5, 40, background_count_rate]  # 6/12 17:27 before starting T1
#    nv13_2019_06_10 = [-0.379, 0.278, 50.5, 71, background_count_rate]  # ND 1.0
#    nv13_2019_06_10 = [-0.379, 0.278, 50.5, 40, background_count_rate]  # ND 1.5
#    nv13_2019_06_10 = [-0.379, 0.278, 50.5, 15, background_count_rate]  # ND 2.0

    # After 6/13
#    nv13_2019_06_10 = [*nv_sig_list[13][0:3], 32, 3]  # ND 1.5
    nv13_2019_06_10 = [*nv_sig_list[13][0:3], 30, 3]  # ND 1.5 6/17
#    nv13_2019_06_10 = [*nv_sig_list[13][0:3], 12, 3]  # ND 2.0
#    nv13_2019_06_10 = [*nv_sig_list[13][0:3], 11, 3]  # ND 2.0 6/18
#    nv13_2019_06_10 = [*nv_sig_list[13][0:3], 10, 3]  # ND 2.0 6/18

    # For ND 2.0
#    nv12_2019_06_10 = [*nv_sig_list[12][0:3], 20, 2]
#    nv13_2019_06_10 = [*nv_sig_list[13][0:3], 18, 2]
#    nv21_2019_06_10 = [*nv_sig_list[21][0:3], 15, 2]

    nv12_2019_06_10 = [*nv_sig_list[12][0:3], 40, 3]  # ND 1.5 6/24

#    nv_sig_list = [nv13_2019_06_10]
    nv_sig_list = [nv12_2019_06_10]

    # %% t1 measurements, preparation population and readout population.

    zero_to_zero = [0,0]
    plus_to_plus = [1,1]
    minus_to_minus = [-1,-1]
    plus_to_zero = [1,0]
    minus_to_zero = [-1,0]
    zero_to_plus = [0,1]
    zero_to_minus = [0,-1]
    plus_to_minus = [1,-1]
    minus_to_plus = [-1,1]

    # Array for the t1 measuremnt, formatted:
    # [init_read_list, relaxation_time_range, num_steps, num_reps]

#    t1_exp_array = numpy.array([
#                                [plus_to_minus, [0, 800*10**3], 51, 2 * 10**4],
#                                [minus_to_plus, [0, 800*10**3], 51, 2 * 10**4],
#                                [plus_to_minus, [0, 100*10**3], 101, 4 * 10**4],
#                                [minus_to_plus, [0, 100*10**3], 101, 4 * 10**4],
#
#                                [plus_to_plus,   [0, 100*10**3],  101, 4 * 10**4],
#                                [minus_to_minus, [0, 100*10**3],  101, 4 * 10**4],
#                                [plus_to_plus,   [0, 800*10**3],  26, 2 * 10**4],
#                                [minus_to_minus, [0, 800*10**3],  26, 2 * 10**4],
#
#                                [zero_to_plus,   [0, 1000*10**3], 26, 2 * 10**4],
#                                [zero_to_minus,  [0, 1000*10**3], 26, 2 * 10**4],
#                                [plus_to_zero,   [0, 800*10**3], 51, 2 * 10**4],
#                                [minus_to_zero,  [0, 800*10**3], 51, 2 * 10**4],
#
#                                [zero_to_zero,   [0, 1000*10**3], 26, 2 * 10**4]])


    # For splittings < 75 MHz

    # ~13 hours
#    t1_exp_array = numpy.array([[plus_to_minus,  [0, 100*10**3], 51, 2 * 10**4],
#                                [plus_to_minus,  [0, 500*10**3], 41,  1 * 10**4],
#                                [plus_to_plus,   [0, 100*10**3], 51, 2 * 10**4],
#                                [plus_to_plus,   [0, 500*10**3], 41,  1 * 10**4],
#                                [plus_to_zero,   [0, 500*10**3], 41, 1 * 10**4],
#                                [zero_to_plus,   [0, 1500*10**3], 41, 1 * 10**4],
#                                [zero_to_zero,   [0, 1500*10**3], 41, 1 * 10**4]])

    # For splittings > 75 MHz

    # ~18 hours
#    t1_exp_array = numpy.array([[plus_to_minus,  [0, 1500*10**3], 41, 1 * 10**4],
#                                [plus_to_plus,   [0, 1500*10**3], 41, 1 * 10**4],
#                                [plus_to_zero,   [0, 1500*10**3], 41, 1 * 10**4],
#                                [zero_to_plus,   [0, 1500*10**3], 41, 1 * 10**4],
#                                [zero_to_zero,   [0, 1500*10**3], 41, 1 * 10**4]])

    # ~18 hours
#    t1_exp_array = numpy.array([[plus_to_minus,  [0, 1500*10**3], 41, 1 * 10**4],
#                                [plus_to_plus,   [0, 1500*10**3], 41, 1 * 10**4],
#                                [plus_to_zero,   [0, 2000*10**3], 31, 1 * 10**4],
#                                [zero_to_plus,   [0, 2000*10**3], 31, 1 * 10**4],
#                                [zero_to_zero,   [0, 2000*10**3], 31, 1 * 10**4]])

    # ~18 hours
#    t1_exp_array = numpy.array([[plus_to_minus,  [0, 2000*10**3], 31, 1 * 10**4],
#                                [plus_to_plus,   [0, 2000*10**3], 31, 1 * 10**4],
#                                [plus_to_zero,   [0, 2000*10**3], 31, 1 * 10**4],
#                                [zero_to_plus,   [0, 2000*10**3], 31, 1 * 10**4],
#                                [zero_to_zero,   [0, 2000*10**3], 31, 1 * 10**4]])
    
#    t1_exp_array = numpy.array([[plus_to_minus,  [0, 100*10**3], 51, 2 * 10**4],
#                                [plus_to_minus,   [0, 500*10**3], 41, 1 * 10**4],
#                                [plus_to_plus,  [0, 100*10**3], 51, 2 * 10**4],
#                                [plus_to_plus,   [0, 500*10**3], 41, 1 * 10**4]])
    
    # nv13_2019_06_10 150 MHz ~13.5 hours
#    t1_exp_array = numpy.array([[plus_to_minus,  [0, 200*10**3], 51, 2 * 10**4],
#                                [plus_to_minus,   [0, 500*10**3], 41, 1 * 10**4],
#                                [plus_to_plus,  [0, 200*10**3], 51, 2 * 10**4],
#                                [plus_to_plus,   [0, 500*10**3], 41, 1 * 10**4],
#                                [zero_to_plus,   [0, 1500*10**3], 41, 1 * 10**4],
#                                [zero_to_zero,   [0, 1500*10**3], 41, 1 * 10**4]])
    
    # nv13_2019_06_10 50/20 MHz ~12 hours
#    t1_exp_array = numpy.array([[plus_to_minus,  [0, 100*10**3], 51, 2 * 10**4],
#                                [plus_to_minus,   [0, 500*10**3], 41, 1 * 10**4],
#                                [plus_to_plus,  [0, 100*10**3], 51, 2 * 10**4],
#                                [plus_to_plus,   [0, 500*10**3], 41, 1 * 10**4],
#                                [zero_to_plus,   [0, 1500*10**3], 41, 1 * 10**4],
#                                [zero_to_zero,   [0, 1500*10**3], 41, 1 * 10**4]])
    
    t1_exp_array = numpy.array([[plus_to_minus,  [0, 50*10**3], 51, 2 * 10**4],
                                [plus_to_plus,  [0, 50*10**3], 51, 2 * 10**4]])
    

    # Array for the parameters of a given NV, formatted:
    # [nv_sig, uwave_freq_plus, uwave_pi_pulse_plus, uwave_freq_minus, uwave_pi_pulse_minus]
    # uwave_MINUS should be associated with the HP signal generator
    params_array = numpy.array([[nv13_2019_06_10, 2.8289, 105, 2.8520, 139]])

    # %% Functions to run

    try:

        # Routines that don't need an NV
#        set_xyz_zero()
#        set_xyz()
#        tool_belt.set_drift([-0.017, -0.002, -0.4])

        # Routines that expect listss
#        optimize_list(name, cxn, nv_sig_list, nd_filter, apd_indices)
#        do_sample_nvs(name, nv_sig_list, nd_filter, apd_indices)

        # Routines that expect single NVs
        for nv_sig in nv_sig_list:
#            coords = [-0.3, 0.3, z_voltage]
#            coords = (numpy.array(nv_sig[0:3]) + numpy.array(tool_belt.get_drift())).tolist()
#            nv_sig = [*coords, *nv_sig[3:]]
#            do_image_sample(name, coords, nd_filter, apd_indices)
#            do_optimize(name, nv_sig, nd_filter, apd_indices)
#            do_stationary_count(name, nv_sig, nd_filter, apd_indices)
#            do_g2_measurement(name, nv_sig, nd_filter, apd_indices[0], apd_indices[1])
            do_resonance(name, nv_sig, nd_filter, apd_indices)
#            do_resonance(name, nv_sig, nd_filter, apd_indices)
#            do_resonance(name, nv_sig, nd_filter, apd_indices, freq_center=2.84, freq_range=0.05)
#            do_resonance(name, nv_sig, nd_filter, apd_indices, freq_center=2.76, freq_range=0.10)
#            do_resonance(name, nv_sig, nd_filter, apd_indices, freq_center=2.825, freq_range=0.05)
#            do_resonance(name, nv_sig, nd_filter, apd_indices, freq_center=2.878, freq_range=0.05)
#            do_pulsed_resonance(name, nv_sig, nd_filter, apd_indices, freq_center=2.84, freq_range=0.05)
#            do_pulsed_resonance(name, nv_sig, nd_filter, apd_indices, freq_center=2.95, freq_range=0.05)
#            do_rabi(name, nv_sig, nd_filter, apd_indices, 2.8289, 0)
#            do_rabi(name, nv_sig, nd_filter, apd_indices, 2.8520, 1)
#            do_ramsey_measurement(name, nv_sig, nd_filter, apd_indices)
#            do_set_drift_from_reference_image(nv_sig, nd_filter, apd_indices)
#            do_test_major_routines(name, nv_sig, nd_filter, apd_indices)

#         %% FULL CONTROL T1

#        for nv_ind in range(len(params_array)):
#
#            nv_sig = params_array[nv_ind, 0]
#
#            uwave_freq_plus = params_array[nv_ind, 1]
#            uwave_pi_pulse_plus = params_array[nv_ind, 2]
#            uwave_freq_minus = params_array[nv_ind, 3]
#            uwave_pi_pulse_minus = params_array[nv_ind, 4]
#
#            for exp_ind in range(len(t1_exp_array)):
##            for exp_ind in [2,3,4,5,6,7]:
#
#                init_read_list = t1_exp_array[exp_ind, 0]
#                relaxation_time_range = t1_exp_array[exp_ind, 1]
#                num_steps = t1_exp_array[exp_ind, 2]
#                num_reps = t1_exp_array[exp_ind, 3]
#
#                do_t1_double_quantum(name, nv_sig, nd_filter,
#                              apd_indices,
#                              uwave_freq_plus, uwave_freq_minus,
#                              uwave_pi_pulse_plus, uwave_pi_pulse_minus,
#                              relaxation_time_range, num_steps, num_reps,
#                              init_read_list)


    finally:
        # Reset our hardware - this should be done in each routine, but
        # let's double check here
        tool_belt.reset_cfm()
        # Kill safe stop
        if tool_belt.check_safe_stop_alive():
            print("\n\nRoutine complete. Press enter to exit.")
            tool_belt.poll_safe_stop()
