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
import numpy
import time
import copy
import utils.tool_belt as tool_belt
import majorroutines.image_sample as image_sample
import majorroutines.image_sample_xz as image_sample_xz
import majorroutines.optimize as optimize
import majorroutines.stationary_count as stationary_count
import majorroutines.resonance as resonance
import majorroutines.pulsed_resonance as pulsed_resonance
#import majorroutines.optimize_magnet_angle as optimize_magnet_angle
import majorroutines.rabi as rabi
#import majorroutines.ramsey as ramsey
#import majorroutines.spin_echo as spin_echo

# import majorroutines.set_drift_from_reference_image as set_drift_from_reference_image
import debug.test_major_routines as test_major_routines
from utils.tool_belt import States


apd_indices = [0]


# %% Major Routines


def do_image_sample(nv_sig, apd_indices):

    # scan_range = 0.5
    # num_steps = 90
    # num_steps = 120
    #
    # scan_range = 0.15
    # num_steps = 60
    #
    # scan_range = 0.75
    # num_steps = 150
    
    # scan_range = 5
    # num_steps = 160
    # scan_range =.5
    # num_steps = 90
    # scan_range = 2
    # num_steps = 120
    # scan_range = 0.05
    # num_steps = 60
    # 80 um / V
    # 
    # scan_range = 5.0
    # scan_range = 3
    # scan_range = 1.5
#    scan_range =4
#    scan_range = 1
#    scan_range = 0.5
    scan_range = 0.35
#    scan_range = 0.25
#    scan_range = 0.2
#    scan_range = 0.15
#    scan_range = 0.1
#    scan_range = 0.05
    # scan_range = 0.025
    
    # num_steps = 400
    # num_steps = 300
    # num_steps = 200
    # num_steps = 160
    # num_steps = 135
    # num_steps =120
#    num_steps = 90
    num_steps = 60
#    num_steps = 31
    # num_steps = 15
    
    #individual line pairs:
    # scan_range = 0.16
    # num_steps = 160
    
    #both line pair sets:
    # scan_range = 0.35
    # num_steps = 160
        

    # For now we only support square scans so pass scan_range twice
    image_sample.main(nv_sig, scan_range, scan_range, num_steps, apd_indices, save_data= False)

def do_image_sample_xz(nv_sig, apd_indices):
    
    x_range = 0.5
    z_range = 4
    num_steps = 60
    
    image_sample_xz.main(nv_sig, x_range, z_range, num_steps, apd_indices)

def do_optimize(nv_sig, apd_indices):

    optimize.main(
        nv_sig,
        apd_indices,
        set_to_opti_coords=False,
        save_data=True,
        plot_data=True,
    )



def do_stationary_count(nv_sig, apd_indices):

    run_time = 1 * 60 * 10 ** 9  # ns

    stationary_count.main(nv_sig, run_time, apd_indices)



def do_resonance(nv_sig, opti_nv_sig,apd_indices, freq_center=2.87, freq_range=0.2):

    num_steps = 101
    num_runs = 1
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
        opti_nv_sig = opti_nv_sig
    )


def do_resonance_state(nv_sig, opti_nv_sig, apd_indices, state):

    freq_center = nv_sig["resonance_{}".format(state.name)]
    uwave_power = -10.0

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
        opti_nv_sig = opti_nv_sig
    )


def do_pulsed_resonance(nv_sig, opti_nv_sig, apd_indices, freq_center=2.87, freq_range=0.2):

    num_steps =101
    num_reps = 0.3e4
    num_runs = 10
    uwave_power = 14.5
    uwave_pulse_dur = int(100/2)

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
        opti_nv_sig = opti_nv_sig
    )


def do_pulsed_resonance_state(nv_sig, opti_nv_sig,apd_indices, state):

    # freq_range = 0.150
    # num_steps = 51
    # num_reps = 10**4
    # num_runs = 8

    # Zoom
    freq_range = 0.05
    # freq_range = 0.120
    num_steps = 51
    num_reps = int(0.5e4)
    num_runs = 5

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
        opti_nv_sig = opti_nv_sig
    )
    nv_sig["resonance_{}".format(state.name)] = res


def do_optimize_magnet_angle(nv_sig, apd_indices):

    # angle_range = [132, 147]
    #    angle_range = [315, 330]
    num_angle_steps = 6
    #    freq_center = 2.7921
    #    freq_range = 0.060
    angle_range = [0, 150]
    #    num_angle_steps = 6
    freq_center = 2.87
    freq_range = 0.3
    num_freq_steps = 101
    num_freq_runs = 10

    # Pulsed
    uwave_power = 14.5
    uwave_pulse_dur = 100/2
    num_freq_reps = int(1e4)

    # CW
    #uwave_power = -10.0
    #uwave_pulse_dur = None
    #num_freq_reps = None

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


