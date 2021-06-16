# -*- coding: utf-8 -*-
"""This file contains functions to control the CFM. Just change the function call
in the main section at the bottom of this file and run the file. Shared or
frequently changed parameters are in the __main__ body and relatively static
parameters are in the function definitions.

Created on Sun Nov 25 14:00:28 2018

@author: mccambria
"""


# %% Imports


import labrad
import numpy
import time
import copy
import utils.tool_belt as tool_belt
import majorroutines.image_sample as image_sample
import majorroutines.optimize as optimize
import majorroutines.stationary_count as stationary_count
import majorroutines.resonance as resonance
import majorroutines.pulsed_resonance as pulsed_resonance
import majorroutines.optimize_magnet_angle as optimize_magnet_angle
import majorroutines.rabi as rabi
import majorroutines.g2_measurement as g2_measurement
import majorroutines.t1_double_quantum as t1_double_quantum
import majorroutines.t1_interleave as t1_interleave
import majorroutines.ramsey as ramsey
import majorroutines.spin_echo as spin_echo
import majorroutines.lifetime as lifetime
import majorroutines.lifetime_v2 as lifetime_v2
import majorroutines.set_drift_from_reference_image as set_drift_from_reference_image
import debug.test_major_routines as test_major_routines
import minorroutines.time_resolved_readout as time_resolved_readout
import chargeroutines.moving_target as moving_target
from utils.tool_belt import States


# %% Minor Routines


def set_xyz(nv_sig):

    with labrad.connect() as cxn:
        tool_belt.set_xyz(cxn, nv_sig)

def set_xyz_zero():

    with labrad.connect() as cxn:
        tool_belt.set_xyz_zero(cxn)


# %% Major Routines


def do_image_sample(nv_sig, apd_indices,  color_ind, save_data, plot_data,  
                    readout = 10**7, flip = False, um_scaled= False):
    
#    num_steps = 250
#    scan_range = 0.7
#    scan_range = 0.5
#    num_steps = 125
#    scan_range = 0.45
#    scan_range = 0.3
#    scan_range = 0.2
#    scan_range = 0.1
    scan_range = 0.05
#    num_steps = 90
    num_steps = 60
    save_data=True
    
    # For now we only support square scans so pass scan_range twice
    image_sample.main(nv_sig, scan_range, scan_range, num_steps, apd_indices,
                      color_ind, save_data, plot_data, readout, flip, um_scaled )
    
def do_optimize(nv_sig, apd_indices, color_ind):

    optimize.main(nv_sig, apd_indices,color_ind,
              set_to_opti_coords=False, save_data=True, plot_data=True)

def do_optimize_list(nv_sig_list, apd_indices, color_ind):

    optimize.optimize_list(nv_sig_list, apd_indices, color_ind)
    
def do_opti_z(nv_sig_list, apd_indices):
    
    optimize.opti_z(nv_sig_list, apd_indices,
              set_to_opti_coords=False, save_data=True, plot_data=True)

def do_stationary_count(nv_sig, apd_indices, color_ind):

    run_time = 90* 10**9  # ns

    average, st_dev = stationary_count.main(nv_sig, run_time, apd_indices, color_ind)
    
    return average, st_dev
        
def do_g2_measurement(nv_sig, apd_a_index, apd_b_index):

    run_time = 60 * 10  # s
    diff_window = 75  # ns

    g2_measurement.main(nv_sig, run_time, diff_window,
                        apd_a_index, apd_b_index)

def do_resonance(nv_sig, apd_indices, freq_center=2.87, freq_range=0.2):

    num_steps = 51
    num_runs = 2
    uwave_power = -7.0

    resonance.main(nv_sig, apd_indices, freq_center, freq_range,
                   num_steps, num_runs, uwave_power)

def do_resonance_state(nv_sig, apd_indices, state):

    freq_center = nv_sig['resonance_{}'.format(state.name)]
    uwave_power = -13.0  # -13.0 with a 1.5 ND is a good starting point
