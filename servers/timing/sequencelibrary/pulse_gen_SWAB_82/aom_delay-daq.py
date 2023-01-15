# -*- coding: utf-8 -*-
"""
Template for Pulse Streamer sequences. If you don't follow this template,
the pulse_streamer server won't be able to read your sequence.

Determine the delay from lasers by illuminating an NV and sweeping the 
readout pulse over the end of the laser pulse. 

Created on Sun Jun 16 11:22:40 2019

@author: mccambria
"""


# %% Imports


from pulsestreamer import Sequence
from pulsestreamer import OutputState
import numpy
import utils.tool_belt as tool_belt
#from utils.tool_belt import Digital
import logging


# %% Constants


LOW = 0
HIGH = 1


# %% Functions


# %% Sequence definition


def get_seq(pulse_streamer, config, args):
    """This is called by the pulse_streamer server to get the sequence object
    based on the wiring (from the registry) and the args passed by the client.
    """
    
    durations = args[0:3]
    durations = [numpy.int64(el) for el in durations]
    tau, max_tau, readout = durations

    laser_name, laser_power = args[3:5]
    
    pulser_wiring = config['Wiring']['PulseGen']
    do_apd_gate = pulser_wiring['do_apd_gate']
    pulser_do_daq_clock = pulser_wiring['do_sample_clock']
        
    illumination = 10*readout
    half_illumination = illumination // 2
    inter_time = max(10**3, max_tau) + 100
    back_buffer = inter_time
    period = (2 * illumination) + inter_time + back_buffer
    
    seq = Sequence()

    # Keep the signal readout fixed at the back end of the illumination
    # to account for transients and because the laser should lag the readout.
    # Sweep the illumination delay. Place the reference
    # readout squarely in the middle of the illumination so its 
    # independent of the actual delay.
    train = [(half_illumination, LOW),
             (readout, HIGH),
             (half_illumination-readout, LOW),
             (inter_time, LOW),
             (illumination-readout, LOW), 
             (readout, HIGH),
             (back_buffer, LOW),
             ]
    seq.setDigital(do_apd_gate, train)
    
    
    train = [(half_illumination, LOW),
             (readout, LOW),
             (100, HIGH),
             (half_illumination-readout - 100, LOW),
             (inter_time, LOW),
             (illumination-readout, LOW), 
             (readout, LOW),
             (100, HIGH),
             (back_buffer - 100, LOW),
             ]
    seq.setDigital(pulser_do_daq_clock, train)

    train = [(illumination, HIGH), 
             (inter_time-tau, LOW), 
             (illumination, HIGH),
             (back_buffer+tau, LOW),
             ]
    tool_belt.process_laser_seq(pulse_streamer, seq, config, 
                                laser_name, laser_power, train)
    
    final_digital = []
    final = OutputState(final_digital, 0.0, 0.0)
    return seq, final, [period]


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # The whole point of defining sequences in their own files is so that we
    # can run the file to plot the sequence for debugging and analysis. We'll
    # go through that here.

    config = tool_belt.get_config_dict()
    pulser_wiring = config['Wiring']['PulseStreamer']
    print(pulser_wiring)

    # Set up a dummy args list
    args = [0, 200, 1000, 0, 'cobolt_515', None]

    # get_seq returns the sequence and an arbitrary list to pass back to the
    # client. We just want the sequence.
    seq = get_seq(None, config, args)[0]

    # Plot the sequence
    seq.plot()
