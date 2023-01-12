# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 15:18:03 2022

@author: Carter Fox

This will be the interface where the web user interface can run all the microscope commands/experiments. 
It will run nv_control_panel with the inputted parameters

"""
import nv_control_panel as nv
import utils.tool_belt as tool_belt
from utils.tool_belt import States
import labrad
import time
import sys
import argparse
# from utils.tool_belt import reset_xy_drift as reset_xy_drift
# import utils.tool_belt.reset_drift as reset_xyz_drift
# import utils.tool_belt.laser_on_no_cxn as laser_on
# import utils.tool_belt.laser_off_no_cxn as laser_off

# %%
lase_namer = 'cobolt_515'
def turn_laser_on(time_on): #time to leave laser on in seconds
    tool_belt.laser_on_no_cxn(lase_namer)
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
    parser.add_argument('--pulse-duration',action='store',type=int)
    args = parser.parse_args()

    # %%%%%%%%%%%%%%% NV Parameters %%%%%%%%%%%%%%%
    
    nv_coords = [5, 5, 5 ] # V
    expected_count_rate = None     # kcps
    magnet_angle =  30.07
           # deg
    
    resonance_LOW = 2.7917 # 2.7911           # GHz
    rabi_LOW = 78.9 # 80.7 #88.2 # 84.3, today:88.9ns                  # ns   
    uwave_power_LOW = 14      # dBm
    
    resonance_HIGH = 2.9484 # 2.9483          # GHz
    rabi_HIGH = 76.9 # 80.8 # 89.6 # 89.7  , today 88.3ns               # ns 
    uwave_power_HIGH = 14      # dBm
    
    #%%  Prepare nv_sig with nv parameters  (do not alter nv_sig)
    
    green_power =4.8
    sample_name = "johnson"
    green_laser = "cobolt_515"
    
    nv_sig = { 
          "coords":nv_coords,
        "name": "{}-nv1".format(sample_name,),
        "disable_opt":False, "ramp_voltages": True,
        "expected_count_rate":expected_count_rate,
        
        "spin_laser": green_laser, "spin_laser_power": green_power, "spin_readout_laser_power": green_power,
        "spin_pol_dur": 1e4, "spin_readout_dur": 350,
        "imaging_laser":green_laser, "imaging_laser_power": green_power,
        "imaging_readout_dur": 1e7,

        "collection_filter": "630_lp",
        "magnet_angle": magnet_angle,
        "resonance_LOW":resonance_LOW,"rabi_LOW": rabi_LOW,
        "uwave_power_LOW": uwave_power_LOW,  # 14.5 max
        "resonance_HIGH": resonance_HIGH,
        "rabi_HIGH": rabi_HIGH, 
        "uwave_power_HIGH": uwave_power_HIGH, }  # 14.5 max
    
    nv_sig = nv_sig

    
    # %% %%%%%%%%%%%%%%% Experimental section %%%%%%%%%%%%%%%
    
    try:

        ####### Useful global functions #######
        ### Reset drift
        # tool_belt.reset_xy_drift()
        # print(tool_belt.get_drift())
        # tool_belt.set_drift([0.0, 0.0, 0.0]) 
        # turn_laser_on(2000) # To see the laser on, you can use this function to turn on the laser for the inputted amount of seconds
        # tool_belt.set_xyz(labrad.connect(), [5,5,5])

    
        ####### EXPERIMENT 0: Finding an nv #######
        ### Take confocal image
        ### xy scans can be ['small', 'medium', 'big-ish', 'big', 'huge']
        
        # nv.do_image_sample(nv_sig,  scan_size='small')
        # nv.do_image_sample(nv_sig, scan_size='medium')
        # nv.do_image_sample(nv_sig,  scan_size='big-ish')
        # nv.do_image_sample(nv_sig,  scan_size='big')
        # nv.do_image_sample(nv_sig,  scan_size='huge')
        # nv.do_image_sample_xz(nv_sig,steps=80,zrange=6) 
        # for z in [2,3,4,5,6,7,8]:
        #     nv_sig['coords'][2] = z
        #     nv.do_image_sample(nv_sig,  scan_size='big')#xz scan for finding better z position if needed
        
        ### Optimize on NV
         # nv.do_optimize(nv_sig)
            
        
        ####### EXPERIMENT 1: CW electron spin resonance #######
        ### Measure CW resonance
        # nv.do_resonance(nv_sig, freq_center=2.87, freq_range=0.2, num_steps=101, num_runs=20, uwave_power=-15)
        # Dan: what to do with args.pulse_duration?
        # Dan: should uwave_power be an input parameter?
        if args.experiment_type == "ESR":
            nv.do_resonance(nv_sig, freq_center=args.center_freq, freq_range=args.sweep_freq_range, num_steps=args.sweep_points, num_runs=args.num_sweeps, uwave_power=-15)
        else:
            raise Exception("Unsupported experiment type: " + repr(args.experiment_type))

        ####### EXPERIMENT 2: Rabi oscillations #######
        # nv.do_rabi(nv_sig,  States.LOW, uwave_time_range=[0, 200], num_steps = 51, num_reps = 1e4, num_runs=15)
        #nv.do_rabi(nv_sig,  States.HIGH, uwave_time_range=[0, 200], num_steps = 51, num_reps = 1e4, num_runs=15)
        
        
        
        ####### EXPERIMENT 3: Ramsey experiment #######
        # nv.do_ramsey(nv_sig, state=States.LOW, precession_time_range=[0, 2000],  
                                       # num_steps=151, set_detuning=4, num_reps=1e4, num_runs=200) 
        
        # nv.do_ramsey(nv_sig, state=States.HIGH, precession_time_range=[0, 120],  
        #                             num_steps=101, set_detuning=4, num_reps=1e4, num_runs=50) 
        
        ####### EXPERIMENT 4: Spim echo #######
        # nv.do_spin_echo(nv_sig, state=States.HIGH, echo_time_range=[0, 150e3], 
                            # num_steps=151, num_reps = 1e4, num_runs=200) 
    
    except Exception as exc:
        print("Code crashed. Press enter to see error")
        raise exc
    
    finally:
        # Reset our hardware - this should be done in each routine, but
        # let's double check here
        
        tool_belt.reset_cfm()
        # Kill safe stop
        if tool_belt.check_safe_stop_alive():
            print("\n\nRoutine complete. Press enter to exit.")
            tool_belt.poll_safe_stop()
