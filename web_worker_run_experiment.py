# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 15:18:03 2022

@author: Carter Fox

This will be the interface where the web user interface can run all the microscope commands/experiments. 
It will run nv_control_panel with the inputted parameters

"""
import nv_control_panel as nv
import utils.tool_belt as tool_belt
from utils.tool_belt import States, NormStyle
import labrad
import time
import sys
import argparse
# from utils.tool_belt import reset_xy_drift as reset_xy_drift
# import utils.tool_belt.reset_drift as reset_xyz_drift
# import utils.tool_belt.laser_on_no_cxn as laser_on
# import utils.tool_belt.laser_off_no_cxn as laser_off

# %%
laser_namer = 'cobolt_515'
def turn_laser_on(time_on): #time to leave laser on in seconds
    tool_belt.laser_on_no_cxn(laser_namer)
    time.sleep(time_on)
# def turn_laser_off():
#     tool_belt.laser_off_no_cxn(lase_namer)
    
# %%
if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog = sys.argv[0],description = 'Run nvcenter experiments executed by the web worker process.')
    parser.add_argument('--experiment-type',action='store',required=True)
    parser.add_argument('--center-freq',action='store',type=float)
    parser.add_argument('--sweep-freq-range',action='store',type=float)
    parser.add_argument('--sweep-points',action='store',type=int)
    parser.add_argument('--num-sweeps',action='store',type=int)
    parser.add_argument('--pulse-duration',action='store',type=float)
    parser.add_argument('--image-size',action='store',type=str)
    parser.add_argument('--state',action='store',type=str)
    parser.add_argument('--uwave_time_max',action='store',type=float)
    parser.add_argument('--precession_time_max',action='store',type=float)
    parser.add_argument('--echo_time_max',action='store',type=float)
    parser.add_argument('--detuning',action='store',type=float)
    args = parser.parse_args()

    # %%%%%%%%%%%%%%% NV Parameters %%%%%%%%%%%%%%%
    
    coords = [6.429, 5.664,4.25] # V
    expected_count_rate = 18     # kcps
    magnet_angle =  60  # deg
    
    resonance_LOW = 2.7641 # 2.7911           # GHz
    rabi_LOW = 75.2 # 80.7 #88.2 # 84.3, today:88.9ns                  # ns   
    
    resonance_HIGH = 2.9098 # 2.9483          # GHz
    rabi_HIGH = 76.9 # 80.8 # 89.6 # 89.7  , today 88.3ns               # ns 
    
    #%%  Prepare nv_sig with nv parameters  (do not alter nv_sig)
    
    green_power = 8
    sample_name = "E6test"
    green_laser = "cobolt_515"
    
    nv_sig = { 
          "coords":coords,
        "name": "{}-nv1".format(sample_name,),
        "disable_opt":False, "ramp_voltages": True,
        "expected_count_rate":expected_count_rate,
        
        "spin_laser": green_laser, "spin_laser_power": green_power, "spin_readout_laser_power": green_power,
        "spin_pol_dur": 1e4, "spin_readout_dur": 350,
        "imaging_laser":green_laser, "imaging_laser_power": green_power,
        "imaging_readout_dur": 1e7,
        'norm_style':NormStyle.SINGLE_VALUED,

        "collection_filter": "630_lp",
        "magnet_angle": magnet_angle,
        "resonance_LOW":resonance_LOW,"rabi_LOW": rabi_LOW,
        "uwave_power_LOW": 15.5 ,  # 14.5 max
        "resonance_HIGH": resonance_HIGH,
        "rabi_HIGH": rabi_HIGH, 
        "uwave_power_HIGH": 14.5 }  # 14.5 max
    
    nv_sig = nv_sig

    
    # %% %%%%%%%%%%%%%%% Experimental section %%%%%%%%%%%%%%%
    
    try:

        ####### Useful global functions #######
        ### Reset drift
        # tool_belt.reset_xy_drift()
        # print(tool_belt.get_drift())
        # tool_belt.set_drift([0.0, 0.0, 0.0]) 
       
        
        if args.experiment_type == "image":
            nv.do_image_sample(nv_sig, scan_size=args.image_size)
            
        elif args.experiment_type == "optimize":
            nv.do_optimize(nv_sig)

        elif args.experiment_type == "ESR":
            nv.do_resonance(nv_sig, freq_center=args.center_freq, freq_range=args.sweep_freq_range, num_steps=args.sweep_points, num_runs=args.num_sweeps)
        
        elif args.experiment_type == "rabi":
            if args.state == 'low':
                state_input = States.LOW
            elif args.state == 'high':
                state_input = States.HIGH
            nv.do_rabi(nv_sig,state=state_input,uwave_time_range=[0,args.uwave_time_max], num_steps=args.sweep_points, num_runs=args.num_sweeps)
        
        elif args.experiment_type == "ramsey":
            if args.state == 'low':
                state_input = States.LOW
            elif args.state == 'high':
                state_input = States.HIGH
            nv.do_ramsey(nv_sig,state=state_input,set_detuning=args.detuning,precession_time_range=[0,args.precession_time_max], num_steps=args.sweep_points, num_runs=args.num_sweeps)
        
        elif args.experiment_type == "spin-echo":
            if args.state == 'low':
                state_input = States.LOW
            elif args.state == 'high':
                state_input = States.HIGH
            nv.do_spin_echo(nv_sig,state=state_input,precession_time_range=[0,args.echo_time_max], num_steps=args.sweep_points, num_runs=args.num_sweeps)
        
        else:
            raise Exception("Unsupported experiment type: " + repr(args.experiment_type))
    
    except Exception as exc:
        print("Code crashed. Press enter to see error")
        raise exc
    
    finally:
        # Reset our hardware - this should be done in each routine, but
        # let's double check here
        tool_belt.reset_cfm()
        tool_belt.reset_safe_stop()
