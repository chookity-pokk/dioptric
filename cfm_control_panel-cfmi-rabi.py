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
import utils.positioning as positioning
import utils.kplotlib as kpl
import matplotlib.pyplot as plt
import majorroutines.image_sample as image_sample
# import majorroutines.image_sample_xz as image_sample_xz
import majorroutines.charge_majorroutines.image_sample_charge_state_compare as image_sample_charge_state_compare
import majorroutines.optimize as optimize
import majorroutines.stationary_count as stationary_count
import majorroutines.resonance as resonance
import majorroutines.pulsed_resonance as pulsed_resonance
# import majorroutines.esr_srt as esr_srt
import majorroutines.optimize_magnet_angle as optimize_magnet_angle
import majorroutines.rabi as rabi
import majorroutines.rabi_srt as rabi_srt
import majorroutines.rabi_consec as rabi_consec
import majorroutines.rabi_two_pulse as rabi_two_pulse
# import majorroutines.discrete_rabi as discrete_rabi
import majorroutines.g2_measurement as g2_measurement
import majorroutines.ramsey as ramsey
import majorroutines.t1_dq_main as t1_dq_main
import majorroutines.spin_echo as spin_echo
import majorroutines.dynamical_decoupling_cpmg as dynamical_decoupling_cpmg
import majorroutines.dynamical_decoupling_xy4 as dynamical_decoupling_xy4
import majorroutines.dynamical_decoupling_xy8 as dynamical_decoupling_xy8
import majorroutines.lifetime_v2 as lifetime_v2
# import minorroutines.time_resolved_readout as time_resolved_readout
import majorroutines.charge_majorroutines.SPaCE as SPaCE
# import chargeroutines.SPaCE_simplified as SPaCE_simplified
import majorroutines.charge_majorroutines.scc_pulsed_resonance as scc_pulsed_resonance
import majorroutines.charge_majorroutines.scc_spin_echo as scc_spin_echo
import majorroutines.determine_standard_readout_params as determine_standard_readout_params
import majorroutines.charge_majorroutines.super_resolution_pulsed_resonance as super_resolution_pulsed_resonance
import majorroutines.charge_majorroutines.super_resolution_ramsey as super_resolution_ramsey
import majorroutines.charge_majorroutines.super_resolution_spin_echo as super_resolution_spin_echo
# import majorroutines.charge_majorroutines.g2_measurement as g2_SCC_branch
import majorroutines.charge_majorroutines.determine_charge_readout_params as determine_charge_readout_params

# import majorroutines.set_drift_from_reference_image as set_drift_from_reference_image
# import debug.test_major_routines as test_major_routines
from utils.tool_belt import States
from utils.tool_belt import NormStyle
import time


# %% Major Routines


def do_image_sample(nv_sig):

    # scan_range = 0.25
    # num_steps = 150

    # scan_range = 2
    # 80 um / V
    #
    # scan_range = 5.0
    # scan_range = 3
    # scan_range = 1.2
    # scan_range =4
    # scan_range = 2
    # scan_range = 0.5
    # scan_range = 0.35
    # scan_range = 0.2
    # scan_range = 0.15
    # scan_range = 0.1
    scan_range = 0.05
    # scan_range = 0.025
    # scan_range = 0.012

    #num_steps = 400
    # num_steps = 300
    # num_steps = 200
    # num_steps = 135
    # num_steps =120
    # num_steps = 90
    num_steps = 60
    # num_steps = 35
    # num_steps = 21

    #individual line pairs:
    # scan_range = 0.16
    # num_steps = 160

    #both line pair sets:
    # scan_range = 0.35
    # num_steps = 160


    # For now we only support square scans so pass scan_range twice
    ret_vals = image_sample.main(nv_sig, scan_range, scan_range, num_steps)
    img_array, x_voltages, y_voltages = ret_vals

    return img_array, x_voltages, y_voltages


def do_image_sample_xz(nv_sig):

    x_range = .05
    z_range =0.2
    num_steps = 60

    image_sample.main(
        nv_sig,
        x_range,
        z_range,
        num_steps,
        scan_type = 'XZ'
    )


def do_image_charge_states(nv_sig):

    scan_range = 0.01

    num_steps = 31
    num_reps= 10

    image_sample_charge_state_compare.main(
        nv_sig, scan_range, scan_range, num_steps,num_reps
    )


def do_optimize(nv_sig):

    
    optimize.main(
        nv_sig,
        set_to_opti_coords=False,
        save_data=True,
        plot_data=True,
    )


def do_optimize_list(nv_sig_list):

    optimize.optimize_list(nv_sig_list)



def do_stationary_count(nv_sig):

    run_time = 1 * 60 * 10 ** 9  # ns

    stationary_count.main(nv_sig, run_time)

def do_stationary_count_bg_subt(
    nv_sig,
    bg_coords
):

    run_time = 3 * 60 * 10**9  # ns

    stationary_count.main(
        nv_sig,
        run_time,
        disable_opt=True,
        background_subtraction=True,
        background_coords=bg_coords,
    )