#    uwave_power = -5.0  # After inserting mixer
    
#    freq_range = 0.200
#    num_steps = 51
#    num_runs = 2
    
    # Zoom
    freq_range = 0.05
    num_steps = 51
    num_runs = 4

    resonance.main(nv_sig, apd_indices, freq_center, freq_range,
                   num_steps, num_runs, uwave_power)

def do_pulsed_resonance(nv_sig, apd_indices,
                        freq_center=2.87, freq_range=0.2):

    num_steps = 51
    num_reps = 10**5
    num_runs = 1
    uwave_power = 9.0
    uwave_pulse_dur = 60

    pulsed_resonance.main(nv_sig, apd_indices, freq_center, freq_range,
                          num_steps, num_reps, num_runs,
                          uwave_power, uwave_pulse_dur)

def do_pulsed_resonance_state(nv_sig, apd_indices, state):

#    freq_range = 0.150
#    num_steps = 51
#    num_reps = 10**5
#    num_runs = 1
    
    # Zoom
    freq_range = 0.050
    num_steps = 51
    num_reps = 10**5
    num_runs = 2

    pulsed_resonance.state(nv_sig, apd_indices, state, freq_range,
                          num_steps, num_reps, num_runs)

def do_optimize_magnet_angle(nv_sig, apd_indices):

#    angle_range = [0, 150]
    angle_range = [25, 35]
    num_angle_steps = 6
    freq_center = 2.870
    freq_range = 0.5
    num_freq_steps = 76
    num_freq_runs = 1
#    uwave_power = 9.0
    uwave_power = -13.0
    uwave_pulse_dur = None  # Set to None for CWESR
    num_freq_reps = 10**5

    optimize_magnet_angle.main(nv_sig, apd_indices,
               angle_range, num_angle_steps, freq_center, freq_range,
               num_freq_steps, num_freq_reps, num_freq_runs,
               uwave_power, uwave_pulse_dur)

def do_rabi(nv_sig, apd_indices, state, uwave_time_range=[0, 200]):

    num_steps = 51
    num_reps = 10**5
    num_runs = 2

    rabi.main(nv_sig, apd_indices, uwave_time_range,
              state, num_steps, num_reps, num_runs)

def do_t1_battery(nv_sig, apd_indices):

    # T1 experiment parameters, formatted:
    # [[init state, read state], relaxation_time_range, num_steps, num_reps, num_runs]
    t1_exp_array = numpy.array([
        [[States.HIGH, States.LOW], [0, 2*10**6], 11, 25*10**3, 20],
        [[States.HIGH, States.LOW], [0, 15*10**6], 11, 3.5*10**3, 100],
    
        [[States.HIGH, States.HIGH], [0, 2*10**6], 11, 25*10**3, 20],
        [[States.HIGH, States.HIGH], [0, 15*10**6], 11, 3.5*10**3, 100],
    
        [[States.ZERO, States.HIGH], [0, 20*10**6], 11, 2.5*10**3, 140],
    
        [[States.ZERO, States.ZERO], [0, 20*10**6], 11, 2.5*10**3, 140]
        ])

    # Loop through the experiments
    for exp_ind in range(len(t1_exp_array)):

        init_read_states = t1_exp_array[exp_ind, 0]
        relaxation_time_range = t1_exp_array[exp_ind, 1]
        num_steps = t1_exp_array[exp_ind, 2]
        num_reps = t1_exp_array[exp_ind, 3]
        num_runs = t1_exp_array[exp_ind, 4]

        t1_double_quantum.main(nv_sig, apd_indices, relaxation_time_range,
                           num_steps, num_reps, num_runs, init_read_states)

