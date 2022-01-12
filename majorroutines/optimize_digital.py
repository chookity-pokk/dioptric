# -*- coding: utf-8 -*-
"""
Optimize on an NV, but digitally connect to the xy positioner

Created on Thu Apr 11 11:19:56 2019

@author: agardill
"""


# %% Imports


import utils.tool_belt as tool_belt
import numpy
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import time
import copy
import labrad

num_steps =61
# %% Plotting functions


def create_figure():
    fig, axes_pack = plt.subplots(1, 3, figsize=(17, 8.5))
    axis_titles = ["X Axis", "Y Axis", "Z Axis"]
    for ind in range(3):
        ax = axes_pack[ind]
        ax.set_title(axis_titles[ind])
        ax.set_xlabel("Volts (V)")
        ax.set_ylabel("Count rate (kcps)")
    fig.set_tight_layout(True)
    fig.canvas.draw()
    fig.canvas.flush_events()
    return fig


def update_figure(fig, axis_ind, voltages, count_rates, text=None):
    axes = fig.get_axes()
    ax = axes[axis_ind]
    ax.plot(voltages, count_rates)

    if text is not None:
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        ax.text(
            0.05,
            0.95,
            text,
            transform=ax.transAxes,
            fontsize=12,
            verticalalignment="top",
            bbox=props,
        )

    fig.canvas.draw()
    fig.canvas.flush_events()


# %% Other functions


def read_timed_counts(cxn, num_steps, period, apd_indices):

    cxn.apd_tagger.start_tag_stream(apd_indices)
    num_read_so_far = 0
    counts = []

    timeout_duration = ((period * (10 ** -9)) * num_steps) + 10
    timeout_inst = time.time() + timeout_duration

    cxn.pulse_streamer.stream_start(num_steps)

    while num_read_so_far < num_steps:

        if time.time() > timeout_inst:
            break

        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break

        # Read the samples and update the image
        new_samples = cxn.apd_tagger.read_counter_simple()
        num_new_samples = len(new_samples)
        if num_new_samples > 0:
            counts.extend(new_samples)
            num_read_so_far += num_new_samples

    cxn.apd_tagger.stop_tag_stream()

    return numpy.array(counts, dtype=int)


def read_manual_counts(cxn, period, apd_indices, axis_write_func, scan_vals):

    cxn.apd_tagger.start_tag_stream(apd_indices)
    counts = []

    for ind in range(len(scan_vals)):

        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break

        # Write the new value to the axis and run a rep. The delay to account
        # for the time it takes the axis to move is already handled in the
        # sequence loaded on the pulse streamer. Also note that server calls
        # are synchronous so if the write function has a built-in wait until
        # the write completes, then no delay is necessary in the sequence
        axis_write_func(scan_vals[ind])
        cxn.pulse_streamer.stream_start(1)

        # Read the samples and update the image
        new_samples = cxn.apd_tagger.read_counter_simple(1)
        counts.extend(new_samples)

    cxn.apd_tagger.stop_tag_stream()

    return numpy.array(counts, dtype=int)


def stationary_count_lite(cxn, nv_sig, coords, config, apd_indices):

    seq_file_name = "simple_readout.py"

    # Some initial values
    laser_name = nv_sig["imaging_laser"]
    power_key = "imaging_laser_power"
    laser_power = tool_belt.set_laser_power(cxn, nv_sig, "imaging_laser")
    readout = nv_sig["imaging_readout_dur"]
    total_num_samples = 2
    x_center, y_center, z_center = coords
    
    if nv_sig["ramp_voltages"] == True:
        tool_belt.set_xyz_ramp(cxn, [x_center, y_center, z_center])
    else:
        tool_belt.set_xyz(cxn, [x_center, y_center, z_center])
    
    time.sleep(0.01)
    delay = config["Positioning"]["xy_small_response_delay"]
    seq_args = [delay, readout, apd_indices[0], laser_name, laser_power]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    cxn.pulse_streamer.stream_load(seq_file_name, seq_args_string)

    # Collect the data
    cxn.apd_tagger.start_tag_stream(apd_indices)
    cxn.pulse_streamer.stream_start(total_num_samples)
    new_samples = cxn.apd_tagger.read_counter_simple(total_num_samples)
    new_samples_avg = numpy.average(new_samples)
    cxn.apd_tagger.stop_tag_stream()
    counts_kcps = (new_samples_avg / 1000) / (readout / 10 ** 9)

    return counts_kcps


