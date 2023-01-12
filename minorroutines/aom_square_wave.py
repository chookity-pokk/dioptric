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
import utils.tool_belt as tool_belt
import time


# %% Constants


LOW = 0
HIGH = 1


# %% Functions


def constant(cxn, laser_names, laser_powers=None):
    
    # seq_file = 'square_wave.py'
    # period = int(1000)
    # # period = int(0.25e6)
    # # period = int(2000)
    # seq_args = [period, laser_name, laser_power]
    # seq_args_string = tool_belt.encode_seq_args(seq_args)

    # cxn.pulse_streamer.stream_immediate(seq_file, -1, seq_args_string)

    # tool_belt.laser_off(cxn, laser_name)
    
    num_lasers = len(laser_names)
    
    if laser_powers is None:
        laser_powers = [None] * num_lasers

    for ind in range(num_lasers):
        laser_name = laser_names[ind]
        laser_power = laser_powers[ind]
        tool_belt.laser_on(cxn, laser_name, laser_power)
        
    # cxn.pulse_streamer.constant([3], 1.0)
    # cxn.pulse_streamer.constant([], 1.0)

    input('Press enter to stop...')

    cxn.pulse_streamer.constant()
    for laser_name in laser_names:
        tool_belt.laser_off(cxn, laser_name)


# %% Main


def main(cxn, laser_name, laser_power=None):
    """Run a laser on on a square wave."""
    
    seq_file = 'square_wave.py'
    period = int(20000)
    # period = int(0.25e6)
    # period = int(10000)
    seq_args = [period, laser_name, laser_power]
    
    # seq_file = 'SCC_optimize_pulses_w_uwaves.py'
    # seq_args = [58000.0, 1000.0, 125, 68, 150, 68, 'laserglow_532', 'laserglow_589', 'cobolt_638', 'signal_generator_sg394', 1, 0.68, 0.9]
    
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    cxn.pulse_streamer.stream_immediate(seq_file, -1, seq_args_string)

    input('Press enter to stop...')

    cxn.pulse_streamer.constant()
    tool_belt.laser_off(cxn, laser_name)


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here

    # Rabi
    
    
    # laser_name = 'cobolt_515'
    # laser_name = 'cobolt_638'
    # filter_name = 'nd_0.5'
    # pos = [-0.025, -0.009, 4.89]

    # Hahn
    laser_names = ['cobolt_515']
    # laser_names = ['laserglow_589']
    # laser_names = ['laserglow_532']
    # laser_names = ['cobolt_638', 'laserglow_532']
    # laser_names = ['laserglow_532', 'laserglow_589']
    # laser_powers = [None, 1.0]
    # laser_powers = [1.0]
    # laser_names = ['laserglow_589', 'cobolt_638', 'laserglow_532']
    # filter_name = 'nd_0.5'
    # pos = [0.0, 0.0, 5]
    # laser_powers = None

    with labrad.connect() as cxn:
        # start = time.time()
        # tool_belt.set_filter(cxn, optics_name='laserglow_532', filter_name=filter_name)
        # finish = time.time()
        # print(finish - start)
        # tool_belt.set_xyz(cxn, pos)
#        for el in laser_names:
        # tool_belt.set_filter(cxn, optics_name=laser_name, filter_name=filter_name)
        # tool_belt.set_filter(cxn, optics_name='laserglow_532', filter_name="nd_0.5")
        # tool_belt.set_filter(cxn, optics_name='collection', filter_name='630_lp')
        # constant(cxn, laser_names, laser_powers)
        main(cxn, laser_names[0])
    
        
    
        # cxn.pulse_streamer.constant([3], 1.0)
        # cxn.pulse_streamer.constant([], 1.0)
        # cxn.pulse_streamer.constant([4])
    
        input('Press enter to stop...')
        
        # cxn.pulse_streamer.constant()