# def do_g2_measurement(nv_sig, apd_a_index, apd_b_index):

#     run_time = 3*60  # s
#     diff_window =120# ns

#     # g2_measurement.main(
#     g2_SCC_branch.main(
#         nv_sig, run_time, diff_window, apd_a_index, apd_b_index
#     )


def do_resonance(nv_sig, opti_nv_sig,freq_center=2.87, freq_range=0.2):

    num_steps = 101
    num_runs = 15
    uwave_power = -10.0

    resonance.main(
        nv_sig,
        freq_center,
        freq_range,
        num_steps,
        num_runs,
        uwave_power,
        state=States.HIGH,
        opti_nv_sig = opti_nv_sig
    )

def do_resonance_state(nv_sig, opti_nv_sig,  state):

    freq_center = nv_sig["resonance_{}".format(state.name)]
    uwave_power = -10.0

    freq_range = 0.15
    num_steps = 51
    num_runs = 20

    # Zoom
    # freq_range = 0.060
    # num_steps = 51
    # num_runs = 10

    resonance.main(
        nv_sig,
        freq_center,
        freq_range,
        num_steps,
        num_runs,
        uwave_power,
        opti_nv_sig = opti_nv_sig
    )


def do_pulsed_resonance(nv_sig, opti_nv_sig,  freq_center=2.87, freq_range=0.2):

    num_steps =101
    num_reps = 1e4
    num_runs = 10
    uwave_power = 10
    uwave_pulse_dur = int(176.3/2)

    pulsed_resonance.main(
        nv_sig,
        freq_center,
        freq_range,
        num_steps,
        num_reps,
        num_runs,
        uwave_power,
        uwave_pulse_dur,
        state=States.HIGH,
        opti_nv_sig = opti_nv_sig
    )


def do_pulsed_resonance_state(nv_sig, opti_nv_sig, state):

    # freq_range = 0.150
    # num_steps = 51
    # num_reps = 10**4
    # num_runs = 8

    # Zoom
    freq_range = 0.12
    num_steps = 75
    # freq_range = 0.010
    # num_steps = 101
    num_reps = int(1e4)
    num_runs =  7

    composite = False

    res, _ = pulsed_resonance.state(
        nv_sig,
        state,
        freq_range,
        num_steps,
        num_reps,
        num_runs,
        composite,
        opti_nv_sig = opti_nv_sig,
    )
    # nv_sig["resonance_{}".format(state.name)] = res


def do_optimize_magnet_angle(nv_sig):

    # angle_range = [132, 147]
    #    angle_range = [315, 330]
    num_angle_steps = 6
    #    freq_center = 2.7921
    #    freq_range = 0.060
    angle_range = [0, 150]
    #    num_angle_steps = 6
    freq_center = 2.87
    freq_range = 0.25
    num_freq_steps = 101
    num_freq_runs = 10

    # Pulsed
    uwave_power = 10
    uwave_pulse_dur = 130/2
    num_freq_reps = int(1e4)

    # CW
    #uwave_power = -10.0
    #uwave_pulse_dur = None
    #num_freq_reps = None

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
    

def do_rabi(nv_sig, opti_nv_sig, state, 
            uwave_time_range=[0, 200]):

    num_steps =51
    num_reps = int(2e4)    
    num_runs =  5

    rabi.main(
        nv_sig,
        uwave_time_range,
        state,
        num_steps,
        num_reps,
        num_runs,
        opti_nv_sig = opti_nv_sig
    )
    # nv_sig["rabi_{}".format(state.name)] = period


def do_rabi_consec(nv_sig,  initial_state, readout_state,  uwave_time_range=[0, 500],
                    ):
    
    num_steps = 101
    num_reps = int(1e4)
    num_runs = 5 

    norm_avg_sig, norm_avg_ste = rabi_consec.main(nv_sig, 
             num_steps, 
             num_reps, 
             num_runs,
             uwave_time_range, 
             readout_state,
             initial_state,
             do_err_plot = True,
             )
    return norm_avg_sig, norm_avg_ste
    
def do_rabi_consec_pop(nv_sig, uwave_time_range=[0, 500]):
    
    # deviation_high = 0
    # deviation_low = 0
    
    # deviation = 0
    
    num_steps = 101
    num_reps = int(1e4)
    num_runs = 20

    rabi_consec.full_pop_consec(nv_sig,  uwave_time_range,
             num_steps, num_reps, num_runs)
    
def do_rabi_two_pulse(nv_sig, uwave_time_range_LOW, uwave_time_range_HIGH, num_steps):
        
    readout_state = States.HIGH
    initial_state = States.LOW
    
    # num_steps = 101
    num_reps = int(5e5)
    num_runs = 2 #200

    rabi_two_pulse.main(nv_sig, 
             num_steps, num_reps, num_runs,
             uwave_time_range_LOW, 
             uwave_time_range_HIGH, 
             readout_state,
             initial_state,)
    
