# -*- coding: utf-8 -*-
"""
Created on Fri May 31 11:06:46 2019

This routine takes the rates found from the modified functions used in the
Myer's paper (ex: [0,0] - [0,1] and [1,1] - [1,-1]) split into different bins
to extract a stdev of one bin. Then it propegates this statistical uncertainty
into the actual values of omega nad gamma.

The main of this file uses the
relaxation_rate_binning.main function to caluclate the average and standard
deviation of the g and o rate values. It either calculates the factors of
the experiment's  num_runs for the bin sizes or takes a list of bin sizes. It
then fits the standard deviation values vs number of bins to a square root fit
to extract the standard deviation of one single bin. Then it will propegate the
uncertainty for the actual omega and gamma values, as well as calculate the
actual value of omega and gamma.

Calculations, given a rates o and g from the exponential fits:
    omega = o / 3
    gamma = (g - omega) / 2

    omega_stdev = del(o) / 3
    gamma_stdev = Sqrt[del(g)**2 + omega_stdev**2] / 2


This file only works if all the experiments in a folder have the same number
of num_runs, and can only handle two data sets of the same experiment (ie +1 to
+1, a short and a long run).

@author: Aedan
"""

# %% Imports

import time
import numpy
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

import utils.tool_belt as tool_belt
import analysis.relaxation_rate_binning as relaxation_rate_binning

# %% Constants

data_folder = 't1_double_quantum'

# %% Functions

# Calculate the factors
def factors(number):
    factor_list = []
    for n in range(1, number + 1):
        if number % n == 0:
            factor_list.append(n)

    return factor_list

def sqrt_eq(x, amp):
    return amp * (x)**(1/2)

# %% Main

