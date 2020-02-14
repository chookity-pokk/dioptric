# -*- coding: utf-8 -*-
"""
Optimize on an NV

Created on Thu Apr 11 11:19:56 2019

@author: mccambria
"""


# %% Imports


import utils.tool_belt as tool_belt
import numpy
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import time
import copy
import labrad


# %% Plotting functions


def create_figure():
    fig, axes_pack = plt.subplots(1, 3, figsize=(17, 8.5))
    axis_titles = ['X Axis', 'Y Axis', 'Z Axis']
    for ind in range(3):
        ax = axes_pack[ind]
        ax.set_title(axis_titles[ind])
        ax.set_xlabel('Volts (V)')
        ax.set_ylabel('Count rate (kcps)')
    fig.set_tight_layout(True)
    fig.canvas.draw()
    fig.canvas.flush_events()
    return fig
    
    
def update_figure(fig, axis_ind, voltages, count_rates, text=None):
    axes = fig.get_axes()
    ax = axes[axis_ind]
    ax.plot(voltages, count_rates)

    if text is not None:
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=12,
                verticalalignment='top', bbox=props)

    fig.canvas.draw()
    fig.canvas.flush_events()


# %% Other functions


def read_timed_counts(cxn, num_steps, period, apd_indices):

    cxn.apd_tagger.start_tag_stream(apd_indices)
    num_read_so_far = 0
    counts = []

    timeout_duration = ((period*(10**-9)) * num_steps) + 10
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

    
def stationary_count_lite(cxn, coords, shared_params, apd_indices):
    
    # Some initial values
    readout = shared_params['continuous_readout_dur']
    total_num_samples = 2
    x_center, y_center, z_center = coords

    seq_args = [shared_params['532_aom_delay'], readout, apd_indices[0]]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    cxn.pulse_streamer.stream_load('simple_readout.py', seq_args_string)

    tool_belt.set_xyz(cxn, [x_center, y_center, z_center])

    # Collect the data
    cxn.apd_tagger.start_tag_stream(apd_indices)
    cxn.pulse_streamer.stream_start(total_num_samples)
    new_samples = cxn.apd_tagger.read_counter_simple(total_num_samples)
    new_samples_avg = numpy.average(new_samples)
    cxn.apd_tagger.stop_tag_stream()
    counts_kcps = (new_samples_avg / 1000) / (readout / 10**9)
    
    return counts_kcps
    
    
def optimize_on_axis(cxn, nv_sig, axis_ind, shared_params,
                     apd_indices, fig=None):
    
    seq_file_name = 'simple_readout.py'
    num_steps = 31
    coords = nv_sig['coords']
    x_center, y_center, z_center = coords
    scan_range_nm = 2 * shared_params['airy_radius']
    readout = shared_params['continuous_readout_dur']

    # Reset to centers
    tool_belt.set_xyz(cxn, coords)
    
    tool_belt.init_safe_stop()
    
    # x/y
    if axis_ind in [0, 1]:
        
        scan_range = scan_range_nm / shared_params['galvo_nm_per_volt']
        seq_args = [shared_params['galvo_delay'], readout, apd_indices[0]]
        seq_args_string = tool_belt.encode_seq_args(seq_args)
        ret_vals = cxn.pulse_streamer.stream_load(seq_file_name,
                                                  seq_args_string)
        period = ret_vals[0]

        # Get the proper scan function
        if axis_ind == 0:
            scan_func = cxn.galvo.load_x_scan
        elif axis_ind == 1:
            scan_func = cxn.galvo.load_y_scan
            
        voltages = scan_func(x_center, y_center, scan_range,
                             num_steps, period)

    # z
    elif axis_ind == 2:
        
        scan_range = scan_range_nm / shared_params['piezo_nm_per_volt']
        seq_args = [shared_params['objective_piezo_delay'],
                    readout, apd_indices[0]]
        seq_args_string = tool_belt.encode_seq_args(seq_args)
        ret_vals = cxn.pulse_streamer.stream_load(seq_file_name,
                                                  seq_args_string)
        period = ret_vals[0]

        voltages = cxn.objective_piezo.load_z_scan(z_center, scan_range,
                                                   num_steps, period)

    counts = read_timed_counts(cxn, num_steps, period, apd_indices)
    count_rates = (counts / 1000) / (readout / 10**9)
    
    if fig is not None:
        update_figure(fig, axis_ind, voltages, count_rates)
        
    opti_coord = fit_gaussian(nv_sig, voltages, count_rates, axis_ind, fig)
        
    return opti_coord, voltages, counts
    
    
