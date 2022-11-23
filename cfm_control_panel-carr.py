# -*- coding: utf-8 -*-
"""
This file contains functions to control the CFM. Just change the function call
in the main section at the bottom of this file and run the file. Shared or
frequently changed parameters are in the __main__ body and relatively static
parameters are in the function definitions. 

Created on Sun Nov 25 14:00:28 2018

@author: mccambria
"""


# %% Imports


import labrad
import numpy
import time
import copy
import utils.tool_belt as tool_belt
import majorroutines.image_sample_digital as image_sample_digital
import majorroutines.image_sample_xz_digital as image_sample_xz_digital
import majorroutines.optimize_digital as optimize_digital
import majorroutines.stationary_count as stationary_count
import majorroutines.resonance as resonance
import majorroutines.optimize_magnet_angle as optimize_magnet_angle
import majorroutines.pulsed_resonance as pulsed_resonance
import majorroutines.rabi as rabi
import majorroutines.ramsey as ramsey
import majorroutines.spin_echo as spin_echo
import minorroutines.determine_delays as determine_delays
import minorroutines.determine_standard_readout_params as determine_standard_readout_params
import chargeroutines.determine_charge_readout_params as determine_charge_readout_params
import chargeroutines.determine_scc_pulse_params as determine_scc_pulse_params
import chargeroutines.scc_pulsed_resonance as scc_pulsed_resonance
import majorroutines.charge_majorroutines.rabi_SCC as rabi_SCC
import majorroutines.charge_majorroutines.ramsey_SCC as ramsey_SCC
import majorroutines.charge_majorroutines.ramsey_SCC_one_tau_no_ref as ramsey_SCC_one_tau_no_ref
import majorroutines.ramsey_one_tau_no_ref as ramsey_one_tau_no_ref
from utils.tool_belt import States
import time
import copy
import matplotlib.pyplot as plt


# %% Major Routines
    
    

def do_image_sample(nv_sig, apd_indices,scan_range=2,num_steps=30,cmin=None,cmax=None):
    scale = 1 #um / V
   
    # For now we only support square scans so pass scan_range twice
    image_sample_digital.main(nv_sig, scan_range, scan_range, num_steps, apd_indices,save_data=True,cbarmin=cmin,cbarmax=cmax)

def do_image_sample_xz(nv_sig, apd_indices,scan_range=2,num_steps=30,cmin=None,cmax=None):
    scale = 1 #um / V
   
    # For now we only support square scans so pass scan_range twice
    image_sample_xz_digital.main(nv_sig, scan_range, scan_range, num_steps, apd_indices,save_data=True,cbarmin=cmin,cbarmax=cmax)


def do_optimize(nv_sig, apd_indices):

    optimize_coords = optimize_digital.main(
        nv_sig,
        apd_indices,
        set_to_opti_coords=False,
        save_data=True,
        plot_data=True,
    )
    return optimize_coords



def do_optimize_z(nv_sig, apd_indices):
    
    adj_nv_sig = copy.deepcopy(nv_sig)
    adj_nv_sig["only_z_opt"] = True

    optimize_coords = optimize_digital.main(
        adj_nv_sig,
        apd_indices,
        set_to_opti_coords=False,
        save_data=True,
        plot_data=True,
    )
    return optimize_coords

def do_stationary_count(nv_sig, apd_indices,disable_opt=False):

    run_time = 1 * 60 * 10 ** 9  # ns

    stationary_count.main(nv_sig, run_time, apd_indices,disable_opt)
    
def do_laser_delay_calibration(nv_sig,apd_indices,laser_name,num_reps = int(2e6),
                              delay_range = [50, 500],num_steps=21):
    # laser_delay
    # num_reps = int(2e6)
    # delay_range = [50, 500]
    # num_steps = 21
    with labrad.connect() as cxn:
        determine_delays.aom_delay(
            cxn,
            nv_sig,
            apd_indices,
            delay_range,
            num_steps,
            num_reps,
            laser_name,
            1,
        )
        