def main(folder_name, num_bins_list = None, offset = True):

    # If the list for number of bins is not passed through, use the factors of
    # the num_runs
    if num_bins_list == None:

        # Get the file list from this folder
        file_list = tool_belt.get_file_list(data_folder, '.txt', folder_name)

        # Get the number of runs to create the empty arrays from the first file in
        # the list. This requires all the relaxation measurements to have the same
        # num_runs
        for file in file_list:
            data = tool_belt.get_raw_data(data_folder, file[:-4], folder_name)

            try:
                num_runs = data['num_runs']
            except Exception:
                continue

        # Get the num_bins to use based on the factors of the number of runs

        num_bins_list = factors(num_runs)

    # Set up lists to save relavent data to

    o_value_list = []
    o_stdev_list = []
    g_value_list = []
    g_stdev_list = []

    # Create lists to put the fit_failed information in. We will fill each
    # element of the list with the list given by the analysis routine
    o_fit_failed_list = [None] * len(num_bins_list)
    g_fit_failed_list = [None] * len(num_bins_list)


    # Step through the various bin sizes and compute the average and standard
    # deviation
    for num_bins_ind in range(len(num_bins_list)):
        num_bins = num_bins_list[num_bins_ind]
        retvals = relaxation_rate_binning.main(folder_name, num_bins, False, True)

        # Save the data to the lists
        o_value_list.append(retvals[0])
        o_stdev_list.append(retvals[1])
        g_value_list.append(retvals[2])
        g_stdev_list.append(retvals[3])
        splitting_MHz = retvals[4]

        o_fit_failed_list[num_bins_ind] = retvals[5]
        g_fit_failed_list[num_bins_ind] = retvals[6]


        # Save the calculated value of omega and gamma for the data for one bin
        if num_bins == 1:
            o_value_one_bin = retvals[0]
            g_value_one_bin = retvals[2]

    # Take the average over the different values found using the different bin
    # sizes to compare to the value found using one bin
    o_value_avg = numpy.average(o_value_list)
    g_value_avg = numpy.average(g_value_list)


    # Fit the data to sqrt and extract the standard deviation value for one bin

    opti_params, cov_arr = curve_fit(sqrt_eq, num_bins_list,
                                     o_stdev_list, p0 = (0.1))
    o_stdev = sqrt_eq(1, opti_params[0])

    opti_params, cov_arr = curve_fit(sqrt_eq, num_bins_list,
                                     g_stdev_list, p0 = (1))
    g_stdev = sqrt_eq(1, opti_params[0])


    # Plot the data to visualize it. This plot is not saved
    bin_linspace = numpy.linspace(num_bins_list[0], num_bins_list[-1], 1000
                                  )
    plt.loglog(num_bins_list, g_stdev_list, 'go', label = 'g rate standard deviation')
    plt.loglog(bin_linspace, sqrt_eq(bin_linspace, opti_params), 'teal', label = 'Sqrt[bin_size]')
    plt.loglog(num_bins_list, o_stdev_list, 'bo', label = 'o rate standard deviation')
    plt.xlabel('Number of bins for num_runs')
    plt.ylabel('Standard Deviation (kHz)')
    plt.legend()

    # We have calculated the average rate for the two fits and their stdev, and
    # NOW we finally calculate what omega nad gamma are, and their uncertainty

    omega_value_one_bin = o_value_one_bin / 3.0
    gamma_value_one_bin = (g_value_one_bin - omega_value_one_bin) / 2.0

    omega_value_avg = o_value_avg / 3.0
    gamma_value_avg = (g_value_avg - omega_value_one_bin) / 2.0

    omega_stdev = o_stdev / 3.0
    gamma_stdev = numpy.sqrt(g_stdev**2 + omega_stdev**2) / 2.0

    print('Omega Value = {}, std dev = {}'.format(omega_value_one_bin, omega_stdev))
    print('Gamma Value = {}, std dev = {}'.format(gamma_value_one_bin, gamma_stdev))
    time_stamp = tool_belt.get_time_stamp()
    raw_data = {'time_stamp': time_stamp,
                'splitting_MHz': splitting_MHz,
                'splitting_MHz-units': 'MHz',
                'offset_free_param?': offset,
                'omega_value_one_bin': omega_value_one_bin,
                'omega_value-units': 'kHz',
                'omega_stdev': omega_stdev,
                'omega_stdev-units': 'kHz',
                'gamma_value_one_bin': gamma_value_one_bin,
                'gamma_value-units': 'kHz',
                'gamma_stdev': gamma_stdev,
                'gamma_stdev-units': 'kHz',
                'omega_value_avg': omega_value_avg,
                'omega_value_avg-units': 'kHz',
                'gamma_value_avg': gamma_value_avg,
                'gamma_value_avg-units': 'kHz',
                'num_bins_list': num_bins_list,
                'o_fit_failed_list': o_fit_failed_list,
                'g_fit_failed_list': g_fit_failed_list,
                'o_value_list': o_value_list,
                'o_value_list-units': 'kHz',
                'o_stdev_list': o_stdev_list,
                'o_stdev_list-units': 'kHz',
                'g_value_list': g_value_list,
                'g_value_list-units': 'kHz',
                'g_stdev_list': g_stdev_list,
                'g_stdev_list-units': 'kHz'
                }

    data_dir='E:/Shared drives/Kolkowitz Lab Group/nvdata'

    file_name = time_stamp + '_' + str('%.1f'%splitting_MHz) + \
                '_MHz_splitting_rate_analysis'
    file_path = '{}/{}/{}/{}'.format(data_dir, data_folder, folder_name,
                                                         file_name)

    print(file_path)

    tool_belt.save_raw_data(raw_data, file_path)


# %% Run the file

if __name__ == '__main__':


    # Set the file to pull data from here. These should be files in our
    # Double_Quantum nvdata folder, filled with the 6 relevant experiments

    folder = 'nv0_2019_06_27_233MHz'


    '''
    MAIN: this will calculate the value and standard deviation of gamma and
        omega for the whole data set.

        First try to run main(folder)

        It's important to check that the values make sense: occaionally when
        the bins get too small the data is too noisy to accurately fit.
        Check that the standard deviation is reasonable (we've been seeing a
        stdev ~ 20-5%), in the saved txt file, compare the values found from
        averaging all the data (one bin) and averaging the bins seperately
        (average value).
        If those seem off, check the bottom of the saved txt file for the list
        of values. If some of the values are orders of magnitude larger,
        exclude those bin numbers from the bin list, and run this file with a
        set bin list.

    '''


#    main(folder, offset= True)


    # Specify the number of bins

    num_bins_list = [1, 2, 3, 4, 5, 6, 8, 10, 12]
    main(folder, num_bins_list, offset = True)