def do_rabi_srt(nv_sig,  initial_state, readout_state, dev, uwave_time_range=[0, 1000]):
    
    deviation_high = dev
    deviation_low = dev
    
    
    num_steps = 51
    num_reps = int(1e4)
    num_runs = 10
    v = 1.0

    rabi_srt.main(nv_sig, 
              uwave_time_range, 
              deviation_high,
              deviation_low, 
              num_steps, 
              num_reps,
              num_runs,
              readout_state,
              initial_state,
              low_dev_analog_voltage = v
    )

def do_rabi_srt_pop(nv_sig,  deviation, num_steps,  uwave_time_range=[0, 1000]):
    
    # deviation_high = 0
    # deviation_low = 0
    
    # deviation = 0
    
    #num_steps = 101
    num_reps = int(1e4)
    num_runs = 10 #200

    # rabi_srt.main(nv_sig, 
    #           apd_indices, 
    #           uwave_time_range, 
    #           deviation_high,
    #           deviation_low, 
    #           num_steps, 
    #           num_reps,
    #           num_runs,
    #           readout_state,
    #           initial_state,
    # )
    rabi_srt.full_pop_srt(nv_sig,  uwave_time_range, deviation, 
             num_steps, num_reps, num_runs)


def do_lifetime(nv_sig):

    num_reps = 2e4 # SM
    num_bins = 201
    # num_runs = 500
    num_runs = 10
    readout_time_range = [0.95e3, 1.15e3]  # ns
    polarization_time = 1e3 # ns

    lifetime_v2.main(
        nv_sig, 
        readout_time_range,
        num_reps, 
        num_runs, 
        num_bins, 
        polarization_time )



def do_ramsey(nv_sig, opti_nv_sig, t1,state = States.LOW):

    detuning = 0 # MHz
    
    # precession_time_range = [0, 2 * 10 ** 3]
    # precession_time_range = [1e3, 2e3]
    #t1=5e3
    precession_time_range = [t1, t1+1e3]
    num_steps = 51
    
    # code to collect data at the Nyquist frequency
    # step_size = 75 #ns
    # num_steps = 1000
    # start_time = 0
    # end_time = start_time + step_size * (num_steps-1)
    # precession_time_range = [start_time, end_time]


    num_reps = int(1e4)
    num_runs = int(40)
    
    ramsey.main(
        nv_sig,
        detuning,
        precession_time_range,
        num_steps,
        num_reps,
        num_runs,
        state,
        opti_nv_sig = opti_nv_sig,
        do_fm = False,
        do_dq = False
    )


def do_spin_echo(nv_sig, state = States.LOW):

    #max_time = 2.5e3
    max_time = 2000
    num_steps = 21
    precession_time_range = [0, max_time*10**3]

    # revival_time= 9.934e3
    # num_steps = 25
    # precession_time_range = [0, revival_time*(num_steps - 1)]

    # num_reps = 1e3
    # num_runs = 100
    num_reps = 1e3
    num_runs = 300

    #    num_steps = 151
    #    precession_time_range = [0, 10*10**3]
    #    num_reps = int(10.0 * 10**4)
    #    num_runs = 6




    spin_echo.main(
        nv_sig,
        precession_time_range,
        num_steps,
        num_reps,
        num_runs,
        state,
        do_dq = True
    )
    return

def do_dd_cpmg(nv_sig, pi_pulse_reps, step_size,  T_min, T_max, do_dq_):
    
    shift = 100 #ns
    
    max_time = T_max / (2*pi_pulse_reps)  # us
    min_time = T_min / (2*pi_pulse_reps) #us
    
    
    num_steps = int((T_max - T_min) / step_size ) + 1   # 1 point per 1 us
    precession_time_range = [int(min_time*10**3+shift), int(max_time*10**3+shift)]
    
    num_reps = 1e3
    num_runs= 300#150

    state = States.HIGH

    dynamical_decoupling_cpmg.main(
        nv_sig,
        precession_time_range,
        pi_pulse_reps,
        num_steps,
        num_reps,
        num_runs,
        state=state,
        do_dq= do_dq_
    )
    return 