def do_rabi(nv_sig, opti_nv_sig, apd_indices, state, uwave_time_range=[0, 200]):

    num_steps = 51
    num_reps = int(0.3e4)
    num_runs = 50

    period = rabi.main(
        nv_sig,
        apd_indices,
        uwave_time_range,
        state,
        num_steps,
        num_reps,
        num_runs,
        opti_nv_sig = opti_nv_sig
    )
    nv_sig["rabi_{}".format(state.name)] = period




def do_ramsey(nv_sig, opti_nv_sig, apd_indices):

    detuning = 10  # MHz
    precession_time_range = [0, 2 * 10 ** 3]
    num_steps = 101
    num_reps = int( 10 ** 4)
    num_runs = 6

    ramsey.main(
        nv_sig,
        apd_indices,
        detuning,
        precession_time_range,
        num_steps,
        num_reps,
        num_runs,
        opti_nv_sig = opti_nv_sig
    )




def do_spin_echo(nv_sig, apd_indices):

    # T2* in nanodiamond NVs is just a couple us at 300 K
    # In bulk it's more like 100 us at 300 K
    # max_time = 40  # us
    num_steps = int(20*2 + 1)  # 1 point per us
    #    num_steps = int(max_time/2) + 1  # 2 point per us
    #    max_time = 1  # us
    #    num_steps = 51
    precession_time_range = [20e3, 40 * 10 ** 3]
    #    num_reps = 8000
    #    num_runs = 5
    num_reps = 1000
    num_runs = 40

    #    num_steps = 151
    #    precession_time_range = [0, 10*10**3]
    #    num_reps = int(10.0 * 10**4)
    #    num_runs = 6

    state = States.LOW

    angle = spin_echo.main(
        nv_sig,
        apd_indices,
        precession_time_range,
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
    sample_name = "johnson"
    green_laser = "cobolt_515"

    
    nv_sig = { 
          "coords":[5.052, 4.328, 3.196], 
        "name": "{}-search".format(sample_name,),
        "disable_opt":False,
        "ramp_voltages": True,
        "expected_count_rate":None,
        
        "spin_laser": green_laser,
        "spin_laser_power": green_power,
        "spin_pol_dur": 1e4,
        "spin_readout_laser_power": green_power,
        "spin_readout_dur": 350,
        
        "imaging_laser":green_laser,
        "imaging_laser_power": green_power,
        "imaging_readout_dur": 1e7,
        
        "collection_filter": "630_lp",
        "magnet_angle": None,
        "resonance_LOW":2.8459,"rabi_LOW": 109.2,
        "uwave_power_LOW": 15.5,  # 15.5 max
        "resonance_HIGH": 2.8992,
        "rabi_HIGH": 59.6,
        "uwave_power_HIGH": 14.5,
    }  # 14.5 max
    
    
    
    
      
    
    nv_sig = nv_sig
    
    
    # %% Functions to run

    try:

        # tool_belt.init_safe_stop()

#         tool_belt.set_drift([0.0, 0.0, tool_belt.get_drift()[2]])  # Keep z
        # tool_belt.set_drift([0.0, 0.0, 0.0])  
        # tool_belt.set_xyz(labrad.connect(), [5,5,5]) 
#        tool_belt.set_xyz(labrad.connect(), [0,0,0])   


        # do_optimize(nv_sig,apd_indices)
        do_image_sample(nv_sig, apd_indices)
#        time.sleep(30)
#        do_image_sample(nv_sig, apd_indices)
#        do_stationary_count(nv_sig, apd_indices)
#        do_image_sample_xz(nv_sig, apd_indices)
        
#         do_optimize_magnet_angle(nv_sig, apd_indices)
#         do_resonance(nv_sig, nv_sig, apd_indices,  2.875, 0.2)
#         do_resonance(nv_sig, nv_sig, apd_indices,  2.875, 0.1)
        # do_resonance_state(nv_sig,nv_sig, apd_indices, States.LOW)
        
#         do_rabi(nv_sig, nv_sig, apd_indices, States.LOW, uwave_time_range=[0, 200])
        # do_rabi(nv_sig, nv_sig,apd_indices, States.HIGH, uwave_time_range=[0, 200])
        
         # do_pulsed_resonance(nv_sig, nv_sig, apd_indices, 2.875, 0.1)
        # do_pulsed_resonance_state(nv_sig, nv_sig,apd_indices, States.LOW)
        # do_ramsey(nv_sig, opti_nv_sig,apd_indices)
        # do_spin_echo(nv_sig, apd_indices)
        
        # do_spin_echo(nv_sig, apd_indices)


    finally:
        # Reset our hardware - this should be done in each routine, but
        # let's double check here
        
        tool_belt.reset_cfm()
        # Kill safe stop
        if tool_belt.check_safe_stop_alive():
            print("\n\nRoutine complete. Press enter to exit.")
            tool_belt.poll_safe_stop()