def do_t1_interleave(nv_sig, apd_indices):
    # T1 experiment parameters, formatted:
    # [[init state, read state], relaxation_time_range, num_steps, num_reps]
    # ~18 hrs
    num_runs = 30
    t1_exp_array = numpy.array([
        [[States.HIGH, States.LOW], [0, 50*10**3], 51, 8*10**4, num_runs],
        [[States.HIGH, States.LOW], [0, 120*10**3], 26, 8*10**4, num_runs],
    
        [[States.HIGH, States.HIGH], [0, 50*10**3], 51, 8*10**4, num_runs],
        [[States.HIGH, States.HIGH], [0, 120*10**3], 26, 8*10**4, num_runs],
    
        [[States.ZERO, States.HIGH], [0, 2.5*10**6], 26, 1*10**4, num_runs],
    
        [[States.ZERO, States.ZERO], [0, 2.5*10**6], 26, 1*10**4, num_runs],
        ])

    t1_interleave.main(nv_sig, apd_indices, t1_exp_array, num_runs)
    
def do_lifetime(nv_sig, apd_indices, filter, voltage, reference = False):
    
#    num_reps = 100 #MM 
    num_reps = 500 #SM
    num_bins = 101 
    num_runs = 10
    readout_time_range = [0, 1.0 * 10**6] #ns
    polarization_time = 60 * 10**3 #ns
    
    lifetime_v2.main(nv_sig, apd_indices, readout_time_range,
         num_reps, num_runs, num_bins, filter, voltage, polarization_time, reference)
    
def do_ramsey(nv_sig, apd_indices):

    detuning = 2.5  # MHz
    precession_time_range = [0, 4 * 10**3]
    num_steps = 151
    num_reps = 3 * 10**5
    num_runs = 1

    ramsey.main(nv_sig, apd_indices, detuning, precession_time_range,
                num_steps, num_reps, num_runs)

def do_spin_echo(nv_sig, apd_indices):

    # T2 in nanodiamond NVs without dynamical decoupling is just a couple
    # us so don't bother looking past 10s of us
    
    num_steps = 101
    precession_time_range = [0, 150 * 10**3]
    num_reps = int(1.75 * 10**4)
    num_runs = 4
    
    state = States.LOW

    spin_echo.main(nv_sig, apd_indices, precession_time_range,
                   num_steps, num_reps, num_runs, state)

def do_sample_nvs(nv_sig_list, apd_indices):

    # g2 parameters
    run_time = 60 * 5
    diff_window = 150

    # PESR parameters
    num_steps = 101
    num_reps = 10**5
    num_runs = 5
    uwave_power = 9.0
    uwave_pulse_dur = 100

    g2 = g2_measurement.main_with_cxn
    pesr = pulsed_resonance.main_with_cxn

    with labrad.connect() as cxn:
        for nv_sig in nv_sig_list:
            g2_zero = g2(cxn, nv_sig, run_time, diff_window,
                         apd_indices[0], apd_indices[1])
            if g2_zero < 0.5:
                pesr(cxn, nv_sig, apd_indices, 2.87, 0.1, num_steps,
                     num_reps, num_runs, uwave_power, uwave_pulse_dur)

