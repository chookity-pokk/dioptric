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
    readout, uwave_switch_delay, apd_index = args

    readout = numpy.int64(readout)
    readout = numpy.int64(readout)
    uwave_switch_delay = numpy.int64(uwave_switch_delay)
    clock_pulse = numpy.int64(100)
    clock_buffer = 3 * clock_pulse
    period = readout + clock_pulse + uwave_switch_delay + readout + clock_pulse

    # Get what we need out of the wiring dictionary
    pulser_do_daq_clock = pulser_wiring['do_daq_clock']
    pulser_do_apd_gate = pulser_wiring['do_apd_gate_{}'.format(apd_index)]
    pulser_do_uwave = pulser_wiring['do_uwave_gate_0']
    pulser_do_aom = pulser_wiring['do_aom']

    seq = Sequence()

    # Collect two samples
    train = [(readout + clock_pulse, LOW),
             (clock_pulse, HIGH),
             (clock_pulse, LOW),
             (uwave_switch_delay + readout + clock_pulse, LOW),
             (clock_pulse, HIGH),
             (clock_pulse, LOW)]
    seq.setDigital(pulser_do_daq_clock, train)

    # Ungate the APD channel for the readouts
    train = [(readout, HIGH), (clock_buffer, LOW),
             (uwave_switch_delay, LOW),
             (readout, HIGH), (clock_buffer, LOW)]
    seq.setDigital(pulser_do_apd_gate, train)

    # Uwave should be on for the first measurement and off for the second
    train = [(readout, LOW), (clock_buffer, LOW),
             (uwave_switch_delay, HIGH),
             (readout, HIGH), (clock_buffer, LOW)]
    seq.setDigital(pulser_do_uwave, train)

    # The AOM should always be on
    train = [(period, HIGH)]
    seq.setDigital(pulser_do_aom, train)

    return seq, [period]


if __name__ == '__main__':
    wiring = {'do_daq_clock': 0,
              'do_apd_gate_0': 1,
              'do_aom': 2,
              'do_uwave_gate_0': 3}
    args = [10 * 10**6, 1 * 10**6, 0]
    seq, ret_vals = get_seq(wiring, args)
    seq.plot()
