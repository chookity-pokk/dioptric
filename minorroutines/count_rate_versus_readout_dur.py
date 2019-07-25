# -*- coding: utf-8 -*-
"""See how our reported count rates are affected by changing the duration of
the readout window.

Created on Sun Jun 16 11:22:40 2019

@author: mccambria
"""

# %% Imports

import labrad
import utils.tool_belt as tool_belt
import numpy
import majorroutines.optimize as optimize
import os
import matplotlib.pyplot as plt

# %% Main

def main(cxn, name, nv_sig, nd_filter, apd_indices, readout_dur_range, num_steps, num_reps):
    """When you run the file, we'll call into main, which should contain the
    body of the script.
    """
    
    polarization_dur = 3 * 10**3
    reference_wait_dur = 2 * 10**3
    aom_delay = 1000
    
    file_name = os.path.basename(__file__)
    
    taus = numpy.linspace(readout_dur_range[0], readout_dur_range[1],
                          num=num_steps, dtype=numpy.int32)

    counts = numpy.empty(num_steps, dtype=numpy.uint32)
    counts[:] = numpy.nan
    count_rates = numpy.zeros(num_steps)
    
    tool_belt.init_safe_stop()
    
    tool_belt.reset_cfm(cxn)
    
    optimize.main(cxn, nv_sig, nd_filter, apd_indices)

    # Load the APD
    cxn.apd_tagger.start_tag_stream(apd_indices)
    
    for tau_ind in range(num_steps):

        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break
        
        tau = taus[tau_ind]

        # Stream the sequence
        args = [polarization_dur, reference_wait_dur,
                tau, aom_delay, apd_indices[0]]
        # Scale the number of reps so that we collect for a roughly
        # static duration
        scaled_num_reps = int(num_reps * (readout_dur_range[0] / tau))
        if scaled_num_reps == 0:
            scaled_num_reps = 1
        cxn.pulse_streamer.stream_immediate(file_name, scaled_num_reps, args, 1)

        # Get the counts
        new_counts = cxn.apd_tagger.read_counter_simple(1)[0]
        counts[tau_ind] = new_counts
        count_rates[tau_ind] = (new_counts / (1000 * scaled_num_reps)) / (tau * 10**-9)
        
    cxn.apd_tagger.stop_tag_stream()
    
    tool_belt.reset_cfm(cxn)
    
    fig, ax = plt.subplots(1, 1, figsize=(8.5, 8.5))
    ax.plot(taus, count_rates)
    ax.set_title('Count Rate Versus Readout Duration')
    ax.set_xlabel('Readout duration (ns)')
    ax.set_ylabel('Count rate (kcps)')
    fig.canvas.draw()
    fig.set_tight_layout(True)
    fig.canvas.flush_events()
    
    timestamp = tool_belt.get_time_stamp()

    raw_data = {'timestamp': timestamp,
                'name': name,
                'nv_sig': nv_sig,
                'nv_sig-units': tool_belt.get_nv_sig_units(),
                'nv_sig-format': tool_belt.get_nv_sig_format(),
                'nd_filter': nd_filter,
                'num_steps': num_steps,
                'num_reps': num_reps,
                'readout_dur_range': readout_dur_range,
                'readout_dur_range-units': 'ns',
                'counts': counts.astype(int).tolist(),
                'counts-units': 'counts',
                'count_rates': count_rates.astype(float).tolist(),
                'count_rates-units': 'kcps'}

    file_path = tool_belt.get_file_path(__file__, timestamp, name)
    tool_belt.save_figure(fig, file_path)
    tool_belt.save_raw_data(raw_data, file_path)

# %% Run the file

# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here
    readout_dur_range = [320, 5000]
    num_reps = 10**6  # This will be scaled - see scaled_num_reps
    num_steps = 101
    nd_filter = 0.5
    apd_indices = [0]
    name = 'johnson1'
    nv_sig = [-0.169, -0.306, 38.74, 40, 2]

    # Run the script
    with labrad.connect() as cxn:
        main(cxn, name, nv_sig, nd_filter, apd_indices, readout_dur_range, num_steps, num_reps)
