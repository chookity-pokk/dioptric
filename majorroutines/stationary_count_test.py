# -*- coding: utf-8 -*-
"""
Created on Fri Apr  1 13:31:01 2022

@author: student
"""


import utils.tool_belt as tool_belt
import numpy
import matplotlib.pyplot as plt
import time
import labrad



def main(nv_sig, readout, run_time):

    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig, readout,  run_time)

    return 

def main_with_cxn(cxn, nv_sig, readout,  run_time):

    # %% Some initial setup
    apd_indices = [0]
#    tool_belt.reset_cfm(cxn)

    num_samples = int(run_time/readout)
    print('num to read: ' + str(num_samples))


    # %% Set up the imaging laser

    laser_key = 'imaging_laser'
    readout_laser = nv_sig[laser_key]
    readout_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)

    # %% Load the PulseStreamer


    seq_args = [0, readout, apd_indices[0], readout_laser, readout_power]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    ret_vals = cxn.pulse_streamer.stream_load('simple_readout.py',
                                              seq_args_string)
    period = ret_vals[0]
    print(1/(period*1e-9))


    # %% Set up the APD
    
    apd_server = tool_belt.get_apd_server(cxn)
    
#    apd_server.start_tag_stream(apd_indices)
    apd_server.load_stream_reader(apd_indices[0],period,  num_samples)
    

    # %% Initialize the figure

    samples = numpy.empty(num_samples)
    samples.fill(numpy.nan)  # Only floats support NaN


    # %% Collect the data
    cxn.pulse_streamer.stream_start(num_samples)

    # timeout_duration = ((period*(10**-9)) * total_num_samples) + 10
    # timeout_inst = time.time() + timeout_duration

    num_read_so_far = 0

    tool_belt.init_safe_stop()

    while num_read_so_far < num_samples:

        # if time.time() > timeout_inst:
        #     break

        if tool_belt.safe_stop():
            break

#        new_samples = apd_server.read_counter_simple()
        new_samples = apd_server.read_stream(apd_indices[0], num_samples)

        # Read the samples and update the image
#        print(new_samples)
        num_new_samples = len(new_samples)
        if num_new_samples > 0:


#            update_line_plot(new_samples, num_read_so_far, *args)
            num_read_so_far += num_new_samples
            
    print('total num read: ' + str(num_read_so_far))
    print(new_samples)
    
    # %% Clean up and report the data

#    tool_belt.reset_cfm(cxn)

    return 

# %%
nv_sig = { 
          "coords":[-0.121, 0.691,  6.241], 
        "name": "test",
        "disable_opt":True,
        
        "imaging_laser":'cobolt_515',
        "imaging_laser_power": 10,
        "imaging_readout_dur": 1e7,
        
        "magnet_angle": None,
        "resonance_LOW":2.87,"rabi_LOW": 150,
        "uwave_power_LOW": 15.5,  # 15.5 max
        "resonance_HIGH": 2.932,
        "rabi_HIGH": 59.6,
        "uwave_power_HIGH": 14.5,
    }  # 14.5 max

readout = 4e6 #timing issues if readout is too short. might need to impose some limit to the samplign frequency?
run_time = 100e7

main(nv_sig, readout, run_time)