# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 12:04:28 2019

@author: kolkowitz
"""

freqs = numpy.linspace(freq_low, freq_high, num_steps)
    
def get_freq_subgroups(freqs, fm_range):
    
    # subgroups will be a list of lists. Each list contains a set of
    # frequencies we wish to probe that differ by no more than fm_range.
    subgroups = []
    
    # Bit of setup
    outer_ind = 0
    len_freqs = len(freqs)
    
    # Loop until we break
    while True:
        
        # Include the starting frequency in the subgroup
        subgroup_low = freqs[outer_ind]
        subgroup = [subgroup_low]
        
        # If there are subsequent frequencies, loop through them
        # until we pass fm_range
        if outer_ind < len_freqs - 1:
            for inner_ind in range(outer_ind + 1, len_freqs):
                freq = freqs[inner_ind]
                if freqs[inner_ind] - subgroup_low <= fm_range:
                    subgroup.append(freq)
                else:
                    # Done with this subgroup
                    break
        
        subgroups.append(subgroup)
            
        outer_ind += len(subgroup)
            
        # If we just passed through the end of freqs, then we're all done
        if outer_ind == len_freqs - 1:
            break
        