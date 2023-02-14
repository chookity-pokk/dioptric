# -*- coding: utf-8 -*-
"""
Electron spin resonance routine. Scans the microwave frequency, taking counts
at each point.

Created on April 11th, 2019

@author: mccambria
"""

import utils.tool_belt as tool_belt
import utils.kplotlib as kpl
from utils.kplotlib import KplColors
import majorroutines.optimize as optimize
import numpy as np
import matplotlib.pyplot as plt
import time
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
import labrad
from utils.tool_belt import States, NormStyle
from random import shuffle
import sys
from utils.positioning import get_scan_1d as calculate_freqs
from pathlib import Path


# region Plotting


def create_fit_figure(
    freq_center,
    freq_range,
    num_steps,
    norm_avg_sig,
    norm_avg_sig_ste,
    fit_func=None,
    popt=None,
    guess_params=None,
):
    """Create a figure showing the normalized average signal and the fit. If you pass
    fit_func and popt, then no actual fit will be performed - we'll just plot the passed
    fit_func and popt

    Parameters
    ----------
    freq_center : numeric
        Center of the frequency range used in the ESR scan
    freq_range : numeric
        Frequency range of the ESR scan
    num_steps : numeric
        Number of steps in the ESR scan
    norm_avg_sig : 1D array
        Normalized average signal
    norm_avg_sig_ste : 1D array
        Standard error of the normalized average signal
    fit_func : Function, optional
        Function used to fit the data. If None, we will use a default fit function - either
        a single or double Rabi line depending on how many dips are apparent in the data
    popt : 1D array, optional
        Fit parameters for the fit function. If None, the fit function will be fit
        to the data
    guess_params : 1D array, optional
        Guess parameters for fitting the fit function to the data. If None,
        we will estimate fit parameters by inspecting the data before actually fitting

    Returns
    -------
    matplotlib.figure.Figure
    matplotlib.axes.Axes
    Function
        Function used to fit the data
    1D array
        Fit parameters for the fit function
    2D array
        Covariance matrix of the fit
    """

    # Fitting
    if (fit_func is None) or (popt is None):
        fit_func, popt, pcov = fit_resonance(
            freq_center,
            freq_range,
            num_steps,
            norm_avg_sig,
            norm_avg_sig_ste,
            fit_func,
            guess_params,
        )
    else:
        pcov = None

    # Plot setup
    fig, ax = plt.subplots()
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Normalized fluorescence")
    freqs = calculate_freqs(freq_center, freq_range, num_steps)
    smooth_freqs = calculate_freqs(freq_center, freq_range, 1000)

    # Plotting
    if norm_avg_sig_ste is not None:
        kpl.plot_points(ax, freqs, norm_avg_sig, yerr=norm_avg_sig_ste)
    else:
        kpl.plot_line(ax, freqs, norm_avg_sig)
    kpl.plot_line(
        ax,
        smooth_freqs,
        fit_func(smooth_freqs, *popt),
        color=KplColors.RED,
    )

    # Text boxes to describe the fits
    low_text = None
    high_text = None
    base_text = "A = {:.3f} \nwidth = {:.1f} MHz \nf = {:.4f} GHz"
    if len(popt) == 3:
        contrast, hwhm, freq = popt[0:3]
        low_text = base_text.format(contrast, hwhm, freq)
        high_text = None
    elif len(popt) == 6:
        contrast, hwhm, freq = popt[0:3]
        low_text = base_text.format(contrast, hwhm, freq)
        contrast, hwhm, freq = popt[3:6]
        high_text = base_text.format(contrast, hwhm, freq)
        print(popt[2])
        print(np.sqrt(pcov[2][2]))
        print(popt[5])
        print(np.sqrt(pcov[5][5]))
    size = kpl.Size.SMALL
    if low_text is not None:
        kpl.anchored_text(ax, low_text, kpl.Loc.LOWER_LEFT, size=size)
    if high_text is not None:
        kpl.anchored_text(ax, high_text, kpl.Loc.LOWER_RIGHT, size=size)

    return fig, ax, fit_func, popt, pcov


