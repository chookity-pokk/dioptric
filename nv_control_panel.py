# -*- coding: utf-8 -*-
"""
This file contains functions to control the CFM. Just change the function call
in the main section at the bottom of this file and run the file. Shared or
frequently changed parameters are in the __main__ body and relatively static
parameters are in the function definitions.

Created on Sun Nov 25 14:00:28 2018

@author: mccambria

use file 5/5/2022
"""


# %% Imports

import labrad
import utils.positioning as positioning
import utils.tool_belt as tool_belt
import utils.common as common
import majorroutines.image_sample as image_sample
# import majorroutines.image_sample_xz as image_sample_xz
import majorroutines.optimize as optimize
import majorroutines.stationary_count as stationary_count
import majorroutines.resonance as resonance
import majorroutines.pulsed_resonance as pulsed_resonance
import majorroutines.optimize_magnet_angle as optimize_magnet_angle
import majorroutines.rabi as rabi
import majorroutines.ramsey as ramsey
import majorroutines.spin_echo as spin_echo
from utils.tool_belt import States, NormStyle
import time
import numpy as np

apd_indices = [0]


# %% Major Routines


def do_image_sample(nv_sig, scan_size='medium'):
    scan_options=['huge','medium','big-ish','small','small-ish','big','test','bigger-highres']
    if scan_size not in scan_options:
    #     raise Exception():
        print('scan_size must be in: ', scan_options)
        return 
    if scan_size == 'huge':
        scan_range = 4.0#0.6 # large scan
        num_steps = 40
    elif scan_size == 'big':
        scan_range = .6 # large scan
        num_steps = 40
    elif scan_size == 'bigger-highres':
        scan_range = 1# large scan
        num_steps = 120
    elif scan_size == 'medium':
        scan_range = 0.4 # large scan
        num_steps = 40
    elif scan_size == 'small-ish':
        scan_range = 0.25 # large scan
        num_steps = 30
    elif scan_size == 'small':
        scan_range = 0.15 # large scan
        num_steps = 30
    elif scan_size == 'big-ish':
        scan_range = 0.425
        num_steps = 45
    elif scan_size == 'test':
        scan_range = .2
        num_steps = 10
        
    # For now we only support square scans so pass scan_range twice
    image_sample.main(nv_sig, scan_range, scan_range, num_steps)

# def do_image_sample_xz(nv_sig, zrange=2,steps=60):
    
#     x_range = .5
#     z_range = zrange
#     num_steps = steps
    
#     image_sample_xz.main(nv_sig, x_range, z_range, num_steps, apd_indices)

def do_optimize(nv_sig):

    optimize.main(
        nv_sig,
        apd_indices,
        set_to_opti_coords=False,
        save_data=True,
        plot_data=True,
    )



def do_stationary_count(nv_sig):

    run_time = 1 * 60 * 10 ** 9  # ns

    stationary_count.main(nv_sig, run_time, apd_indices)



def do_resonance(nv_sig,  freq_center=2.87, freq_range=0.2, num_steps = 101, num_runs = 40):
    
    uwave_power = -15.0

    resonance.main(
        nv_sig,
        apd_indices,
        freq_center,
        freq_range,
        num_steps,
        num_runs,
        uwave_power,
        state=States.HIGH,
        opti_nv_sig = nv_sig
    )


def do_resonance_state(nv_sig,  state):

    freq_center = nv_sig["resonance_{}".format(state.name)]
    uwave_power = -15.0

    freq_range = 0.1
    num_steps = 51
    num_runs = 10

    # Zoom
    # freq_range = 0.060
    # num_steps = 51
    # num_runs = 10

    resonance.main(
        nv_sig,
        apd_indices,
        freq_center,
        freq_range,
        num_steps,
        num_runs,
        uwave_power,
        opti_nv_sig = nv_sig
    )


def do_pulsed_resonance(nv_sig, freq_center=2.87, freq_range=0.2,num_runs=30):

    num_steps =31
    num_reps = 2e4
    # num_runs = runs
    uwave_power = 14.5
    uwave_pulse_dur = int(nv_sig["rabi_LOW"]/2)

    pulsed_resonance.main(
        nv_sig,
        apd_indices,
        freq_center,
        freq_range,
        num_steps,
        num_reps,
        num_runs,
        uwave_power,
        uwave_pulse_dur,
        opti_nv_sig = nv_sig
    )


def do_pulsed_resonance_state(nv_sig, state):

    # freq_range = 0.150
    # num_steps = 51
    # num_reps = 10**4
    # num_runs = 8

    # Zoom
    freq_range = 0.05
    # freq_range = 0.120
    num_steps = 51
    num_reps = int(1e4)
    num_runs = 10

    composite = False

    res, _ = pulsed_resonance.state(
        nv_sig,
        apd_indices,
        state,
        freq_range,
        num_steps,
        num_reps,
        num_runs,
        composite,
        opti_nv_sig = nv_sig
    )
    nv_sig["resonance_{}".format(state.name)] = res


def do_optimize_magnet_angle(nv_sig, num_angle_steps = 4, angle_range = [0, 150], num_runs=30):

    freq_center = 2.87
    freq_range = 0.3
    num_freq_steps = 101
    num_freq_runs = num_runs

    # Pulsed
    # uwave_power = 14.5
    # uwave_pulse_dur =int(nv_sig["rabi_LOW"]/2)
    # num_freq_reps = int(1e4)

    # CW
    uwave_power = -15.0
    uwave_pulse_dur = None
    num_freq_reps = None

    optimize_magnet_angle.main(
        nv_sig,
        apd_indices,
        angle_range,
        num_angle_steps,
        freq_center,
        freq_range,
        num_freq_steps,
        num_freq_reps,
        num_freq_runs,
        uwave_power,
        uwave_pulse_dur,
    )


