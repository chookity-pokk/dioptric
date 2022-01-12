# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 10:17:30 2020

Plot spectra data from a json file with the wavelengths and counts

Specifically for plotting data from 3/11 of trying to focus on Er in 10 sample 
with ionic gel

@author: agardill
"""

import utils.tool_belt as tool_belt
from scipy.optimize import curve_fit
import numpy
import matplotlib.pyplot as plt

# %%

props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)

data_path = 'C:/Users/Public/Documents/Jobin Yvon/SpectraData'

#folder = '5_nm_Er_graphene/2020_03_02'

#folder = '5_nm_Er_NO_graphene_NO_ig'

# %%

def cosmic_ray_subtraction(counts, cutoff):
    index_list = []
    double_index_list = []
    i = 0
    while i < len(counts):
        print(i)
        if counts[i] > cutoff:         
            if i == 0 or i == len(counts)-1 or i == len(counts)-2:
                index_list.append(i)
                i = i + 1
            else:
                if counts[i+1] > cutoff:
                    double_index_list.append(i)
#                    double_index_list.append(i+1)
                    i = i + 2
                else:
                    index_list.append(i)
                    i = i + 1
        else:
            i = i+1
    # average down single spikes in counts 
    for ind in index_list:
        if ind == 0:
            counts[0] = counts[1]
        elif ind == len(counts)-1:
            counts[-1] = counts[-2]
        else:
            counts[ind] = numpy.average([counts[ind-1], counts[ind+1]])
            
    # average down two consecutive spikes in counts 
    for ind in double_index_list:
        avg = numpy.average([counts[ind-1], counts[ind+2]])
        counts[ind] = avg
        counts[ind+1] = avg
            
    return counts

def wavelength_range_calc(wavelength_range, wavelength_list):
    wvlngth_range_strt = wavelength_range[0]
    wvlngth_range_end = wavelength_range[1]
    
    wvlngth_list_strt = wavelength_list[0]
    wvlngth_list_end = wavelength_list[-1]
    step_size = wavelength_list[1] - wavelength_list[0]
    
    # Try to calculate the indices for plotting, if they are given
    try: 
        start_index = int( (wvlngth_range_strt - wvlngth_list_strt) /  step_size )
    except Exception:
        pass
    try: 
        end_index = -(int((wvlngth_list_end - wvlngth_range_end) /  step_size) + 1)
    except Exception:
        pass
            
    
    #If both ends of range are specified
    if wvlngth_range_strt and wvlngth_range_end:
        
        #However, if the range is outside the actual data, just plot all data
        # Or if one of the bounds is outside the range, do not include that range
        if wvlngth_range_strt < wvlngth_list_strt and \
                                    wvlngth_range_end > wvlngth_list_end:
            print('Wavelength range outside of data range. Plotting full range of data')
            plot_strt = 0
            plot_end = -1
        elif wvlngth_range_strt < wvlngth_list_strt and \
            wvlngth_range_end <= wvlngth_list_end:
                
            print('Requested lower bound of wavelength range outside of data range. Starting data at lowest wavelength')
            plot_strt = 0
            plot_end = end_index
            
        elif wvlngth_range_strt >= wvlngth_list_strt and \
            wvlngth_range_end > wvlngth_list_end:
                
            print('Requested upper bound of wavelength range outside of data range. Plotting up to highest wavelength')
            plot_strt = start_index
            plot_end = -1
        else:
            #If they are given, then plot the requested range
            plot_strt = start_index
            plot_end = end_index
            
    # If the lower bound is given, but not the upper bound
    elif wvlngth_range_strt and not wvlngth_range_end:
        plot_end = -1
        
        if wvlngth_range_strt < wvlngth_list_strt:
            print('Requested lower bound of wavelength range outside of data range. Plotting full range of data')
            plot_strt = 0
        else:
            plot_strt = start_index
            
    # If the upper bound is given, but not the lower bound
    elif wvlngth_range_end and not wvlngth_range_strt:
        plot_strt = 0
        
        if wvlngth_range_end > wvlngth_list_end:
            print('Requested upper bound of wavelength range outside of data range. Plotting full range of data')
            plot_end = -1
        else:
            plot_end = end_index
    # Lastly, if no range is given
    elif not wvlngth_range_end and not wvlngth_range_strt:
       plot_strt = 0 
       plot_end = -1
        
    return plot_strt, plot_end

# %%
    
def plot_spectra(file,folder, wavelength_range, vertical_range, plot_title):
    data = tool_belt.get_raw_data(folder, file,
                 nvdata_dir=data_path)
    wavelengths = numpy.array(data['wavelengths'])
    counts = numpy.array(data['counts'])
    
    counts = cosmic_ray_subtraction(counts, 1010)
    
    plot_strt_ind, plot_end_ind  = wavelength_range_calc(wavelength_range, wavelengths)
    
    # subtract off a constant background
#    counts_cnst_bkgd = counts - numpy.average(counts[plot_end_ind-8:plot_end_ind])
    
    return wavelengths[plot_strt_ind : plot_end_ind], counts[plot_strt_ind : plot_end_ind]
        
        
        
    
# %%

# Measurements on 10 nm Er 3/11, collecting data at different focus
folder_10 = '10_nm_ionic_gel_tests'

file_ionic_gel_10nm_1 = 'no_g_yes_ig_550_01'
file_ionic_gel_10nm_2 = 'no_g_yes_ig_550_02'
file_ionic_gel_10nm_3 = 'no_g_yes_ig_550_03'
file_ionic_gel_10nm_4 = 'no_g_yes_ig_550_04'
file_ionic_gel_10nm_5 = 'no_g_yes_ig_550_05'
file_ionic_gel_10nm_6 = 'no_g_yes_ig_550_06'

if __name__ == '__main__':

    labels = ['below oxide surface', 'at oxide surface', '~mm above oxide surface', 'inbetween oxide and ionic gel surface',
              'ionic gel surface', 'sample a few mm our of focus']
    fig, ax= plt.subplots(1, 1, figsize=(10, 8))
    for i in range(6):
        file = 'no_g_yes_ig_550_0' + str(i + 1)
    
        wvlngth, counts = plot_spectra(file, folder_10, [None, None], [-100, 300],'')
    
        ax.set_xlabel('Wavelength (nm)')
        ax.set_ylabel('Counts')
        ax.set_title('Spectra of 10 nm Er (with ionic gel)')
        ax.set_ylim([300, 1360]) 
        ax.plot(wvlngth, counts, label = labels[i])
        ax.legend()

    
    