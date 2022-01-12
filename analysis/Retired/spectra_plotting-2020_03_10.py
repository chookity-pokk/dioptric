# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 10:17:30 2020

Plot spectra data from a json file with the wavelengths and counts

Specifically for plotting data from 3/10 and 3/9 of Er samples without graphene

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
    
    plot_strt_ind, plot_end_ind  = wavelength_range_calc(wavelength_range, wavelengths)
    
    # subtract off a constant background
    counts_cnst_bkgd = counts - numpy.average(counts[plot_end_ind-8:plot_end_ind])
    
    return wavelengths[plot_strt_ind : plot_end_ind], counts[plot_strt_ind : plot_end_ind]
        
        
        
    
# %%

# Measurements on 5 nm Er 3/9
folder_5 = '5_nm_ionic_gel_tests'

file_n_g_n_ig_550_5nm = 'no_g_no_ig_550'
file_n_g_n_ig_660_5nm = 'no_g_no_ig_660'

file_n_g_y_ig_550_5nm = 'no_g_yes_ig_550'
file_n_g_y_ig_660_5nm = 'no_g_yes_ig_660'


# Measurements on 10 nm Er 3/10
folder_10 = '10_nm_ionic_gel_tests'

file_n_g_n_ig_550_10nm = 'no_g_no_ig_550'
file_n_g_n_ig_660_10nm = 'no_g_no_ig_660'

file_n_g_y_ig_550_10nm = 'no_g_yes_ig_550'
file_n_g_y_ig_660_10nm = 'no_g_yes_ig_660'

if __name__ == '__main__':
    
     # 550 nm, no ionic gel
#    wvlngth_1, counts_1 = plot_spectra(file_n_g_n_ig_550_5nm, folder_5,  [None, None], [-100, 300],'5 nm Er')
#    wvlngth_1, counts_1 = plot_spectra(file_n_g_n_ig_550_10nm, folder_10, [None, None], [-100, 300],'10 nm Er')
#     660 nm, no ionic gel
    wvlngth_1, counts_1 = plot_spectra(file_n_g_n_ig_660_5nm, folder_5,  [None, None], [-100, 300],'5 nm Er')
#    wvlngth_1, counts_1 = plot_spectra(file_n_g_n_ig_660_10nm, folder_10, [None, None], [-100, 300],'10 nm Er')
    
        
     # 550 nm, with ionic gel
#    wvlngth_2, counts_2 = plot_spectra(file_n_g_y_ig_550_5nm, folder_5,  [None, None], [-100, 300],'5 nm Er')
#    wvlngth_2, counts_2 = plot_spectra(file_n_g_y_ig_550_10nm, folder_10, [None, None], [-100, 300],'10 nm Er')
    # 660 nm, with ionic gel
    wvlngth_2, counts_2 = plot_spectra(file_n_g_y_ig_660_5nm, folder_5,  [None, None], [-100, 300],'5 nm Er')
#    wvlngth_2, counts_2 = plot_spectra(file_n_g_y_ig_660_10nm, folder_10, [None, None], [-100, 300],'10 nm Er')

    fig, ax= plt.subplots(1, 1, figsize=(10, 8))
    
#    print(counts_1)
    ax.set_xlabel('Wavelength (nm)')
    ax.set_ylabel('Counts')
    ax.set_title('Spectra (compare ionic gel addition)')
    ax.set_ylim([500, 1000]) 
    ax.plot(wvlngth_1, counts_1, label = '5 nm Er w/out ionic gel')
    ax.plot(wvlngth_2, counts_2, label = '5 nm Er w/ ionic gel')
    ax.legend()

    
    
    
    