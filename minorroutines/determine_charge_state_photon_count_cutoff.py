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
from random import shuffle
from scipy.optimize import curve_fit
import labrad
from utils.tool_belt import States

#%% Main

def main_with_cxn(cxn, nv_sig, apd_indices, readout_time, state,
                  num_runs):

    tool_belt.reset_cfm(cxn)
    
# %% Initial Calculation and setup
    apd_indices = [0]
    
    #Assume low state 
    state = States.LOW
    
    shared_params = tool_belt.get_shared_parameters_dict(cxn)
    
    #Define some time
    #We need high power pump 532 laser to ionize NV to NV-
    polarization_dur = 150 * 10**3
    #exp_dur = 5 * 10**3 #not sure what it is
    #delay of aoms and laser
    aom_delay532 = shared_params['532_aom_delay']
    aom_delay589 = None
    aom_delay638 = None
    #ionization time, typically ~150 ns, just make sure NV is ionized
    Ionization_time = 300
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
    
    
    
    
    
    
    
    
    
    
    
