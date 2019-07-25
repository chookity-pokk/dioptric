# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import utils.tool_belt as tool_belt
import matplotlib.pyplot as plt
import numpy

data = tool_belt.get_raw_data('ramsey', '2019-07-12_16-32-47_johnson1', 'branch_ramsey2')
# data = tool_belt.get_raw_data('ramsey', '2019-07-12_18-29-39_johnson1', 'branch_ramsey2')
# data = tool_belt.get_raw_data('rabi', '2019-07-12_18-10-13_johnson1')
# data = tool_belt.get_raw_data('t1_double_quantum', '2019-07-14_16-56-45_johnson1')
# data = tool_belt.get_raw_data('pulsed_resonance', '2019-07-12_17-59-35_johnson1')

ref_counts = data['ref_counts']
ref_counts_list = ref_counts[0]
for run_ind in range(data['num_runs'] - 1):
    ref_counts_list.extend(ref_counts[run_ind + 1])
# ref_counts_list.sort()

hist = numpy.histogram(ref_counts_list, 10)

# plt.plot(ref_counts_list)
plt.plot(hist[1][0:-1], hist[0])