def create_raw_data_figure(
    freq_center,
    freq_range,
    num_steps,
    sig_counts_avg_kcps=None,
    ref_counts_avg_kcps=None,
    norm_avg_sig=None,
    magnet_angle= None,
):
    """Create a 2-panel figure showing the raw data (signal and reference) as well as the
    normalized average signal

    Parameters
    ----------
    freq_center : numeric
        Center of the frequency range used in the ESR scan
    freq_range : numeric
        Frequency range of the ESR scan
    num_steps : numeric
        Number of steps in the ESR scan
    sig_counts_avg_kcps : 1D array, optional
        Average signal count rate in kcps
    ref_counts_avg_kcps : 1D array, optional
        Average reference count rate in kcps
    norm_avg_sig : 1D array, optional
        Normalized average signal

    Returns
    -------
    matplotlib.figure.Figure
    matplotlib.axes.Axes
        Ax for the signal and reference plot
    matplotlib.axes.Axes
        Ax for the normalized average signal plot
    """

    # Plot setup
    fig, axes_pack = plt.subplots(1, 2, figsize=kpl.double_figsize)
    ax_sig_ref, ax_norm = axes_pack
    ax_sig_ref.set_xlabel("Frequency (GHz)")
    ax_sig_ref.set_ylabel("Count rate (kcps)")
    ax_norm.set_xlabel("Frequency (GHz)")
    ax_norm.set_ylabel("Normalized fluorescence")
    freqs = calculate_freqs(freq_center, freq_range, num_steps)

    # Plotting
    if sig_counts_avg_kcps is None:
        sig_counts_avg_kcps = np.empty(num_steps)
        sig_counts_avg_kcps[:] = np.nan
    kpl.plot_line(
        ax_sig_ref, freqs, sig_counts_avg_kcps, label="Signal", color=KplColors.GREEN
    )
    if ref_counts_avg_kcps is None:
        ref_counts_avg_kcps = np.empty(num_steps)
        ref_counts_avg_kcps[:] = np.nan
    kpl.plot_line(
        ax_sig_ref, freqs, ref_counts_avg_kcps, label="Reference", color=KplColors.RED
    )
    ax_sig_ref.legend(loc=kpl.Loc.LOWER_RIGHT)
    if norm_avg_sig is None:
        norm_avg_sig = np.empty(num_steps)
        norm_avg_sig[:] = np.nan
    kpl.plot_line(ax_norm, freqs, norm_avg_sig, color=KplColors.BLUE)

    if magnet_angle:
        kpl.anchored_text(ax_norm, '{} deg'.format(magnet_angle), kpl.Loc.LOWER_RIGHT, size=kpl.Size.SMALL)
    return fig, ax_sig_ref, ax_norm


# endregion
# region Math functions


def rabi_line(freq, constrast, rabi_freq, res_freq):
    """Lineshape for PESR under a pi pulse for the actual resonant frequency"""

    rabi_freq_ghz = rabi_freq / 1000
    detuning = freq - res_freq
    effective_rabi_freq = np.sqrt(detuning**2 + rabi_freq_ghz**2)
    effective_contrast = constrast * ((rabi_freq_ghz / effective_rabi_freq) ** 2)
    pulse_dur = np.pi / rabi_freq_ghz  # Assumed
    return effective_contrast * np.sin(effective_rabi_freq * pulse_dur / 2) ** 2


def rabi_line_hyperfine(freq, constrast, rabi_freq, res_freq):
    """Sum of 3 Rabi lineshapes separated by hyperfine splitting for N14"""

    hyperfine = 2.14 / 1000  # Hyperfine in GHz
    val = (1 / 3) * (
        rabi_line(freq, constrast, rabi_freq, res_freq - hyperfine)
        + rabi_line(freq, constrast, rabi_freq, res_freq)
        + rabi_line(freq, constrast, rabi_freq, res_freq + hyperfine)
    )
    return val