def do_dd_xy4(nv_sig,num_xy4_reps, step_size,  T_min, T_max):

    #step_size = 1 # us
    shift = 100 #ns
    #T_min = 0
    #T_max = 200
    
    # max_time = T_max / (2*4*num_xy4_reps)  # us
    # min_time = T_min / (2*4*num_xy4_reps) #us
    
    
    #step_size = 2 # us
    #shift = 0 #ns
    #T_min = 350-50
    #T_max = 350+50
    
    max_time = T_max / (2*4*num_xy4_reps)  # us
    min_time = T_min / (2*4*num_xy4_reps) #us
    
    # # revival_time= nv_sig['t2_revival_time']
    # # T_min = (revival_time/1e3 - 3)*(2*4*num_xy4_reps) 
    # # T_max = (revival_time/1e3 + 3)*(2*4*num_xy4_reps)
    
    num_steps = int((T_max - T_min) / step_size ) + 1   # 1 point per 1 us
    # min_time =0.0# 1 / (2*pi_pulse_reps) #us
    # num_steps = int(T/1+1 )  # 1 point per 1 us
    precession_time_range = [int(min_time*10**3+shift), int(max_time*10**3+shift)]
    
    #conventional readout
    num_reps = 1e3
    num_runs= 200
    
    # # scc readout
    # num_reps = 4 #should optimize every 10 min
    # num_runs= 3750

    state = States.HIGH



    dynamical_decoupling_xy4.main(
        nv_sig,
        precession_time_range,
        num_xy4_reps,
        num_steps,
        num_reps,
        num_runs,
        state=state,
        do_dq=True,
    )
    return 

def do_dd_xy4_revivals(nv_sig, num_xy4_reps):

    revival_time= nv_sig['t2_revival_time']
    num_revivals = 5
    precession_time_range = [0, revival_time*(num_revivals - 1)]
    #num_steps= int(num_revivals * 2 - 1)
    
    dt = 5e3 #us
    dt_xy4 = dt/(2*4*num_xy4_reps)
    taus = [0, dt_xy4]
    for ind in range(num_revivals-1):
        # print(ind)
        i = ind+1
        t0 = revival_time*(i-0.5)
        t1 = revival_time*i - dt_xy4
        t2 = revival_time*i
        t3 = revival_time*i + dt_xy4
        taus = taus + [t0, t1, t2, t3]
    
    i = num_revivals
    t0 = revival_time*(i-0.5)
    t1 = revival_time*i - dt_xy4
    t2 = revival_time*i
    taus = taus + [t0, t1, t2]
    # print(taus)
    
    taus = numpy.array(taus)
    num_steps=len(taus)
    # taus = numpy.linspace(
    #     precession_time_range[0],
    #     precession_time_range[1],
    #     num=num_steps,
    #     dtype=numpy.int32,
    # )
    # taus[0] = 500

    # num_xy4_reps = 1
    num_reps = 1e4
    num_runs= 75





    dynamical_decoupling_xy4.main(
        nv_sig,
        precession_time_range,
        num_xy4_reps,
        num_steps,
        num_reps,
        num_runs,
        taus = taus,
        state = States.HIGH,
    )
    return 

def do_dd_xy8(nv_sig, num_xy8_reps, step_size,  T_min, T_max):

    #step_size = 1 # us
    shift = 100 #ns
    #T_min = 0
    #T_max = 200
    
    # max_time = T_max / (2*4*num_xy4_reps)  # us
    # min_time = T_min / (2*4*num_xy4_reps) #us
    
    
    #step_size = 2 # us
    #shift = 0 #ns
    #T_min = 350-50
    #T_max = 350+50
    
    max_time = T_max / (2*8*num_xy8_reps)  # us
    min_time = T_min / (2*8*num_xy8_reps) #us
    
    # # revival_time= nv_sig['t2_revival_time']
    # # T_min = (revival_time/1e3 - 3)*(2*4*num_xy4_reps) 
    # # T_max = (revival_time/1e3 + 3)*(2*4*num_xy4_reps)
    
    num_steps = int((T_max - T_min) / step_size ) + 1   # 1 point per 1 us
    # min_time =0.0# 1 / (2*pi_pulse_reps) #us
    # num_steps = int(T/1+1 )  # 1 point per 1 us
    precession_time_range = [int(min_time*10**3+shift), int(max_time*10**3+shift)]
    
    #conventional readout
    num_reps = 2e3
    num_runs= 2#150
    
    # # scc readout
    # num_reps = 4 #should optimize every 10 min
    # num_runs= 3750

    state = States.HIGH



    dynamical_decoupling_xy8.main(
        nv_sig,
        precession_time_range,
        num_xy8_reps,
        num_steps,
        num_reps,
        num_runs,
        state,
    )
    return 

def do_relaxation(nv_sig ):
    min_tau = 0
    max_tau_omega = 5e6
    max_tau_gamma = 10e3
    num_steps_omega = 21
    num_steps_gamma = 21
    num_reps = 1e3
    num_runs = 400
    
    if True:
     t1_exp_array = numpy.array(
        [[
                [States.ZERO, States.ZERO],
                [min_tau, max_tau_omega],
                num_steps_omega,
                num_reps,
                num_runs,
            ],
        # [
        #         [States.ZERO, States.HIGH],
        #         [min_tau, max_tau_omega],
        #         num_steps_omega,
        #         num_reps,
        #         num_runs,
        #     ],
             
             ])
    if False:
     t1_exp_array = numpy.array(
        [ 
            #[
            #    [States.ZERO, States.ZERO],
            #    [min_tau, max_tau_omega],
           #     num_steps_omega,
            #    num_reps,
            #    num_runs,
           # ],
        [
                [States.ZERO, States.HIGH],
                [min_tau, max_tau_omega],
                num_steps_omega,
                num_reps,
                num_runs,
            ],
                [
                [States.HIGH, States.HIGH],
                [min_tau, max_tau_gamma],
                num_steps_gamma,
                num_reps,
                num_runs,
            ],
                    [
                [States.HIGH, States.LOW],
                [min_tau, max_tau_gamma],
                num_steps_gamma,
                num_reps,
                num_runs,
            ]] )

    t1_dq_main.main(
            nv_sig,
            t1_exp_array,
            num_runs,
            composite_pulses=False,
            scc_readout=False,
        )

