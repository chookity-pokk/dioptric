# -*- coding: utf-8 -*-
"""
Created on Fri Nov 19 09:55:03 2021

@author: agard
"""



import utils.tool_belt as tool_belt
import numpy
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

m = 2
dx_max= 0.00796*m #um
dy_max= 0.006189*m #um
dz_max= 0.0703*m #V

def do_postselect(file, folder, scale = 1000):
    data = tool_belt.get_raw_data(file, folder)
    drift_list_master = data['drift_list_master']
    # rad_dist =data['rad_dist']
    coords_voltages = data['coords_voltages']
    x_voltages = numpy.array([el[0] for el in coords_voltages])
    y_voltages = numpy.array([el[1] for el in coords_voltages])
    num_steps = data['num_steps_a']
    readout_counts_array = numpy.flipud(numpy.rot90(data['readout_counts_array']))
    ps_readout_counts_array = []
    
    drift_x = []
    drift_y = []
    drift_z = []
    
    # create a single list of all the drifts
    for i in range(len(drift_list_master)):
        drifts_for_run = drift_list_master[i]
        for j in range(len(drifts_for_run)):
            #just take the first optimize, which should ocur at regular intervals
            # based on the time elapsed and the number of runs
            drift_x.append(drifts_for_run[j][0])
            drift_y.append(drifts_for_run[j][1])
            drift_z.append(drifts_for_run[j][2])
    
    # create a single lists of the change in drift from point n-1 to point n, 
    # starting at 1. Put in a 0th index with value of 0
    dx_drift = [0]
    dy_drift = [0]
    dz_drift = [0]
    
    for i in range(len(drift_x)-1):
        i = i+1
        dx = drift_x[i] - drift_x[i-1]
        dx_drift.append(dx)
        dy = drift_y[i] - drift_y[i-1]
        dy_drift.append(dy)
        dz = drift_z[i] - drift_z[i-1]
        dz_drift.append(dz)
    #now go throguh the lsit of drifts, keep track of what change in drift we are on,
    # and if the change in drift during a run is too large, exclude that data.
    #the change in drift corresponds to the current index, so if it is too large, we throw out that index
    flattened_d_ind = 0
    for n in range(len(drift_list_master)):
        num_opti = len(drift_list_master[n])
        drift_too_large = False
        # check each of the drifts in the run. Right now, we're tossing out the whole run if 
        #one of the change in drifts was too large. Could get more sophisticated in future.
        for i in range(num_opti):
            d = flattened_d_ind + i # the index we want to consider in the flattened change-in-drift lists
            # print(n)
            # print(dx_drift[d])
            # print(dy_drift[d])
            # print(dz_drift[d])
            if abs(dz_drift[d]) > dz_max:
            # if abs(dx_drift[d]) > dx_max:# or abs(dy_drift[d]) > dy_max:#or abs(dz_drift[d]) > dz_max:
                drift_too_large = True #if the change in any axis is too large, flag it
            # print(drift_too_large)
        
        if not drift_too_large:
            ps_readout_counts_array.append(readout_counts_array[n]) #only keep the data if the changes were small
        flattened_d_ind = flattened_d_ind + num_opti

    print(len(ps_readout_counts_array))
    
             
    # Take the average and ste. 
    readout_counts_avg = numpy.average(ps_readout_counts_array, axis = 0)

# %% Plot    
    rad_dist = numpy.sqrt((x_voltages - x_voltages[0])**2 + (y_voltages - y_voltages[0])**2 )*scale
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    ax.plot(rad_dist,readout_counts_avg, 'b.')
    ax.set_xlabel('r (m)')
    ax.set_ylabel('Average counts')
        
    opti_params = []
    
    fit_func = tool_belt.gaussian


    init_fit = [2, rad_dist[int(num_steps/2)], 15, 7]
    opti_params, cov_arr = curve_fit(fit_func,
          rad_dist,
          readout_counts_avg,
          p0=init_fit
          )
    text = r'$C + A^2 e^{-(r - r_0)^2/(2*\sigma^2)}$'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)
    lin_radii = numpy.linspace(rad_dist[0],
                    rad_dist[-1], 100)
    ax.plot(lin_radii,
            fit_func(lin_radii, *opti_params), 'r-')
    text = 'A={:.3f} sqrt(counts)\n$r_0$={:.3f} nm\n ' \
        '$\sigma$={:.3f}+/-{:.3f} nm\nC={:.3f} counts'.format(opti_params[0],
                    opti_params[1],opti_params[2],cov_arr[2][2],opti_params[3])
    ax.text(0.3, 0.1, text, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)
    print(opti_params[2])
    print(cov_arr[2][2])
# %%
folder = 'pc_rabi/branch_CFMIII/SPaCE_digital/2021_11'
file = '2021_11_22-09_01_24-johnson-nv1_2021_11_17'
do_postselect(file, folder)