def gaussian(freq, constrast, sigma, center):
    sigma_ghz = sigma / 1000
    return constrast * np.exp(-((freq - center) ** 2) / (2 * (sigma_ghz**2)))


def lorentzian(freq, constrast, hwhm, center):
    """Normalized that the value at the center is the contrast"""
    hwhm_ghz = hwhm / 1000
    return constrast * (hwhm_ghz**2) / ((freq - center) ** 2 + hwhm_ghz**2)


def double_dip(
    freq,
    low_contrast,
    low_width,
    low_center,
    high_contrast,
    high_width,
    high_center,
    dip_func=rabi_line,
):
    low_dip = dip_func(freq, low_contrast, low_width, low_center)
    high_dip = dip_func(freq, high_contrast, high_width, high_center)
    return 1.0 - (low_dip + high_dip)


def single_dip(freq, contrast, width, center, dip_func=rabi_line):
    return 1.0 - dip_func(freq, contrast, width, center)


# endregion
# region Analysis functions


def return_res_with_error(data, fit_func=None, guess_params=None):
    """Returns the frequency/error of the resonance in a spectrum.
    Intended for extracting the frequency/error of a single resonance -
    if there's a double, we'll return the average. data should be some
    completed experiment file's raw data dictionary
    """

    freq_center = data["freq_center"]
    freq_range = data["freq_range"]
    num_steps = data["num_steps"]
    ref_counts = data["ref_counts"]
    sig_counts = data["sig_counts"]
    num_reps = data["num_reps"]
    nv_sig = data["nv_sig"]
    readout = nv_sig["spin_readout_dur"]
    try:
        norm_style = NormStyle[str.upper(nv_sig["norm_style"])]
    except Exception as exc:
        # norm_style = NormStyle.POINT_TO_POINT
        norm_style = NormStyle.SINGLE_VALUED

    _, _, norm_avg_sig, norm_avg_sig_ste = tool_belt.process_counts(
        sig_counts, ref_counts, num_reps, readout, norm_style
    )

    fit_func, popt, pcov = fit_resonance(
        freq_center,
        freq_range,
        num_steps,
        norm_avg_sig,
        norm_avg_sig_ste,
        fit_func,
        guess_params,
    )

    if len(popt) == 6:
        # print("Double resonance")
        low_res_ind = 2
        high_res_ind = low_res_ind + 3
        avg_res = (popt[low_res_ind] + popt[high_res_ind]) / 2
        low_res_err = np.sqrt(pcov[low_res_ind, low_res_ind])
        hig_res_err = np.sqrt(pcov[high_res_ind, high_res_ind])
        avg_res_err = np.sqrt(low_res_err**2 + hig_res_err**2) / 2
        return avg_res, avg_res_err
    else:
        # print("Single resonance")
        res_ind = 2
        # res_ind = 1  # MCC sigma
        res = popt[res_ind]
        res_err = np.sqrt(pcov[res_ind, res_ind])
        return res, res_err