def do_rabi(nv_sig,  state, uwave_time_range=[0, 200], num_steps = 51, num_reps = 2e4, num_runs=20):

    num_reps = int(num_reps)

    period = rabi.main(
        nv_sig,
        apd_indices,
        uwave_time_range,
        state,
        num_steps,
        num_reps,
        num_runs,
        opti_nv_sig = nv_sig
    )
    nv_sig["rabi_{}".format(state.name)] = period




def do_ramsey(nv_sig,  precession_time_range = [0, 0.2 * 10 ** 4], num_steps = 101,
                      set_detuning=10,num_reps = 2e4, num_runs=10, state=States.LOW,):

    detuning = set_detuning  # MHz
    # precession_time_range = [0, 1 * 10 ** 4]
    # precession_time_range = [0, .6 * 10 ** 3]
    # num_steps = 101
    num_reps = int(num_reps)
    # num_runs = runs

    # angle= 
    ramsey.main(
        nv_sig,
        apd_indices,
        detuning,
        precession_time_range,
        num_steps,
        num_reps,
        num_runs,
        state,
        opti_nv_sig = nv_sig
    )
    # return angle




def do_spin_echo(nv_sig, echo_time_range = [0, 80 * 10 ** 3],num_steps = 81,
                 num_reps = 1e4, num_runs=40, state = States.LOW):

    # T2* in nanodiamond NVs is just a couple us at 300 K
    # In bulk it's more like 100 us at 300 K

    num_reps = int(num_reps)


    # state = States.LOW

    angle = spin_echo.main(
        nv_sig,
        apd_indices,
        echo_time_range,
        num_steps,
        num_reps,
        num_runs,
        state,
    )
    return angle



# %% Run the file


if __name__ == "__main__":


    # %% Shared parameters
    

    green_power =10
    sample_name = "E6test"
    green_laser = "cobolt_515"
        
    nv_sig = {
        "coords":[6.423, 5.660,4.25],
        "name": "{}-nv1".format(sample_name,),
        "disable_opt":False,
        "ramp_voltages": False,
        
        "spin_laser": green_laser,
        "spin_laser_power": green_power,
        "spin_pol_dur": 1e4,
        "spin_readout_laser_power": green_power,
        "spin_readout_dur": 350,
        
        "imaging_laser":green_laser,
        "imaging_laser_power": green_power,
        "imaging_readout_dur": 1e7,
        "collection_filter": "630_lp",
        
        "expected_count_rate":17,
        # "expected_count_rate":None,
        "magnet_angle": 100, 
        "resonance_LOW":2.7641 ,"rabi_LOW": 75.2, "uwave_power_LOW": 15.5,  # 15.5 max. units is dBm
        "resonance_HIGH": 2.9098 , "rabi_HIGH": 100.0, "uwave_power_HIGH": 14.5, 
        'norm_style':NormStyle.POINT_TO_POINT}  # 14.5 max. units is dBm
    
    nv_sig = nv_sig

    # %% Functions to run
    try:

        # tool_belt.init_safe_stop()
        # tool_belt.set_drift([0.0, 0.0, tool_belt.get_drift()[2]])  # Keep z. we should explain how you can set the z focus if there are more nvs ate other depths
        # tool_belt.set_drift([0.0, 0.0, 0.0])  
        # print(tool_belt.get_drift())
        # tool_belt.set_xyz(labrad.connect(), [5,5,5])
        
        # tool_belt.laser_on_no_cxn('cobolt_515') # turn the laser on
        # tool_belt.laser_off_no_cxn('cobolt_515') # turn the laser on
        
        # do_optimize(nv_sig,)

        # do_image_sample(nv_sig, scan_size='test')
        do_image_sample(nv_sig,  scan_size='medium')
        # do_image_sample(nv_sig,  scan_size='big-ish')
        # z_list = np.arange(9.5,0.5,-0.25)
        # for z in z_list:
        #     nv_sig['coords'][2] = z
        #     do_image_sample(nv_sig,  scan_size='big')
        # do_image_sample(nv_sig,  scan_size='bigger-highres')
        # do_image_sample(nv_sig,  scan_size='small-ish')
        # do_image_sample(nv_sig, scan_size='huge')
        # do_image_sample_xz(nv_sig, zrange=5,steps=30)
        
        # nv_sig['disable_opt']=True
        # do_stationary_count(nv_sig, )
        # do_optimize_magnet_angle(nv_sig, num_angle_steps= 10, angle_range = [0,160], num_runs=15)
        # do_pulsed_resonance(nv_sig, freq_center=2.87, freq_range=0.2,num_runs=15)
        # do_pulsed_resonance_state(nv_sig, nv_sig, States.LOW)
        
        # do_resonance(nv_sig, 2.87, 0.2, num_runs = 40)
        # do_resonance(nv_sig, 2.875, 0.1)
        # do_resonance_state(nv_sig , States.LOW)
        
        #do_optimize_magnet_angle(nv_sig, num_runs=15)
        
        # do_rabi(nv_sig,  States.LOW, uwave_time_range=[0, 250],num_runs=15)
        # do_rabi(nv_sig,  States.HIGH, uwave_time_range=[0, 250],num_runs=30)
        # detunings=[0,2,4]
        # for d in detunings:
        #     do_ramsey(nv_sig, set_detuning=d,num_runs=50, precession_time_range = [0, 1.75 * 10 ** 3],num_steps = 101)  
        # do_spin_echo(nv_sig,echo_time_range = [0, 60 * 10 ** 3], num_steps=41, num_runs=100) 
        # print('Run time: ',(time.time()-startt)/60,' minutes')
    finally:

        # Make sure everything is reset
        tool_belt.reset_cfm()
        tool_belt.reset_safe_stop()
