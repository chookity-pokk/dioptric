# -*- coding: utf-8 -*-
"""
This is a test to create a pulse sequence using analog outputs of the pulse 
streamer

Created on Wed Jun 5 14:49:23 2019

@author: gardill
"""


# %% Imports

import os
import labrad
import numpy
import utils.tool_belt as tool_belt

# %% Main


def main(cxn, aom_on_time, aom_off_time, low_voltage, mid_voltage, high_voltage):

    # %% Initial set up
    
    # Define some times (in ns)
    aom_on_time = int(aom_on_time)
    aom_off_time = int(aom_off_time)        
    
    # %% Run the sequence
    
    file_name = os.path.basename(__file__)    
    args = [aom_on_time, aom_off_time, low_voltage, mid_voltage, high_voltage]
    
    cxn.pulse_streamer.stream_immediate(file_name, 1 * 10**8, args, 1)
#    cxn.pulse_streamer.stream_immediate(file_name, 3, args, 1)
    
def on_589(cxn):
    cxn.pulse_streamer.constant(5)
    
def on_638(cxn):
    cxn.pulse_streamer.constant(4)
    
def off(cxn):
    cxn.pulse_streamer.constant(1)
    

    
    
    # %%
    
    # %%
    
if __name__ == '__main__':
    try:
        
        with labrad.connect() as cxn:
            main(cxn, 500, 500, 0, 0, 1)
            
            
#            on_589(cxn)
            
#            on_638(cxn)
            
#            off(cxn)
        
    finally:
        # Kill safe stop
        if tool_belt.check_safe_stop_alive():
            print("\n\nRoutine complete. Press enter to exit.")
            tool_belt.poll_safe_stop()
    
            