def do_determine_standard_readout_params(nv_sig):
    
    num_reps = 5e5
    max_readouts = [1e3]
    state = States.HIGH
    
    determine_standard_readout_params.main(nv_sig, num_reps, 
                                           max_readouts, state=state)
    
def do_determine_charge_readout_params(nv_sig):
        num_reps = int(5e2)
        readout_durs = [50e6]
        readout_durs = [int(el) for el in readout_durs]
        max_readout_dur = max(readout_durs)
        readout_powers = [0.1]
        
            
        determine_charge_readout_params.main(  
          nv_sig,
          num_reps,
          max_readout_dur=max_readout_dur,
          readout_powers=readout_powers,
          plot_readout_durs=readout_durs,
          fit_threshold_full_model= False,)
        
          
# def do_time_resolved_readout(nv_sig, apd_indices):

#     # nv_sig uses the initialization key for the first pulse
#     # and the imaging key for the second

#     num_reps = 1000
#     num_bins = 2001
#     num_runs = 20
#     # disp = 0.0001#.05

#     bin_centers, binned_samples_sig = time_resolved_readout.main(
#         nv_sig,
#         apd_indices,
#         num_reps,
#         num_runs,
#         num_bins
#     )
#     return bin_centers, binned_samples_sig

# def do_time_resolved_readout_three_pulses(nv_sig, apd_indices):

#     # nv_sig uses the initialization key for the first pulse
#     # and the imaging key for the second

#     num_reps = 1000
#     num_bins = 2001
#     num_runs = 20


#     bin_centers, binned_samples_sig = time_resolved_readout.main_three_pulses(
#         nv_sig,
#         apd_indices,
#         num_reps,
#         num_runs,
#         num_bins
#     )

#     return bin_centers, binned_samples_sig



def do_SPaCE(nv_sig, opti_nv_sig, apd_indices,num_runs, num_steps_a, num_steps_b,
               img_range_1D, img_range_2D, offset, charge_state_threshold = None):
    # dr = 0.025 / numpy.sqrt(2)
    # img_range = [[-dr,-dr],[dr, dr]] #[[x1, y1], [x2, y2]]
    # num_steps = 101
    # num_runs = 50
    # measurement_type = "1D"

    # img_range = 0.075
    # num_steps = 71
    # num_runs = 1
    # measurement_type = "2D"

    # dz = 0
    SPaCE.main(nv_sig, opti_nv_sig, apd_indices,num_runs, num_steps_a, num_steps_b,
               charge_state_threshold, img_range_1D, img_range_2D, offset )



def do_scc_resonance(nv_sig, opti_nv_sig, apd_indices, state=States.LOW):
    freq_center = nv_sig['resonance_{}'.format(state.name)]
    uwave_power = nv_sig['uwave_power_{}'.format(state.name)]
    uwave_pulse_dur = nv_sig['rabi_{}'.format(state.name)]/2

    freq_range = 0.05
    num_steps = 51
    num_reps = int(10**3)
    num_runs = 30

    scc_pulsed_resonance.main(nv_sig, opti_nv_sig, apd_indices, freq_center, freq_range,
         num_steps, num_reps, num_runs, uwave_power, uwave_pulse_dur, state )

def do_scc_spin_echo(nv_sig, opti_nv_sig, apd_indices, tau_start, tau_stop, state=States.LOW):
    step_size = 1 # us
    num_steps = int((tau_stop - tau_start)/step_size + 1)

    precession_time_range = [tau_start *1e3, tau_stop *1e3]

    num_reps = int(10**3)
    num_runs = 40

    scc_spin_echo.main(nv_sig, opti_nv_sig, apd_indices, precession_time_range,
         num_steps, num_reps, num_runs,
         state )



def do_super_resolution_resonance(nv_sig, opti_nv_sig, apd_indices, state=States.LOW):
    freq_center = nv_sig['resonance_{}'.format(state.name)]
    uwave_power = nv_sig['uwave_power_{}'.format(state.name)]
    uwave_pulse_dur = nv_sig['rabi_{}'.format(state.name)]/2

    freq_range = 0.05
    num_steps = 51
    num_reps = int(10**3)
    num_runs = 30

    super_resolution_pulsed_resonance.main(nv_sig, opti_nv_sig, apd_indices, freq_center, freq_range,
         num_steps, num_reps, num_runs, uwave_power, uwave_pulse_dur, state )