def fit_gaussian(nv_sig, voltages, count_rates, axis_ind, fig=None):
        
    fit_func = tool_belt.gaussian
    
    # The order of parameters is 
    # 0: coefficient that defines the peak height
    # 1: mean, defines the center of the Gaussian
    # 2: standard deviation, defines the width of the Gaussian
    # 3: constant y value to account for background
    expected_count_rate = nv_sig['expected_count_rate']
    if expected_count_rate is None:
        expected_count_rate = 50  # Guess 50
    expected_count_rate = float(expected_count_rate)
#    background_count_rate = nv_sig[4]
#    if background_count_rate is None:
#        background_count_rate = 0  # Guess 0
#    background_count_rate = float(background_count_rate)
    background_count_rate = 0.0  # Guess 0
    low_voltage = voltages[0]
    high_voltage = voltages[-1]
    scan_range = high_voltage - low_voltage
    coords = nv_sig['coords']
    init_fit = (expected_count_rate - background_count_rate,
                coords[axis_ind],
                scan_range / 3,
                background_count_rate)
    opti_params = None
    try:
        inf = numpy.inf
        low_bounds = [0, low_voltage, 0, 0]
        high_bounds = [inf, high_voltage, inf, inf]
        opti_params, cov_arr = curve_fit(fit_func, voltages,
                                         count_rates, p0=init_fit,
                                         bounds=(low_bounds, high_bounds))
        # Consider it a failure if we railed or somehow got out of bounds
        for ind in range(len(opti_params)):
            param = opti_params[ind]
            if not (low_bounds[ind] < param < high_bounds[ind]):
                opti_params = None
    except Exception:
        pass
        
    if opti_params is None:
        print('Optimization failed for axis {}'.format(axis_ind))
        
    # Plot
    if (fig is not None) and (opti_params is not None):
        # Plot the fit
        linspace_voltages = numpy.linspace(low_voltage, high_voltage,
                                           num=1000)
        fit_count_rates = fit_func(linspace_voltages, *opti_params)
        # Add info to the axes
        # a: coefficient that defines the peak height
        # mu: mean, defines the center of the Gaussian
        # sigma: standard deviation, defines the width of the Gaussian
        # offset: constant y value to account for background
        text = 'a={:.3f}\n $\mu$={:.3f}\n ' \
            '$\sigma$={:.3f}\n offset={:.3f}'.format(*opti_params)
        update_figure(fig, axis_ind, linspace_voltages,
                      fit_count_rates, text)
    
    center = None
    if opti_params is not None:
        center = opti_params[1]
        
    return center


# %% User functions
    

def optimize_list(nv_sig_list, apd_indices):

    with labrad.connect() as cxn:
        optimize_list_with_cxn(cxn, nv_sig_list, apd_indices)

def optimize_list_with_cxn(cxn, nv_sig_list, apd_indices):
    
    tool_belt.init_safe_stop()
    
    opti_coords_list = []
    for ind in range(len(nv_sig_list)):
        
        print('Optimizing on NV {}...'.format(ind))
        
        if tool_belt.safe_stop():
            break
        
        nv_sig = nv_sig_list[ind]
        opti_coords = main_with_cxn(cxn, nv_sig, apd_indices,
                           set_to_opti_coords=False, set_drift=False)
        if opti_coords is not None:
            opti_coords_list.append('[{:.3f}, {:.3f}, {:.2f}],'.format(*opti_coords))
        else:
            opti_coords_list.append('Optimization failed for NV {}.'.format(ind))
    
    for coords in opti_coords_list:
        print(coords)
    

# %% Main


def main(nv_sig, apd_indices,
         set_to_opti_coords=True, save_data=False, plot_data=False):

    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig, apd_indices,
                      set_to_opti_coords, save_data, plot_data)

