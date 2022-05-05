# -*- coding: utf-8 -*-
"""
Ramsey measruement.

This routine polarizes the nv state into 0, then applies a pi/2 pulse to
put the state into a superposition between the 0 and + or - 1 state. The state
then evolves for a time, tau, of free precesion, and then a second pi/2 pulse
is applied. The amount of population in 0 is read out by collecting the
fluorescence during a readout.

It then takes a fast fourier transform of the time data to attempt to extract
the frequencies in the ramsey experiment. If the funtion can't determine the
peaks in the fft, then a detuning is used.

Lastly, this file curve_fits the data to a triple sum of cosines using the
found frequencies.

Created on Wed Apr 24 15:01:04 2019

@author: agardill
"""

# %% Imports


import utils.tool_belt as tool_belt
import majorroutines.optimize as optimize
from scipy.signal import find_peaks
from numpy import pi
import numpy
import time
import matplotlib.pyplot as plt
from random import shuffle
import labrad
from utils.tool_belt import States
from scipy.optimize import curve_fit


# %% fit

def extract_oscillations(norm_avg_sig, precession_time_range, num_steps, detuning):
    # Create an empty array for the frequency arrays
    FreqParams = numpy.empty([3])

    # Perform the fft
    time_step = (precession_time_range[1]/1e3 - precession_time_range[0]/1e3) \
                                                    / (num_steps - 1)

    transform = numpy.fft.rfft(norm_avg_sig)
#    window = max_precession_time - min_precession_time
    freqs = numpy.fft.rfftfreq(num_steps, d=time_step)
    transform_mag = numpy.absolute(transform)

    # Plot the fft
    fig_fft, ax= plt.subplots(1, 1, figsize=(10, 8))
    ax.plot(freqs[1:], transform_mag[1:])  # [1:] excludes frequency 0 (DC component)
    ax.set_xlabel('Frequency (MHz)')
    ax.set_ylabel('FFT magnitude')
    ax.set_title('Ramsey FFT')
    fig_fft.canvas.draw()
    fig_fft.canvas.flush_events()


    # Guess the peaks in the fft. There are parameters that can be used to make
    # this more efficient
    freq_guesses_ind = find_peaks(transform_mag[1:]
                                  , prominence = 0.5
#                                  , height = 0.8
#                                  , distance = 2.2 / freq_step
                                  )

#    print(freq_guesses_ind[0])

    # Check to see if there are three peaks. If not, try the detuning passed in
    if len(freq_guesses_ind[0]) != 3:
        print('Number of frequencies found: {}'.format(len(freq_guesses_ind[0])))
#        detuning = 3 # MHz

        FreqParams[0] = detuning - 2.2
        FreqParams[1] = detuning
        FreqParams[2] = detuning + 2.2
    else:
        FreqParams[0] = freqs[freq_guesses_ind[0][0]]
        FreqParams[1] = freqs[freq_guesses_ind[0][1]]
        FreqParams[2] = freqs[freq_guesses_ind[0][2]]
        
    return fig_fft, FreqParams

