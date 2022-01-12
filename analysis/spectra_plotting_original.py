# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 10:17:30 2020

Plot spectra data from a json file with the wavelengths and counts

(note, the function to specify range doesn't set the upper bound properly...
Might be with multiple spectra stitched together, the step sizes are slightly 
different)

@author: agardill
"""

import utils.tool_belt as tool_belt
from scipy.optimize import curve_fit
import numpy
import matplotlib.pyplot as plt
import analysis.file_conversion.spectra_csv_to_json as spectra_csv_to_json

# %%
directory = 'E:/Shared drives/Kolkowitz Lab Group/nvdata'

# %%

def wavelength_range_calc(wavelength_range, wavelength_list):
    '''
    A function to input wavelengths and have pythion figure out what indexes 
    of the data that corresponds to
    Parameters
    ----------
    wavelength_range : TYPE
        DESCRIPTION.
    wavelength_list : TYPE
        DESCRIPTION.

    Returns
    -------
    plot_strt : TYPE
        DESCRIPTION.
    plot_end : TYPE
        DESCRIPTION.

    '''
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

#%%
def read_csv(file, folder):
    folder_path = directory + '/' + folder
    file_path = directory + '/' + folder + '/' + file + '.csv'
    
    wavelength_list = []
    counts_list = []
    # try:
    #     #see if there is a .txt file already
    #     f = open(file_path, 'r')
    # except Exception:
    #     # if not, convert .csv file to .txt file
    spectra_csv_to_json.convert_single_file(folder_path, file)
    f = open(file_path, 'r')
        
    f_lines = f.readlines()
    for line in f_lines:
        wavelength, counts = line.split()
        wavelength_list.append(float(wavelength))
        counts_list.append(float(counts))
        
    return numpy.array(wavelength_list), numpy.array(counts_list)
    

# %%
    
def plot_spectra(file, wavelengths, counts, plot_title):
    
    fig, ax= plt.subplots(1, 1, figsize=(10, 8))
    ax.plot(wavelengths, counts)
    ax.set_xlabel('Wavelength (nm)')
    ax.set_ylabel('Counts')
    ax.set_title(plot_title)

        
        
        
    
# %%


if __name__ == '__main__':
    
    
    folder = 'horiba_spectrometer/2022_01'
    file = '2022_01_05-spot1_1'
    wavelengths, counts = read_csv(file, folder)

    plot_title = 'Quantum dot, collecting from spot 1, 1/10/2022'
    plot_spectra(file, wavelengths, counts, plot_title)

    
    
    