def do_super_resolution_ramsey(nv_sig, opti_nv_sig, apd_indices,
                                  tau_start, tau_stop, state=States.LOW):

    detuning = 5  # MHz

    # step_size = 0.05 # us
    # num_steps = int((tau_stop - tau_start)/step_size + 1)
    num_steps = 101
    precession_time_range = [tau_start *1e3, tau_stop *1e3]


    num_reps = int(10**3)
    num_runs = 30

    super_resolution_ramsey.main(nv_sig, opti_nv_sig, apd_indices,
                                    precession_time_range, detuning,
         num_steps, num_reps, num_runs, state )

def do_super_resolution_spin_echo(nv_sig, opti_nv_sig, apd_indices,
                                  tau_start, tau_stop, state=States.LOW):
    step_size = 1 # us
    num_steps = int((tau_stop - tau_start)/step_size + 1)
    print(num_steps)
    precession_time_range = [tau_start *1e3, tau_stop *1e3]


    num_reps = int(10**3)
    num_runs = 20

    super_resolution_spin_echo.main(nv_sig, opti_nv_sig, apd_indices,
                                    precession_time_range,
         num_steps, num_reps, num_runs, state )

def do_sample_nvs(nv_sig_list, apd_indices):

    # g2 parameters
    run_time = 60 * 5
    diff_window = 150

    # PESR parameters
    num_steps = 101
    num_reps = 10 ** 5
    num_runs = 3
    uwave_power = 9.0
    uwave_pulse_dur = 100

    g2 = g2_measurement.main_with_cxn
    pesr = pulsed_resonance.main_with_cxn

    with labrad.connect() as cxn:
        for nv_sig in nv_sig_list:
            g2_zero = g2(
                cxn,
                nv_sig,
                run_time,
                diff_window,
                apd_indices[0],
                apd_indices[1],
            )
            if g2_zero < 0.5:
                pesr(
                    cxn,
                    nv_sig,
                    apd_indices,
                    2.87,
                    0.1,
                    num_steps,
                    num_reps,
                    num_runs,
                    uwave_power,
                    uwave_pulse_dur,
                )



# %% Run the file