def find_resonance_and_rabi(nv_sig, apd_indices):
    # Given resonances and rabi periods in the nv_sig, automatically remeasures
    state_list = [States.LOW, States.HIGH]
    num_steps = 51
    num_runs = 2

    fail_bool = False

    value_list = []
    for state in state_list:

        # Run resonance and save the resonance found
        num_reps = 10**5
        freq_range = 0.04

        print('Measureing pESR on {}\n'.format(state.name))
        resonance_list = pulsed_resonance.state(nv_sig, apd_indices, state, freq_range,
                              num_steps, num_reps, num_runs)
        resonance = resonance_list[0]
        value_list.append('%.4f'%resonance)

        if resonance is None:
            print('Resonance fitting failed')
            fail_bool = True
            return

        # If the resonance has shifted more than 1 MHz in either direction, stop
        shift_res = 10/1000
        limit_high_res = (nv_sig['resonance_{}'.format(state.name)] + shift_res)
        limit_low_res =  (nv_sig['resonance_{}'.format(state.name)] - shift_res)

        if resonance > limit_high_res or resonance < limit_low_res:
            print('Resonance has shifted more than {} MHz'.format(float(shift_res)))
            fail_bool = True
            return
        else:
            nv_sig['resonance_{}'.format(state.name)] = float('%.4f'%resonance)

        # Run rabi and save the rabi period
        uwave_time_range = [0, 200]
        num_reps = 2*10**5

        print('Measureing rabi on {}\n'.format(state.name))
        rabi_per = rabi.main(nv_sig, apd_indices, uwave_time_range,
                  state, num_steps, num_reps, num_runs)
        value_list.append('%.1f'%rabi_per)

        if rabi_per is None:
            print('Rabi fitting failed')
            fail_bool = True
            return

        # If the rabi period has shifted more than 50 ns in either direction, stop
        shift_per =50
        limit_high_per = (nv_sig['rabi_{}'.format(state.name)] + shift_per)
        limit_low_per =  (nv_sig['rabi_{}'.format(state.name)] - shift_per)

        if rabi_per > limit_high_per or rabi_per < limit_low_per:
            print('Rabi period has changed more than {} ns'.format(shift_per))
            fail_bool = True
            return
        else:
            nv_sig['rabi_{}'.format(state.name)] = float('%.1f'%rabi_per)

    print(value_list)

    timestamp = tool_belt.get_time_stamp()
    raw_data = {'nv_sig': nv_sig,
                'nv_sig-units': tool_belt.get_nv_sig_units(),
                'value_list': value_list,
                'value_list-units': 'GHz, ns, GHz, ns'
                }

    file_path = 'E:/Shared drives/Kolkowitz Lab Group/nvdata/auto_pESR_rabi/' + '{}-{}'.format(timestamp, nv_sig['name'])
    tool_belt.save_raw_data(raw_data, file_path)

    return fail_bool

def do_set_drift_from_reference_image(nv_sig, apd_indices):

    # ref_file_name = '2019-06-10_15-22-25_ayrton12'  # 60 x 60
    ref_file_name = '2019-06-27_16-37-18_johnson1' # bulk nv, first one we saw

    set_drift_from_reference_image.main(ref_file_name, nv_sig, apd_indices)

def do_test_major_routines(nv_sig, apd_indices):
    """Run this whenver you make a significant code change. It'll make sure
    you didn't break anything in the major routines.
    """

    test_major_routines.main(nv_sig, apd_indices)
    
def do_time_resolved_readout(nv_sig, apd_indices,
                                 init_color_ind, illum_color_ind):
    illumination_time = 10**6 
    num_reps = 10**3
    num_bins = 500
   
    init_pulse_duration = 2*10**6
    num_runs = 5
    time_resolved_readout.main(nv_sig, apd_indices, 
                   illumination_time, init_pulse_duration,
                   init_color_ind, illum_color_ind,
                   num_reps, num_runs, num_bins)

def do_SPaCE(nv_sig):
    start_coords = nv_sig['coords']
    optimize_coords = start_coords
    img_range = 0.06
    pulse_time = 0.01*10**6
    num_steps = 10
    num_runs = 3
    init_color = '515a'
    pulse_color = '515a'
    measurement_type = '2D'
    
    moving_target.main(nv_sig, start_coords, optimize_coords, img_range, 
                       pulse_time,num_steps, num_runs, init_color, pulse_color, 
                              measurement_type)
    
# %% Run the file


if __name__ == '__main__':

    # %% Shared parameters

