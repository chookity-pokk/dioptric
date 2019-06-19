# -*- coding: utf-8 -*-
"""IQ modulation test script

Created on Wed Jun 19 10:27:36 2019

@author: mccambria
"""

# %% Imports


import labrad
import os


# %% Constants


# %% Functions


# %% Main


def main(cxn):

    
    # Set up the microwave signal generator
#    cxn.microwave_signal_generator.set_freq(2.00)
#    cxn.microwave_signal_generator.set_amp(0.0)
#    cxn.microwave_signal_generator.load_iq_mod()
#    cxn.microwave_signal_generator.uwave_on()
#    
    # Load the arbitrary waveform
    cxn.arbitrary_waveform_generator.load_iq_waveform(16 * [1.0, 0.0],
                                                      16 * [0.0, 1.0])
    
    # Set up the arbitrary waveform triggers
    file_name = os.path.basename(__file__)
#    period = 10000  # square wave period in ns
    period = 10**9  # square wave period in ns
    cxn.pulse_streamer.stream_load(file_name, [period], 0)
    cxn.pulse_streamer.stream_start(-1)
    
    input('Press enter to stop...')
    
    cxn.arbitrary_waveform_generator.wave_off()
    cxn.pulse_streamer.force_final()
    


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here

    # Run the script
    with labrad.connect() as cxn:
        main(cxn)

