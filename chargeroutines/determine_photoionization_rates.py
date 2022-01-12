# -*- coding: utf-8 -*-
"""
Created on mon Apr 8 10:45:09 2020

This file ru ns a sequence that places the NV in NV- (NV0), then applies a test
pulse of some length, then reads out the NV with yellow.

The point of this measurement is to determine how fast the NV charge states
change under illumination. 

USE WITH 515 DM MOD

@author: agardill
"""
import utils.tool_belt as tool_belt
import majorroutines.optimize_digital as optimize
import numpy
import time
import matplotlib.pyplot as plt
import labrad
import copy


#%% Main
# Connect to labrad in this file, as opposed to control panel
def main(nv_sig, apd_index, num_reps):

    with labrad.connect() as cxn:
        green_counts, red_counts = main_with_cxn(cxn, nv_sig, apd_index,
                                 num_reps)
        
    return green_counts, red_counts
def main_with_cxn(cxn, nv_sig, apd_index, num_reps):

    tool_belt.reset_cfm(cxn)
    
    tool_belt.set_filter(cxn, nv_sig, 'charge_readout_laser')
    tool_belt.set_filter(cxn, nv_sig, 'nv-_prep_laser')
    
    yellow_laser_power = tool_belt.set_laser_power(cxn, nv_sig, 'charge_readout_laser')
    green_laser_power = tool_belt.set_laser_power(cxn, nv_sig, "nv-_prep_laser")
    red_laser_power = tool_belt.set_laser_power(cxn,nv_sig,"nv0_prep_laser")
    test_laser_power = tool_belt.set_laser_power(cxn,nv_sig,"test_laser")
    
    yellow_laser_key = nv_sig['charge_readout_laser']
    green_laser_key = nv_sig['nv-_prep_laser']
    red_laser_key = nv_sig['nv0_prep_laser']
    
    test_laser_key = nv_sig["test_laser"]
    #test_laser_power = nv_sig["test_laser_power"]
    test_laser_dur = nv_sig["test_laser_duration"]
    
    readout_pulse_time = nv_sig['charge_readout_dur']
    
    reionization_time = nv_sig['nv-_prep_laser_dur']
    ionization_time = nv_sig['nv0_prep_laser_dur']
    coords = nv_sig['coords']
      

    # Set up our data lists
    opti_coords_list = []
    
    # Optimize
    opti_coords = optimize.main_with_cxn(cxn, nv_sig, apd_index)
    opti_coords_list.append(opti_coords)
    drift = tool_belt.get_drift()
    adjusted_nv_coords = coords + numpy.array(drift)
    tool_belt.set_xyz(cxn, adjusted_nv_coords)
    
    
    # Pulse sequence to do a single pulse followed by readout           
    # seq_file = 'photoionization_rates_temp.py'
      
    # seq_args = [readout_pulse_time, reionization_time, ionization_time, test_laser_dur, \
    #     yellow_laser_key, green_laser_key, red_laser_key, test_laser_key, \
    #       yellow_laser_power, green_laser_power, red_laser_power,  \
    #         apd_index[0]]
    # seq_args_string = tool_belt.encode_seq_args(seq_args)

    # # Load the APD
    # cxn.apd_tagger.start_tag_stream(apd_index)
    # # Clear the buffer
    # cxn.apd_tagger.clear_buffer()
    # # Run the sequence
    # cxn.pulse_streamer.stream_immediate(seq_file, num_reps, seq_args_string)

    # # ret_vals = cxn.apd_tagger.read_counter_separate_gates(1)
    # # counts = ret_vals[0]
    
    # # green_counts = counts[0::2]
    # # red_counts = counts[1::2]
    
    
    # counts = cxn.apd_tagger.read_counter_simple(num_reps*2)
    # green_counts = counts[0::2]
    # red_counts = counts[1::2]
    # print(len(ret_vals))
    # return
    
    # Pulse sequence to do a single pulse followed by readout          
    seq_file = 'simple_readout_three_pulse.py'
        
    ################## Load the measuremnt with green laser ##################
      
            
    seq_args = [reionization_time, test_laser_dur,readout_pulse_time, 
                green_laser_key, test_laser_key,yellow_laser_key,  
                green_laser_power ,test_laser_power, yellow_laser_power, 
                apd_index[0]]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    # print(seq_args)
    
    cxn.pulse_streamer.stream_load(seq_file, seq_args_string)

    # Load the APD
    cxn.apd_tagger.start_tag_stream(apd_index)
    # Clear the buffer
    cxn.apd_tagger.clear_buffer()
    # Run the sequence
    cxn.pulse_streamer.stream_immediate(seq_file, num_reps, seq_args_string)

    green_counts = cxn.apd_tagger.read_counter_simple(num_reps)
    
    ################## Load the measuremnt with red laser ##################
    seq_args = [ionization_time, test_laser_dur,readout_pulse_time, 
                red_laser_key, test_laser_key, yellow_laser_key, 
                red_laser_power ,test_laser_power, yellow_laser_power, 
                apd_index[0]]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    cxn.pulse_streamer.stream_load(seq_file, seq_args_string)
    # print(seq_args)
    # Load the APD
    cxn.apd_tagger.start_tag_stream(apd_index)
    # Clear the buffer
    cxn.apd_tagger.clear_buffer()
    # Run the sequence
    cxn.pulse_streamer.stream_immediate(seq_file, num_reps, seq_args_string)

    red_counts = cxn.apd_tagger.read_counter_simple(num_reps)

    
    return green_counts, red_counts

# %%