def main_with_cxn(cxn, nv_sig, apd_indices,
                  set_to_opti_coords=True, save_data=False,
                  plot_data=False, set_drift=True):
    
    # Reset the microscope and make sure we're at the right ND
    tool_belt.reset_cfm(cxn)
    
    # Be sure the right ND is in place and the magnet aligned
    cxn.filter_slider_ell9k.set_filter(nv_sig['nd_filter'])
    magnet_angle = nv_sig['magnet_angle']
    if magnet_angle is not None:
        cxn.rotation_stage_ell18k.set_angle(magnet_angle)
    
    # Adjust the sig we use for drift
    drift = tool_belt.get_drift()
    passed_coords = nv_sig['coords']
    adjusted_coords = (numpy.array(passed_coords) + numpy.array(drift)).tolist()
    adjusted_nv_sig = copy.deepcopy(nv_sig)
    adjusted_nv_sig['coords'] = adjusted_coords
    
    # Get the shared parameters from the registry
    shared_params = tool_belt.get_shared_parameters_dict(cxn)
    
    expected_count_rate = adjusted_nv_sig['expected_count_rate']
    
    opti_succeeded = False
    
    # %% Try to optimize
    
    num_attempts = 2
    
    for ind in range(num_attempts):
        
        if ind > 0:
            print('Trying again...')
        
        # Create 3 plots in the figure, one for each axis
        fig = None
        if plot_data:
            fig = create_figure()
        
        # Optimize on each axis
        opti_coords = []
        voltages_by_axis = []
        counts_by_axis = []
        for axis_ind in range(3):
            ret_vals = optimize_on_axis(cxn, adjusted_nv_sig, axis_ind,
                                        shared_params, apd_indices, fig)
            opti_coords.append(ret_vals[0])
            voltages_by_axis.append(ret_vals[1])
            counts_by_axis.append(ret_vals[2])
            
        # We failed to get optimized coordinates, try again
        if None in opti_coords:
            continue
            
        # Check the count rate
        opti_count_rate = stationary_count_lite(cxn, opti_coords,
                                                shared_params, apd_indices)
        
        # Verify that our optimization found a reasonable spot by checking
        # the count rate at the center against the expected count rate
        if expected_count_rate is not None:
            
            lower_threshold = expected_count_rate * 2/4
            upper_threshold = expected_count_rate * 6/4
            
            if ind == 0:
                print('Expected count rate: {}'.format(expected_count_rate))
                
            print('Count rate at optimized coordinates: {:.1f}'.format(opti_count_rate))
            
            # If the count rate close to what we expect, we succeeded!
            if lower_threshold <= opti_count_rate <= upper_threshold:
                print('Optimization succeeded!')
                opti_succeeded = True
            else:
                print('Count rate at optimized coordinates out of bounds.')
                # If we failed by expected counts, try again with the
                # coordinates we found. If x/y are off initially, then
                # z will give a false optimized coordinate. x/y will give
                # true optimized coordinates regardless of the other initial
                # coordinates, however. So we might succeed by trying z again 
                # at the optimized x/y. 
                adjusted_nv_sig['coords'] = opti_coords
                
        # If the threshold is not set, we succeed based only on optimize       
        else:
            print('Count rate at optimized coordinates: {:.0f}'.format(opti_count_rate))
            print('Optimization succeeded! (No expected count rate passed.)')
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
            tool_belt.set_xyz(cxn, opti_coords)
        else:
            # Let the user know something went wrong
            print('Optimization failed. Resetting to coordinates ' \
                  'about which we attempted to optimize.')
            tool_belt.set_xyz(cxn, adjusted_coords)
    else:
        if opti_succeeded:
            print('Optimized coordinates: ')
            print('{:.3f}, {:.3f}, {:.2f}'.format(*opti_coords))
            print('Drift: ')
            print('{:.3f}, {:.3f}, {:.2f}'.format(*drift))
        else:
            print('Optimization failed.')
            
    print('\n')
                               
    # %% Clean up and save the data
    
    tool_belt.reset_cfm(cxn)

    # Don't bother saving the data if we're just using this to find the
    # optimized coordinates
    if save_data:

        timestamp = tool_belt.get_time_stamp()

        rawData = {'timestamp': timestamp,
                   'nv_sig': nv_sig,
                   'nv_sig-units': tool_belt.get_nv_sig_units(),
                   'readout': shared_params['continuous_readout_dur'],
                   'readout-units': 'ns',
                   'opti_coords': opti_coords,
                   'opti_coords-units': 'V',
                   'x_voltages': voltages_by_axis[0].tolist(),
                   'x_voltages-units': 'V',
                   'y_voltages': voltages_by_axis[1].tolist(),
                   'y_voltages-units': 'V',
                   'z_voltages': voltages_by_axis[2].tolist(),
                   'z_voltages-units': 'V',
                   'x_counts': counts_by_axis[0].tolist(),
                   'x_counts-units': 'number',
                   'y_counts': counts_by_axis[1].tolist(),
                   'y_counts-units': 'number',
                   'z_counts': counts_by_axis[2].tolist(),
                   'z_counts-units': 'number'}

        filePath = tool_belt.get_file_path(__file__, timestamp,
                                           nv_sig['name'])
        tool_belt.save_raw_data(rawData, filePath)
        
        if fig is not None:
            tool_belt.save_figure(fig, filePath)
            
    # %% Return the optimized coordinates we found
    
    return opti_coords

# %%

def opti_z(nv_sig, apd_indices,
                  set_to_opti_coords=True, save_data=False,
                  plot_data=False, set_drift=True):
    
    with labrad.connect() as cxn:
            opti_z_cxn(cxn, nv_sig, apd_indices,
                          set_to_opti_coords, save_data, plot_data)
        
