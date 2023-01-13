# -*- coding: utf-8 -*-
"""

Sequence for determining the delay beween the rf and the AOM

Created on Sun Aug 6 11:22:40 2019

@author: agardill
"""


# %% Imports


from pulsestreamer import Sequence
from pulsestreamer import OutputState
import numpy
import utils.tool_belt as tool_belt
from utils.tool_belt import States


# %% Constants


LOW = 0
HIGH = 1


# %% Functions


# %% Sequence definition


def get_seq(pulse_streamer, config, args):
    """This is called by the pulse_streamer server to get the sequence object
    based on the wiring (from the registry) and the args passed by the client.
    """
    
    # Extract the delay (that the rf is applied from the start of the seq),
    # the readout time, and the pi pulse duration
    durations = args[0:5]
    durations = [numpy.int64(el) for el in durations]
    tau, max_tau, readout, pi_pulse, polarization = durations
    
    state, apd_index, laser_name, laser_power = args[5:9]
    state = States(state)
    sig_gen = config['Microwaves']['sig_gen_{}'.format(state.name)]
    
    wait_time = config['CommonDurations']['uwave_buffer']
    aom_delay_time = config['Optics'][laser_name]['delay']
    
    pulser_wiring = config['Wiring']['PulseStreamer']
    pulser_do_apd_gate = pulser_wiring['do_apd_{}_gate'.format(apd_index)]
    pulser_do_sig_gen_gate = pulser_wiring['do_{}_gate'.format(sig_gen)]
    pulser_do_daq_clock = pulser_wiring['do_sample_clock']
    
    # Include a buffer on the front end so that we can delay channels that
    # should start off the sequence HIGH
    front_buffer = max(max_tau+pi_pulse, aom_delay_time)
    
    period = front_buffer + polarization + wait_time + polarization + wait_time

    seq = Sequence()
    
    # The readout windows are what everything else is relative to so keep
    # those fixed
    train = [(front_buffer, LOW),
             (readout, HIGH),
             (polarization + wait_time - readout, LOW), 
             (readout, HIGH),
             (polarization + wait_time - readout, LOW),
             ]
    seq.setDigital(pulser_do_apd_gate, train)
    
    #Clock 
    train = [(front_buffer, LOW),
             (readout, LOW),
             (100, HIGH),
             (polarization + wait_time - readout - 100, LOW), 
             (readout, LOW),
             (100, HIGH),
             (polarization + wait_time - readout - 100, LOW),
             ]
    seq.setDigital(pulser_do_daq_clock, train)

    # Laser sequence
    train = [(front_buffer - aom_delay_time, LOW),
             (polarization, HIGH), 
             (wait_time, LOW), 
             (polarization, HIGH),
             (wait_time + aom_delay_time, LOW), 
             ]
    tool_belt.process_laser_seq(pulse_streamer, seq, config, 
                                laser_name, laser_power, train)
    
    # Vary the position of the rf pi pulse
    train = [(front_buffer - pi_pulse - tau, LOW),
             (pi_pulse, HIGH),
             (period - (front_buffer - tau), LOW),
             ]
    train = [(front_buffer + polarization + wait_time - pi_pulse - tau, LOW),
             (pi_pulse, HIGH),
             (polarization + wait_time + tau, LOW),
             ]
    seq.setDigital(pulser_do_sig_gen_gate, train)

    final_digital = []
    final = OutputState(final_digital, 0.0, 0.0)
    return seq, final, [period]


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    config = tool_belt.get_config_dict()
    pulser_wiring = config['Wiring']['PulseStreamer']
    print(pulser_wiring)
    config['Optics']['cobolt_515']['delay'] = 0

    # Set up a dummy args list
    args = [44.0, 200, 350, 50, 100000.0, 1, 0, 'cobolt_515', None]

    # get_seq returns the sequence and an arbitrary list to pass back to the
    # client. We just want the sequence.
    seq = get_seq(None, config, args)[0]

    # Plot the sequence
    seq.plot()
