# -*- coding: utf-8 -*-
"""Template for scripts that should be run directly from the files themselves
(as opposed to from the control panel, for example).

Created on Sun Jun 16 11:22:40 2019

@author: mccambria
"""


# %% Imports


import labrad
import utils.tool_belt as tool_belt


# %% Constants


# %% Functions


# %% Main


def main(nv_sig):
    """When you run the file, we'll call into main, which should contain the
    body of the script.
    """

    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig)
        
def main_with_cxn(cxn, nv_sig):
    
#    freq_center = 2.8202
#    dev = 0.010
    uwave_power = 10.0
    
    tool_belt.reset_cfm(cxn)
    
    res_low = nv_sig['resonance_LOW']
    res_high = nv_sig['resonance_HIGH']
    sig_gen_cxn = cxn.signal_generator_tsg4104a
    sig_gen_cxn.set_freq((res_low + res_high) / 2)
    sig_gen_cxn.set_amp(uwave_power)
    sig_gen_cxn.load_split_freq(res_high - res_low)
    sig_gen_cxn.uwave_on()
    
#    sig_gen_cxn = cxn.signal_generator_tsg4104a
#    sig_gen_cxn.set_freq(freq_center - dev)
#    sig_gen_cxn.set_amp(uwave_power)
#    sig_gen_cxn.uwave_on()
    
#    sig_gen_cxn = cxn.signal_generator_bnc835
#    sig_gen_cxn.set_freq(freq_center + dev)
#    sig_gen_cxn.set_amp(uwave_power)
#    sig_gen_cxn.uwave_on()
    
    cxn.pulse_streamer.constant([4])
    
    input('Press enter to stop...')
    
    cxn.pulse_streamer.constant()
    tool_belt.reset_cfm(cxn)
    

# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here
    sample_name = 'ayrton12'
    nv16_2019_07_25 = {'coords': [-0.191, 0.041, 5.04],
          'name': '{}-nv{}_2019_07_25'.format(sample_name, 16),
          'expected_count_rate': 30,
          'nd_filter': 'nd_1.5', 'pulsed_readout_dur': 450, 'magnet_angle': 194.1,
          'resonance_LOW': 2.8148, 'rabi_LOW': None, 'uwave_power_LOW': 10.0,
          'resonance_HIGH': 2.8242, 'rabi_HIGH': None, 'uwave_power_HIGH': 10.0}

    # Run the script
    main(nv16_2019_07_25)