#    apd_indices = [0]
    apd_indices = [0, 1]
    
    sample_name = 'goeppert-mayer'
     
    search = { 'coords':[0, 0 ,5.0],
            'name': '{}-search'.format(sample_name),
            'expected_count_rate': None,'nd_filter': 'nd_0',
            'color_filter': '635-715 bp', 
#            'color_filter': '715 lp',
            'pulsed_readout_dur': 300,
            'pulsed_SCC_readout_dur': 10*10**7,  'am_589_power': 0.08, 
            'pulsed_initial_ion_dur': 25*10**3,
            'pulsed_shelf_dur': 200, 
            'am_589_shelf_power': 0.35,
            'pulsed_ionization_dur': 10**3, 'cobalt_638_power': 130, 
            'ao_638_pwr': 0.8,
            'pulsed_reionization_dur': 100*10**3, 'cobalt_532_power':12,
            'ao_515_pwr': 0.64,
            'magnet_angle': 0,
            "resonance_LOW": 2.7,"rabi_LOW": 146.2, "uwave_power_LOW": 9.0,
            "resonance_HIGH": 2.9774,"rabi_HIGH": 95.2,"uwave_power_HIGH": 10.0} 
    

    nv0_2021_06_14 = { 'coords':[0.043, 0.004 ,5.0],
            'name': '{}-nv0_2021_06_14'.format(sample_name),
            'expected_count_rate': 40,'nd_filter': 'nd_0.5',
            'color_filter': '635-715 bp',
#            'color_filter': '715 lp',
            'pulsed_readout_dur': 300,
            'pulsed_SCC_readout_dur': 10*10**7,  'am_589_power': 0.15,
            'pulsed_initial_ion_dur': 25*10**3,
            'pulsed_shelf_dur': 200,
            'am_589_shelf_power': 0.35,
            'pulsed_ionization_dur': 10**3, 'cobalt_638_power': 130,
            'ao_638_pwr': 0.8,
            'pulsed_reionization_dur': 100*10**3, 'cobalt_532_power':12,
            'ao_515_pwr': 0.65,
            'magnet_angle': 0,
            "resonance_LOW": 2.7,"rabi_LOW": 146.2, "uwave_power_LOW": 9.0,
            "resonance_HIGH": 2.9774,"rabi_HIGH": 95.2,"uwave_power_HIGH": 10.0}
    



    expected_count_list = [] # 4/13/21 ###
    nv_list_2021_06_14 = [
[-0.070, -0.154 ,5.0],
[-0.068, -0.059 ,5.0],
[-0.049, -0.038 ,5.0],
[0.092, -0.047 ,5.0],
[0.071, 0.095 ,5.0],
[-0.016, -0.042, 4.9],
[0.003, 0.060, 4.9],]

    nv_sig_list =[]
    for i in [6]:#range(len(nv_list_2021_06_14)):
        nv_coords = nv_list_2021_06_14[i]
        nv_sig = copy.deepcopy(nv0_2021_06_14)
        nv_sig['coords'] = nv_coords
#        nv_sig['expected_count_rate'] = expected_count_list[i]
        nv_sig['name'] = 'goeppert-mayer-nv{}_2021_06_14'.format(i)
        nv_sig_list.append(nv_sig)
        
#    nv_sig_list = [search]
    

    # %% Functions to run

    try:
        
        # Operations that don't need an NV
        
#        drift = [0.01, 0.01, -0.06]
#        tool_belt.set_drift(drift)  
#        tool_belt.set_drift([0.0,0.0,0.0])  # Totally reset 
#        tool_belt.set_drift([tool_belt.get_drift()[0], tool_belt.get_drift()[1], 0.0])  # Keep x, y
#        tool_belt.set_drift([0.0, 0.0, tool_belt.get_drift()[2]])  # Keep z
#        set_xyz([0.0, 0.0,  5.0])

      
#        with labrad.connect() as cxn:
#            cxn.filter_slider_ell9k_color.set_filter('635-715 bp')  
#            cxn.filter_slider_ell9k.set_filter('nd_0')           
#            cxn.pulse_streamer.constant([], 0.65, 0.0)
#            cxn.objective_piezo.write(5.1)
        
