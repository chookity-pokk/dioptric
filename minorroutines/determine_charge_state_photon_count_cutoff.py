#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 15:28:18 2019

@author: yanfeili
"""

# %% import
import utils.tool_belt as tool_belt
import majorroutines.optimize as optimize
import numpy
import os
import time
import matplotlib.pyplot as plt
import labrad
from utils.tool_belt import States

#%% Main

def main_with_cxn(cxn, nv_sig, apd_indices, readout_power,readout_time,ionization_power, 
                  ionization_time,state,num_runs):

    tool_belt.reset_cfm(cxn)
    
# %% Initial Calculation and setup
    apd_indices = [0]
    
    #Assume low state 
    state = States.LOW
    
    shared_params = tool_belt.get_shared_parameters_dict(cxn)
    
    #Define parameters
    #We need high power pump 532 laser to ionize NV to NV-
    polarization_dur = 150 * 10**3
    #exp_dur = 5 * 10**3 #not sure what it is
    #delay of aoms and laser
    aom_delay532 = shared_params['532_aom_delay']
    aom_delay589 = None
    aom_delay638 = None
    #ionization time, typically ~150 ns, just make sure NV is ionized
    Ionization_time = ionization_time
    #not sure necessary
    buffer_time = 100
    #TBD 
    gate_time = 2.5*10**3
    # Analyze the sequence
    file_name = os.path.basename(__file__)
    seq_args = [gate_time, polarization_dur,Ionization_time,buffer_time,aom_delay532,aom_delay589,
                  aom_delay638,readout_time,apd_indices,state]
    seq_args = [int(el) for el in seq_args]
#    print(seq_args)
#    return
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    cxn.pulse_streamer.stream_load(file_name, seq_args_string)

    # Set up our data structure, an array of NaNs that we'll fill
    # incrementally. NaNs are ignored by matplotlib, which is why they're
    # useful for us here.
    # We define 2D arrays, with the horizontal dimension for the frequency and
    # the veritical dimension for the index of the run.
    sig_counts = numpy.empty(num_runs, dtype=numpy.uint32)
    sig_counts[:] = numpy.nan
    ref_counts = numpy.copy(sig_counts)
    # norm_avg_sig = numpy.empty([num_runs, num_steps])
#%% Collect data
    tool_belt.init_safe_stop()

    for run_ind in range(num_runs):

        print('Run index: {}'. format(run_ind))

        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break

        # Optimize
        opti_coords = optimize.main_with_cxn(cxn, nv_sig, apd_indices)
        opti_coords_list.append(opti_coords)
        
        # Load the APD
        cxn.apd_tagger.start_tag_stream(apd_indices)
    
        # Get the counts
        new_counts = cxn.apd_tagger.read_counter_separate_gates(1)

        sample_counts = new_counts[0]

        # signal counts are even - get every second element starting from 0
        sig_gate_counts = sample_counts[0]
        sig_counts[run_ind] = sum(sig_gate_counts)

        # ref counts are odd - sample_counts every second element starting from 1
        ref_gate_counts = sample_counts[1]
        ref_counts[run_ind] = sum(ref_gate_counts)

    cxn.apd_tagger.stop_tag_stream()
#%% Save data 
    timestamp = tool_belt.get_time_stamp()
     
    raw_data = {'timestamp': timestamp,
            'nv_sig': nv_sig,
            'readout_power':readout_power,
            'readout_power_unit':'nW',
            'readout_time':readout_time,
            'readout_time_unit':'ns',
            'ionization_time':Ionization_time,
            'ionization_time_units':'ns',
            'ionization_power':ionization_power,
            'ionization_power_unit':'nW',
            '532_aom_delay':aom_delay532,
            '532_aom_delay_time_unit':'ns',
            'nv_sig-units': tool_belt.get_nv_sig_units(),
            'gate_time': gate_time,
            'gate_time-units': 'ns',
            'num_runs': num_runs,
            'sig_counts': sig_counts.astype(int).tolist(),
            'sig_counts-units': 'counts',
            'ref_counts': ref_counts.astype(int).tolist(),
            'ref_counts-units': 'counts'}

    file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
    tool_belt.save_raw_data(raw_data, file_path)    
#%% Convert photon counts into photon distribution
#The raw data only gives us how many photons are gotten from each run (same tR, same P). 
#Now, we need to convert the raw data to the photon distribution
    def plot_Probability_distribution(aList,colorlabel):
        aList = aList.tolist()
        def get_unique_value(aList):
            unique_value_list = []
            for i in range(0,len(aList)):
                if aList[i] not in unique_value_list:
                    unique_value_list.append(aList[i])
            return unique_value_list
        unique_value = get_unique_value(aList)
        relative_frequency = []
        for i in range(0,len(unique_value)):
            relative_frequency.append(aList.count(unique_value[i])/ (len(aList)))
        fig = plt.plot(unique_value,relative_frequency,'or', color = colorlabel)
        plt.xlabel('number of photons (n)')
        plt.ylabel('P(n)')
        return fig
     
    sig_plot = plot_Probability_distribution(sig_counts,'r')
    ref_plot = plot_Probability_distribution(ref_counts,'b')
    raw_plot = plt.show()
    timestamp = tool_belt.get_time_stamp()
    file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])    
    tool_belt.save_raw_figure(raw_plot, file_path)
    
    
    
    
    
    
    
    
