# -*- coding: utf-8 -*-
"""
Optimize on an NV, but digitally connect to the xy positioner

Created on Thu Apr 11 11:19:56 2019

@author: agardill
"""


# %% Imports


import utils.tool_belt as tool_belt
import utils.positioning as positioning
import numpy
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import time
import copy
import labrad
from majorroutines.optimize import create_figure, update_figure, read_manual_counts, read_timed_counts, fit_gaussian, stationary_count_lite, prepare_microscope, optimize_list, main , optimize_list_with_cxn

num_steps =31



# %% Other functions


def optimize_on_axis(cxn, nv_sig, axis_ind, config, apd_indices, fig=None):
    
    counter_server = tool_belt.get_counter_server(cxn)
    pulsegen_server = tool_belt.get_pulsegen_server(cxn)

    seq_file_name = "simple_readout.py"
    
    coords = nv_sig["coords"]
    x_center, y_center, z_center = coords
    readout = nv_sig["imaging_readout_dur"]
    laser_key = "imaging_laser"

    laser_name = nv_sig[laser_key]
    tool_belt.set_filter(cxn, nv_sig, laser_key)
    laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)

    # tool_belt.init_safe_stop()
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
        ret_vals = pulsegen_server.stream_load(seq_file_name, seq_args_string)
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
        ret_vals = pulsegen_server.stream_load(seq_file_name, seq_args_string)
        period = ret_vals[0]
        
        # if hasattr(z_server, "load_scan_z"):
        #     scan_vals = z_server.load_scan_z(z_center, scan_range, num_steps, period)
        #     auto_scan = True
    # else:
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


# %% Main


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
    
    tool_belt.init_safe_stop()

    # Adjust the sig we use for drift
    drift = positioning.get_drift()
    passed_coords = nv_sig["coords"]
    adjusted_coords = (numpy.array(passed_coords) + numpy.array(drift)).tolist()
    # If optimize is disabled, just set the filters and magnet in place
    if nv_sig["disable_opt"]:
        prepare_microscope(cxn, nv_sig, adjusted_coords)
        return None
    adjusted_nv_sig = copy.deepcopy(nv_sig)
    adjusted_nv_sig["coords"] = adjusted_coords

    tool_belt.set_filter(cxn, nv_sig, "collection")
    tool_belt.set_filter(cxn, nv_sig, "imaging_laser")

    expected_count_rate = adjusted_nv_sig["expected_count_rate"]

    config = tool_belt.get_config_dict(cxn)

    opti_succeeded = False

     # %% Check if we need to optimize

    print("Expected count rate: {}".format(expected_count_rate))

    if expected_count_rate is not None:
        lower_threshold = expected_count_rate * 9 / 10
        upper_threshold = expected_count_rate * 6 / 5
    
    # Check the count rate
    opti_count_rate = stationary_count_lite(cxn, nv_sig, adjusted_coords,
                                            config, apd_indices)
    
    print("Count rate at optimized coordinates: {:.1f}".format(opti_count_rate))
    
    # If the count rate close to what we expect, we succeeded!
    if (expected_count_rate is not None) and (lower_threshold <= opti_count_rate <= upper_threshold):
        print("No need to optimize.")
        opti_unnecessary = True
        # opti_unnecessary = False
        opti_coords = adjusted_coords
    else:
        print("Count rate at optimized coordinates out of bounds.")
        opti_unnecessary = False


    # %% Try to optimize

    num_attempts = 4

    for ind in range(num_attempts):
        
        
        if opti_succeeded or opti_unnecessary:
            break

        if tool_belt.safe_stop():
            break

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
        if "only_z_opt" in nv_sig and nv_sig["only_z_opt"]:
            opti_coords = [adjusted_coords[0], adjusted_coords[1]]
            for i in range(2):
                scan_vals_by_axis.append(numpy.array([]))
                counts_by_axis.append(numpy.array([]))
        else:
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
            if not opti_unnecessary:
                # Let the user know something went wrong
                print(
                    "Optimization failed. Resetting to coordinates "
                    "about which we attempted to optimize."
                )
            prepare_microscope(cxn, nv_sig, adjusted_coords)
    else:
        if opti_succeeded or opti_unnecessary:
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
    if save_data and not opti_unnecessary:

        if len(scan_vals_by_axis) < 3:
            z_scan_vals = None
        else:
            z_scan_vals = scan_vals_by_axis[2].tolist()
            
        timestamp = tool_belt.get_time_stamp()
        rawData = {
            "timestamp": timestamp,
            'time_elapsed': time_elapsed,
            "nv_sig": nv_sig,
            "nv_sig-units": tool_belt.get_nv_sig_units(),
            "opti_coords": opti_coords,
            "x_scan_vals": scan_vals_by_axis[0].tolist(),
            "y_scan_vals": scan_vals_by_axis[1].tolist(),
            "z_scan_vals": z_scan_vals,
            "x_counts": counts_by_axis[0].tolist(),
            "x_counts-units": "number",
            "y_counts": counts_by_axis[1].tolist(),
            "y_counts-units": "number",
            "z_counts": z_scan_vals,
            "z_counts-units": "number",
        }

        filePath = tool_belt.get_file_path(__file__, timestamp, nv_sig["name"])
        tool_belt.save_raw_data(rawData, filePath)

        if fig is not None:
            tool_belt.save_figure(fig, filePath)

    # %% Return the optimized coordinates we found

    return opti_coords, opti_count_rate