def optimize_on_axis(cxn, nv_sig, axis_ind, config, apd_indices, fig=None):

    seq_file_name = "simple_readout.py"
    coords = nv_sig["coords"]
    x_center, y_center, z_center = coords
    readout = nv_sig["imaging_readout_dur"]
    laser_key = "imaging_laser"

    laser_name = nv_sig[laser_key]
    tool_belt.set_filter(cxn, nv_sig, laser_key)
    laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)

    tool_belt.init_safe_stop()
    # xy
    if axis_ind in [0, 1]:

        scan_range = config["Positioning"]["xy_optimize_range"]
        scan_dtype = eval(config["Positioning"]["xy_dtype"])
        delay = config["Positioning"]["xy_small_response_delay"]


        # Move to first point in scan
        half_scan_range = scan_range / 2
        x_low = x_center - half_scan_range
        y_low = y_center - half_scan_range
        if axis_ind == 0:
            start_coords = [x_low, coords[1], coords[2]]
        elif axis_ind == 1:
            start_coords = [coords[0], y_low, coords[2]]
            
        if nv_sig["ramp_voltages"] == True:
            tool_belt.set_xyz_ramp(cxn, start_coords)
        else:
            tool_belt.set_xyz(cxn, start_coords)
    
        # Get the proper scan function
        xy_server = tool_belt.get_xy_server(cxn)
            
        seq_args = [delay, readout, apd_indices[0], laser_name, laser_power]
        seq_args_string = tool_belt.encode_seq_args(seq_args)
        ret_vals = cxn.pulse_streamer.stream_load(seq_file_name, seq_args_string)
        period = ret_vals[0]
        
        auto_scan = False
        
        if axis_ind == 0:
            scan_func = xy_server.load_scan_x
            manual_write_func = xy_server.write_x
        elif axis_ind == 1:
            scan_func = xy_server.load_scan_y
            manual_write_func = xy_server.write_y
        
        scan_vals = scan_func(x_center, y_center, scan_range, num_steps, period)
            

    # z
    elif axis_ind == 2:

        scan_range = config["Positioning"]["z_optimize_range"]
        scan_dtype = eval(config["Positioning"]["z_dtype"])
        delay = config["Positioning"]["z_delay"]
        
        # Move to first point in scan
        half_scan_range = scan_range / 2
        z_low = z_center - half_scan_range
        start_coords = [coords[0], coords[1], z_low]
        if nv_sig["ramp_voltages"] == True:
            tool_belt.set_xyz_ramp(cxn, start_coords)
        else:
            tool_belt.set_xyz(cxn, start_coords)
            

        z_server = tool_belt.get_z_server(cxn)
        
        seq_args = [delay, readout, apd_indices[0], laser_name, laser_power]
        seq_args_string = tool_belt.encode_seq_args(seq_args)
        ret_vals = cxn.pulse_streamer.stream_load(seq_file_name, seq_args_string)
        period = ret_vals[0]
        
        if hasattr(z_server, "load_scan_z"):
            scan_vals = z_server.load_scan_z(z_center, scan_range, num_steps, period)
            auto_scan = True
        else:
            manual_write_func = z_server.write_z
            adj_z_center = z_center

            scan_vals = tool_belt.get_scan_vals(
                adj_z_center, scan_range, num_steps, scan_dtype
            )
            auto_scan = False
    if auto_scan:
        counts = read_timed_counts(cxn, num_steps, period, apd_indices)
    else:
        counts = read_manual_counts(
            cxn, period, apd_indices, manual_write_func, scan_vals
        )

    # print(scan_vals)
    # counts = read_timed_counts(cxn, num_steps, period, apd_indices)
    count_rates = (counts / 1000) / (readout / 10 ** 9)

    if fig is not None:
        update_figure(fig, axis_ind, scan_vals, count_rates)

    opti_coord = fit_gaussian(nv_sig, scan_vals, count_rates, axis_ind, fig)

    return opti_coord, scan_vals, counts


