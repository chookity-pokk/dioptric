# -*- coding: utf-8 -*-
"""
Loop through extremely abbreviated versions of all the major routines
to make sure they all run to completion. This should be run whenever
significant changes are made to the code. 

Created on Thu Jun 13 14:30:42 2019

@author: mccambria
"""


import majorroutines.image_sample as image_sample
import majorroutines.optimize as optimize
import majorroutines.stationary_count as stationary_count
import majorroutines.resonance as resonance
import majorroutines.pulsed_resonance as pulsed_resonance 
import majorroutines.rabi as rabi
import majorroutines.g2_measurement as g2_measurement
import majorroutines.t1_double_quantum as t1_double_quantum
import majorroutines.ramsey as ramsey
import majorroutines.spin_echo as spin_echo
import majorroutines.optimize_magnet_angle as optimize_magnet_angle


def main(nv_sig, apd_indices):
    
    # g2_measurement
    print('\nTesting g2_measurement...\n')
    if len(apd_indices) < 2:
        # Setting apd_indices to [0, 1] for g2_measurement
        apd_indices_temp = [0, 1]
    else:
        apd_indices_temp = apd_indices
    run_time = 5
    diff_window = 150
    g2_measurement.main(nv_sig, run_time, diff_window,
                        apd_indices_temp[0], apd_indices_temp[1])
    
    # image_sample
    print('\nTesting image_sample...\n')
    scan_range = 0.01
    num_scan_steps = 5
    # For now we only support square scans so pass scan_range twice
    image_sample.main(nv_sig, scan_range, scan_range,
                      num_scan_steps, apd_indices)
    
    # optimize
    print('\nTesting optimize...\n')
    optimize.main(nv_sig, apd_indices,
              set_to_opti_coords=False, save_data=True, plot_data=True)
    
    # stationary_count
    print('\nTesting stationary_count...\n')
    run_time = 5
    stationary_count.main(nv_sig, run_time, apd_indices)
    
    # resonance
    print('\nTesting resonance...\n')
    freq_center = 2.87
    freq_range = 0.05
    num_steps = 5
    num_runs = 2
    uwave_power = -13.0
    resonance.main(nv_sig, apd_indices, freq_center, 
                   freq_range, num_steps, num_runs, uwave_power)
    
    # pulsed_resonance
    print('\nTesting pulsed_resonance...\n')
    freq_center = 2.87
    freq_range = 0.05
    num_steps = 5
    num_reps = 10
    num_runs = 2
    uwave_power = -13.0
    uwave_pulse_dur = 70
    pulsed_resonance.main(nv_sig, apd_indices, freq_center,
                          freq_range, num_steps, num_reps, num_runs,
                          uwave_power, uwave_pulse_dur)
    
    # rabi
    print('\nTesting rabi...\n')
    uwave_freq = 2.87
    uwave_power = 9.0
    uwave_time_range = [0, 100]
    do_uwave_gate_number = 0
    num_steps = 10
    num_reps = 10
    num_runs = 2
    rabi.main(nv_sig, apd_indices, 
              uwave_freq, uwave_power, uwave_time_range,
              do_uwave_gate_number,
              num_steps, num_reps, num_runs)
    
    # t1_double_quantum
    print('\nTesting t1_double_quantum...\n')
    uwave_freq_plus = 2.86
    uwave_freq_minus = 2.88
    uwave_power = 9
    uwave_pi_pulse_plus = 65
    uwave_pi_pulse_minus = 75
    relaxation_time_range = [0, 10*10**3]
    num_steps = 10
    num_reps = 10
    num_runs = 2
    init_read_list = [-1, +1]
    t1_double_quantum.main(nv_sig, apd_indices,
                 uwave_freq_plus, uwave_freq_minus,
                 uwave_power, uwave_power,
                 uwave_pi_pulse_plus, uwave_pi_pulse_minus,
                 relaxation_time_range, num_steps, num_reps, num_runs, 
                 init_read_list)
    
    # ramsey
    print('\nTesting ramsey...\n')
    uwave_power = 9
    uwave_freq = 2.8086
    detuning = 2.5  # MHz
    uwave_pi_half_pulse = 33
    precession_time_range = [0, 4 * 10**3]
    num_steps = 6
    num_reps = 10
    num_runs = 2
    ramsey.main(nv_sig, apd_indices,
                uwave_freq, detuning, uwave_power, uwave_pi_half_pulse,
                precession_time_range, num_steps, num_reps, num_runs)
    
    # spin_echo
    print('\nTesting spin_echo...\n')
    uwave_power = 9
    uwave_freq = 2.8086
    rabi_period = 123
    precession_time_range = [0, 4 * 10**3]
    num_steps = 6
    num_reps = 10
    num_runs = 2
    spin_echo.main(nv_sig, apd_indices,
                   uwave_freq, uwave_power, rabi_period,
                   precession_time_range, num_steps, num_reps, num_runs)
    
    # optimize_magnet_angle
    print('\nTesting optimize_magnet_angle...\n')
    angle_range = [45, 65]
    num_angle_steps = 2
    freq_center = 2.87
    freq_range = 0.05
    num_freq_steps = 3
    num_freq_reps = 10
    num_freq_runs = 1
    uwave_power = 9.0
    uwave_pulse_dur = 70
    optimize_magnet_angle.main(nv_sig, apd_indices,
                               angle_range, num_angle_steps,
                               freq_center, freq_range,
                               num_freq_steps, num_freq_reps, num_freq_runs,
                               uwave_power, uwave_pulse_dur)
    
    # Success!
    print('\nNo crashes went unhandled. Success!')
    