def fit_ramsey(norm_avg_sig,taus,  precession_time_range, FreqParams):
    
    taus_us = numpy.array(taus)/1e3
    # Guess the other params for fitting
    amp_1 = 0.3
    amp_2 = amp_1
    amp_3 = amp_1
    decay = 1
    offset = 1

    guess_params = (offset, decay, amp_1, FreqParams[0],
                        amp_2, FreqParams[1],
                        amp_3, FreqParams[2])

    # Try the fit to a sum of three cosines

    try:
        popt,pcov = curve_fit(tool_belt.cosine_sum, taus_us, norm_avg_sig,
                      p0=guess_params,
                       bounds=(0, [numpy.infty, numpy.infty, numpy.infty, numpy.infty,
                                   numpy.infty, numpy.infty,
                                   numpy.infty, numpy.infty, ])
                      )
    except Exception:
        print('Something went wrong!')
        popt = guess_params
    print(popt)

    taus_us_linspace = numpy.linspace(precession_time_range[0]/1e3, precession_time_range[1]/1e3,
                          num=1000)

    fig_fit, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.plot(taus_us, norm_avg_sig,'b',label='data')
    ax.plot(taus_us_linspace, tool_belt.cosine_sum(taus_us_linspace,*popt),'r',label='fit')
    ax.set_xlabel('Free precesion time (ns)')
    ax.set_ylabel('Contrast (arb. units)')
    ax.legend()
    text1 = "\n".join((r'$C + e^{-t/d} [a_1 \mathrm{cos}(2 \pi \nu_1 t) + a_2 \mathrm{cos}(2 \pi \nu_2 t) + a_3 \mathrm{cos}(2 \pi \nu_3 t)]$',
                       r'$d = $' + '%.2f'%(abs(popt[1])) + ' us',
                       r'$\nu_1 = $' + '%.2f'%(popt[3]) + ' MHz',
                       r'$\nu_2 = $' + '%.2f'%(popt[5]) + ' MHz',
                       r'$\nu_3 = $' + '%.2f'%(popt[7]) + ' MHz'
                       ))
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)

    ax.text(0.40, 0.25, text1, transform=ax.transAxes, fontsize=12,
                            verticalalignment="top", bbox=props)



#  Plot the data itself and the fitted curve

    fig_fit.canvas.draw()
#    fig.set_tight_layout(True)
    fig_fit.canvas.flush_events()
    
    return fig_fit

# %% Main


def main(
    nv_sig,
    apd_indices,
    detuning,
    precession_dur_range,
    num_steps,
    num_reps,
    num_runs,
    state=States.LOW,
    opti_nv_sig = None
):

    with labrad.connect() as cxn:
        angle = main_with_cxn(
            cxn,
            nv_sig,
            apd_indices,
    detuning,
            precession_dur_range,
            num_steps,
            num_reps,
            num_runs,
            state,
            opti_nv_sig
        )
        return angle