def fit_gaussian(nv_sig, scan_vals, count_rates, axis_ind, fig=None):

    fit_func = tool_belt.gaussian

    # The order of parameters is
    # 0: coefficient that defines the peak height
    # 1: mean, defines the center of the Gaussian
    # 2: standard deviation, defines the width of the Gaussian
    # 3: constant y value to account for background
    expected_count_rate = nv_sig["expected_count_rate"]
    if expected_count_rate is None:
        expected_count_rate = 50  # Guess 50
    expected_count_rate = float(expected_count_rate)
    #    background_count_rate = nv_sig[4]
    #    if background_count_rate is None:
    #        background_count_rate = 0  # Guess 0
    #    background_count_rate = float(background_count_rate)
    background_count_rate = 0.0  # Guess 0
    low_voltage = numpy.min(scan_vals)
    high_voltage = numpy.max(scan_vals)
    scan_range = high_voltage - low_voltage
    coords = nv_sig["coords"]
    init_fit = (
        expected_count_rate - background_count_rate,
        coords[axis_ind],
        scan_range / 3,
        background_count_rate,
    )
    opti_params = None
    try:
        inf = numpy.inf
        low_bounds = [0, low_voltage, 0, 0]
        high_bounds = [inf, high_voltage, inf, inf]
        opti_params, cov_arr = curve_fit(
            fit_func,
            scan_vals,
            count_rates,
            p0=init_fit,
            bounds=(low_bounds, high_bounds),
        )
        # Consider it a failure if we railed or somehow got out of bounds
        for ind in range(len(opti_params)):
            param = opti_params[ind]
            if not (low_bounds[ind] < param < high_bounds[ind]):
                opti_params = None
    except Exception as ex:
        print(ex)
        # pass

    if opti_params is None:
        print("Optimization failed for axis {}".format(axis_ind))

    # Plot
    if (fig is not None) and (opti_params is not None):
        # Plot the fit
        linspace_voltages = numpy.linspace(low_voltage, high_voltage, num=1000)
        fit_count_rates = fit_func(linspace_voltages, *opti_params)
        # Add info to the axes
        # a: coefficient that defines the peak height
        # mu: mean, defines the center of the Gaussian
        # sigma: standard deviation, defines the width of the Gaussian
        # offset: constant y value to account for background
        text = "a={:.3f}\n $\mu$={:.3f}\n $\sigma$={:.3f}\n offset={:.3f}".format(
            *opti_params
        )
        update_figure(fig, axis_ind, linspace_voltages, fit_count_rates, text)

    center = None
    if opti_params is not None:
        center = opti_params[1]

    return center


# %% User functions


def optimize_list(nv_sig_list, apd_indices, laser_ind=532, aom_ao_589_pwr=1.0):

    with labrad.connect() as cxn:
        optimize_list_with_cxn(cxn, nv_sig_list, apd_indices, laser_ind, aom_ao_589_pwr)


def optimize_list_with_cxn(cxn, nv_sig_list, apd_indices, laser_ind, aom_ao_589_pwr):

    tool_belt.init_safe_stop()

    opti_coords_list = []
    for ind in range(len(nv_sig_list)):

        print("Optimizing on NV {}...".format(ind))

        if tool_belt.safe_stop():
            break

        nv_sig = nv_sig_list[ind]
        opti_coords = main_with_cxn(
            cxn,
            nv_sig,
            apd_indices,
            laser_ind,
            set_to_opti_coords=False,
            set_drift=False,
        )
        if opti_coords is not None:
            opti_coords_list.append("[{:.3f}, {:.3f}, {:.2f}],".format(*opti_coords))
        else:
            opti_coords_list.append("Optimization failed for NV {}.".format(ind))

    for coords in opti_coords_list:
        print(coords)