def get_guess_params(
    freq_center, freq_range, num_steps, norm_avg_sig, norm_avg_sig_ste
):
    """Get guess params for line fitting. Most importantly how many resonances and what
    their frequencies are
    """

    # Setup for scipy's peak finding algorithm
    freqs = calculate_freqs(freq_center, freq_range, num_steps)
    inverted_norm_avg_sig = 1 - norm_avg_sig

    hwhm = 0.004  # GHz
    hwhm_mhz = hwhm * 1000
    fwhm = 2 * hwhm

    # Convert to index space
    fwhm_ind = fwhm * (num_steps / freq_range)
    if fwhm_ind < 1:
        fwhm_ind = 1

    # Peaks should have an SNR of at least 3
    height = 3 * np.average(norm_avg_sig_ste)

    # Peaks must be separated from each other by the estimated fwhm (rayleigh
    # criteria), have a contrast of at least the noise or 5% (whichever is
    # greater), and have a width of at least two points
    peak_inds, details = find_peaks(
        inverted_norm_avg_sig, distance=fwhm_ind, height=height, width=2
    )
    peak_inds = peak_inds.tolist()
    peak_heights = details["peak_heights"].tolist()

    low_freq_guess = None
    high_freq_guess = None

    if len(peak_heights) == 0:
        fit_func = single_dip
        guess_params = [height, hwhm_mhz, freq_center]
        return fit_func, guess_params

    # Find the location of the highest peak
    max_peak_height = max(peak_heights)
    max_peak_peak_ind = peak_heights.index(max_peak_height)
    max_peak_freq = freqs[peak_inds[max_peak_peak_ind]]

    if len(peak_inds) > 1:

        # Remove what we just found so we can find the second highest peak
        peak_inds.pop(max_peak_peak_ind)
        peak_heights.pop(max_peak_peak_ind)

        # Find the location of the next highest peak
        next_max_peak_height = max(peak_heights)
        next_max_peak_peak_inds = peak_heights.index(
            next_max_peak_height
        )  # Index in peak_inds
        next_max_peak_freq = freqs[peak_inds[next_max_peak_peak_inds]]

        # Only keep the smaller peak if it's at least 50% the height of the larger peak
        if next_max_peak_height > 0.5 * max_peak_height:
            # Sort by frequency
            if max_peak_freq < next_max_peak_freq:
                low_freq_guess = max_peak_freq
                high_freq_guess = next_max_peak_freq
                low_contrast_guess = max_peak_height
                high_contrast_guess = next_max_peak_height
            else:
                low_freq_guess = next_max_peak_freq
                high_freq_guess = max_peak_freq
                low_contrast_guess = next_max_peak_height
                high_contrast_guess = max_peak_height
        else:
            low_freq_guess = max_peak_freq
            low_contrast_guess = max_peak_height
            high_freq_guess = None

    elif len(peak_inds) == 1:
        low_freq_guess = max_peak_freq
        high_freq_guess = None
        low_contrast_guess = max_peak_height
    else:
        # print("Could not locate peaks, using center frequency")
        low_freq_guess = freq_center
        high_freq_guess = None
        low_contrast_guess = height

    # Returns
    if low_freq_guess is None:
        return None, None
    if high_freq_guess is None:
        fit_func = single_dip
        guess_params = [low_contrast_guess, hwhm_mhz, low_freq_guess]
    else:
        fit_func = double_dip
        guess_params = [
            low_contrast_guess,
            hwhm_mhz,
            low_freq_guess,
            high_contrast_guess,
            hwhm_mhz,
            high_freq_guess,
        ]
    return fit_func, guess_params


def fit_resonance(
    freq_center,
    freq_range,
    num_steps,
    norm_avg_sig,
    norm_avg_sig_ste,
    fit_func=None,
    guess_params=None,
):
    """_summary_

    Parameters
    ----------
    freq_center : numeric
        Center of the frequency range used in the ESR scan
    freq_range : numeric
        Frequency range of the ESR scan
    num_steps : numeric
        Number of steps in the ESR scan
    norm_avg_sig : 1D array
        Normalized average signal
    norm_avg_sig_ste : 1D array
        Standard error of the normalized average signal
    fit_func : Function, optional
        Function used to fit the data. If None, we will use a default fit function - either
        a single or double Rabi line depending on how many dips are apparent in the data
    guess_params : 1D array, optional
        Guess parameters for fitting the fit function to the data. If None,
        we will estimate fit parameters by inspecting the data before actually fitting

    Returns
    -------
    Function
        Function used to fit the data
    1D array
        Fit parameters for the fit function
    2D array
        Covariance matrix of the fit
    """

    freqs = calculate_freqs(freq_center, freq_range, num_steps)

    # Guess the fit function and params if not provided
    if (fit_func is None) or (guess_params is None):
        algo_fit_func, algo_guess_params = get_guess_params(
            freq_center, freq_range, num_steps, norm_avg_sig, norm_avg_sig_ste
        )
    if fit_func is None:
        fit_func = algo_fit_func
    if guess_params is None:
        guess_params = algo_guess_params

    popt, pcov = curve_fit(
        fit_func,
        freqs,
        norm_avg_sig,
        p0=guess_params,
        sigma=norm_avg_sig_ste,
        absolute_sigma=True,
    )

    return fit_func, popt, pcov


