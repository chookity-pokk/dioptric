# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 14:09:39 2021

@author: samli
"""

# import labrad
import scipy.stats
import scipy.special
import numpy
import math  
import copy
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import random
import photonstatistics as model
import labrad

import utils.tool_belt as tool_belt
import majorroutines.optimize_digital as optimize

#%% import your data in the data_file 
import NV_data as data
#%% functions 

#fit the NV- and NV0 counts to the rate model 
def get_photon_dis_curve_fit_plot(readout_time,NV0,NVm, do_plot = True): # NV0, NVm in array
    trail_nv0_30ms = numpy.array(NV0)
    trail_nvm_30ms = numpy.array(NVm)
    tR = readout_time 
    combined_count = trail_nvm_30ms.tolist() + trail_nv0_30ms.tolist()
    random.shuffle(combined_count)
    # fit = [g0,g1,y1,y0]
    
    # if it is the SiV sample, use this guess 
    # guess = [ 0.01 ,0.02, 0.57, 0.08] 
    
    # if it is the E6 sample, use this guess 
    guess = [ 10*10**-4,100*10**-4, 1000*10**-4, 500*10**-4]
    # fit gives g0, g1, y1, y0
    fit,dev = model.get_curve_fit(tR,0,combined_count,guess)
#    print(fit,np.diag(dev))
    
    if do_plot:
        u_value0, freq0 = model.get_Probability_distribution(trail_nv0_30ms.tolist())
        u_valuem, freqm = model.get_Probability_distribution(trail_nvm_30ms.tolist())
        u_value2, freq2 = model.get_Probability_distribution(combined_count)
        curve = model.get_photon_distribution_curve(tR,u_value2, fit[0] ,fit[1], fit[2] ,fit[3])
        
        A1, A1pcov = model.get_curve_fit_to_weight(tR,0,trail_nv0_30ms.tolist(),[0.5],fit)
        A2, A2pcov = model.get_curve_fit_to_weight(tR,0,trail_nvm_30ms.tolist(),[0.5],fit)
    
        nv0_curve = model.get_photon_distribution_curve_weight(u_value0,tR, fit[0] ,fit[1], fit[2] ,fit[3],A1[0])    
        nvm_curve = model.get_photon_distribution_curve_weight(u_valuem,tR, fit[0] ,fit[1], fit[2] ,fit[3],A2[0])
        fig4, ax = plt.subplots()
        ax.plot(u_value0,0.5*np.array(freq0),"-ro")
        ax.plot(u_valuem,0.5*np.array(freqm),"-go")
        ax.plot(u_value2,freq2,"-bo")
        ax.plot(u_value2,curve)
        ax.plot(u_valuem,0.5*np.array(nvm_curve),"green")
        ax.plot(u_value0,0.5*np.array(nv0_curve),"red")
        textstr = '\n'.join((
        r'$g_0(s^{-1}) =%.2f$'% (fit[0]*10**3, ),
        r'$g_1(s^{-1})  =%.2f$'% (fit[1]*10**3, ),
        r'$y_0 =%.2f$'% (fit[3], ),
        r'$y_1 =%.2f$'% (fit[2], )))
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.6, 0.95, textstr, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)
        plt.xlabel("Number of counts")
        plt.ylabel("Probability Density")
        plt.show()
    return fit 

# calculate the threshold of given NV0 and NV- data 
# tR in units of ms
def calculate_threshold_plot(readout_time,nv0_array,nvm_array, nd_filter, aom_power):
    tR = readout_time
    fit_rate = get_photon_dis_curve_fit_plot(readout_time,nv0_array,nvm_array)
    x_data = np.linspace(0,500,501)
    thresh_para = model.calculate_threshold(tR,x_data,fit_rate )
    print(thresh_para)
    
    x_data = np.linspace(0,60,61)
    fig3,ax = plt.subplots()
    ax.plot(x_data,model.get_PhotonNV0_list(x_data,tR,fit_rate,0.5),"-o")
    ax.plot(x_data,model.get_PhotonNVm_list(x_data,tR,fit_rate,0.5),"-o")
    plt.axvline(x=thresh_para[0],color = "red")
    textstr = '\n'.join((
        r'$\mu_1=%.2f$' % (fit_rate[3]*tR, ),
        r'$\mu_2=%.2f$'% (fit_rate[2]*tR, ),
        r'$fidelity =%.2f$'% (thresh_para[1] ),
        r'$threshold = %.1f$'% (thresh_para[0], )))
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.65, 0.95, textstr, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)
    plt.xlabel("Number of counts")
    plt.ylabel("Probability Density")
    plt.title('{} ms readout, {}, {} V'.format(readout_time, nd_filter, aom_power))
    
    fidelity = thresh_para[1]
    threshold =thresh_para[0]
    mu_1 = fit_rate[3]*tR
    mu_2 = fit_rate[2]*tR
    return threshold, fidelity, mu_1, mu_2, fig3
    
# %%
# Apply a gren or red pulse, then measure the counts under yellow illumination. 
# Repeat num_reps number of times and returns the list of counts after red illumination, then green illumination
# Use with DM on red and green
def measure(nv_sig, opti_nv_sig, apd_indices, num_reps):

    with labrad.connect() as cxn:
        sig_counts, ref_counts = measure_with_cxn(cxn, nv_sig,opti_nv_sig,  apd_indices, num_reps)
        
    return sig_counts, ref_counts
def measure_with_cxn(cxn, nv_sig, opti_nv_sig, apd_indices, num_reps):

    tool_belt.reset_cfm(cxn)

    # Initial Calculation and setup
    
    tool_belt.set_filter(cxn, nv_sig, 'charge_readout_laser')
    tool_belt.set_filter(cxn, nv_sig, 'nv-_prep_laser')
    
    readout_laser_power = tool_belt.set_laser_power(cxn, nv_sig, 'charge_readout_laser')
    nvm_laser_power = tool_belt.set_laser_power(cxn, nv_sig, "nv-_prep_laser")
    nv0_laser_power = tool_belt.set_laser_power(cxn,nv_sig,"nv0_prep_laser")
    
    
    readout_pulse_time = nv_sig['charge_readout_dur']
    
    reionization_time = nv_sig['nv-_prep_laser_dur']
    ionization_time = nv_sig['nv0_prep_laser_dur']
    coords = nv_sig['coords']
      

    # Set up our data lists
    opti_coords_list = []
    
    # Optimize
    opti_coords = optimize.main_with_cxn(cxn, opti_nv_sig, apd_indices)
    opti_coords_list.append(opti_coords)
    drift = tool_belt.get_drift()
    adjusted_nv_coords = coords + numpy.array(drift)
    tool_belt.set_xyz(cxn, adjusted_nv_coords)

    # Pulse sequence to do a single pulse followed by readout           
    seq_file = 'simple_readout_two_pulse.py'     
        
        
    ################## Load the measuremnt with green laser ##################
      
    seq_args = [reionization_time, readout_pulse_time, nv_sig["nv-_prep_laser"], 
                nv_sig["charge_readout_laser"], nvm_laser_power, 
                readout_laser_power, 2, apd_indices[0]]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    cxn.pulse_streamer.stream_load(seq_file, seq_args_string)
    # print(seq_args)

    # Load the APD
    cxn.apd_tagger.start_tag_stream(apd_indices)
    # Clear the buffer
    cxn.apd_tagger.clear_buffer()
    # Run the sequence
    cxn.pulse_streamer.stream_immediate(seq_file, num_reps, seq_args_string)

    nvm = cxn.apd_tagger.read_counter_simple(num_reps)
    
    ################## Load the measuremnt with red laser ##################
    seq_args = [ionization_time, readout_pulse_time, nv_sig["nv0_prep_laser"], 
                nv_sig["charge_readout_laser"], nv0_laser_power, 
                readout_laser_power, 2,apd_indices[0]]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    cxn.pulse_streamer.stream_load(seq_file, seq_args_string)
    # print(seq_args)

    # Load the APD
    cxn.apd_tagger.start_tag_stream(apd_indices)
    # Clear the buffer
    cxn.apd_tagger.clear_buffer()
    # Run the sequence
    cxn.pulse_streamer.stream_immediate(seq_file, num_reps, seq_args_string)

    nv0 = cxn.apd_tagger.read_counter_simple(num_reps)
    
    
    tool_belt.reset_cfm(cxn)
    
    return nv0, nvm

def determine_readout_dur(nv_sig, opti_nv_sig, readout_times = None, readout_yellow_powers = None,
                          nd_filter = 'nd_0.5'):
    num_reps = 250
    apd_indices =[0]
    
    if not readout_times:
        readout_times = [50*10**6, 100*10**6, 250*10**6]
    if not readout_yellow_powers:
        readout_yellow_powers = [0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6]
        
    # first index will be power, second will be time, third wil be individual points
    nv0_master = []
    nvm_master =[]
    
    tool_belt.init_safe_stop()
    
    for p in readout_yellow_powers:
        nv0_power =[]
        nvm_power =[]
        for t in readout_times:
            # Break out of the while if the user says stop
            if tool_belt.safe_stop():
                break
            
            nv_sig_copy = copy.deepcopy(nv_sig)
            nv_sig_copy['charge_readout_laser_filter'] = nd_filter
            nv_sig_copy['charge_readout_dur'] = t
            nv_sig_copy['charge_readout_laser_power'] = p
            
            nv0, nvm = measure(nv_sig_copy, opti_nv_sig, apd_indices, num_reps)
            nv0_power.append(nv0)
            nvm_power.append(nvm)
            timestamp = tool_belt.get_time_stamp()
            raw_data = {'timestamp': timestamp,
                    'nv_sig': nv_sig_copy,
                    'nv_sig-units': tool_belt.get_nv_sig_units(),
                    'num_runs':num_reps,
                    'nv0': nv0.tolist(),
                    'nv0_list-units': 'counts',
                    'nvm': nvm.tolist(),
                    'nvmt-units': 'counts',
                    }
            
            fig_hist, ax = plt.subplots(1, 1)
            max_0 = max(nv0)
            max_m = max(nvm)
            occur_0, x_vals_0 = numpy.histogram(nv0, numpy.linspace(0,max_0, max_0+1))
            occur_m, x_vals_m = numpy.histogram(nvm, numpy.linspace(0,max_m, max_m+1))
            ax.plot(x_vals_0[:-1],occur_0,  'r-o', label = 'Initial red pulse' )
            ax.plot(x_vals_m[:-1],occur_m,  'g-o', label = 'Initial green pulse' )
            ax.set_xlabel('Counts')
            ax.set_ylabel('Occur.')
            ax.set_title('{} ms readout, {}, {} V'.format(t/10**6, nd_filter, p))
            ax.legend()
            
            file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
            tool_belt.save_raw_data(raw_data, file_path)
            tool_belt.save_figure(fig_hist, file_path + '_histogram')
            
            print('data collected!')
            # return
            print('{} ms readout, {}, {} V'.format(t/10**6, nd_filter, p))
            threshold, fidelity, mu_1, mu_2, fig = calculate_threshold_plot(t/10**6, nv0, nvm, nd_filter, p)
            
            raw_data = {'timestamp': timestamp,
                    'nv_sig': nv_sig_copy,
                    'nv_sig-units': tool_belt.get_nv_sig_units(),
                    'num_runs':num_reps,
                    'nv0': nv0.tolist(),
                    'nv0_list-units': 'counts',
                    'nvm': nvm.tolist(),
                    'nvmt-units': 'counts',
                    'mu_1': mu_1,
                    'mu_2': mu_2,
                    'fidelity': fidelity,
                    'threshold': threshold
                    }
            
            tool_belt.save_raw_data(raw_data, file_path)
            tool_belt.save_figure(fig, file_path)
    
            
        nv0_master.append(nv0_power)
        nvm_master.append(nvm_power)
    
    return

def sweep_readout_dur(nv_sig, readout_times = None, readout_yellow_power = 0.4,
                          nd_filter = 'nd_0.5'):
    num_reps = 250
    apd_indices =[0]
    
    if not readout_times:
        readout_times = [10*10**3, 
                           20*10**3, 30*10**3, 40*10**3, 
                                  50*10**3, 100*10**3,500*10**3, 
                                  1*10**6, 2*10**6, 3*10**6, 4*10**6, 5*10**6, 
                                  6*10**6, 7*10**6, 8*10**6, 9*10**6, 1*10**7,
                                 2*10**7,3*10**7,4*10**7,
                                 5*10**7
                               ]
        
    # first index will be power, second will be time, third wil be individual points
    nv0_count_raw = []
    nvm_count_raw = []
    nv0_counts_avg = []
    nvm_counts_avg = []
    snr_list = []
    
    tool_belt.init_safe_stop()
    
    for t in readout_times:
        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break
        
        nv_sig_copy = copy.deepcopy(nv_sig)
        nv_sig_copy['charge_readout_laser_filter'] = nd_filter
        nv_sig_copy['charge_readout_dur'] = t
        nv_sig_copy['charge_readout_laser_power'] = readout_yellow_power
        
        nv0, nvm = measure(nv_sig_copy, apd_indices, num_reps)
        nv0 = [int(el) for el in nv0]
        nvm = [int(el) for el in nvm]
        nv0_count_raw.append(nv0)
        nvm_count_raw.append(nvm)
        
        snr = tool_belt.calc_snr(nvm, nv0)
        nv0_counts_avg.append(numpy.average(nv0))
        nvm_counts_avg.append(numpy.average(nvm))
        snr_list.append(snr)
        
        timestamp = tool_belt.get_time_stamp()
        raw_data = {'timestamp': timestamp,
                'nv_sig': nv_sig_copy,
                'nv_sig-units': tool_belt.get_nv_sig_units(),
                'num_runs':num_reps,
                'nv0': nv0,
                'nv0_list-units': 'counts',
                'nvm': nvm,
                'nvm-units': 'counts',
                }
    
        #plot histogram of counts
        fig_hist, ax = plt.subplots(1, 1)
        max_0 = max(nv0)
        max_m = max(nvm)
        occur_0, x_vals_0 = numpy.histogram(nv0, numpy.linspace(0,max_0, max_0+1))
        occur_m, x_vals_m = numpy.histogram(nvm, numpy.linspace(0,max_m, max_m+1))
        ax.plot(x_vals_0[:-1],occur_0,  'r-o', label = 'Initial red pulse' )
        ax.plot(x_vals_m[:-1],occur_m,  'g-o', label = 'Initial green pulse' )
        ax.set_xlabel('Counts')
        ax.set_ylabel('Occur.')
        ax.set_title('{} ms readout, {}, {} V'.format(t/10**6, nd_filter, readout_yellow_power))
        ax.legend()
        
        file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
        tool_belt.save_raw_data(raw_data, file_path)
        tool_belt.save_figure(fig_hist, file_path + '_histogram')
        
    title = '{}, {} V'.format( nd_filter, readout_yellow_power)
    # plot average counts
    readout_times = numpy.array(readout_times)
    
    fig, axes = plt.subplots(1,2, figsize = (17, 8.5)) 
    ax = axes[0]
    ax.plot(readout_times / 10**3, nvm_counts_avg, 'ro', 
           label = 'Initial green pulse')
    ax.plot(readout_times / 10**3, nv0_counts_avg, 'ko', 
           label = 'Initial red pulse')
    ax.set_xlabel('Test pulse length (us)')
    ax.set_ylabel('Counts (single shot measurement)')
    ax.set_title(title)
    ax.legend()
    
    ax = axes[1]    
    ax.plot(readout_times / 10**3, snr_list, 'ro')
    ax.set_xlabel('Test pulse length (us)')
    ax.set_ylabel('SNR')
    ax.set_title(title)
    
    # then try to find optimum time based on readout time and SNR
    max_tr = max(readout_times)
    # print(max_tr)
    SNR_tot = numpy.array(snr_list) * numpy.sqrt(max_tr/(readout_times + 6e6))
    fig2, ax = plt.subplots(1,1) 
    ax.plot(readout_times / 10**3, SNR_tot, 'bo')
    ax.set_xlabel('Test pulse length (us)')
    ax.set_ylabel('SNR, scaled with sqrt(readout time/max readout time)')
    
    
    raw_data = {'timestamp': timestamp,
            'nv_sig': nv_sig,
            'nv_sig-units': tool_belt.get_nv_sig_units(),
            'readout_yellow_power': readout_yellow_power,
            'nd_filter': nd_filter,
            'num_runs':num_reps,
            'readout_times': readout_times.tolist(),
            
            'nv0_counts_avg': nv0_counts_avg,
            'nv0_counts_avg-units': 'counts',
            'nvm_counts_avg': nvm_counts_avg,
            'nvm_counts_avg-units': 'counts',
            
            'nv0_count_raw': nv0_count_raw,
            'nv0_count_raw-units': 'counts',
            'nvm_count_raw': nvm_count_raw,
            'nvm_count_raw-units': 'counts',
            'snr_list': snr_list,
            'SNR_tot': SNR_tot.tolist()
            }
    tool_belt.save_raw_data(raw_data, file_path + '-duration_sweep')
    tool_belt.save_figure(fig, file_path + '-snr')
    tool_belt.save_figure(fig2, file_path + '-snr_scaled')
    return

#%%     
if __name__ == '__main__':
    # load the data here 
    sample_name = 'johnson'    
    
    green_laser = "cobolt_515"
    yellow_laser = 'laserglow_589'
    red_laser = 'cobolt_638'
    green_power= 8
    
    
    opti_nv_sig = {
        "coords": [-0.20177, 0.12953,  4.09457485],
        "name": "{}-nv0_2021_10_08".format(sample_name,),
        "disable_opt": False,
        "expected_count_rate": 35,
        "imaging_laser":green_laser,
        "imaging_laser_power": green_power,
        "imaging_readout_dur": 1e7,
        "collection_filter": "630_lp",
        "magnet_angle": None,
    }  # 14.5 max
    
    nv_sig = {
        "coords":[250.422, 250.982, 5],
        "name": "{}-nv0_2021_12_22".format(sample_name,),
        "disable_opt": False,
        "ramp_voltages": False,
        "expected_count_rate":35,
            'imaging_laser': green_laser, 'imaging_laser_power': green_power, 'imaging_readout_dur': 1E7,
            'nv-_prep_laser': green_laser, 'nv-_prep_laser_power': green_power, 'nv-_prep_laser_dur': 1E3,
            'nv0_prep_laser': red_laser, 'nv0_prep_laser_value': 120, 'nv0_prep_laser_dur': 1E3,
            'charge_readout_laser': yellow_laser, 'charge_readout_laser_filter': None, 
            'charge_readout_laser_power': None, 'charge_readout_dur':None,
            'collection_filter': '630_lp', 'magnet_angle': None,
            'resonance_LOW': 2.8012, 'rabi_LOW': 141.5, 'uwave_power_LOW': 15.5,  # 15.5 max
            'resonance_HIGH': 2.9445, 'rabi_HIGH': 191.9, 'uwave_power_HIGH': 14.5}   # 14.5 max

    try:
        # sweep_readout_dur(nv_sig, readout_yellow_power = 0.1,
        #                   nd_filter = 'nd_0.5')
        determine_readout_dur(nv_sig, nv_sig, readout_times = [75e6,100e6],
                              readout_yellow_powers = [0.15,0.17],
                          nd_filter = 'nd_1.0')
    finally:
        # Reset our hardware - this should be done in each routine, but
        # let's double check here
        tool_belt.reset_cfm()
        # Kill safe stop
        if tool_belt.check_safe_stop_alive():
            print('\n\nRoutine complete. Press enter to exit.')
            tool_belt.poll_safe_stop()


# Replotting

    # file_name = '2021_08_27-14_37_14-johnson-nv1_2021_08_26-duration_sweep'
    # folder = 'pc_rabi/branch_master/determine_charge_readout_dur/2021_08'
    # data_in = tool_belt.get_raw_data(file_name, folder)
    # snr_list = data_in['snr_list']
    # readout_times = numpy.array(data_in['readout_times'])
    # # then try to find optimum time based on readout time and SNR
    # max_tr = max(readout_times)
    # # print(max_tr)
    # SNR_tot = numpy.array(snr_list) * numpy.sqrt(max_tr/(readout_times + 10e6))
    # fig2, ax = plt.subplots(1,1) 
    # ax.plot(readout_times / 10**3, SNR_tot, 'bo')
    # ax.set_xlabel('Test pulse length (us)')
    # ax.set_ylabel('SNR, scaled with sqrt(readout time/max readout time)')