def main_with_cxn(
    cxn,
    nv_sig,
    apd_indices,
    detuning,
    precession_time_range,
    num_steps,
    num_reps,
    num_runs,
    state=States.LOW,
    opti_nv_sig = None
):

    tool_belt.reset_cfm(cxn)

    # %% Sequence setup

    laser_key = "spin_laser"
    laser_name = nv_sig[laser_key]
    tool_belt.set_filter(cxn, nv_sig, laser_key)
    laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)
    polarization_time = nv_sig["spin_pol_dur"]
    gate_time = nv_sig["spin_readout_dur"]

    rabi_period = nv_sig["rabi_{}".format(state.name)]
    uwave_freq = nv_sig["resonance_{}".format(state.name)]
    uwave_power = nv_sig["uwave_power_{}".format(state.name)]
    # Detune the pi/2 pulse frequency
    uwave_freq_detuned = uwave_freq + detuning / 10**3

    # Get pulse frequencies
    uwave_pi_pulse = 0
    uwave_pi_on_2_pulse = tool_belt.get_pi_on_2_pulse_dur(rabi_period)

    seq_file_name = "spin_echo.py"

    # %% Create the array of relaxation times

    # Array of times to sweep through
    # Must be ints
    min_precession_time = int(precession_time_range[0])
    max_precession_time = int(precession_time_range[1])

    taus = numpy.linspace(
        min_precession_time,
        max_precession_time,
        num=num_steps,
        dtype=numpy.int32,
    )

    # %% Fix the length of the sequence to account for odd amount of elements

    # Our sequence pairs the longest time with the shortest time, and steps
    # toward the middle. This means we only step through half of the length
    # of the time array.

    # That is a problem if the number of elements is odd. To fix this, we add
    # one to the length of the array. When this number is halfed and turned
    # into an integer, it will step through the middle element.

    if len(taus) % 2 == 0:
        half_length_taus = int(len(taus) / 2)
    elif len(taus) % 2 == 1:
        half_length_taus = int((len(taus) + 1) / 2)

    # Then we must use this half length to calculate the list of integers to be
    # shuffled for each run

    tau_ind_list = list(range(0, half_length_taus))

    # %% Create data structure to save the counts

    # We create an array of NaNs that we'll fill
    # incrementally for the signal and reference counts.
    # NaNs are ignored by matplotlib, which is why they're useful for us here.
    # We define 2D arrays, with the horizontal dimension for the frequency and
    # the veritical dimension for the index of the run.

    sig_counts = numpy.zeros([num_runs, num_steps])
    sig_counts[:] = numpy.nan
    ref_counts = numpy.copy(sig_counts)

    # %% Make some lists and variables to save at the end

    opti_coords_list = []
    tau_index_master_list = [[] for i in range(num_runs)]

    # %% Analyze the sequence

    seq_args = [
        min_precession_time/2,
        polarization_time,
        gate_time,
        uwave_pi_pulse,
        uwave_pi_on_2_pulse,
        max_precession_time/2,
        apd_indices[0],
        state.value,
        laser_name,
        laser_power,
    ]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    ret_vals = cxn.pulse_streamer.stream_load(seq_file_name, seq_args_string)
    seq_time = ret_vals[0]
    #    print(seq_args)
    #    return
    #    print(seq_time)

    # %% Let the user know how long this will take

    seq_time_s = seq_time / (10 ** 9)  # to seconds
    expected_run_time_s = (
        (num_steps / 2) * num_reps * num_runs * seq_time_s
    )  # s
    expected_run_time_m = expected_run_time_s / 60  # to minutes

    print(" \nExpected run time: {:.1f} minutes. ".format(expected_run_time_m))
    #    return

    # %% Get the starting time of the function, to be used to calculate run time

    startFunctionTime = time.time()
    start_timestamp = tool_belt.get_time_stamp()

    # %% Collect the data

    # Start 'Press enter to stop...'
    tool_belt.init_safe_stop()

    for run_ind in range(num_runs):

        print(" \nRun index: {}".format(run_ind))

        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break

        # Optimize and save the coords we found
        if opti_nv_sig:
            opti_coords = optimize.main_with_cxn(cxn, opti_nv_sig, apd_indices)
            drift = tool_belt.get_drift()
            adj_coords = nv_sig['coords'] + numpy.array(drift)
            tool_belt.set_xyz(cxn, adj_coords)
        else:
            opti_coords = optimize.main_with_cxn(cxn, nv_sig, apd_indices)
        opti_coords_list.append(opti_coords)

        # Set up the microwaves
        sig_gen_cxn = tool_belt.get_signal_generator_cxn(cxn, state)
        sig_gen_cxn.set_freq(uwave_freq_detuned)
        sig_gen_cxn.set_amp(uwave_power)
        sig_gen_cxn.uwave_on()

        # Set up the laser
        tool_belt.set_filter(cxn, nv_sig, laser_key)
        laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)

        # Load the APD
        apd_server = tool_belt.get_apd_server(cxn)
        apd_server_name = tool_belt.get_registry_entry(cxn, "apd_server", ["", "Config", "Counter"])
        
        if apd_server_name == 'apd_tagger':
            apd_server.start_tag_stream(apd_indices)
            n_apd_samples = 1

        # Shuffle the list of tau indices so that it steps thru them randomly
        shuffle(tau_ind_list)

        for tau_ind in tau_ind_list:

            # 'Flip a coin' to determine which tau (long/shrt) is used first
            rand_boolean = numpy.random.randint(0, high=2)

            if rand_boolean == 1:
                tau_ind_first = tau_ind
                tau_ind_second = -tau_ind - 1
            elif rand_boolean == 0:
                tau_ind_first = -tau_ind - 1
                tau_ind_second = tau_ind

            # add the tau indexxes used to a list to save at the end
            tau_index_master_list[run_ind].append(tau_ind_first)
            tau_index_master_list[run_ind].append(tau_ind_second)

            # Break out of the while if the user says stop
            if tool_belt.safe_stop():
                break

            print(" \nFirst relaxation time: {}".format(taus[tau_ind_first]))
            print("Second relaxation time: {}".format(taus[tau_ind_second]))

            seq_args = [
                taus[tau_ind_first]/2,
                polarization_time,
                gate_time,
                uwave_pi_pulse,
                uwave_pi_on_2_pulse,
                taus[tau_ind_second]/2,
                apd_indices[0],
                state.value,
                laser_name,
                laser_power,
            ]
            seq_args_string = tool_belt.encode_seq_args(seq_args)
            # Clear the tagger buffer of any excess counts
            apd_server.clear_buffer()
            cxn.pulse_streamer.stream_immediate(
                seq_file_name, num_reps, seq_args_string
            )

            if apd_server_name == 'apd_daq':
                apd_server.load_stream_reader(apd_indices[0], seq_time,  int(4*num_reps))
                n_apd_samples = int(4*num_reps)
                
            # Each sample is of the form [*(<sig_shrt>, <ref_shrt>, <sig_long>, <ref_long>)]
            # So we can sum on the values for similar index modulus 4 to
            # parse the returned list into what we want.
            new_counts = apd_server.read_counter_separate_gates(n_apd_samples)
            sample_counts = new_counts[0]

            count = sum(sample_counts[0::4])
            sig_counts[run_ind, tau_ind_first] = count
            print("First signal = " + str(count))

            count = sum(sample_counts[1::4])
            ref_counts[run_ind, tau_ind_first] = count
            print("First Reference = " + str(count))

            count = sum(sample_counts[2::4])
            sig_counts[run_ind, tau_ind_second] = count
            print("Second Signal = " + str(count))

            count = sum(sample_counts[3::4])
            ref_counts[run_ind, tau_ind_second] = count
            print("Second Reference = " + str(count))

        apd_server.stop_tag_stream()

        # %% Save the data we have incrementally for long T1s

        raw_data = {
            "start_timestamp": start_timestamp,
            "nv_sig": nv_sig,
            "nv_sig-units": tool_belt.get_nv_sig_units(),
            'detuning': detuning,
            'detuning-units': 'MHz',
            "gate_time": gate_time,
            "gate_time-units": "ns",
            "uwave_freq": uwave_freq_detuned,
            "uwave_freq-units": "GHz",
            "uwave_power": uwave_power,
            "uwave_power-units": "dBm",
            "rabi_period": rabi_period,
            "rabi_period-units": "ns",
            "uwave_pi_on_2_pulse": uwave_pi_on_2_pulse,
            "uwave_pi_on_2_pulse-units": "ns",
            "precession_time_range": precession_time_range,
            "precession_time_range-units": "ns",
            "state": state.name,
            "num_steps": num_steps,
            "num_reps": num_reps,
            "run_ind": run_ind,
            "tau_index_master_list": tau_index_master_list,
            "opti_coords_list": opti_coords_list,
            "opti_coords_list-units": "V",
            "taus": taus.tolist(),
            "taus-units": 'ns',
            "sig_counts": sig_counts.astype(int).tolist(),
            "sig_counts-units": "counts",
            "ref_counts": ref_counts.astype(int).tolist(),
            "ref_counts-units": "counts",
        }

        # This will continuously be the same file path so we will overwrite
        # the existing file with the latest version
        file_path = tool_belt.get_file_path(
            __file__, start_timestamp, nv_sig["name"], "incremental"
        )
        tool_belt.save_raw_data(raw_data, file_path)

    # %% Hardware clean up

    tool_belt.reset_cfm(cxn)

    # %% Average the counts over the iterations

    avg_sig_counts = numpy.average(sig_counts, axis=0)
    avg_ref_counts = numpy.average(ref_counts, axis=0)

    # %% Calculate the ramsey data, signal / reference over different
    # relaxation times

    # Replace x/0=inf with 0
    try:
        norm_avg_sig = avg_sig_counts / avg_ref_counts
    except RuntimeWarning as e:
        print(e)
        inf_mask = numpy.isinf(norm_avg_sig)
        # Assign to 0 based on the passed conditional array
        norm_avg_sig[inf_mask] = 0

    # %% Plot the data

    raw_fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))

    ax = axes_pack[0]
    # Account for the pi/2 pulse on each side of a tau
    plot_taus = (taus + uwave_pi_pulse) / 1000
    ax.plot(plot_taus, avg_sig_counts, "r-", label="signal")
    ax.plot(plot_taus, avg_ref_counts, "g-", label="reference")
    ax.set_xlabel(r"$\tau + \pi$ ($\mathrm{\mu s}$)")
    ax.set_ylabel("Counts")
    ax.legend()

    ax = axes_pack[1]
    ax.plot(plot_taus, norm_avg_sig, "b-")
    ax.set_title("Ramsey Measurement")
    ax.set_xlabel(r"$\tau$ ($\mathrm{\mu s}$)")
    ax.set_ylabel("Contrast (arb. units)")

    raw_fig.canvas.draw()
    raw_fig.set_tight_layout(True)
    raw_fig.canvas.flush_events()

    # %% Save the data

    endFunctionTime = time.time()

    timeElapsed = endFunctionTime - startFunctionTime

    timestamp = tool_belt.get_time_stamp()

    raw_data = {
        "timestamp": timestamp,
        "timeElapsed": timeElapsed,
        "nv_sig": nv_sig,
        "nv_sig-units": tool_belt.get_nv_sig_units(),
        'detuning': detuning,
        'detuning-units': 'MHz',
        "gate_time": gate_time,
        "gate_time-units": "ns",
        "uwave_freq": uwave_freq_detuned,
        "uwave_freq-units": "GHz",
        "uwave_power": uwave_power,
        "uwave_power-units": "dBm",
        "rabi_period": rabi_period,
        "rabi_period-units": "ns",
        "uwave_pi_on_2_pulse": uwave_pi_on_2_pulse,
        "uwave_pi_on_2_pulse-units": "ns",
        "precession_time_range": precession_time_range,
        "precession_time_range-units": "ns",
        "state": state.name,
        "num_steps": num_steps,
        "num_reps": num_reps,
        "num_runs": num_runs,
        "tau_index_master_list": tau_index_master_list,
        "opti_coords_list": opti_coords_list,
        "opti_coords_list-units": "V",
        "taus": taus.tolist(),
        "taus-units": 'ns',
        "sig_counts": sig_counts.astype(int).tolist(),
        "sig_counts-units": "counts",
        "ref_counts": ref_counts.astype(int).tolist(),
        "ref_counts-units": "counts",
        "norm_avg_sig": norm_avg_sig.astype(float).tolist(),
        "norm_avg_sig-units": "arb",
    }

    file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig["name"])
    tool_belt.save_figure(raw_fig, file_path)
    tool_belt.save_raw_data(raw_data, file_path)

    # %% Fit and save figs
    
    # Fourier transform
    fig_fft, FreqParams = extract_oscillations(norm_avg_sig, 
                               precession_time_range, num_steps, detuning)
    
    # Save the fft figure
    tool_belt.save_figure(fig_fft, file_path + '_fft')
    
    # Fit actual data
    fig_fit = fit_ramsey(norm_avg_sig,taus,  precession_time_range, FreqParams)

    # Save the file in the same file directory
    tool_belt.save_figure(fig_fit, file_path + '-fit')

    return 


# %% Run the file


if __name__ == "__main__":


    folder = "pc_rabi/branch_master/ramsey/2021_10"
    file = '2021_10_15-10_37_22-johnson-nv0_2021_10_08'
    
    # detuning = 0
    data = tool_belt.get_raw_data(file, folder)
    detuning= data['detuning']
    norm_avg_sig = data['norm_avg_sig']
    precession_time_range = data['precession_time_range']
    num_steps = data['num_steps']
    try:
        taus = data['taus']
    except Exception:
        
        taus = numpy.linspace(
            precession_time_range[0],
            precession_time_range[1],
            num=num_steps,
        )
        
        
    _, FreqParams = extract_oscillations(norm_avg_sig, precession_time_range, num_steps, detuning)
    print(FreqParams)

    fit_ramsey(norm_avg_sig,taus,  precession_time_range, [2.4, 4.5, 6.9])
