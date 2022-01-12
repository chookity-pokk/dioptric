# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 12:00:14 2019

@author: Aedan
"""

import numpy
import matplotlib.pyplot as plt
import utils.tool_belt as tool_belt
from scipy.optimize import curve_fit

# %%
def gaussian(x, *params):
    """
    Calculates the value of a gaussian for the given input and parameters

    Params:
        x: float
            Input value
        params: tuple
            The parameters that define the Gaussian
            0: coefficient that defines the peak height
            1: mean, defines the center of the Gaussian
            2: standard deviation, defines the width of the Gaussian
            3: constant y value to account for background
    """

    coeff, mean, stdev = params
    var = stdev**2  # variance
    centDist = x-mean  # distance from the center
    return coeff**2*numpy.exp(-(centDist**2)/(2*var))

def txt_read(file_name):
    folder = 'E:/Shared drives/Kolkowitz Lab Group/nvdata/spectra/Brar/Graphene Y2O3/'

    wavelength_list = []
    counts_list = []

# Read in the wavelengths and counts, save to lists
    f = open(folder + '/' + file_name + '.txt', 'r')
    
    f_lines = f.readlines()
    for line in f_lines:
        wavelength, counts = line.split()
        wavelength_list.append(float(wavelength))
        counts_list.append(float(counts))
        
    return numpy.array(wavelength_list), numpy.array(counts_list)
    

def creat_fig(low_wavelength_ind, upper_wavelength_ind, y_lim,
              wavelengths, data_arrays, labels, number_of_subplots):
    
    fig, axes = plt.subplots(4, 2, figsize=(10, 14))
    
    r_ind = 0
    c_ind = 0
    for i in range(number_of_subplots):
        
        
        ax = axes[r_ind,c_ind]
        counts = data_arrays[i]
        if i % 2 == 0 :
            format = 'b-'
        else:
            format = 'r-'
        ax.plot(wavelengths[low_wavelength_ind:upper_wavelength_ind],
                counts[low_wavelength_ind:upper_wavelength_ind], format, 
                label = labels[i])
        ax.set_xlabel('Wavelength (nm)')
        ax.set_ylabel('Counts (arb.)')
        ax.set_ylim(y_lim)
        ax.legend()
        
        if c_ind == 0:
            c_ind = 1
        elif c_ind == 1:
            c_ind = 0
            r_ind = r_ind +  1
#        elif c_ind == 2:
#            r_ind = r_ind +  1
#            c_ind = 0 
        
    return fig
        
        
# %%

if __name__ == '__main__':
    a_1= '2019_11_26_18_38_15_01' # LOW
    b_1 = '2019_11_26_18_42_13_01'
    
    a_2= '2019_11_26_18_52_04_01'  # HIGH
    b_2 = '2019_11_26_18_47_32_01'
    
    a_3= '2019_11_26_18_58_17_01' # LOW
    b_3 = '2019_11_26_19_00_37_01'
    
    a_4= '2019_11_26_19_07_53_01' # HIGH
    b_4 = '2019_11_26_19_10_47_01'
    
    a_5= '2019_11_26_19_18_14_01' # LOW
    b_5 = '2019_11_26_19_21_14_01'
    
    a_6= '2019_11_26_19_27_02_01' # HIGH
    b_6 = '2019_11_26_19_31_11_01'
    
    a_7= '2019_11_26_19_43_20_01'  # LOW
    b_7 = '2019_11_26_19_39_25_01'
    
#    bckd_550 = '550_background_01'
#    bckd_670 = '670_background_01'
    
#    wavelength_550, bckd_550_counts = txt_read(bckd_550)
#    wavelength_670, bckd_670_counts = txt_read(bckd_670)
    
    wavelength_550, a_1_counts = txt_read(a_1)
    wavelength_670, b_1_counts = txt_read(b_1)
    _, a_2_counts = txt_read(a_2)
    _, b_2_counts = txt_read(b_2)
    _, a_3_counts = txt_read(a_3)
    _, b_3_counts = txt_read(b_3)
    _, a_4_counts = txt_read(a_4)
    _, b_4_counts = txt_read(b_4)
    _, a_5_counts = txt_read(a_5)
    _, b_5_counts = txt_read(b_5)
    _, a_6_counts = txt_read(a_6)
    _, b_6_counts = txt_read(b_6)
    _, a_7_counts = txt_read(a_7)
    _, b_7_counts = txt_read(b_7)
    
    
    a_1_norm = (a_1_counts - numpy.average(a_1_counts[0:170]))*1
    b_1_norm = b_1_counts - numpy.average(b_1_counts[0:170])
    
    a_2_norm = (a_2_counts - numpy.average(a_2_counts[0:170]))*1.0654
    b_2_norm = b_2_counts - numpy.average(b_2_counts[0:170])
    
    a_3_norm = (a_3_counts - numpy.average(a_3_counts[0:170]))*1.1094
    b_3_norm = b_3_counts - numpy.average(b_3_counts[0:170])
    
    a_4_norm = (a_4_counts - numpy.average(a_4_counts[0:170]))*1.0834
    b_4_norm = b_4_counts - numpy.average(b_4_counts[0:170])
    
    a_5_norm = (a_5_counts - numpy.average(a_5_counts[0:170]))*1.1026
    b_5_norm = b_5_counts - numpy.average(b_5_counts[0:170])
    
    a_6_norm = (a_6_counts - numpy.average(a_6_counts[0:170]))*1.1171
    b_6_norm = b_6_counts - numpy.average(b_6_counts[0:170])
    
    a_7_norm = (a_7_counts - numpy.average(a_7_counts[0:170]))*1.2102
    b_7_norm = b_7_counts - numpy.average(b_7_counts[0:170])

    a_counts = [a_1_norm, a_2_norm, a_3_norm, a_4_norm, a_5_norm, a_6_norm, a_7_norm]
    b_counts = [b_1_norm,b_2_norm,b_3_norm, b_4_norm, b_5_norm, b_6_norm, b_7_norm]
    
    labels = ['-3.5 V (1)', '4.2 V (2)', '-3.5 V (3)', '4.2 V (4)', '-3.5 V (5)'
              , '4.2 V (6)', '-3.5 V (7)']
    
    fig_550 = creat_fig(490, 830, [-20,200],
              wavelength_550, a_counts, labels, 7)
    
    fig_550.tight_layout()
#    
    fig_670 = creat_fig(180, 520, [-20,200],
              wavelength_670, b_counts, labels, 7)
    
    fig_670.tight_layout()
    
#    lower = 740
#    upper = 850
#    
#    init_guess = [100, 564, 1, 5]
#    popt,pcov = curve_fit(tool_belt.gaussian, wavelength_550[lower:upper], 
#                          a_5_norm[lower:upper], p0=init_guess)
#    linspace_wavelength = numpy.linspace(562,570,1000)
##    
#
#    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
##    
#    ax.plot(wavelength_550[lower:upper], a_5_norm[lower:upper], 'r.')
#    ax.plot(linspace_wavelength, tool_belt.gaussian(linspace_wavelength,*popt), 
#            'b-')
    
#    init_guess = [10, 662, 1, 10]
#    popt,pcov = curve_fit(tool_belt.gaussian, wavelength_670[346:401], 
#                          b_7_norm[346:401], p0=init_guess)
#    linspace_wavelength = numpy.linspace(660,664,1000)
##    
#    print(popt[0]**2 + popt[3])
#    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
##    
#    ax.plot(wavelength_670[346:401], b_7_norm[346:401], 'r.')
#    ax.plot(linspace_wavelength, tool_belt.gaussian(linspace_wavelength,*popt), 
#            'b-')
    
#    print(popt[0]**2 + popt[3])