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
import utils.positioning as positioning
import utils.tool_belt as tool_belt
import utils.common as common
import majorroutines.image_sample_digital as image_sample_digital
import majorroutines.image_sample as image_sample
import majorroutines.optimize as optimize
import majorroutines.stationary_count as stationary_count
import majorroutines.resonance as resonance
import majorroutines.optimize_magnet_angle as optimize_magnet_angle
import majorroutines.pulsed_resonance as pulsed_resonance
import majorroutines.rabi as rabi
import majorroutines.ramsey as ramsey
import majorroutines.spin_echo as spin_echo
import minorroutines.determine_delays as determine_delays
import majorroutines.determine_standard_readout_params as determine_standard_readout_params
import majorroutines.charge_majorroutines.determine_charge_readout_params as determine_charge_readout_params
import majorroutines.charge_majorroutines.determine_scc_pulse_params as determine_scc_pulse_params
import majorroutines.charge_majorroutines.scc_pulsed_resonance as scc_pulsed_resonance
import majorroutines.charge_majorroutines.rabi_SCC as rabi_SCC
import majorroutines.charge_majorroutines.ramsey_SCC as ramsey_SCC
import majorroutines.charge_majorroutines.ramsey_SCC_one_tau_no_ref as ramsey_SCC_one_tau_no_ref
import majorroutines.charge_majorroutines.test_charge_state_pre_selection as test_charge_state_pre_selection
import majorroutines.charge_majorroutines.test_spin_repolarization_scc as test_spin_repolarization_scc
from utils.tool_belt import States, NormStyle
import time
import copy
import matplotlib.pyplot as plt


# %% Major Routines

def do_image_sample(nv_sig,nv_minus_init=False,scan_range=2,num_steps=30,cmin=None,cmax=None,scan_type='XY'):
    scale = 1 #um / V
   
    # For now we only support square scans so pass scan_range twice
    # image_sample_digital.main(nv_sig, scan_range, scan_range, num_steps,nvm_initialization,save_data=True,cbarmin=cmin,cbarmax=cmax)
    image_sample.main(nv_sig, scan_range, scan_range, num_steps,nv_minus_init,vmin=cmin,vmax=cmax,scan_type=scan_type)


def do_optimize(nv_sig,save_data):

    optimize_coords = optimize.main(
        nv_sig,
        set_to_opti_coords=False,
        save_data=save_data,
        plot_data=True,
    )
    return optimize_coords



def do_optimize_z(nv_sig):
    
    adj_nv_sig = copy.deepcopy(nv_sig)
    adj_nv_sig["only_z_opt"] = True

    optimize_coords = optimize.main(
        adj_nv_sig,
        set_to_opti_coords=False,
        save_data=True,
        plot_data=True,
    )
    return optimize_coords

def do_stationary_count(nv_sig,disable_opt=False):

    run_time = 1 * 60 * 10 ** 9  # ns
    nv_sig["imaging_readout_dur"] = 100e6
    stationary_count.main(nv_sig, run_time,disable_opt)
    
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
        
def do_resonance(nv_sig, freq_center=2.87, freq_range=0.2,num_steps = 51, num_runs = 20):

    # num_steps = 51
    # num_runs = 20
    uwave_power = -7.5
    nv_sig['spin_pol_dur']=2e3

    resonance.main(
        nv_sig,
        freq_center,
        freq_range,
        num_steps,
        num_runs,
        uwave_power,
        state=States.HIGH,
    )

def do_rabi(nv_sig, uwave_time_range, state ,num_steps = 51, num_reps = 1e4, num_runs = 20):

    # num_steps = 51
    # num_runs = 20
    nv_sig['spin_pol_dur']=2e3

    rabi.main(
        nv_sig,
        uwave_time_range,
        state,
        num_steps,
        num_reps,
        num_runs,
    )    