def do_resonance(nv_sig, apd_indices, freq_center=2.87, freq_range=0.2,num_steps = 51, num_runs = 20):

    # num_steps = 51
    # num_runs = 20
    uwave_power = -7.5
    nv_sig['spin_pol_dur']=2e3

    resonance.main(
        nv_sig,
        apd_indices,
        freq_center,
        freq_range,
        num_steps,
        num_runs,
        uwave_power,
        state=States.HIGH,
    )

def do_rabi(nv_sig, apd_indices, uwave_time_range, state ,num_steps = 51, num_reps = 1e4, num_runs = 20):

    # num_steps = 51
    # num_runs = 20
    nv_sig['spin_pol_dur']=2e3

    rabi.main(
        nv_sig,
        apd_indices,
        uwave_time_range,
        state,
        num_steps,
        num_reps,
        num_runs,
    )    

def do_spin_echo(nv_sig, apd_indices,max_time=120,num_reps=4e3,num_runs=5,state=States.LOW):

    # T2* in nanodiamond NVs is just a couple us at 300 K
    # In bulk it's more like 100 us at 300 K
    # max_time = 120  # us
    num_steps = int(max_time/2)  # 1 point per us
    precession_time_range = [1e3, max_time * 10 ** 3]
    # num_reps = 4e3
    # num_runs = 5
    # num_runs = 20
    
    # state = States.LOW

    angle = spin_echo.main(
        nv_sig,
        apd_indices,
        precession_time_range,
        num_steps,
        num_reps,
        num_runs,
        state,
    )
    return angle

def do_ramsey(nv_sig, opti_nv_sig, apd_indices,detuning=4):

    # detuning = 5  # MHz
    precession_time_range = [20, 1320]
    num_steps =41
    num_reps = int(4e4)
    num_runs = 20

    ramsey.main(
        nv_sig,
        apd_indices,
        detuning,
        precession_time_range,
        num_steps,
        num_reps,
        num_runs,
        opti_nv_sig = opti_nv_sig
    )

def do_pulsed_resonance(nv_sig, opti_nv_sig, apd_indices, freq_center=2.87, freq_range=0.2, uwave_pulse_dur=100, num_steps=51, num_reps=1e4, num_runs=10):

    # num_steps =101
    # num_reps = 1e4
    # num_runs = 10
    uwave_power = 16.5
    nv_sig['spin_pol_dur']=2e3
    # uwave_pulse_dur = 200

    pulsed_resonance.main(
        nv_sig,
        apd_indices,
        freq_center,
        freq_range,
        num_steps,
        num_reps,
        num_runs,
        uwave_power,
        uwave_pulse_dur,
        opti_nv_sig = opti_nv_sig
    )

def do_optimize_magnet_angle(nv_sig, apd_indices):

    angle_range = [0,150]
    num_angle_steps = 6
    freq_center = 2.87
    freq_range = 0.07
    num_freq_steps = 31
    # num_freq_runs = 30
    num_freq_runs = 4

    # Pulsed
    uwave_power = 16.5
    uwave_pulse_dur = 92
    num_freq_reps = 2e4

    # CW
    # uwave_power = -5.0
    # uwave_pulse_dur = None
    # num_freq_reps = None

    optimize_magnet_angle.main(
        nv_sig,
        apd_indices,
        angle_range,
        num_angle_steps,
        freq_center,
        freq_range,
        num_freq_steps,
        num_freq_reps,
        num_freq_runs,
        uwave_power,
        uwave_pulse_dur,
    )
    
def do_determine_standard_readout_params(nv_sig, apd_indices):
    
    num_reps = 5e5
    max_readouts = [1e3]
    state = States.LOW
    
    determine_standard_readout_params.main(nv_sig, apd_indices, num_reps, 
                                           max_readouts, state=state)