def sweep_test_pulse_length(nv_sig,  test_pulse_dur_list = None):
    apd_indices = [0]
    num_reps = 250
    if not test_pulse_dur_list:
        test_pulse_dur_list = [0, 25, 50, 75, 100,  150 , 200, 250, 300, 400, 
                                   500, 750, 1000, 1500,
                                   2000]
#        test_pulse_dur_list = [0]
    # measure laser powers:
#    green_optical_power_pd, green_optical_power_mW, \
#            red_optical_power_pd, red_optical_power_mW, \
#            yellow_optical_power_pd, yellow_optical_power_mW = \
#            tool_belt.measure_g_r_y_power( 
#                                  nv_sig['am_589_power'], nv_sig['nd_filter'])
        
    # create some lists for data
    green_count_raw = []
    red_count_raw = []
    
    # Step through the pulse lengths for the test laser
    for test_time in test_pulse_dur_list:
        print('Testing {} us'.format(test_time/10**3))
        nv_sig['test_laser_duration'] = test_time
        green_count, red_count = main(nv_sig, apd_indices, num_reps)
        
        # print(green_count)
        # print(red_count)
        green_count = [int(el) for el in green_count]
        red_count = [int(el) for el in red_count]
        
        green_count_raw.append(green_count)
        red_count_raw.append(red_count)
        
        # fig_hist, ax = plt.subplots(1, 1)
        # max_0 = max(red_count)
        # max_m = max(green_count)
        # occur_0, x_vals_0 = numpy.histogram(red_count, numpy.linspace(0,max_0, max_0+1))
        # occur_m, x_vals_m = numpy.histogram(green_count, numpy.linspace(0,max_m, max_m+1))
        # ax.plot(x_vals_0[:-1],occur_0,  'r-o', label = 'Initial red pulse' )
        # ax.plot(x_vals_m[:-1],occur_m,  'g-o', label = 'Initial green pulse' )
        # ax.set_xlabel('Counts')
        # ax.set_ylabel('Occur.')
        # # ax.set_title('{} ms readout, {}, {} V'.format(t/10**6, nd_filter, p))
        # ax.legend()
            
    green_counts = numpy.average(green_count_raw, axis = 1)
    red_counts = numpy.average(red_count_raw, axis = 1)
    fig, ax = plt.subplots() 
    ax.plot(test_pulse_dur_list, green_counts, 'go')
    ax.plot(test_pulse_dur_list, red_counts, 'ro')
    ax.set_xlabel('Test Pulse Illumination Time (ns)')
    ax.set_ylabel('Counts')
    
    # Save
    test_pulse_dur_list = numpy.array(test_pulse_dur_list)
    timestamp = tool_belt.get_time_stamp()
    raw_data = {'timestamp': timestamp,
            'test_pulse_dur_list': test_pulse_dur_list.tolist(),
            'test_pulse_dur_list-units': 'ns',
            'num_reps':num_reps,
            'nv_sig': nv_sig,
            'nv_sig-units': tool_belt.get_nv_sig_units(),
            'green_count_raw':green_count_raw,
            'green_count_raw-units': 'counts',
            'red_count_raw': red_count_raw,
            'red_count_raw-units': 'counts', 
            'green_count':green_count,
            'green_count-units': 'counts',
            'red_count': red_count,
            'red_count-units': 'counts', 
            }

    file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
    tool_belt.save_raw_data(raw_data, file_path)
    tool_belt.save_figure(fig, file_path)
    
    return

# %% Run the files
    
if __name__ == '__main__':
    sample_name = 'johnson'
    
    green_laser = "cobolt_515"
    yellow_laser = 'laserglow_589'
    red_laser = 'cobolt_638'
    green_power= 10
    red_power= 120
    
    
    nv_sig = {
        "coords": [249.787, 250.073, 5],
        "name": "{}-nv1_2021_11_17".format(sample_name,),
        "disable_opt": False,
        "ramp_voltages": False,
        "expected_count_rate": 55,
            'test_laser': red_laser, 'test_laser_power': red_power, 'test_laser_duration': None,
            'imaging_laser': green_laser, 'imaging_laser_power': green_power, 'imaging_readout_dur': 1E7,
            'nv-_prep_laser': green_laser, 'nv-_prep_laser_power': green_power, 'nv-_prep_laser_dur': 1E3,
            'nv0_prep_laser': red_laser, 'nv0_prep_laser_value': red_power, 'nv0_prep_laser_dur': 1E3,
            'charge_readout_laser': yellow_laser, 'charge_readout_laser_filter': 'nd_1.0', 
            'charge_readout_laser_power': 0.12, 'charge_readout_dur':100e6,
            'collection_filter': '630_lp', 'magnet_angle': None,
            'resonance_LOW': 2.8012, 'rabi_LOW': 141.5, 'uwave_power_LOW': 15.5,  # 15.5 max
            'resonance_HIGH': 2.9445, 'rabi_HIGH': 191.9, 'uwave_power_HIGH': 14.5}   # 14.5 max

    try:
        
        # test_pulses = [0, 50, 100, 500, 1e3, 5e3, 1e4, 5e4, 1e5, 2e5, 3e5, 4e5, 5e5, 6e5, 7e5, 8e5, 9e5,
        #                1e6, ]
        test_pulses = numpy.linspace(0,500, 51)
        sweep_test_pulse_length(nv_sig,  test_pulse_dur_list = test_pulses.tolist())
    finally:
        # Reset our hardware - this should be done in each routine, but
        # let's double check here
        tool_belt.reset_cfm()
        # Kill safe stop
        if tool_belt.check_safe_stop_alive():
            print('\n\nRoutine complete. Press enter to exit.')
            tool_belt.poll_safe_stop()
    