def do_spin_echo(nv_sig, max_time=130,num_reps=4e3,num_runs=5,state=States.LOW):

    # T2* in nanodiamond NVs is just a couple us at 300 K
    # In bulk it's more like 100 us at 300 K
    # max_time = 120  # us
    # num_steps = int(1*max_time)  # 1 point per us
    num_steps = int(50)  # 1 point per us
    precession_time_range = [10**2, max_time * 10 ** 3]
    # precession_time_range = [600,2512]
    # num_reps = 4e3
    # num_runs = 5
    # num_runs = 20
    
    # state = States.LOW

    angle = spin_echo.main(
        nv_sig,
        precession_time_range,
        num_steps,
        num_reps,
        num_runs,
        state,
    )
    return angle

def do_ramsey(nv_sig, detuning=4):

    # detuning = 5  # MHz
    precession_time_range = [0, 2336]
    num_steps = 74
    num_reps = int(2e4)
    num_runs = 50

    ramsey.main(
        nv_sig,
        detuning,
        precession_time_range,
        num_steps,
        num_reps,
        num_runs,
    )

def do_pulsed_resonance(nv_sig, freq_center=2.87, freq_range=0.2, uwave_pulse_dur=100, num_steps=51, num_reps=1e4, num_runs=10):

    # num_steps =101
    # num_reps = 1e4
    # num_runs = 10
    uwave_power = 16.5
    nv_sig['spin_pol_dur']=2e3
    # uwave_pulse_dur = 200

    ret_vals = pulsed_resonance.main(
        nv_sig,
        freq_center,
        freq_range,
        num_steps,
        num_reps,
        num_runs,
        uwave_power,
        uwave_pulse_dur,
        opti_nv_sig = nv_sig
    )
    return ret_vals