# endregion
# region Control panel functions


def state(
    nv_sig,
    state,
    freq_range,
    num_steps,
    num_reps,
    num_runs,
    composite=False,
    opti_nv_sig=None,
):
    """Same as main, but the center frequency, microwave power, and pulse duration are taken from nv_sig"""

    freq_center = nv_sig["resonance_{}".format(state.name)]
    uwave_power = nv_sig["uwave_power_{}".format(state.name)]
    uwave_pulse_dur = tool_belt.get_pi_pulse_dur(nv_sig[f"rabi_{state.name}"])

    return main(
        nv_sig,
        freq_center,
        freq_range,
        num_steps,
        num_reps,
        num_runs,
        uwave_power,
        uwave_pulse_dur,
        state,
        composite,
        opti_nv_sig,
    )


def main(
    nv_sig,
    freq_center,
    freq_range,
    num_steps,
    num_reps,
    num_runs,
    uwave_power,
    uwave_pulse_dur,
    state=States.HIGH,
    composite=False,
    opti_nv_sig=None,
):
    """Pulsed electron spin resonance measurement

    Parameters
    ----------
    nv_sig : dict
        Dictionary with the properties of the NV to work with
    freq_center : numeric
        Center of the frequency range used in the ESR scan
    freq_range : numeric
        Frequency range of the ESR scan
    num_steps : numeric
        Number of steps in the ESR scan
    num_reps : int
        Number of times to repeat each experiment at each frequency per run
    num_runs : int
        Number of times to scan through the frequencies under test
    uwave_power : float
        Microwave power to set in dBm
    uwave_pulse_dur : int
        Microwave pulse duration in ns
    state : States(enum), optional
        Determines which signal generator to use, by default States.HIGH
    composite : bool, optional
        Use a Knill composite pulse? By default False
    opti_nv_sig : _type_, optional
        nv to optimize on - useful if you're working with a troublesome NV.
        If None, just use the initial passed nv_sig

    Returns single_res, data_file_name, [low_freq, high_freq]
    -------
    float
        Single-valued resonance (GHz) - may be incorrect if there are multiple resonances
    str
        Extension-less name of the data file generated
    list
        list containing the low frequency resonance (GHz) and the high frequency resonance if
        there is one - may be incorrect if there are more than 2 resonances
    """

    with labrad.connect() as cxn:
        return main_with_cxn(
            cxn,
            nv_sig,
            freq_center,
            freq_range,
            num_steps,
            num_reps,
            num_runs,
            uwave_power,
            uwave_pulse_dur,
            state,
            composite,
            opti_nv_sig,
        )


