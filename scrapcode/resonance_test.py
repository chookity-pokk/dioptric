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
import nidaqmx
import nidaqmx.stream_writers as stream_writers

    
actural_freqs = [2.85, 2.852, 2.854, 2.856, 2.858, 
                  2.86, 2.862, 2.864, 2.866, 2.868, 2.87, 2.872, 2.874, 
                  2.876, 2.878, 2.88, 2.882, 2.884, 2.886, 2.888, 2.89]


num_steps = 21 
freq_center = 2.87  # GHz
fm_dev = 0.034  # GHz
uwave_power = 5.0  # dBm
freq_range = 0.2

freq_low = freq_center - freq_range
freq_high = freq_center + freq_range
#divide the frequencies range into subintervals so that each interval can be covered 
#by the fm deviation
freq_list = numpy.linspace(freq_low, freq_high, int(freq_range//fm_dev)+2).tolist()   

def get_subgroups(Alist,length_step):
    result = []
    ind = 0
    while ind < len(Alist)-1:
        sub_interval = [Alist[ind]]
        if Alist[ind+1] - Alist[ind] > length_step:
            result.append(sub_interval)
            ind+=1
        elif Alist[ind+1] - Alist[ind] <= length_step:                     
            for ind2 in range(ind+1,len(Alist)):
                if Alist[ind2]-Alist[ind] <= length_step:
                    sub_interval.append(Alist[ind2])
                else:                    
                    break                    
            result.append(sub_interval)
            ind += len(sub_interval)                
        else:
            ind+=1
    if ind == len(Alist)-1:
        result.append([Alist[len(Alist)-1]])     
    return result

print(freq_list)

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
def stopServer(self):
    self.close_task_internal()

def close_task_internal(self, task_handle=None, status=None,                            
        callback_data=None):
        task = self.task
        if task is not None:
            task.close()
            self.task = None
        return 0
    
def write(self,ao_voltages):
    "Write the specified voltages to the output channels"
    #Close previous task 
    if self.task is not None:
        self.close_task_internal()
    with nidaqmx.Task() as task: 
        #Set up the output channel 
        task.ao_channels.add_ao_voltage_chan(self.ao_voltages,min_val = -1.0, max_val = +1.0)
        task.write(ao_voltages)


def load_stream_writer(self,voltages):
    
    #Close the existing task 
    if self.task is not None:
        self.close_task_internal()
    
    #Write the initial voltages and stream the rest
#    num_voltage = len(ao_voltages) #why do we need this? 
    self.write(voltages)
    stream_voltages = ao_voltages
    
    #Create a new task
#    task = nidaqmx.Task(task_name)
#    self.task = task
#    
    #Set up the output stream (set the output signal that is readable by the DAQ?)
    out_stream = nidaqmx.task.OutStream(task) #this is a "Outsream" class object 
    writer = stream_writrs.AnalogMultiChannelWriter(output_stream) #this is now a stream_writer class object
    
    writer.write_many_sample(stream_voltages)

    
#%%
#iterate over a list of subintervals that cover the fm_dev 
freq_sublist = get_subgroups(freq_list,fm_dev*2)
for ind_sublist in range(len(freq_sublist)):
#    if len(freq_sublist) %2 != 0: # for odd size sublist
        freq_subcenter = (freq_sublist[ind_sublist][-1]-freq_sublist[ind_sublist][0])/2
#        load_stream_writer(freq_sub,)
        ao_voltages = numpy.linspace(-1.0, +1.0, len(freq_sublist[ind_sublist])).tolist()
        load_stream_writer(ao_voltages)
        if input('Enter nothing to continue or "q" to quit: ') == 'q':
            break
    
    
    
    
    
    
    
    
    
    
    
    
    
    