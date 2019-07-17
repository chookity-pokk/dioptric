# -*- coding: utf-8 -*-
"""
Created on Wed Jun 5 14:49:23 2019

@author: gardill
"""

from pulsestreamer import Sequence
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
    
    LOW = args[2]
    HIGH = args[3]

    pulser_ao = pulser_wiring['ao_638_aom']
        
    seq = Sequence()

    train = [(aom_on_time, HIGH), (aom_on_time, LOW)]
    seq.setAnalog(pulser_ao, train)
    

    return seq, [period]

    # %% Define the sequence




if __name__ == '__main__':
    wiring = {'pulser_ao': 0}
    args = [100, 100, 0, 0.5]
    seq = get_seq(wiring, args)
    seq.plot()   
