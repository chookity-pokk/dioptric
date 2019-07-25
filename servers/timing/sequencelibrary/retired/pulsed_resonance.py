# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 16:19:44 2019

@author: mccambria
"""

from pulsestreamer import Sequence
import numpy

LOW = 0
HIGH = 1


def get_seq(pulser_wiring, args):
    
    # Unpack the args
    durations = args[0:2]
    durations = [numpy.int64(el) for el in durations]
    readout_dur, uwave_switch_delay_dur, pi_pulse_dur = durations
    apd_index = args[2]
    
    clock_pulse_dur = numpy.int64(100)
    clock_buffer = 3 * clock_pulse
    period = readout_dur + clock_pulse_dur + uwave_switch_delay_dur + readout_dur + clock_pulse_dur

    # Get what we need out of the wiring dictionary
    pulser_do_daq_clock = pulser_wiring['do_daq_clock']
    pulser_do_apd_gate = pulser_wiring['do_apd_gate_{}'.format(apd_index)]
    pulser_do_uwave = pulser_wiring['do_uwave_gate_0']
    pulser_do_aom = pulser_wiring['do_aom']

    seq = Sequence()

    # Collect two samples
    train = [(readout_dur + clock_pulse, LOW),
             (clock_pulse, HIGH),
             (clock_pulse, LOW),
             (uwave_switch_delay_dur + readout_dur + clock_pulse, LOW),
             (clock_pulse, HIGH),
             (clock_pulse, LOW)]
    seq.setDigital(pulser_do_daq_clock, train)
    
    # Ungate the APD channel for the readout_durs
    train = [(readout_dur, HIGH), (clock_buffer, LOW),
             (uwave_switch_delay_dur, LOW),
             (readout_dur, HIGH), (clock_buffer, LOW)]
    seq.setDigital(pulser_do_apd_gate, train)

    # Uwave should be on for the first measurement and off for the second
    train = [(readout_dur, LOW), (clock_buffer, LOW),
             (uwave_switch_delay_dur, HIGH),
             (readout_dur, HIGH), (clock_buffer, LOW)]
    seq.setDigital(pulser_do_uwave, train)

    # The AOM should always be on
    train = [(period, HIGH)]
    seq.setDigital(pulser_do_aom, train)
    
    step_time = 1 * 10**6
    train = [(step_time, -1.0),
             (step_time, -0.75),
             (step_time, -0.5),
             (step_time, -0.25),
             (step_time, 0.0),
             (step_time, 0.25),
             (step_time, 0.5),
             (step_time, 0.75),
             (step_time, 1.0),
             (step_time, 0.0)]
    
    seq.setAnalog(0, train)

    return seq, [period]


if __name__ == '__main__':
    wiring = {'do_daq_clock': 0,
              'do_apd_gate_0': 1,
              'do_aom': 2,
              'do_uwave_gate_0': 3}
    args = [10 * 10**6, 1 * 10**6, 0]
    seq, ret_vals = get_seq(wiring, args)
    seq.plot()
