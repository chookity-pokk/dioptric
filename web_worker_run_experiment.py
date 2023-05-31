# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 15:18:03 2022

@author: Carter Fox and Dan Bradley

This will be the interface where the web user interface can run all the microscope commands/experiments. 
It will run nv_control_panel with the inputted parameters

"""

# avoid login prompts
import os
os.environ['LABRADUSER'] = ""
os.environ['LABRADPASSWORD'] = ""

import nv_control_panel as nv
import utils.tool_belt as tool_belt
from utils.tool_belt import States, NormStyle
import labrad
import time
import sys
import argparse
from pathlib import Path
# from utils.tool_belt import reset_xy_drift as reset_xy_drift
# import utils.tool_belt.reset_drift as reset_xyz_drift
# import utils.tool_belt.laser_on_no_cxn as laser_on
# import utils.tool_belt.laser_off_no_cxn as laser_off

# %%
def cwd_get_file_path(file,timestamp,fname,subfolder=None):
    """write output files into the current working directory
       rather than the default location
    """
    return Path(os.getcwd()) / fname

def cwd_get_raw_data_path(
    file_name,
    path_from_nvdata=None,
    nvdata_dir=None,
):
    """retrieve files from the current working directory if they exist there"""
    file_name_ext = "{}.txt".format(file_name)
    if os.path.exists(file_name_ext):
        return Path(file_name_ext)
    return tool_belt.orig_get_raw_data_path(file_name,path_from_nvdata,nvdata_dir)

def safeFileName(fname):
    fname = fname.replace("/","_")
    fname = fname.replace("\\","_")
    fname = fname.replace(" ","_")
    return fname

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog = sys.argv[0],description = 'Run nvcenter experiments executed by the web worker process.')
    parser.add_argument('--experiment-type',action='store',required=True)
    parser.add_argument('--name',action='store')
    parser.add_argument('--center-freq',action='store',type=float)
    parser.add_argument('--sweep-freq-range',action='store',type=float)
    parser.add_argument('--sweep-points',action='store',type=int)
    parser.add_argument('--num-sweeps',action='store',type=int)
    parser.add_argument('--pulse-duration',action='store',type=float)
    parser.add_argument('--image-size',action='store',type=str)
    parser.add_argument('--state',action='store',type=str)
    parser.add_argument('--uwave-time-max',action='store',type=float)
    parser.add_argument('--precession-time-max',action='store',type=float)
    parser.add_argument('--echo-time-max',action='store',type=float)
    parser.add_argument('--detuning',action='store',type=float)
    parser.add_argument('--x',action='store',type=float,required=True)
    parser.add_argument('--y',action='store',type=float,required=True)
    parser.add_argument('--z',action='store',type=float,required=True)
    args = parser.parse_args()

    tool_belt.get_file_path = cwd_get_file_path
    tool_belt.orig_get_raw_data_path = tool_belt.get_raw_data_path
    tool_belt.get_raw_data_path = cwd_get_raw_data_path

    # %%%%%%%%%%%%%%% NV Parameters %%%%%%%%%%%%%%%
    
    sample_name = args.name
    if not sample_name:
        sample_name = args.experiment_type
    sample_name = safeFileName(sample_name)

    nv_coords = [args.x,args.y,args.z] # V
    expected_count_rate = 19   # kcps
    magnet_angle =  60  # deg
    
    resonance_LOW = 2.7641 # 2.7911           # GHz
    rabi_LOW = 75.2 # 80.7 #88.2 # 84.3, today:88.9ns                  # ns   
    
    resonance_HIGH = 2.9098 # 2.9483          # GHz
    rabi_HIGH = 76.9 # 80.8 # 89.6 # 89.7  , today 88.3ns               # ns 
    
    #%%  Prepare nv_sig with nv parameters  (do not alter nv_sig)

    green_power = 10
    green_laser = "cobolt_515"

    nv_sig = { 
        "coords":nv_coords,
        "name": sample_name,
        "disable_opt":False, "ramp_voltages": False,
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
    
    
    # %% %%%%%%%%%%%%%%% Experimental section %%%%%%%%%%%%%%%
    
    try:

        ####### Useful global functions #######
        ### Reset drift
        # tool_belt.reset_xy_drift()
        # print(tool_belt.get_drift())
        # tool_belt.set_drift([0.0, 0.0, 0.0]) 
        
        if args.experiment_type == 'auto-tracker':
            nv.do_auto_check_location(nv_sig)
        
        elif args.experiment_type == "image":
            fname = nv.do_image_sample(nv_sig, scan_size=args.image_size, close_plot=True)
            print("Image fname: ",fname)
        elif args.experiment_type == "optimize":
            nv.do_optimize(nv_sig, close_plot=True)

        elif args.experiment_type == "ESR":
            nv.do_resonance(nv_sig, freq_center=args.center_freq, freq_range=args.sweep_freq_range, 
                            num_steps=args.sweep_points, num_runs=args.num_sweeps, close_plot=True)
        
        elif args.experiment_type == "rabi":
            if args.state == 'low':
                state_input = States.LOW
            elif args.state == 'high':
                state_input = States.HIGH
            nv.do_rabi(nv_sig,state=state_input,uwave_time_range=[0,args.uwave_time_max], 
                       num_steps=args.sweep_points, num_runs=args.num_sweeps, close_plot=True)
        
        elif args.experiment_type == "ramsey":
            if args.state == 'low':
                state_input = States.LOW
            elif args.state == 'high':
                state_input = States.HIGH
            nv.do_ramsey(nv_sig,state=state_input,set_detuning=args.detuning,precession_time_range=[0,1000*args.precession_time_max], 
                         num_steps=args.sweep_points, num_runs=args.num_sweeps, close_plot=True)
        
        elif args.experiment_type == "spin-echo":
            if args.state == 'low':
                state_input = States.LOW
            elif args.state == 'high':
                state_input = States.HIGH
            nv.do_spin_echo(nv_sig,state=state_input,echo_time_range=[0,1000*args.echo_time_max], 
                            num_steps=args.sweep_points, num_runs=args.num_sweeps, close_plot=True)
        
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
