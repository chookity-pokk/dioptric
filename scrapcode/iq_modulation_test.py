# -*- coding: utf-8 -*-
"""IQ modulation test script

Created on Wed Jun 19 10:27:36 2019

@author: mccambria
"""

# %% Imports


import labrad
import os
import utils.tool_belt as tool_belt


# %% Constants


# %% Functions


# %% Main


def main(cxn):

    # Set up the microwave signal generator
    cxn.signal_generator_tsg4104a.set_freq(0.400)  # 400 MHz
    cxn.signal_generator_tsg4104a.set_amp(2.0)  # 2.0 dBm
    cxn.signal_generator_tsg4104a.load_iq_mod()
    cxn.signal_generator_tsg4104a.uwave_on()

    # Load the arbitrary waveform
    cxn.arbitrary_waveform_generator.load_iq_waveform(16 * [0.5, 0.0],
                                                      16 * [0.0, 0.5])
#    cxn.arbitrary_waveform_generator.load_iq_waveform(16 * [0.5, 0.0],
#                                                      16 * [0.0, 0.5])
#    cxn.arbitrary_waveform_generator.load_iq_waveform(16 * [0.5, 0.0],
#                                                      16 * [0.0, 0.0])
#    cxn.arbitrary_waveform_generator.load_iq_waveform([0.5] + 31*[0.0],
#                                                      16 * [0.0, 0.0])
#    cxn.arbitrary_waveform_generator.load_iq_waveform(32*[0.5],
#                                                      32*[0.0])
    
    # Set up the arbitrary waveform triggers
    file_name = os.path.basename(__file__)
    # Square wave periods in ns
#    period = 10**9  # 1Hz
#    period = 100  # 10 MHz
    period = 10  # 100 MHz
    seq_args = [period]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    cxn.pulse_streamer.stream_load(file_name, seq_args_string)
    cxn.pulse_streamer.stream_start(-1)
    
    input('Press enter to stop...')
    
    cxn.arbitrary_waveform_generator.reset()
    cxn.signal_generator_tsg4104a.reset()
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