def main_with_cxn(
    cxn,
    nv_sig,
    freq_center,
    freq_range,
    num_steps,
    num_reps,
    num_runs,
    uwave_power,
    uwave_pulse_dur,
    state=States.HIGH,
    composite=False,
    opti_nv_sig=None,
):

    ### Setup

    start_timestamp = tool_belt.get_time_stamp()

    kpl.init_kplotlib()

    counter = tool_belt.get_server_counter(cxn)
    pulse_gen = tool_belt.get_server_pulse_gen(cxn)
    arbwavegen_server = tool_belt.get_server_arb_wave_gen(cxn)

    tool_belt.reset_cfm(cxn)

    # check if running external iq_mod with SRS
    iq_key = False
    if "uwave_iq_{}".format(state.name) in nv_sig:
        iq_key = nv_sig["uwave_iq_{}".format(state.name)]
    # Set up our data structure, an array of NaNs that we'll fill
    # incrementally. NaNs are ignored by matplotlib, which is why they're
    # useful for us here.
    norm_style = nv_sig["norm_style"]
    polarization_time = nv_sig["spin_pol_dur"]
    readout = nv_sig["spin_readout_dur"]

    laser_key = "spin_laser"
    laser_name = nv_sig[laser_key]
    laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)

    freqs = calculate_freqs(freq_center, freq_range, num_steps)

    # Set up our data structure, an array of NaNs that we'll fill incrementally.
    # NaNs are ignored by matplotlib, which is why they're useful for us here.
    # We define 2D arrays, with the horizontal dimension for the frequency and
    # the veritical dimension for the index of the run.
    ref_counts = np.empty([num_runs, num_steps])
    ref_counts[:] = np.nan
    sig_counts = np.copy(ref_counts)

    # Sequence processing
    if composite:
        rabi_period = nv_sig[f"rabi_{state.name}"]
        pi_pulse = tool_belt.get_pi_pulse_dur(rabi_period)
        pi_on_2_pulse = tool_belt.get_pi_on_2_pulse_dur(rabi_period)
        seq_args = [
            polarization_time,
            readout,
            pi_pulse,
            pi_on_2_pulse,
            1,
            1,
            state.value,
            laser_name,
            laser_power,
        ]
        seq_args = [int(el) for el in seq_args]
        seq_name = "discrete_rabi2.py"
    else:
        seq_args = [
            uwave_pulse_dur,
            polarization_time,
            readout,
            uwave_pulse_dur,
            state.value,
            laser_name,
            laser_power,
        ]
        seq_name = "rabi.py"
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    # print(seq_args)

    opti_coords_list = []

    # Create raw data figure for incremental plotting
    raw_fig, ax_sig_ref, ax_norm = create_raw_data_figure(
        freq_center, freq_range, num_steps,
        magnet_angle = nv_sig['magnet_angle']
    )
    # Set up a run indicator for incremental plotting
    run_indicator_text = "Run #{}/{}"
    text = run_indicator_text.format(0, num_runs)
    run_indicator_obj = kpl.anchored_text(ax_norm, text, loc=kpl.Loc.UPPER_RIGHT)

    ### Collect the data

    # Create a list of indices to step through the freqs. This will be shuffled
    freq_index_master_list = [[] for i in range(num_runs)]
    freq_ind_list = list(range(0, num_steps))

    start_timestamp = tool_belt.get_time_stamp()

    # Start 'Press enter to stop...'
    tool_belt.init_safe_stop()

    for run_ind in range(num_runs):
        print("Run index: {}".format(run_ind))

        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break

        # Optimize and save the coords we found
        if opti_nv_sig:
            ret_vals = optimize.main_with_cxn(cxn, opti_nv_sig)
            opti_coords = ret_vals[0]
        else:
            opti_coords = optimize.main_with_cxn(cxn, nv_sig)
        opti_coords_list.append(opti_coords)

        # Set up the microwaves and laser. Then load the pulse streamer
        # (must happen after optimize and iq_switch since run their
        # own sequences)
        sig_gen_cxn = tool_belt.get_server_sig_gen(cxn, state)
        sig_gen_cxn.set_amp(uwave_power)
        if iq_key:
            sig_gen_cxn.load_iq()
        # arbwavegen_server.load_arb_phases([0])
        if composite:
            sig_gen_cxn.load_iq()
            arbwavegen_server.load_knill()
        sig_gen_cxn.uwave_on()
        tool_belt.set_filter(cxn, nv_sig, laser_key)
        laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)

        pulse_gen.stream_load(seq_name, seq_args_string)
        counter.start_tag_stream()

        # Take a sample and step through the shuffled frequencies
        shuffle(freq_ind_list)
        for freq_ind in freq_ind_list:

            # Break out of the while if the user says stop
            if tool_belt.safe_stop():
                break

            freq_index_master_list[run_ind].append(freq_ind)
            sig_gen_cxn.set_freq(freqs[freq_ind])
            counter.clear_buffer()
            pulse_gen.stream_start(int(num_reps))

            # Get and write the counts
            new_counts = counter.read_counter_modulo_gates(2, 1)
            sample_counts = new_counts[0]
            cur_run_sig_counts_summed = sample_counts[0]
            cur_run_ref_counts_summed = sample_counts[1]
            sig_counts[run_ind, freq_ind] = cur_run_sig_counts_summed
            ref_counts[run_ind, freq_ind] = cur_run_ref_counts_summed

        counter.stop_tag_stream()

        ### Incremental plotting

        # Update the run indicator
        text = run_indicator_text.format(run_ind + 1, num_runs)
        run_indicator_obj.txt.set_text(text)

        # Average the counts over the iterations
        inc_sig_counts = sig_counts[: run_ind + 1]
        inc_ref_counts = ref_counts[: run_ind + 1]
        ret_vals = tool_belt.process_counts(
            inc_sig_counts, inc_ref_counts, num_reps, readout, norm_style
        )
        (
            sig_counts_avg_kcps,
            ref_counts_avg_kcps,
            norm_avg_sig,
            norm_avg_sig_ste,
        ) = ret_vals

        kpl.plot_line_update(ax_sig_ref, line_ind=0, y=sig_counts_avg_kcps)
        kpl.plot_line_update(ax_sig_ref, line_ind=1, y=ref_counts_avg_kcps)
        kpl.plot_line_update(ax_norm, y=norm_avg_sig)

        ### Incremental saving

        data = {
            "start_timestamp": start_timestamp,
            "timestamp": tool_belt.get_time_stamp(),
            "nv_sig": nv_sig,
            "opti_coords_list": opti_coords_list,
            "opti_coords_list-units": "V",
            "freq_center": freq_center,
            "freq_center-units": "GHz",
            "freq_range": freq_range,
            "freq_range-units": "GHz",
            "uwave_pulse_dur": uwave_pulse_dur,
            "uwave_pulse_dur-units": "ns",
            "state": state.name,
            "num_steps": num_steps,
            "num_reps": num_reps,
            "num_runs": num_runs,
            "run_ind": run_ind,
            "uwave_power": uwave_power,
            "uwave_power-units": "dBm",
            "readout": readout,
            "readout-units": "ns",
            "freq_index_master_list": freq_index_master_list,
            "opti_coords_list": opti_coords_list,
            "opti_coords_list-units": "V",
            "sig_counts": sig_counts.astype(int).tolist(),
            "sig_counts-units": "counts",
            "ref_counts": ref_counts.astype(int).tolist(),
            "ref_counts-units": "counts",
            "norm_avg_sig": norm_avg_sig.astype(float).tolist(),
            "norm_avg_sig-units": "arb",
            "norm_avg_sig_ste": norm_avg_sig_ste.astype(float).tolist(),
            "norm_avg_sig_ste-units": "arb",
        }

        # This will continuously be the same file path so we will overwrite
        # the existing file with the latest version
        file_path = tool_belt.get_file_path(
            __file__, start_timestamp, nv_sig["name"], "incremental"
        )
        tool_belt.save_figure(raw_fig, file_path)
        tool_belt.save_raw_data(data, file_path)

    ### Process and plot the data

    ret_vals = tool_belt.process_counts(
        sig_counts, ref_counts, num_reps, readout, norm_style
    )
    (
        sig_counts_avg_kcps,
        ref_counts_avg_kcps,
        norm_avg_sig,
        norm_avg_sig_ste,
    ) = ret_vals

    # Raw data
    kpl.plot_line_update(ax_sig_ref, line_ind=0, y=sig_counts_avg_kcps)
    kpl.plot_line_update(ax_sig_ref, line_ind=1, y=ref_counts_avg_kcps)
    kpl.plot_line_update(ax_norm, y=norm_avg_sig)
    run_indicator_obj.remove()

    # Fits
    low_freq = None
    high_freq = None
    fit_fig = None
    try:
        fit_fig, _, fit_func, popt, pcov = create_fit_figure(
            freq_center, freq_range, num_steps, norm_avg_sig, norm_avg_sig_ste
        )

        if len(popt) == 3:
            low_freq = popt[2]
            high_freq = None
            print('Single resonance found at {:.4f} +/- {:.4f} GHz'.format(popt[2], np.sqrt(pcov[2][2])))
        elif len(popt) == 6:
            low_freq = popt[2]
            high_freq = popt[5]
            print('Two resonances found at {:.4f} +/- {:.4f} GHz and {:.4f} +/- {:.4f} GHz'.format(popt[2], np.sqrt(pcov[2][2]),popt[5], np.sqrt(pcov[5][5])))
    except Exception:
        print('Could not fit data')

    ### Clean up, save the data, return

    tool_belt.reset_cfm(cxn)

    timestamp = tool_belt.get_time_stamp()

    # If you update this, also update the incremental data above if necessary
    data = {
        "start_timestamp": start_timestamp,
        "timestamp": timestamp,
        "nv_sig": nv_sig,
        "opti_coords_list": opti_coords_list,
        "opti_coords_list-units": "V",
        "freq_center": freq_center,
        "freq_center-units": "GHz",
        "freq_range": freq_range,
        "freq_range-units": "GHz",
        "uwave_pulse_dur": uwave_pulse_dur,
        "uwave_pulse_dur-units": "ns",
        "state": state.name,
        "num_steps": num_steps,
        "num_reps": num_reps,
        "num_runs": num_runs,
        "uwave_power": uwave_power,
        "uwave_power-units": "dBm",
        "readout": readout,
        "readout-units": "ns",
        "freq_index_master_list": freq_index_master_list,
        "opti_coords_list": opti_coords_list,
        "opti_coords_list-units": "V",
        "sig_counts": sig_counts.astype(int).tolist(),
        "sig_counts-units": "counts",
        "ref_counts": ref_counts.astype(int).tolist(),
        "ref_counts-units": "counts",
        "norm_avg_sig": norm_avg_sig.astype(float).tolist(),
        "norm_avg_sig-units": "arb",
        "norm_avg_sig_ste": norm_avg_sig_ste.astype(float).tolist(),
        "norm_avg_sig_ste-units": "arb",
    }

    nv_name = nv_sig["name"]

    file_path = tool_belt.get_file_path(__file__, timestamp, nv_name)
    data_file_name = file_path.stem
    tool_belt.save_figure(raw_fig, file_path)

    tool_belt.save_raw_data(data, file_path)

    single_res = None
    if fit_fig is not None:
        file_path = tool_belt.get_file_path(__file__, timestamp, nv_name + "-fit")
        tool_belt.save_figure(fit_fig, file_path)

        single_res = return_res_with_error(data)
    return single_res, data_file_name, [low_freq, high_freq]