def opti_z_cxn(cxn, nv_sig, apd_indices,
                  set_to_opti_coords=True, save_data=False,
                  plot_data=False, set_drift=True):
    
    # Reset the microscope and make sure we're at the right ND
    tool_belt.reset_cfm(cxn)
    
    # Be sure the right ND is in place and the magnet aligned
    cxn.filter_slider_ell9k.set_filter(nv_sig['nd_filter'])
    magnet_angle = nv_sig['magnet_angle']
    if magnet_angle is not None:
        cxn.rotation_stage_ell18k.set_angle(magnet_angle)
    
    # Adjust the sig we use for drift
    drift = tool_belt.get_drift()
    passed_coords = nv_sig['coords']
    adjusted_coords = (numpy.array(passed_coords) + numpy.array(drift)).tolist()
    adjusted_nv_sig = copy.deepcopy(nv_sig)
    adjusted_nv_sig['coords'] = adjusted_coords
    
    # Get the shared parameters from the registry
    shared_params = tool_belt.get_shared_parameters_dict(cxn)
    
    expected_count_rate = adjusted_nv_sig['expected_count_rate']
    
    opti_succeeded = False
    
    # %% Try to optimize
    
    num_attempts = 2
    
    for ind in range(num_attempts):
        
        if ind > 0:
            print('Trying again...')
        
        # Create 3 plots in the figure, one for each axis
        fig = None
        if plot_data:
            fig = create_figure()
        
        # Optimize on each axis
        opti_coords = []
        
        opti_coords.append(passed_coords[0])
        opti_coords.append(passed_coords[1])
        

        ret_vals = optimize_on_axis(cxn, adjusted_nv_sig, 2,
                                    shared_params, apd_indices, fig)
        opti_coords.append(ret_vals[0])
        voltages_by_axis = ret_vals[1]
        counts_by_axis = ret_vals[2]
            
        # We failed to get optimized coordinates, try again
        if None in opti_coords:
            continue
            
        # Check the count rate
        opti_count_rate = stationary_count_lite(cxn, opti_coords,
                                                shared_params, apd_indices)
        
        # Verify that our optimization found a reasonable spot by checking
        # the count rate at the center against the expected count rate
        if expected_count_rate is not None:
            
            lower_threshold = expected_count_rate * 3/4
            upper_threshold = expected_count_rate * 5/4
            
            if ind == 0:
                print('Expected count rate: {}'.format(expected_count_rate))
                
            print('Count rate at optimized coordinates: {:.1f}'.format(opti_count_rate))
            
            # If the count rate close to what we expect, we succeeded!
            if lower_threshold <= opti_count_rate <= upper_threshold:
                print('Optimization succeeded!')
                opti_succeeded = True
            else:
                print('Count rate at optimized coordinates out of bounds.')
                # If we failed by expected counts, try again with the
                # coordinates we found. If x/y are off initially, then
                # z will give a false optimized coordinate. x/y will give
                # true optimized coordinates regardless of the other initial
                # coordinates, however. So we might succeed by trying z again 
                # at the optimized x/y. 
                adjusted_nv_sig['coords'] = opti_coords
                
        # If the threshold is not set, we succeed based only on optimize       
        else:
            print('Count rate at optimized coordinates: {:.0f}'.format(opti_count_rate))
            print('Optimization succeeded! (No expected count rate passed.)')
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
            tool_belt.set_xyz(cxn, opti_coords)
        else:
            # Let the user know something went wrong
            print('Optimization failed. Resetting to coordinates ' \
                  'about which we attempted to optimize.')
            tool_belt.set_xyz(cxn, adjusted_coords)
    else:
        if opti_succeeded:
            print('Optimized coordinates: ')
            print('{:.3f}, {:.3f}, {:.2f}'.format(*opti_coords))
            print('Drift: ')
            print('{:.3f}, {:.3f}, {:.2f}'.format(*drift))
        else:
            print('Optimization failed.')
            
    print('\n')
                               
    # %% Clean up and save the data
    
    tool_belt.reset_cfm(cxn)

    # Don't bother saving the data if we're just using this to find the
    # optimized coordinates
    if save_data:

        timestamp = tool_belt.get_time_stamp()

        rawData = {'timestamp': timestamp,
                   'nv_sig': nv_sig,
                   'nv_sig-units': tool_belt.get_nv_sig_units(),
                   'readout': shared_params['continuous_readout_dur'],
                   'readout-units': 'ns',
                   'opti_coords': opti_coords,
                   'opti_coords-units': 'V',
                   'z_voltages': voltages_by_axis.tolist(),
                   'z_voltages-units': 'V',
                   'z_counts': counts_by_axis.tolist(),
                   'z_counts-units': 'number'}

        filePath = tool_belt.get_file_path(__file__, timestamp,
                                           nv_sig['name'])
        tool_belt.save_raw_data(rawData, filePath)
        
        if fig is not None:
            tool_belt.save_figure(fig, filePath)
            
    # %% Return the optimized coordinates we found
    
    return opti_coords