if __name__ == "__main__":

    # In debug mode, don't bother sending email notifications about exceptions
    debug_mode = True
    

    # %% Shared parameters

    # # apd_indices = [0]
    # apd_indices = [1]
    # # apd_indices = [0,1]

    nd_yellow = "nd_0"
    green_power =8000
    nd_green = 'nd_1.1'
    red_power = 120
    sample_name = "siena"
    # sample_name = "ayrton12"
    green_laser = "integrated_520"
    yellow_laser = "laserglow_589"
    red_laser = "cobolt_638"


    sig_base = {
        "disable_opt":False,
        "ramp_voltages": True,
        # "correction_collar": 0.12,
        'expected_count_rate': None,
         "green_power_mW": 1.0,

        "spin_laser":green_laser,
        "spin_laser_power": green_power,
        "spin_laser_filter": nd_green,
        "spin_readout_dur": 300,
        "spin_pol_dur": 10000.0,

        "imaging_laser":green_laser,
        "imaging_laser_power": green_power,
        "imaging_laser_filter": nd_green,
        "imaging_readout_dur": 1e7,
        
        # "imaging_laser":yellow_laser,
        # "imaging_laser_power": 0.2,
        # "imaging_laser_filter": "nd_1.0",
        # "imaging_readout_dur": 5e7,

        "initialize_laser": green_laser,
        "initialize_laser_power": green_power,
        "initialize_laser_dur":  1e3,
        "CPG_laser": green_laser,
        "CPG_laser_power":red_power,
        "CPG_laser_dur": int(1e6),

        "nv-_prep_laser": green_laser,
        "nv-_prep_laser-power": None,
        "nv-_prep_laser_dur": 1e3,
        "nv0_prep_laser": red_laser,
        "nv0_prep_laser-power": None,
        "nv0_prep_laser_dur": 1e3,
        
        "nv-_reionization_laser": green_laser,
        "nv-_reionization_laser_power": green_power,
        "nv-_reionization_dur": 1e3,
        
        "nv0_ionization_laser": red_laser,
        "nv0_ionization_laser_power": None,
        "nv0_ionization_dur": 300,
        
        "spin_shelf_laser": yellow_laser,
        "spin_shelf_laser_power": None,
        "spin_shelf_dur": 0,
        
        "charge_readout_laser": yellow_laser,
        "charge_readout_laser_power": 0.15, 
        "charge_readout_laser_filter": nd_yellow,
        "charge_readout_dur": 200e6, 

        "collection_filter": "715_sp+630_lp", # NV band only
        'magnet_angle': 151.7,
        "uwave_power_LOW": 12.12,  
        "uwave_power_HIGH": 10,
        
        
     "norm_style": NormStyle.SINGLE_VALUED,
     "resonance_LOW": 2.7811,
     "rabi_LOW":130, 
     "resonance_HIGH":2.9600,
     "rabi_HIGH": 176.3,
    
        
    } 

    
    nv_search = copy.deepcopy(sig_base)
    nv_search["coords"] = [0,0,5.5]
    nv_search["name"] = "{}-nv_search".format(sample_name,)
    # nv_search['diasble_opt'] = True
    # nv_search["expected_count_rate"] = 100
    nv_search["disable_opt"] = False
    nv_search["resonance_HIGH"]=3.0073
    nv_search["rabi_HIGH"]=300
    
    coords_list = [
        [-0.5--0.418, -0.494, 5.5], # X
               [-0.5- -0.481, -0.494, 5.5], # X
               [-0.5--0.41, -0.462, 5.6], # X
               
               [-0.367, -0.292, 5.74], #3 ? 
               [-0.396, 0.157, 4.30], # 4
               [-0.002, 0.289, 5.3], #5
               [-0.399, 0.103, 5.51], #6
               [0.355, -0.17, 5.16], #7
               [0.335, 0.194, 4.81],#8
               [0.392, 0.491, 5.14], #9
               
               [0.51, 0.248, 6.4], # X 10
               
               [-0.394, 0.157, 4.50], # 11
               ]
    
    
    
    # nv_sig_0 = copy.deepcopy(sig_base) # 
    # nv_sig_0["coords"] = coords_list[0]
    # nv_sig_0["name"] = "{}-nv0_2022_12_20".format(sample_name,)
    # nv_sig_0["expected_count_rate"] = None
    
    
    # nv_sig_1 = copy.deepcopy(sig_base) # 
    # nv_sig_1["coords"] = coords_list[1]
    # nv_sig_1["name"] = "{}-nv1_2022_12_20".format(sample_name,)
    # nv_sig_1["expected_count_rate"] = None
    
    # nv_sig_2 = copy.deepcopy(sig_base) # 
    # nv_sig_2["coords"] = coords_list[2]
    # nv_sig_2["name"] = "{}-nv2_2022_12_20".format(sample_name,)
    # nv_sig_2["expected_count_rate"] = None
    
    nv_sig_3 = copy.deepcopy(sig_base) # 
    nv_sig_3["coords"] = [-0.367, -0.292, 5.74]
    nv_sig_3["name"] = "{}-nv3_2022_12_20".format(sample_name,)
    nv_sig_3["expected_count_rate"] = 16
    
    nv_sig_4 = copy.deepcopy(sig_base) # 
    nv_sig_4["coords"] = [-0.354, 0.124, 4.27]
    nv_sig_4["name"] = "{}-nv4_2022_12_20".format(sample_name,)
    nv_sig_4["expected_count_rate"] = 22
    
    # nv_sig_5 = copy.deepcopy(sig_base) #  Bad
    # nv_sig_5["coords"] = [-0.002, 0.289, 5.3]
    # nv_sig_5["name"] = "{}-nv5_2022_12_20".format(sample_name,)
    # nv_sig_5["expected_count_rate"] = None
    
    nv_sig_6 = copy.deepcopy(sig_base) # 
    nv_sig_6["coords"] = [-0.397, 0.114, 5.62]
    nv_sig_6["name"] = "{}-nv6_2022_12_20".format(sample_name,)
    nv_sig_6["expected_count_rate"] = 20
    
    nv_sig_7 = copy.deepcopy(sig_base) # Maybe
    nv_sig_7["coords"] = [0.352, -0.162, 5.29]
    nv_sig_7["name"] = "{}-nv7_2022_12_20".format(sample_name,)
    nv_sig_7["expected_count_rate"] = 40
    
    nv_sig_8 = copy.deepcopy(sig_base) # 
    nv_sig_8["coords"] = [0.335, 0.191, 4.82]
    nv_sig_8["name"] = "{}-nv8_2022_12_20".format(sample_name,)
    nv_sig_8["expected_count_rate"] = 22
    
    nv_sig_9 = copy.deepcopy(sig_base) # 
    nv_sig_9["coords"] = [0.391, 0.489, 5.16]
    nv_sig_9["name"] = "{}-nv9_2022_12_20".format(sample_name,)
    nv_sig_9["expected_count_rate"] = 22
    
    # nv_sig_10 = copy.deepcopy(sig_base) # 
    # nv_sig_10["coords"] = coords_list[10]
    # nv_sig_10["name"] = "{}-nv10_2022_12_20".format(sample_name,)
    # nv_sig_10["expected_count_rate"] = None
    
    nv_sig_11 = copy.deepcopy(sig_base) # 
    nv_sig_11["coords"] = [-0.396, 0.155, 4.45]
    nv_sig_11["name"] = "{}-nv11_2022_12_20".format(sample_name,)
    nv_sig_11["expected_count_rate"] = 11
    
    
    # new_coords = numpy.array(nv_sig_1["coords"]) + [-0.139, 0.061, 0.11]
    nv_sig_list = [
                   # nv_sig_3,
                   # nv_sig_4,
                   # nv_sig_6,
                   nv_sig_8,
                   nv_sig_9,
                   
                   nv_sig_11,
                   nv_sig_7,
                   ]
    
    
    nv_sig = nv_sig_9
    bg_coords = nv_sig['coords'] + numpy.array([0.5, 0.5, 0])
    
    # %% Functions to run

    try:

        # positioning.set_drift(labrad.connect(),[0.0, 0.0, positioning.get_drift(labrad.connect())[2]])  # Keep z
        # positioning.set_drift(labrad.connect(),[0.0,0.0,0.0])
        # positioning.set_drift(labrad.connect(),[0.0,0.0, -0.05])
        # positioning.set_xyz(labrad.connect(), [0,0,5])
        
        #     cxn.rotation_stage_ell18k.set_angle(65)
        
        # for x in [-0.25,0.25]:
        #       for y in [-0.25, 0.25]:
        #          for z in numpy.linspace(4.2, 6.8, 27):
        #                       coords= nv_sig["coords"]
        #                       nv_sig["coords"] =[x,y, z ]
        #                       do_image_sample(nv_sig)

        
        # for dz in numpy.linspace(-0.2, 0.2,5):
        #     nv_copy = copy.deepcopy(nv_sig)
        #     coords= nv_sig["coords"]
        #     nv_copy["coords"] =[coords[0], coords[1], coords[2] + dz ]
        #     do_image_sample(nv_copy)
                    
        
        
        # do_optimize(nv_sig)
        # do_image_sample(nv_sig)
        
        #for nv_sig in nv_sig_list:
        # for nv_sig in [nv_sig_11]:
           # positioning.set_drift(labrad.connect(),[0.0,0.0,0.0])
            # do_optimize(nv_sig)
            # do_optimize(nv_sig)
            # do_image_sample(nv_sig)
        #do_pulsed_resonance(nv_sig, nv_sig, 2.87, 0.25) 
            
        # do_image_sample_xz(nv_sig)
        
        # do_stationary_count(nv_sig)
        do_stationary_count_bg_subt(nv_sig, bg_coords)

        # do_g2_measurement(nv_sig, 0, 1)
            
        # do_lifetime(nv_sig)
             
        # do_resonance(nv_sig, nv_sig,freq_center=2.87, freq_range=0.2)
        # do_resonance_state(nv_sig, nv_sig,States.LOW)
        # do_resonance_state(nv_sig, nv_sig,States.HIGH)
        
        # do_optimize_magnet_angle(nv_sig)
        # do_pulsed_resonance(nv_sig, nv_sig, 2.87, 0.25) 
        
        # do_pulsed_resonance_state(nv_sig, nv_sig, States.LOW)
        #do_pulsed_resonance_state(nv_sig, nv_sig,States.HIGH)
        # do_rabi(nv_sig, nv_sig, States.LOW, uwave_time_range=[0, 250])
        # do_rabi(nv_sig, nv_sig, States.HIGH,   uwave_time_range=[0, 250])
        
        
        # uwave_time_range = [0, 400]
        #do_rabi_consec(nv_sig,   States.HIGH, States.ZERO,  uwave_time_range=[0, 300])
        # do_rabi_consec_pop(nv_sig,  uwave_time_range=[0, 300])
        
        # do_rabi_srt(nv_sig, States.LOW, States.HIGH, 0,  uwave_time_range=[0, 300])
        #do_rabi_srt_pop(nv_sig, 0, 51, uwave_time_range=[0, 300])
        
        # for t1 in [60e3]:
        #     do_ramsey(nv_sig, nv_sig, t1)
        
        #do_spin_echo(nv_sig)

        # do_relaxation(nv_sig)  # gamma and omega
                
        
        ###################
        step_size = 250 #us
        T_min = 0 #us
        T_max = 5000 #us      
        # for n in [2, 8]:
        #     do_dd_cpmg(nv_sig, n, step_size, T_min, T_max, do_dq_= True)
        #     do_dd_cpmg(nv_sig, n, step_size, T_min, T_max, do_dq_= False)

        
        # num_xy4_reps = 1
        # do_dd_xy4(nv_sig, num_xy4_reps, step_size, T_min, T_max)
        # num_xy8_reps = 1
        # do_dd_xy8(nv_sig, num_xy8_reps, step_size,  T_min, T_max)
        
        # pi_pulse_rep = 1
        # do_dd_cpmg(nv_sig, pi_pulse_reps, T=None)
        
        ################## 
        
        # do_determine_standard_readout_params(nv_sig)
        # do_determine_charge_readout_params(nv_sig)


    except Exception as exc:
        # Intercept the exception so we can email it out and re-raise it
        if not debug_mode:
            tool_belt.send_exception_email()
        raise exc

    finally:
        # Reset our hardware - this should be done in each routine, but
        # let's double check here
        tool_belt.reset_cfm()
        tool_belt.reset_safe_stop()