def do_determine_charge_readout_params(nv_sig, apd_indices,readout_powers,readout_times,num_reps):
        opti_nv_sig = nv_sig
        # num_reps = 2000
        readout_durs = readout_times
        readout_durs = [int(el) for el in readout_durs]
        max_readout_dur = max(readout_durs)
        # readout_powers = [.5]

            
        determine_charge_readout_params.determine_readout_dur_power(  
          nv_sig,
          opti_nv_sig,
          apd_indices,
          num_reps,
          max_readout_dur=max_readout_dur,
          readout_powers=readout_powers,
          plot_readout_durs=readout_durs,
          fit_threshold_full_model=True,
          extra_green_initialization=True,
          )
        
def do_determine_scc_pulse_params(nv_sig,apd_indices,num_reps):
    
    nv_sig['nv-_reionization_dur'] = 5000
    
    determine_scc_pulse_params.determine_ionization_dur(nv_sig, apd_indices, num_reps)
    
def do_scc_pulsed_resonance(nv_sig,apd_indices):
    
    
    uwave_power = 16.5
    uwave_pulse_dur = 84
    
    num_steps = 21
    num_reps= 1000
    num_runs = 5
    
    freq_center = 2.87
    freq_range = 0.2
    
    scc_pulsed_resonance.main(nv_sig, nv_sig, apd_indices, 
                              freq_center, freq_range, num_steps, num_reps, num_runs, 
                              uwave_power, uwave_pulse_dur)
    
def do_rabi_SCC(nv_sig, apd_indices):
    
    state = States.LOW
    
    num_steps = 31
    num_reps= 100
    num_runs = 3
    uwave_time_range = [16,320]
    
    rabi_SCC.main(nv_sig, apd_indices, uwave_time_range, state,
             num_steps, num_reps, num_runs)
    
def do_ramsey_SCC(nv_sig, opti_nv_sig, apd_indices,detuning=4):

    # detuning = 5  # MHz
    precession_time_range = [20, 704]
    num_steps = 20
    num_reps = int(5e3)
    num_runs = 5

    ramsey_SCC.main(
        nv_sig,
        apd_indices,
        detuning,
        precession_time_range,
        num_steps,
        num_reps,
        num_runs,
        opti_nv_sig = opti_nv_sig
    )
    
    

def do_determine_reion_dur(nv_sig, apd_indices):
    
    reion_durs = numpy.arange(240,556,16)
    num_reps = 30000
    
    determine_charge_readout_params.determine_reion_dur(
        nv_sig,
        apd_indices,
        num_reps,
        reion_durs
        )
    
    
def do_ramsey_SCC_one_tau_no_ref(nv_sig, apd_indices,num_reps):

    detuning = -0.9  # MHz
    precession_time = 200
    conditional_logic = True
    photon_threshold = 1
    chop_factor = 10
    # num_reps = int(8e4)

    ramsey_SCC_one_tau_no_ref.main(
        nv_sig,
        apd_indices,
        detuning,
        precession_time,
        num_reps,
        States.LOW,
        conditional_logic,
        photon_threshold,
        chop_factor
    )

# %% Run the file