#         Routines that expect lists of NVs
#        do_optimize_list(nv_sig_list, apd_indices,'515a')
#        do_sample_nvs(nv_sig_list, apd_indices)
#        do_g2_measurement(nv_sig_list, apd_indices[0], apd_indices[1])
        
        # Routines that expect single NVs
        for ind in range(len(nv_sig_list)):
            nv_sig = nv_sig_list[ind]
            
#            do_optimize(nv_sig, apd_indices, '515a')
            do_optimize(nv_sig, apd_indices, 532)
            
#            [x, y, z] = nv_sig['coords']
#            for z in numpy.linspace(z - 0.1, z + 0.1, 5):
#                nv_sig_copy = copy.deepcopy(nv_sig)
#                [coord_x, coord_y, coord_z] = nv_sig['coords']
#                nv_sig_copy['coords'] = [coord_x, coord_y, z]  
#                do_image_sample(nv_sig_copy,  apd_indices, '515a', save_data=True, plot_data=True) 

            
#            do_image_sample(nv_sig,  apd_indices, 532, save_data=True, plot_data=True, readout = 1*10**7)
#            do_image_sample(nv_sig,  apd_indices, '515a',
#                            save_data=True, plot_data=True, flip = False, readout = 1*10**7)
#            do_image_sample(nv_sig,  apd_indices, 638, save_data=True, plot_data=True, readout = 10**5)
#            do_image_sample(nv_sig,  apd_indices, 589, save_data=True, plot_data=True, readout =4*10**7)

#            do_stationary_count(nv_sig, apd_indices, 532)
#            do_time_resolved_readout(nv_sig, apd_indices,
#                                 532, 638)
            
#            do_SPaCE(nv_sig)

            do_g2_measurement(nv_sig, apd_indices[0], apd_indices[1])
                
#            do_optimize_magnet_angle(nv_sig, apd_indices)
#            do_resonance(nv_sig, apd_indices, 532)
#            do_resonance_state(nv_sig, apd_indices, States.LOW)
#            do_resonance_state(nv_sig, apd_indices, States.HIGH)
#            do_pulsed_resonance(nv_sig, apd_indices)
#            do_pulsed_resonance_state(nv_sig, apd_indices, States.LOW)
#            do_pulsed_resonance_state(nv_sig, apd_indices, States.HIGH)
#            do_pulsed_resonance(nv_sig, apd_indices,
#                        freq_center=nv_sig['resonance_LOW'], freq_range=0.15)
#            do_pulsed_resonance(nv_sig, apd_indices,
#                        freq_center=nv_sig['resonance_HIGH'], freq_range=0.1)
#            do_pulsed_resonance(nv_sig, apd_indices, freq_center=2.600, freq_range=0.15)
#            do_pulsed_resonance(nv_sig, apd_indices, freq_center=3.100, freq_range=0.15)
#            do_rabi(nv_sig, apd_indices, States.LOW, [0, 200])
#            do_rabi(nv_sig, apd_indices, States.HIGH, [0, 300])
#            find_resonance_and_rabi(nv_sig, apd_indices)
#            do_t1_battery(nv_sig, apd_indices)
#            do_t1_interleave(nv_sig, apd_indices)
#            do_t1_image_sample(nv_sig, apd_indices)
#            do_lifetime(nv_sig, apd_indices)
            
#            do_ramsey(nv_sig, apd_indices)
#            do_spin_echo(nv_sig, apd_indices)
#            do_set_drift_from_reference_image(nv_sig, apd_indices)
#            do_test_major_routines(nv_sig, apd_indices)
#            with labrad.connect() as cxn:
#                tool_belt.set_xyz_on_nv(cxn, nv_sig)

    finally:
        # Kill safe stop
        if tool_belt.check_safe_stop_alive():
            print('\n\nRoutine complete. Press enter to exit.')
            tool_belt.poll_safe_stop()