# endregion


if __name__ == "__main__":

    # print(Path(__file__).stem)
    # sys.exit()

    file_name = "2023_01_12-14_49_52-wu-nv10_zfs_vs_t"
    data = tool_belt.get_raw_data(file_name)

    print(return_res_with_error(data))
    sys.exit()

    kpl.init_kplotlib()
    freq_center = data["freq_center"]
    freq_range = data["freq_range"]
    num_steps = data["num_steps"]
    ref_counts = data["ref_counts"]
    sig_counts = data["sig_counts"]
    num_reps = data["num_reps"]
    nv_sig = data["nv_sig"]
    readout = nv_sig["spin_readout_dur"]
    try:
        norm_style = NormStyle[str.upper(nv_sig["norm_style"])]
    except Exception as exc:
        # norm_style = NormStyle.POINT_TO_POINT
        norm_style = NormStyle.SINGLE_VALUED

    ret_vals = tool_belt.process_counts(
        sig_counts, ref_counts, num_reps, readout, norm_style
    )
    (
        sig_counts_avg_kcps,
        ref_counts_avg_kcps,
        norm_avg_sig,
        norm_avg_sig_ste,
    ) = ret_vals
    # create_raw_data_figure(
    #     freq_center,
    #     freq_range,
    #     num_steps,
    #     sig_counts_avg_kcps,
    #     ref_counts_avg_kcps,
    #     norm_avg_sig,
    # )
    create_fit_figure(
        freq_center,
        freq_range,
        num_steps,
        norm_avg_sig,
        norm_avg_sig_ste,
    )

    plt.show(block=True)
