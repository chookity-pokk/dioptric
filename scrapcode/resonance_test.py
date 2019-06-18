#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 11:26:41 2019

@author: yanfeili
"""


import numpy
from pulsestreamer import OutputState
from pulsestreamer import PulseStreamer as Pulser 
#import matplotlib.pyplot as plt
import labrad
#import nidaqmx
#import nidaqmx.stream_writers as stream_writers

    
actural_freqs = [2.85, 2.852, 2.854, 2.856, 2.858, 
                  2.86, 2.862, 2.864, 2.866, 2.868, 2.87, 2.872, 2.874, 
                  2.876, 2.878, 2.88, 2.882, 2.884, 2.886, 2.888, 2.89]


num_steps = 21 
freq_center = 2.87  # GHz
fm_dev = 0.034  # GHz
uwave_power = 5.0  # dBm
freq_range = 0.4
freq_deviation = freq_range/2

freq_low = freq_center - freq_deviation
freq_high = freq_center + freq_deviation

#divide the frequencies range into intervals so that each interval can be covered 
#by the fm deviation
#in order to make sure that the whole frequency range has been included 
freq_list = numpy.linspace(freq_low, freq_high, int(freq_deviation//fm_dev)+2).tolist()   

#%%
#this function returns a list of lists which each represents the interval that fm can cover
#example: divide a frequency range over 2.67 to 3.07 and fm_range is 0.034*2
#input:[2.67, 2.7366666666666664, 2.8033333333333332, 2.87, 2.9366666666666665, 
#3.003333333333333, 3.07]
#output: [[2.67, 2.7366666666666664], [2.8033333333333332, 2.87], [2.9366666666666665, 
#3.003333333333333], [3.07]]
def get_freq_subgroups(freq_list,fm_range):

    #the master list of intervals we want to get 
    freq_subgroups = []
    
    #loop over the freq_list except the last element
    ind = 0
    while ind < len(freq_list)-1:
        
    #set the freq_interval to be a list containing the first frequency in an interval
        freq_interval = [freq_list[ind]]
        
        #if the next frequency is within fm_deviation, go look at the rest frequencies
        if freq_list[ind+1] - freq_list[ind] <= fm_range:                     
        #add all the frequencies that are within the fm_deviation into the interval list    
            for ind2 in range(ind+1,len(freq_list)):
                if freq_list[ind2]-freq_list[ind] <= fm_range:
                    freq_interval.append(freq_list[ind2])
                else:                    
                    break                    
        #once the fm_deviation is passed, an interval is completed and append this interval to the master list    
            freq_subgroups.append(freq_interval)
            ind += len(freq_interval) #the loop will continue with next frequency after this interval            
        
        #jf the next frequency is not within fm_deviation, add to the master list as an one-element list
        elif freq_list[ind+1] - freq_list[ind] > fm_range:
            freq_subgroups.append(freq_interval)
            ind+=1 #go look at the next frequency if there is any        
    
    #if the last frequency has not been included, add it to the master list as an one-element list 
    if ind == len(freq_list)-1:
        freq_subgroups.append([freq_list[-1]])     
    
    return freq_subgroups

#%%
#ao_voltages = numpy.linspace(-1.0, +1.0, num_steps).tolist()

#print(ao_voltages)

# make a plot of the expected frequencies vs. the actural frequences we get 
#plt.plot(ao_voltages,actural_freqs,color = 'red')
#plt.plot(ao_voltages,expected_freqs,color = 'blue')
#plt.axis([-1,1,2.68,3.08])
#plt.text(-0.75,3.00,'red = actural freqs, blue = expected freqs')
#plt.xlabel('voltages/V')
#plt.ylabel('actural frequencies/MHZ')
#plt.show()
#pulser = Pulser('128.104.160.11')

#with labrad.connect() as cxn:
#    cxn.microwave_signal_generator.set_amp(uwave_power)
#    cxn.microwave_signal_generator.load_fm(fm_dev)
#    cxn.microwave_signal_generator.uwave_on()
    
#    for step_ind in range(num_steps):
#        cxn.microwave_signal_generator.set_freq(expected_freqs[step_ind])
#        state = OutputState([4], ao_voltages[step_ind], 0.0)
#        pulser.constant(state)
#        if input('Enter nothing to continue or "q" to quit: ') == 'q':
#            break
    #iterate over a list of subintervals that cover the fm_dev 
#    freq_sublist = get_subgroups(freq_list,fm_dev*2)
#    for ind_sublist in range(len(freq_sublist)):
#        if len(freq_sublist[ind_sublist]) == 1:
#            freq_subcenter = freq_sublist[ind_sublist][0]
#            cxn.microwave_signal_generator.set_freq(freq_subcenter)
#        else:
#            freq_subcenter = (freq_sublist[ind_sublist][-1]-freq_sublist[ind_sublist][0])/2
#            for step_ind in freq_sublist[ind_sublist]:
#                cxn.microwave_signal_generator.set_freq(freq_subcenter)
#                ao_voltages = numpy.linspace(-1.0, +1.0, len(freq_sublist[ind_sublist])).tolist()
#                state = OutputState([4], ao_voltages[step_ind], 0.0)
#                pulser.constant(state)
#                if input('Enter nothing to continue or "q" to quit: ') == 'q':
#                    break
                
        
            
            
#    cxn.microwave_signal_generator.mod_off()
#    cxn.microwave_signal_generator.uwave_off()
#    state = OutputState([], 0.0, 0.0)
#    pulser.constant(state)

#%%
#turn the microwave on and  set up the pulse streamer
with labrad.connect() as cxn:
    cxn.microwave_signal_generator.set_amp(uwave_power)
    cxn.microwave_signal_generator.load_fm(fm_dev)
    cxn.microwave_signal_generator.uwave_on()
pulser = Pulser('128.104.160.11')

#Loop over each interval in the freq_subgroups
#set +1,-1 corresponding to the max and min frequencies in each interval
freq_sublist = get_freq_subgroups(freq_list,fm_dev*2)
print(freq_sublist)

for ind_sublist in range(len(freq_sublist)):
    
    #set the center frequency to be the mean value of frequencies in an interval
    freq_subcenter = (freq_sublist[ind_sublist][-1]-freq_sublist[ind_sublist][0])/2
    
    #match the voltages to the frequencies
    ao_voltages = numpy.linspace(-1.0, +1.0, len(freq_sublist[ind_sublist])).tolist()
    
    #load the voltages into the microwave signal generater
    cxn.microwave_signal_generator.set_freq(freq_subcenter)
    state = OutputState([4], ao_voltages[ind_sublist], 0.0)
    pulser.constant(state)
    if input('Enter nothing to continue or "q" to quit: ') == 'q':
        break    
    
#turn off the microwave signal generator
cxn.microwave_signal_generator.mod_off()
cxn.microwave_signal_generator.uwave_off()
state = OutputState([], 0.0, 0.0)
pulser.constant(state)
    
    
    
    
    
    
    
    
    
    