def prepare_microscope(cxn, nv_sig, coords=None):
    """
     Prepares the microscope for a measurement. In particular,
     sets up the optics (positioning, collection filter, etc) and magnet.
     The laser set up must be handled by each routine since the same laser
     may be specified for multiple purposes.
     """

    if coords is not None:
        if nv_sig["ramp_voltages"] == True:
            tool_belt.set_xyz_ramp(cxn, coords)
        else:
            tool_belt.set_xyz(cxn, coords)
    
    if "collection_filter" in nv_sig:
        filter_name = nv_sig["collection_filter"]
        if filter_name is not None:
            tool_belt.set_filter(
                cxn, optics_name="collection", filter_name=filter_name
            )

    magnet_angle = nv_sig["magnet_angle"]
    if (magnet_angle is not None) and hasattr(cxn, "rotation_stage_ell18k"):
        cxn.rotation_stage_ell18k.set_angle(magnet_angle)

    time.sleep(0.01)


# %% Main


def main(
    nv_sig, apd_indices, set_to_opti_coords=True, save_data=False, plot_data=False):

    with labrad.connect() as cxn:
        optimize_coords = main_with_cxn(
            cxn, nv_sig, apd_indices, set_to_opti_coords, save_data, plot_data
        )
    return optimize_coords

