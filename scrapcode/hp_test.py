# -*- coding: utf-8 -*-
"""Template for scripts that should be run directly from the files themselves
(as opposed to from the control panel, for example).

Created on Sun Jun 16 11:22:40 2019

@author: mccambria
"""


# %% Imports 


from pulsestreamer import PulseStreamer as pulser
from pulsestreamer import OutputState
import labrad


# %% Constants


# %% Functions


# %% Main


def main(cxn):
    """When you run the file, we'll call into main, which should contain the
    body of the script.
    """
    
#    cxn.microwave_signal_generator.set_freq(2.88)
#    cxn.microwave_signal_generator.set_amp(9.0)
#    cxn.microwave_signal_generator.uwave_on()
    
    my_pulser = pulser('128.104.160.111')
#    my_pulser.constant(OutputState([1, 4], 0.0, 0.0))  # both
    my_pulser.constant(OutputState([1], 0.0, 0.0))  # hp
#    my_pulser.constant(OutputState([4], 0.0, 0.0))  # tek
#    my_pulser.constant(OutputState([], 0.0, 0.0))  # none
#    
    input('Press enter to stop...')
    
    my_pulser.constant(OutputState([], 0.0, 0.0))
    cxn.microwave_signal_generator.uwave_off()


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here

    # Run the script
    with labrad.connect() as cxn:
        main(cxn)
