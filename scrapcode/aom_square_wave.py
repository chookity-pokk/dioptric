# -*- coding: utf-8 -*-
"""Template for scripts that should be run directly from the files themselves
(as opposed to from the control panel, for example).

Created on Sun Jun 16 11:22:40 2019

@author: mccambria
"""


# %% Imports
    

from pulsestreamer import PulseStreamer as Pulser
from pulsestreamer import TriggerStart
from pulsestreamer import OutputState
import numpy
from pulsestreamer import Sequence
import labrad


# %% Constants


LOW = 0
HIGH = 1


# %% Functions


def constant(output_state):
    
    with labrad.connect() as cxn:
        cxn.pulse_streamer.constant([], -0.019, -0.019)


# %% Main


def main():
    """When you run the file, we'll call into main, which should contain the
    body of the script.
    """
    
#    period = numpy.int64(100)
    period = numpy.int64(500)
#    period = numpy.int64(10**9)
    half_period = period // 2
    
    seq = Sequence()

#    train = [(half_period, HIGH), (half_period, HIGH)]
    train = [(half_period, HIGH), (half_period, LOW)]
    seq.setDigital(3, train)
    
    pulser = Pulser('128.104.160.111')
    pulser.constant(OutputState([]))
    pulser.setTrigger(start=TriggerStart.SOFTWARE)
    pulser.stream(seq, -1, OutputState([3]))
    pulser.startNow()
    
    input('Press enter to stop...')
    
    pulser.constant(OutputState([]))


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here

    # Run the script
#    main()
#    constant(OutputState([], 1.0, 1.0))
#    constant(OutputState([], -0.019, 0.0))
    constant(OutputState([], 0.0, 0.0))