def main_with_cxn(
    cxn,
    nv_sig,
    apd_indices,
    set_to_opti_coords=True,
    save_data=False,
    plot_data=False,
    set_drift=True,
):

    startFunctionTime = time.time()
    tool_belt.reset_cfm(cxn)

    # Adjust the sig we use for drift
    drift = tool_belt.get_drift()
    passed_coords = nv_sig["coords"]
    adjusted_coords = (numpy.array(passed_coords) + numpy.array(drift)).tolist()
    # If optimize is disabled, just set the filters and magnet in place
    if nv_sig["disable_opt"]:
        prepare_microscope(cxn, nv_sig, adjusted_coords)
        return None
    adjusted_nv_sig = copy.deepcopy(nv_sig)
    adjusted_nv_sig["coords"] = adjusted_coords

    if "collection_filter" in nv_sig:
        tool_belt.set_filter(cxn, nv_sig, "collection")

    if "imaging_laser_filter" in nv_sig:
        tool_belt.set_filter(cxn, nv_sig, "imaging_laser_filter")

    expected_count_rate = adjusted_nv_sig["expected_count_rate"]

    config = tool_belt.get_config_dict(cxn)

    opti_succeeded = False

    # %% Try to optimize

    num_attempts = 4

    for ind in range(num_attempts):

        if ind > 0:
            print("Trying again...")

        # Create 3 plots in the figure, one for each axis
        fig = None
        if plot_data:
            fig = create_figure()

        # Optimize on each axis
        opti_coords = []
        scan_vals_by_axis = []
        counts_by_axis = []

        # xy
        for axis_ind in range(2):
            # print(axis_ind)
            ret_vals = optimize_on_axis(
                cxn, adjusted_nv_sig, axis_ind, config, apd_indices, fig
            )
            opti_coords.append(ret_vals[0])
            scan_vals_by_axis.append(ret_vals[1])
            counts_by_axis.append(ret_vals[2])
        # ret_vals = optimize_on_axis(
        #     cxn, adjusted_nv_sig, 1, config, apd_indices, fig
        # )
        # opti_coords.append(ret_vals[0])
        # scan_vals_by_axis.append(ret_vals[1])
        # counts_by_axis.append(ret_vals[2])
        # ret_vals = optimize_on_axis(
        #     cxn, adjusted_nv_sig, 0, config, apd_indices, fig
        # )
        # opti_coords.insert(0, ret_vals[0])
        # scan_vals_by_axis.insert(0, ret_vals[1])
        # counts_by_axis.insert(0, ret_vals[2])

        # z
        # Help z out by ensuring we're centered in xy first
        if None not in opti_coords:
            int_coords = [opti_coords[0], opti_coords[1], adjusted_coords[2]]
            adjusted_nv_sig_z = copy.deepcopy(nv_sig)
            adjusted_nv_sig_z["coords"] = int_coords
            
            # if nv_sig["ramp_voltages"] == True:
            #     tool_belt.set_xyz_ramp(cxn, int_coords)
            # else:
            #     tool_belt.set_xyz(cxn, int_coords)
        else:
            adjusted_nv_sig_z = copy.deepcopy(nv_sig)
            adjusted_nv_sig_z["coords"] = adjusted_coords
        axis_ind = 2
        # print(axis_ind)
        ret_vals = optimize_on_axis(
            cxn, adjusted_nv_sig_z, axis_ind, config, apd_indices, fig
        )
        opti_coords.append(ret_vals[0])
        scan_vals_by_axis.append(ret_vals[1])
        counts_by_axis.append(ret_vals[2])


        # return
        # We failed to get optimized coordinates, try again
        if None in opti_coords:
            continue

        # Check the count rate
        opti_count_rate = stationary_count_lite(
            cxn, nv_sig, opti_coords, config, apd_indices
        )

        # Verify that our optimization found a reasonable spot by checking
        # the count rate at the center against the expected count rate
        if expected_count_rate is not None:

            lower_threshold = expected_count_rate * 4 / 5
            upper_threshold = expected_count_rate * 6 / 5

            if ind == 0:
                print("Expected count rate: {}".format(expected_count_rate))

            print("Count rate at optimized coordinates: {:.1f}".format(opti_count_rate))

            # If the count rate close to what we expect, we succeeded!
            if lower_threshold <= opti_count_rate <= upper_threshold:
                print("Optimization succeeded!")
                opti_succeeded = True
            else:
                print("Count rate at optimized coordinates out of bounds.")
                # If we failed by expected counts, try again with the
                # coordinates we found. If x/y are off initially, then
                # z will give a false optimized coordinate. x/y will give
                # true optimized coordinates regardless of the other initial
                # coordinates, however. So we might succeed by trying z again
                # at the optimized x/y.
                adjusted_nv_sig["coords"] = opti_coords

        # If the threshold is not set, we succeed based only on optimize
        else:
            print("Count rate at optimized coordinates: {:.0f}".format(opti_count_rate))
            print("Optimization succeeded! (No expected count rate passed.)")
            opti_succeeded = True
        # Break out of the loop if optimization succeeded
        if opti_succeeded:
            break

    if not opti_succeeded:
        opti_coords = None

    # %% Calculate the drift relative to the passed coordinates

    if opti_succeeded and set_drift:
        drift = (numpy.array(opti_coords) - numpy.array(passed_coords)).tolist()
        tool_belt.set_drift(drift)

    # %% Set to the optimized coordinates, or just tell the user what they are

    if set_to_opti_coords:
        if opti_succeeded:
            prepare_microscope(cxn, nv_sig, opti_coords)
        else:
            # Let the user know something went wrong
            print(
                "Optimization failed. Resetting to coordinates "
                "about which we attempted to optimize."
            )
            prepare_microscope(cxn, nv_sig, adjusted_coords)
    else:
        if opti_succeeded:
            print("Optimized coordinates: ")
            print("{:.3f}, {:.3f}, {:.2f}".format(*opti_coords))
            print("Drift: ")
            print("{:.3f}, {:.3f}, {:.2f}".format(*drift))
        else:
            print("Optimization failed.")
            prepare_microscope(cxn, nv_sig)

    print("\n")

    # %% Clean up and save the data

    tool_belt.reset_cfm(cxn)
    endFunctionTime = time.time()
    time_elapsed = endFunctionTime - startFunctionTime

    # Don't bother saving the data if we're just using this to find the
    # optimized coordinates
    if save_data:

        timestamp = tool_belt.get_time_stamp()

        rawData = {
            "timestamp": timestamp,
            'time_elapsed': time_elapsed,
            "nv_sig": nv_sig,
            "nv_sig-units": tool_belt.get_nv_sig_units(),
            "opti_coords": opti_coords,
            'num_steps': num_steps,
            "x_scan_vals": scan_vals_by_axis[0].tolist(),
            "y_scan_vals": scan_vals_by_axis[1].tolist(),
            "z_scan_vals": scan_vals_by_axis[2].tolist(),
            "x_counts": counts_by_axis[0].tolist(),
            "x_counts-units": "number",
            "y_counts": counts_by_axis[1].tolist(),
            "y_counts-units": "number",
            "z_counts": counts_by_axis[2].tolist(),
            "z_counts-units": "number",
        }

        filePath = tool_belt.get_file_path(__file__, timestamp, nv_sig["name"])
        tool_belt.save_raw_data(rawData, filePath)

        if fig is not None:
            tool_belt.save_figure(fig, filePath)

    # %% Return the optimized coordinates we found

    return opti_coords
