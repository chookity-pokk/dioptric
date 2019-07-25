# -*- coding: utf-8 -*-
"""
Created on Wed Jun 5 14:49:23 2019

@author: gardill
"""

from pulsestreamer import Sequence
from pulsestreamer import OutputState
import numpy

def get_seq(pulser_wiring, args):

    # %% Parse wiring and args

    # The first 9 args are ns durations and we need them as int64s
    durations = []
    for ind in range(2):
        durations.append(numpy.int64(args[ind]))

    # Unpack the durations
    aom_on_time, aom_off_time = durations
    
    period = aom_on_time + aom_off_time
    
#    LOW = args[2]
#    MID = args[3]
#    HIGH = args[4]
    
    LOW = 0.0
    MID = 0.2
    HIGH = 0.2
    
#    LOW = -0.019
#    LOW = 0.0
#    MID = LOW
#    HIGH = LOW

    pulser_ao = 0
        
    seq = Sequence()

#    train = [(aom_on_time, HIGH), (aom_off_time, LOW), (aom_on_time, MID), (aom_off_time, LOW)]
#    seq.setAnalog(pulser_ao, train)
    
    train = [(aom_on_time, HIGH), (aom_off_time, LOW)]
    seq.setAnalog(pulser_ao, train)
    
#    train = [(period, LOW)]
#    seq.setAnalog(pulser_ao, train)
    

    return seq, OutputState(pulser_wiring['do_532_aom'], 0.0, 0.0), [period]

    # %% Define the sequence


if __name__ == '__main__':
    wiring = {'pulser_ao': 0}
    args = [100, 100, 0, 0.5, 1.0]
    seq, _, _ = get_seq(wiring, args)[0]
    seq.plot()   