def do_optimize_magnet_angle(nv_sig):

    angle_range = [0,150]
    num_angle_steps = 6
    freq_center = 2.87
    freq_range = 0.2
    num_freq_steps = 51
    # num_freq_runs = 30
    num_freq_runs = 4

    # Pulsed
    uwave_power = 16.5
    uwave_pulse_dur = 50
    num_freq_reps = 2e4

    # CW
    # uwave_power = -5.0
    # uwave_pulse_dur = None
    # num_freq_reps = None

    optimize_magnet_angle.main(
        nv_sig,
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
    
def do_determine_standard_readout_params(nv_sig):
    
    num_reps = 5e5
    max_readouts = [1e3]
    state = States.LOW
    
    determine_standard_readout_params.main(nv_sig, num_reps, 
                                           max_readouts, state=state)

def do_determine_charge_readout_params(nv_sig,readout_powers,readout_times,num_reps):
    
        opti_nv_sig = nv_sig
        readout_durs = readout_times
        readout_durs = [int(el) for el in readout_durs]
        max_readout_dur = max(readout_durs)
        # readout_powers = [.5]

            
        determine_charge_readout_params.main(  
          nv_sig,
          num_reps,
          readout_powers=readout_powers,
          max_readout_dur=max_readout_dur,
          plot_readout_durs=readout_durs,
          fit_threshold_full_model=False,
          extra_green_initialization=True,
          )
        
def do_determine_scc_pulse_params(nv_sig,num_reps,ion_durs=None):
    
    nv_sig['nv-_reionization_dur'] = 5000
    
    determine_scc_pulse_params.determine_ionization_dur(nv_sig, num_reps,ion_durs)
    
def do_scc_pulsed_resonance(nv_sig):
    
    
    uwave_power = 16.5
    uwave_pulse_dur = 84
    
    num_steps = 21
    num_reps= 1000
    num_runs = 5
    
    freq_center = 2.87
    freq_range = 0.2
    
    scc_pulsed_resonance.main(nv_sig, nv_sig, 
                              freq_center, freq_range, num_steps, num_reps, num_runs, 
                              uwave_power, uwave_pulse_dur)
    
def do_rabi_SCC(nv_sig):
    
    state = States.LOW
    
    num_steps = 11
    num_reps= 500
    num_runs = 4
    uwave_time_range = [0,160]
    
    rabi_SCC.main(nv_sig, uwave_time_range, state,
             num_steps, num_reps, num_runs)
    
def do_ramsey_SCC(nv_sig, opti_nv_sig,detuning=4):

    # detuning = 5  # MHz
    precession_time_range = [20, 704]
    num_steps = 20
    num_reps = int(5e3)
    num_runs = 5

    ramsey_SCC.main(
        nv_sig,
        detuning,
        precession_time_range,
        num_steps,
        num_reps,
        num_runs,
        opti_nv_sig = opti_nv_sig
    )
    
    

def do_determine_reion_dur(nv_sig):
    
    reion_durs = numpy.arange(240,556,16)
    num_reps = 30000
    
    determine_charge_readout_params.determine_reion_dur(
        nv_sig,
        num_reps,
        reion_durs
        )
    
    
def do_ramsey_SCC_one_tau_no_ref(nv_sig,num_reps):

    detuning = -0.9  # MHz
    precession_time = 200
    conditional_logic = True
    photon_threshold = 1
    chop_factor = 10
    # num_reps = int(8e4)

    ramsey_SCC_one_tau_no_ref.main(
        nv_sig,
        detuning,
        precession_time,
        num_reps,
        States.LOW,
        conditional_logic,
        photon_threshold,
        chop_factor
    )
    

def do_test_spin_repolarization_scc(nv_sig, second_init_laser_key, second_init_power, 
                                    num_reps,num_runs,min_wait_time,max_time,num_steps,
                                    threshold,do_ion_pulse,do_pi_pulse):
    
    state = States.HIGH
    
    test_spin_repolarization_scc.main(nv_sig, state, 
                                       second_init_laser_key, second_init_power, 
                                       num_reps,num_runs,min_wait_time,max_time,num_steps,threshold,
                                       do_ion_pulse,do_pi_pulse)
    
def do_test_charge_state_pre_selection(nv_sig,num_reps):
    
    state = States.LOW
    
    test_charge_state_pre_selection.main(nv_sig, state, num_reps, opti_nv_sig = None)

# %% Run the file


if __name__ == "__main__":

    # In debug mode, don't bother sending email notifications about exceptions
    debug_mode = True
    # %% Shared parameters
    
    with labrad.connect() as cxn:
        apd_indices = common.get_registry_entry(cxn, "apd_indices", ["","Config"])
        apd_indices = apd_indices.astype(list).tolist()

    sample_name = "johnson"
    green_laser = "cobolt_515"
    yellow_laser = 'laserglow_589'
    red_laser = 'cobolt_638'
#26.605, 50.020, 59.85
    nv_sig = {
        'coords': [70.071, 57.034, 54.5], 'name': '{}-search'.format(sample_name),
        'ramp_voltages': False, "only_z_opt": False, 'disable_opt': False, "disable_z_opt": False, 
        'expected_count_rate': 31,
        # "imaging_laser": yellow_laser, "imaging_laser_power": .35, 
        "imaging_laser": green_laser, "imaging_laser_filter": "nd_0", 
        "imaging_readout_dur": 10e6,
        # "imaging_readout_dur": 50e6,
        "spin_laser": green_laser,
        "spin_laser_filter": "nd_0",
        "spin_pol_dur": 50e3,
        "spin_readout_dur": 340,
        "nv-_reionization_laser": green_laser,
        "nv-_reionization_dur": 5e3,
        "nv-_reionization_laser_filter": "nd_0",
        "nv0_ionization_laser": red_laser,
        "nv0_ionization_dur": 192,
        "nv0_ionization_laser_filter": "nd_0",
        "nv-spin_reinit_laser": green_laser,
        "nv-spin_reinit_laser_dur": 1e3,
        "nv-_prep_laser": green_laser,
        "nv-_prep_laser_dur": 1e4,
        "nv-_prep_laser_filter": "nd_0",
        "nv0_prep_laser": red_laser,
        "nv0_prep_laser_dur": 1e4,
        # "nv0_prep_laser_dur": 16,
        "nv0_prep_laser_filter": "nd_0",
        "charge_readout_laser": yellow_laser,
        "charge_readout_dur": 5e6,
        "charge_readout_laser_power": 0.45,
        "charge_readout_laser_filter": "nd_0",
        "initialize_laser": green_laser,
        "initialize_dur": 1e4,
        'collection_filter': None, 'magnet_angle': 170,
        'resonance_LOW': 2.8206, 'rabi_LOW': 116, 'uwave_power_LOW': 16.5,
        'resonance_HIGH': 2.9217, 'rabi_HIGH': 116, 'uwave_power_HIGH': 16.5,
        'norm_style':NormStyle.SINGLE_VALUED
        }
    
    
    
    # %% Functions to run

    try:
        # with labrad.connect() as cxn:
        #     positioning.reset_drift(cxn)

        # do_determine_standard_readout_params(nv_sig)
        # do_scc_pulsed_resonance(nv_sig)
        # do_rabi_SCC(nv_sig)       
        # do_ramsey_SCC(nv_sig, nv_sig,detuning=-0.74)
        
        # do_determine_scc_pulse_params(nv_sig,5000,ion_durs=None)
        # do_determine_charge_readout_params(nv_sig, readout_powers=powers,readout_times=[10e6], num_reps=50000)
        # do_ramsey_SCC_one_tau_no_ref(nv_sig,num_reps=int(1e6))
        
        # do_test_spin_repolarization_scc(nv_sig, second_init_laser_key='laserglow_589', 
        #                               second_init_power=0.0, 
        #                               num_reps=2000,num_runs=3,
        #                               min_wait_time=0,max_time=20e6,num_steps=6,
        #                               threshold=3,do_ion_pulse=[True,False],do_pi_pulse=[True,False])
        
        # do_test_spin_repolarization_scc_v3(nv_sig, second_init_laser_key='laserglow_589', 
        #                               second_init_power=0.45, 
        #                               num_reps=2000,num_runs=3,
        #                               min_wait_time=0,max_time=20e6,num_steps=6,
        #                               threshold=3,do_ion_pulse=[True,False],do_pi_pulse=[True,False])
        
        # do_test_charge_state_pre_selection(nv_sig, num_reps=2000)
        
        do_image_sample(nv_sig,num_steps=20,scan_range=3,scan_type='XY')
        # do_image_sample(nv_sig,num_steps=20,scan_range=10,scan_type='XZ')
        # do_optimize(nv_sig,save_data=True)
        # do_optimize_z(nv_sig)
        # do_stationary_count(nv_sig,disable_opt=True)
        # 
        # do_laser_delay_calibration(nv_sig,apd_indices,'cobolt_515',num_reps=int(2e6), delay_range=[64,640],num_steps=37)
        # do_laser_delay_calibration(nv_sig,apd_indices,'cobolt_638',num_reps=int(6e6), delay_range=[40,700],num_steps=31)
        
        # do_resonance(nv_sig,num_steps = 41, num_runs = 40,freq_center=2.87,freq_range=.2)
        # do_rabi(nv_sig, uwave_time_range = [0,320], state=States.HIGH,num_reps=2e4,num_runs=4,num_steps=21)
        # do_pulsed_resonance(nv_sig, freq_range=0.2, uwave_pulse_dur=52,num_steps=41, num_reps=2e4, num_runs=4)
        # detunings = [3]
        # for d in detunings:
        #     do_ramsey(nv_sig,detuning=d)
        # do_spin_echo(nv_sig, max_time=130,num_reps=2e4,num_runs=10,state=States.LOW)
        # do_spin_echo(nv_sig, num_reps=2e4, num_runs=200, state=States.LOW)
        # do_spin_echo(nv_sig, max_time=15,num_reps=2e4,num_runs=200,state=States.LOW)
        # do_optimize_magnet_angle(nv_sig)
        # do_determine_charge_readout_params(nv_sig,num_reps=5000,readout_powers=powers,readout_times=[5e6])
        # do_determine_charge_readout_params(nv_sig,num_reps=1000,readout_powers=[.35],readout_times=[20e6])
        # do_determine_charge_readout_params(nv_sig,num_reps=1000,readout_powers=[.3],readout_times=[20e6])
        # do_determine_reion_dur(nv_sig)

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