if __name__ == "__main__":

    # In debug mode, don't bother sending email notifications about exceptions
    debug_mode = True
    # %% Shared parameters
    
    with labrad.connect() as cxn:
        apd_indices = tool_belt.get_registry_entry(cxn, "apd_indices", ["","Config"])
        apd_indices = apd_indices.astype(list).tolist()
        

    sample_name = "johnson"
    green_laser = "cobolt_515"
    yellow_laser = 'laserglow_589'
    red_laser = 'cobolt_638'

    nv_sig = {
        'coords': [86.944, 38.154,76.375], 'name': '{}-search'.format(sample_name),
        'ramp_voltages': False, "only_z_opt": False, 'disable_opt': False, "disable_z_opt": False, 
        'expected_count_rate': 52,
        # "imaging_laser": yellow_laser, "imaging_laser_power": 0.55, 
        # "imaging_laser": red_laser, "imaging_laser_filter": "nd_0", 
        "imaging_laser": green_laser, "imaging_laser_filter": "nd_0", 
        "imaging_readout_dur": 10e6,
        # "imaging_readout_dur": 60e6,
        "spin_laser": green_laser,
        "spin_laser_filter": "nd_0",
        "spin_pol_dur": 1e4,
        "spin_readout_dur": 340,
        "nv-_reionization_laser": green_laser,
        "nv-_reionization_dur": 250,
        "nv-_reionization_laser_filter": "nd_0",
        "nv0_ionization_laser": red_laser,
        "nv0_ionization_dur": 330,
        "nv0_ionization_laser_filter": "nd_0",
        "nv-spin_reinit_laser": green_laser,
        "nv-spin_reinit_laser_dur": 1e3,
        "nv-_prep_laser": green_laser,
        "nv-_prep_laser_dur": 10e4,
        "nv-_prep_laser_filter": "nd_0",
        "nv0_prep_laser": red_laser,
        "nv0_prep_laser_dur": 10e4,
        # "nv0_prep_laser_dur": 16,
        "nv0_prep_laser_filter": "nd_0",
        "charge_readout_laser": yellow_laser,
        "charge_readout_dur": 100e3,
        "charge_readout_laser_power": 0.55,
        "charge_readout_laser_filter": "nd_0",
        "initialize_laser": green_laser,
        "initialize_dur": 1e4,
        'collection_filter': None, 'magnet_angle': 112,
        'resonance_LOW': 2.8586, 'rabi_LOW': 168, 'uwave_power_LOW': 16.5,
        'resonance_HIGH': 2.883, 'rabi_HIGH': 152, 'uwave_power_HIGH': 16.5,
        }
    
    
    
    # %% Functions to run

    try:
        # tool_belt.reset_drift()

        # tool_belt.init_safe_stop()
        # do_determine_standard_readout_params(nv_sig, apd_indices)
        # ion_times = [20,40,60,80,100,200,400]
        # for ion_time in ion_times:
        #     nv_sig['nv0_prep_laser_dur'] = ion_time
        #     do_determine_charge_readout_params(nv_sig, apd_indices)
        # do_determine_scc_pulse_params(nv_sig,apd_indices)
        # do_scc_pulsed_resonance(nv_sig,apd_indices)
        # do_rabi_SCC(nv_sig, apd_indices)       
        # do_ramsey_SCC(nv_sig, nv_sig, apd_indices,detuning=-0.74)
        # times = [100e3,400e3,1e6,3e6,5e6]#1e3,10e3,50e3,100e3,500e3,1e6]
        # # powers = [0.7]
        # num_reps= [1000000,500000,100000,10000,10000]#1000000,1000000,1000000,100000,100000,100000]
        # # num_reps = [3e5]
        # powers = numpy.array([0.3,0.35,0.4,0.45,0.5,0.55,0.6,0.65,0.7,0.75,0.8])
        # times = numpy.array([10e3,50e3,100e3,400e3,1e6,4e6])
        # num_reps = numpy.array([2e7,3e6,2e6,4e5,2e5,3e4])
        # num_reps2 = numpy.array([1e6,1e6,2e6,1e5,2e4,2e4])
        
        # for power in powers:
        #     for i in range(len(times)):
        #         nv_sig['charge_readout_dur'] = times[i]
        #         nv_sig['charge_readout_laser_power'] = power
        #         do_determine_scc_pulse_params(nv_sig,apd_indices,int(num_reps[i]))
        # nv_sig['charge_readout_dur'] = 25e5
        # do_determine_scc_pulse_params(nv_sig,apd_indices,int(2e4))
        
        # for power in powers:
        #     for i in range(len(times)):
        #         do_determine_charge_readout_params(nv_sig, apd_indices, 
        #                                            readout_powers=[power],readout_times=[times[i]],
        #                                            num_reps=int(num_reps2[i]))
        
        # do_determine_scc_pulse_params(nv_sig,apd_indices,5000)
        # do_determine_charge_readout_params(nv_sig, apd_indices,
        #                                    readout_powers=[.55],
        #                                    readout_times=[5e6],
        #                                    num_reps=2000)
        
        # for i in range(3):
        #     nv_sig['charge_readout_dur'] = times[i]
        #     nv_sig['charge_readout_laser_power'] = powers[i]
        # do_determine_scc_pulse_params(nv_sig,apd_indices,int(1e6))
        #     for t in [250,2000]:
        #         nv_sig["nv-_reionization_dur"] = t
        # do_ramsey_SCC_one_tau_no_ref(nv_sig, apd_indices,num_reps=int(1e6))
        
        # do_ramsey_one_tau_no_ref(nv_sig, apd_indices)
        
        # do_image_sample_xz(nv_sig, apd_indices,num_steps=30,scan_range=3)#,cmin=0,cmax=50)
        # for z in [76.2,76.4,76.6]:
        #     nv_sig['coords'][2]=z
        # do_image_sample(nv_sig, apd_indices,num_steps=50,scan_range=5)#,cmin=0,cmax=75)
        # do_image_sample(nv_sig, apd_indices,num_steps=30,scan_range=3)#,cmin=0,cmax=75)
        # nv_sig['coords'] = [87.944, 38.754,76.375]
        # do_image_sample(nv_sig, apd_indices,num_steps=20,scan_range=2)#,cmin=0,cmax=75)
        
        do_optimize(nv_sig, apd_indices)
        # do_optimize_z(nv_sig, apd_indices)
        
        # do_stationary_count(nv_sig, apd_indices,disable_opt=True)
        # 
        # do_laser_delay_calibration(nv_sig,apd_indices,'laserglow_589',num_reps=int(2e6), delay_range=[100,5000],num_steps=101)
        # do_laser_delay_calibration(nv_sig,apd_indices,'cobolt_638',num_reps=int(6e6), delay_range=[40,700],num_steps=31)
        
        # do_resonance(nv_sig, apd_indices,num_steps = 41, num_runs = 40,freq_center=2.83,freq_range=.08)
        # do_resonance_modulo(nv_sig, apd_indices,num_steps = 51, num_runs = 5)
        # do_rabi(nv_sig, apd_indices, uwave_time_range = [16,320], state=States.LOW,num_reps=2e4,num_runs=5,num_steps=51)
        # do_rabi(nv_sig, apd_indices, uwave_time_range = [16,320], state=States.HIGH,num_reps=2e4,num_runs=6,num_steps=51)
        # do_pulsed_resonance(nv_sig, nv_sig, apd_indices,freq_center=2.8582, freq_range=0.03,num_steps=31, num_reps=2e4, num_runs=10)
        # do_pulsed_resonance(nv_sig, nv_sig, apd_indices,uwave_pulse_dur=500,freq_center=2.83,freq_range=.03,num_steps=51, num_reps=2e4, num_runs=15)
        # for det in [-3,-1.2,-1.1,-1,3]:
        #     do_ramsey(nv_sig, nv_sig, apd_indices,detuning=det)
        
        # do_ramsey(nv_sig, nv_sig, apd_indices,detuning=-1)
        # do_ramsey(nv_sig, nv_sig, apd_indices,detuning=2)
        # do_spin_echo(nv_sig, apd_indices,max_time=140,num_reps=2e4,num_runs=80,state=States.LOW)
        # do_image_sample(nv_sig, apd_indices,num_steps=80,scan_range=8)
        # do_optimize_magnet_angle(nv_sig, apd_indices)
        
        # for readout_dur in [200,250,300,350,400,450,500]:
        #     nv_sig['spin_readout_dur'] = readout_dur
        #     do_rabi(nv_sig, apd_indices, uwave_time_range = [16,500], state=States.LOW,num_reps=2e4,num_runs=30,num_steps=51)
            
        # do_determine_charge_readout_params(nv_sig, apd_indices)
        # do_spin_echo(nv_sig, apd_indices,max_time=100,num_reps=2e4,num_runs=10,state=States.LOW)
        # do_determine_reion_dur(nv_sig, apd_indices)

    except Exception as exc:
        # Intercept the exception so we can email it out and re-raise it
        if not debug_mode:
            tool_belt.send_exception_email(email_to="cdfox@wisc.edu")
        raise exc

    finally:
        # Reset our hardware - this should be done in each routine, but
        # let's double check here
        tool_belt.reset_cfm()
        # Kill safe stop
        tool_belt.reset_safe_stop()