# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 15:18:03 2022

@author: Carter Fox

This will be the interface where students can run all the microscope commands/experiments. 
It will run nv_control_panel with the inputted parameters

"""
import labrad
import utils.positioning as positioning
import utils.tool_belt as tool_belt
import utils.common as common
from utils.tool_belt import States, NormStyle 
import time
import numpy as np
import nv_control_panel as nv

# %%
if __name__ == "__main__":
    
    # %%%%%%%%%%%%%%% NV Parameters %%%%%%%%%%%%%%%
    
    nv_coords = [6.373, 4.295, 4.1 ] # V
    expected_count_rate = 13  # kcps
    magnet_angle =  65         # deg
    
    resonance_LOW = 2.8071      # GHz
    rabi_LOW = 80.9             # ns   
    uwave_power_LOW = 15.5      # dBm  15.5 max
    
    resonance_HIGH = 2.9484     # GHz
    rabi_HIGH = 100             # ns 
    uwave_power_HIGH = 14.5     # dBm  14.5 max 
    
    #%%  Prepare nv_sig with nv parameters  (do not alter nv_sig)
    
    green_power =8
    sample_name = "E6"
    green_laser = "cobolt_515"
    
        
    nv_sig = {
        "coords": nv_coords,
        
        "name": "{}-nv1".format(sample_name,),"disable_opt":False,"ramp_voltages": False,
        "spin_laser": green_laser, 
        "spin_laser_power": green_power,
        "spin_pol_dur": 1e4, 
        "spin_readout_laser_power": green_power, 
        "spin_readout_dur": 350,
        'norm_style':NormStyle.SINGLE_VALUED,
        
        "imaging_laser":green_laser, 
        "imaging_laser_power": green_power, 
        "imaging_readout_dur": 1e7, "collection_filter": "630_lp",
        
        "expected_count_rate":expected_count_rate,
        "magnet_angle": magnet_angle, 
        
        "resonance_LOW":resonance_LOW ,"rabi_LOW": rabi_LOW, "uwave_power_LOW": uwave_power_LOW,  
        "resonance_HIGH": resonance_HIGH , "rabi_HIGH": rabi_HIGH, "uwave_power_HIGH": uwave_power_HIGH,
        }   
    
    nv_sig = nv_sig

    
    # %% %%%%%%%%%%%%%%% Experimental section %%%%%%%%%%%%%%%
    
    try:

        ####### Useful global functions #######
        ### Get/Set drift
        # nv.get_drift()
        # nv.reset_xy_drift()
        # nv.reset_xyz_drift()
        
        ### Turn laser on or off 
        # tool_belt.laser_on_no_cxn('cobolt_515') # turn the laser on
        # tool_belt.laser_off_no_cxn('cobolt_515') # turn the laser on

    
        ####### EXPERIMENT 0: Finding an nv #######
        ### Take confocal image
        ### xy scans can be ['small', 'medium', 'big-ish', 'big', 'huge']
        
        # nv.do_image_sample(nv_sig,  scan_size='small')
        nv.do_image_sample(nv_sig, scan_size='medium')
        # nv.do_image_sample(nv_sig,  scan_size='big-ish')
        # nv.do_image_sample(nv_sig,  scan_size='big')
        # nv.do_image_sample(nv_sig,  scan_size='huge')
        
        
        ### Optimize on NV
        # nv.do_optimize(nv_sig)
            
        
        ####### EXPERIMENT 1: CW electron spin resonance #######
        ### Measure CW resonance
        # mangles = [0,30,60,90,120,150]
        # nv.do_resonance(nv_sig, freq_center=2.87, freq_range=0.2, uwave_power=-5.0, num_runs=20, num_steps=51)
    
    
        ####### EXPERIMENT 2: Rabi oscillations #######
        # nv.do_rabi(nv_sig,  States.LOW, uwave_time_range=[0, 150], num_runs=15, num_steps=51, num_reps=2e4)
        # nv.do_rabi(nv_sig,  States.HIGH, uwave_time_range=[0, 200], num_runs=15, num_steps=51, num_reps=2e4)
        
        
        ####### EXPERIMENT 3: Ramsey experiment #######
        # nv.do_ramsey(nv_sig, state=States.LOW, precession_time_range = [0, 1.75 * 10 ** 3],
        #                set_detuning=4, num_runs=20, num_steps = 101,num_reps=2e4)  
        
        # nv.do_ramsey(nv_sig, state=States.HIGH, precession_time_range = [0, 1.75 * 10 ** 3],
                      # set_detuning=4, num_runs=20, num_steps = 101,num_reps=2e4)  
        
        
        ####### EXPERIMENT 4: Spim echo #######
        # do_spin_echo(nv_sig, state=States.LOW, echo_time_range = [0, 110 * 10 ** 3], 
                     # num_runs=50, num_steps=71, num_reps=2e4) 
    
    finally:

        # Make sure everything is reset
        tool_belt.reset_cfm()
        tool_belt.reset_safe_stop()

