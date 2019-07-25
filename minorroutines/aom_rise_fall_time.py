# -*- coding: utf-8 -*-
"""
Will allow tests of rise/fall time of AOM. The rise/fall time can be seen
on an oscilloscope connected to a photodiode.

We first want to test the rise/fall time of the AOM driver. test_aom determines
if the AOM driver will be used to d othe switching or a switch

Must inlcude low and high voltage if working with the analog AOM drivers. Also
specify if analog AOM will be used.

Created on Mon Jun 3 11:49:23 2019

@author: gardill
"""


# %% Imports

import os
import labrad
import utils.tool_belt as tool_belt

# %% Main


def main(cxn, aom_name, aom_on_time, aom_off_time, voltage_tuple):

    # %% Initial set up
    
    if (aom_name == '532_aom') or (aom_name == '589_aom')  \
        or (aom_name == '638_aom'):
        
        if aom_name == '532_aom':
            aom_state = 0
            
        if aom_name == '589_aom':
            aom_state = 1
            
        if aom_name == '638_aom':
            aom_state = 2
            
        # Extract the voltages
        low_voltage, high_voltage = voltage_tuple
        
        # Define some times (in ns)
        aom_on_time = int(aom_on_time)
        aom_off_time = int(aom_off_time)        
        
        # Run the sequence
        file_name = os.path.basename(__file__)    
        args = [aom_state, aom_on_time, aom_off_time, 
                low_voltage, high_voltage]
        
#        cxn.pulse_streamer.stream_immediate(file_name, 1 * 10**8, args, 1)
        cxn.pulse_streamer.stream_immediate(file_name, 3, args, 1)
        
    else:
        print('AOM name not accepted, please use one of the given names:' \
            '\n532_aom \n589_aom \n638_aom')
    
    # %%
    
    # AOM names:
    # 532aom
    # 589aom
    # 638aom
    
if __name__ == '__main__':
    try:
        
        with labrad.connect() as cxn:
            main(cxn, '638_aom', 10**9, 10**9, (0, 1))
        
    finally:
        # Kill safe stop
        if tool_belt.check_safe_stop_alive():
            print("\n\nRoutine complete. Press enter to exit.")
            tool_belt.poll_safe_stop()
            
