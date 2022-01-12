# -*- coding: utf-8 -*-
"""
Created on Fri Nov 12 09:55:03 2021

@author: agard
"""



import utils.tool_belt as tool_belt
import numpy
import matplotlib.pyplot as plt


def do_plot_drift(file, folder, x_unit, y_unit, z_unit):
    data = tool_belt.get_raw_data(file, folder)
    num_runs = data['num_runs']
    opti_timestamps = numpy.array(data['opti_timestamps'])
    drift_list_master = data['drift_list_master']
    
    time_vals = (opti_timestamps - opti_timestamps[0])/60
    
    
    drift_x = []
    drift_y = []
    drift_z = []
    
    for i in range(len(drift_list_master)):
        drifts_for_run = drift_list_master[i]
        for j in range(len(drifts_for_run)):
            #just take the first optimize, which should ocur at regular intervals
            # based on the time elapsed and the number of runs
            drift_x.append(drifts_for_run[j][0])
            drift_y.append(drifts_for_run[j][1])
            drift_z.append(drifts_for_run[j][2])
    
    
    fig, axes = plt.subplots(1,3)
    ax=axes[0]
    ax.plot(time_vals, drift_x)
    ax.set_xlabel('Time elapsed (m)')
    ax.set_ylabel('Drift ({})'.format(x_unit))
    ax.set_title('X')
    ax=axes[1]
    ax.plot(time_vals, drift_y)
    ax.set_xlabel('Time elapsed (m)')
    ax.set_ylabel('Drift ({})'.format(y_unit))
    ax.set_title('Y')
    ax=axes[2]
    ax.plot(time_vals, drift_z)
    ax.set_xlabel('Time elapsed (m)')
    ax.set_ylabel('Drift ({})'.format(z_unit))
    ax.set_title('Z')
    plt.tight_layout()
    
    # create a signle lists of the change in drift from point n-1 to point n, 
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

    print('dx st. dev: {} {}'.format(numpy.std(abs(numpy.array(dx_drift))), x_unit ))
    print('dy st. dev: {} {}'.format(numpy.std(abs(numpy.array(dy_drift))), y_unit ))
    print('dz st. dev: {} {}'.format(numpy.std(abs(numpy.array(dz_drift))), z_unit ))
    fig, axes = plt.subplots(1,3)
    ax=axes[0]
    ax.plot(time_vals, dx_drift, 'r')
    ax.set_xlabel('Time elapsed (m)')
    ax.set_ylabel('Change in drift, n+1 - n ({})'.format(x_unit))
    ax.set_title('X')
    ax=axes[1]
    ax.plot(time_vals, dy_drift,'r')
    ax.set_xlabel('Time elapsed (m)')
    ax.set_ylabel('Change in drift, n+1 - n ({})'.format(y_unit))
    ax.set_title('Y')
    ax=axes[2]
    ax.plot(time_vals, dz_drift, 'r')
    ax.set_xlabel('Time elapsed (m)')
    ax.set_ylabel('Change in drift, n+1 - n ({})'.format(z_unit))
    ax.set_title('Z')
    plt.tight_layout()
    
    


folder = 'pc_rabi/branch_CFMIII/SPaCE_digital/2021_11'
file = '2021_11_24-18_55_36-johnson-nv1_2021_11_17'
file='2021_11_24-18_55_35-johnson-nv1_2021_11_17'
do_plot_drift(file, folder, 'um', 'um', 'V')


folder = 'pc_rabi/branch_CFMIII/SPaCE/2021_11'
file = '2021_11_09-17_08_05-johnson-nv1_2021_11_08'
# do_plot_drift(file, folder, 'V', 'V', 'V')

folder = 'pc_rabi/branch_master/SPaCE/2021_10'
file = '2021_10_23-11_24_22-ayrton_101-nv0_2021_10_20'
# do_plot_drift(file, folder, 'V', 'V', 'V')