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
import time
import copy
import utils.tool_belt as tool_belt
import majorroutines.image_sample_digital as image_sample_digital
import majorroutines.optimize_digital as optimize_digital
import chargeroutines.SPaCE_digital as SPaCE_digital
import chargeroutines.SPaCE_digital_annulus as SPaCE_digital_annulus
import chargeroutines.g2_measurement as g2_SCC_branch
import majorroutines.stationary_count as stationary_count

# import majorroutines.set_drift_from_reference_image as set_drift_from_reference_image
import debug.test_major_routines as test_major_routines
from utils.tool_belt import States
import time
import matplotlib.pyplot as plt


# %% Major Routines


def do_image_sample(nv_sig, apd_indices):
    scale = 1 #um / V
    

    #    scan_range = 5.0*scale
    # scan_range = 3.0*scale
    # scan_range = 1.5*scale
    # scan_range = 1.0*scale
    # scan_range = 0.8*scale
    # scan_range = 0.5*scale
    # scan_range = 0.3*scale
    # scan_range = 0.25*scale
    # scan_range = 0.15*scale
    #scan_range = 0.1*scale
    #scan_range = 0.04*scale
    #scan_range = 0.025*scale
   # scan_range = 0.01*scale
    scan_range = 2.2
    # scan_range = 1
    #
    # num_steps = 400
    # num_steps = 300
    # num_steps = 200
    #num_steps = 150
    # num_steps = 135
    # num_steps = 120
    num_steps =111
    #num_steps=81
    # num_steps = 81
    # num_steps = 61
    #num_steps = 31
    # num_steps = 21

    # For now we only support square scans so pass scan_range twice
    image_sample_digital.main(nv_sig, scan_range, scan_range, num_steps, apd_indices)


def do_optimize(nv_sig, apd_indices):

    optimize_coords = optimize_digital.main(
        nv_sig,
        apd_indices,
        set_to_opti_coords=False,
        save_data=True,
        plot_data=True,
    )
    return optimize_coords

def do_optimize_list(nv_sig_list, apd_indices):

    optimize_digital.optimize_list(nv_sig_list, apd_indices)


def do_opti_z(nv_sig_list, apd_indices):

    optimize_digital.opti_z(
        nv_sig_list,
        apd_indices,
        set_to_opti_coords=False,
        save_data=True,
        plot_data=True,
    )

def do_stationary_count(nv_sig, apd_indices):

    run_time = 1 * 60 * 10 ** 9  # ns

    stationary_count.main(nv_sig, run_time, apd_indices)

def do_g2_measurement(nv_sig, apd_a_index, apd_b_index):

    run_time = 5*60  # s
    diff_window = 150  # ns

    # g2_measurement.main(
    g2_SCC_branch.main(
        nv_sig, run_time, diff_window, apd_a_index, apd_b_index
    )


def do_SPaCE(nv_sig, opti_nv_sig, num_runs, num_steps_a, num_steps_b,
               img_range_1D, img_range_2D, offset,opti_interval = 2, charge_state_threshold = None):
    # dr = 0.025 / numpy.sqrt(2)
    # img_range = [[-dr,-dr],[dr, dr]] #[[x1, y1], [x2, y2]]
    # num_steps = 101
    # num_runs = 50
    # measurement_type = "1D"

    # img_range = 0.075
    # num_steps = 71
    # num_runs = 1
    # measurement_type = "2D"

    # dz = 0
    SPaCE_digital.main(nv_sig, opti_nv_sig, num_runs, num_steps_a, num_steps_b,
               charge_state_threshold, img_range_1D, img_range_2D, offset, opti_interval = opti_interval)


def do_SPaCE_annulus(nv_sig, opti_nv_sig, num_runs, num_steps_a, num_steps_b,
               img_range_1D, img_range_2D,  offset, ring_radii = [],
               opti_interval = 2, charge_state_threshold = None):
    # dz = 0
    SPaCE_digital_annulus.main(nv_sig, opti_nv_sig, num_runs, num_steps_a, num_steps_b,
               charge_state_threshold, img_range_1D, img_range_2D, offset,
               ring_radii,  opti_interval = opti_interval)

# %% Run the file


if __name__ == "__main__":

    # In debug mode, don't bother sending email notifications about exceptions
    debug_mode = False
    

    # %% Shared parameters

    apd_indices = [0]
    # apd_indices = [1]
    # apd_indices = [0,1]

    nd_yellow = "nd_1.0"
    green_power = 9
    red_power = 80
    sample_name = "johnson"
    green_laser = "cobolt_515"
    yellow_laser = "laserglow_589"
    red_laser = "cobolt_638"

    nv_sig_search = {
        "coords": [250.422+4, 250.982-4, 5],
        "name": "{}-search".format(sample_name),
        "disable_opt": False,
        "ramp_voltages": False,
        "expected_count_rate": None,
        "imaging_laser": green_laser,
        "imaging_laser_power": green_power,
        "imaging_readout_dur": 1e7,
        "collection_filter": "630_lp",
        "magnet_angle": None,
        "resonance_LOW": 2.8012,
        "rabi_LOW": 141.5,
        "uwave_power_LOW": 15.5,  # 15.5 max
        "resonance_HIGH": 2.9445,
        "rabi_HIGH": 191.9,
        "uwave_power_HIGH": 14.5,
    }  # 14.5 max

    
     
    nv_sig_1 = {
        "coords":[250.662, 251.083, 5],
        "name": "{}-nv0_2021_12_22".format(sample_name,),
        #"coords":[254.928, 246.916, 5],
       # "name": "{}-nv0_2021_12_27".format(sample_name,),
        "disable_opt": False,
        "ramp_voltages": False,
        "expected_count_rate":30,
        
        
        "spin_laser": green_laser,
        "spin_laser_power": green_power,
        "spin_pol_dur": 1e5,
        "spin_readout_laser_power": green_power,
        "spin_readout_dur": 350,
        
        "imaging_laser":green_laser,
        "imaging_laser_power": green_power,
        "imaging_readout_dur": 1e7,
        
        
        'nv-_reionization_laser': green_laser, 'nv-_reionization_laser_power': green_power, 
        'nv-_reionization_dur': 1E5,
        'nv0_ionization_laser': red_laser, 'nv0_ionization_laser_power': red_power,
        'nv0_ionization_dur':500,
        
        'spin_shelf_laser': yellow_laser, 'spin_shelf_laser_filter': nd_yellow, 
        'spin_shelf_laser_power': 0.4, 'spin_shelf_dur':0,
            
        "initialize_laser": green_laser,
        "initialize_laser_power": green_power,
        "initialize_dur": 1e4,
        "CPG_laser": red_laser,
        'CPG_laser_power': red_power,
        "CPG_laser_dur": 50e3,
        "charge_readout_laser": yellow_laser,
        "charge_readout_laser_filter": nd_yellow,
        "charge_readout_laser_power": 0.15,
        "charge_readout_dur": 100e6,
        
        "collection_filter": "630_lp",
        "magnet_angle": None,
        "resonance_LOW":2.9250,"rabi_LOW": 182.3,
        "uwave_power_LOW": 15.5,  # 15.5 max
        "resonance_HIGH": 2.9496,
        "rabi_HIGH": 215,
        "uwave_power_HIGH": 14.5,
    }  # 14.5 max
    
      
    
    nv_sig = nv_sig_1
    
    
    # %% Functions to run

    try:
            
        
        # Operations that don't need an NV
        #tool_belt.set_drift([0.0, 0.0, 0.0])  # Totally reset
       # tool_belt.set_drift([0.0, 0.0, tool_belt.get_drift()[2]])  # Keep z
        # tool_belt.set_xyz(labrad.connect(), [0.0, 0.0 , 5.0])


        #do_optimize(nv_sig, apd_indices)
        #do_image_sample(nv_sig, apd_indices)
        # do_g2_measurement(nv_sig, 0, 1)
        # do_stationary_count(nv_sig, apd_indices)
        
        offset_x =-1-0.188+0.03+0.05
        offset_y = -1+0.580-0.135+0.090
        offset_z = 0
        offset_list = [offset_x, offset_y, offset_z]
    
    
             
        # 1st airy ring power
        t_list = [10e6]  #20e6 #could also try 10e6
        for t in t_list:
            nv_sig['CPG_laser_dur'] = t
            
            # do_SPaCE_annulus(nv_sig, nv_sig, 1, 111,111, 
            #             None,  [2.2,2.2, 0], [offset_x, offset_y, offset_z], ring_radii = [0.8, 1.0])
            #positive and negative X line scans
            
            
            do_SPaCE(nv_sig, nv_sig,100,201 , None, 
                [[0.830+offset_x, offset_y,offset_z ], [1.030+offset_x, offset_y,offset_z]], None, offset_list, 2)
            
            do_SPaCE(nv_sig, nv_sig, 100,201 , None, 
                      [[-0.830+offset_x, offset_y,offset_z ], [-1.03+offset_x, offset_y,offset_z]], None, offset_list, 2)
            
            
            # # 2D scans
            img_range_2D = [2.2, 2.2, 0]
            do_SPaCE(nv_sig, nv_sig, 2, 111, 111, #10 nm steps
                          None,  img_range_2D,offset_list)
            
            # img_range_2D = [1.2,0, 2]
            # do_SPaCE(nv_sig, nv_sig, 2, 61, 81, 
            #             None,  img_range_2D,offset_list)
            
        # well resolved 2D annulus scan for 5 ms
        #nv_sig['CPG_laser_dur'] = 1e5
        
        # 
        #do_SPaCE_annulus(nv_sig, nv_sig, 1, 51, 51, 
        #                None,  [1.2,1.2,0], [offset_x, offset_y, offset_z], ring_radii = [0.35, 0.55])


    except Exception as exc:
        # Intercept the exception so we can email it out and re-raise it
        if not debug_mode:
            tool_belt.send_exception_email()
        raise exc

    finally:
        # Reset our hardware - this should be done in each routine, but
        # let's double check here
        tool_belt.reset_cfm()
        # Kill safe stop
        if tool_belt.check_safe_stop_alive():
            print("\n\nRoutine complete. Press enter to exit.")
            tool_belt.poll_safe_stop()
