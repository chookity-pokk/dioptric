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

#data_path = 'C:/Users/Public/Documents/Jobin Yvon/SpectraData'

data_path = 'E:/Shared drives/Kolkowitz Lab Group/nvdata/spectra/Brar'

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
    
def plot_spectra(file,folder, wavelength_range = [None, None], vertical_range = [None, None], plot_title = ''):
    data = tool_belt.get_raw_data(folder, file,
                 nvdata_dir=data_path)
    wavelengths = numpy.array(data['wavelengths'])
    counts = numpy.array(data['counts'])
    
    plot_strt_ind, plot_end_ind  = wavelength_range_calc(wavelength_range, wavelengths)
    
    # subtract off a constant background
    counts_cnst_bkgd = counts - numpy.average(counts[plot_end_ind-8:plot_end_ind])
    
    return wavelengths[plot_strt_ind : plot_end_ind], counts[plot_strt_ind : plot_end_ind]
        
        
        
def plot_spectra_list(parent_folder, file_list, title, label_list, y_range, x_range = None):
    fig, ax= plt.subplots(1, 1, figsize=(10, 8))
    
    for f in range(len(file_list)):
        file = file_list[f]
        wvlngth, counts = plot_spectra(file, parent_folder)
        ax.plot(wvlngth, counts, label =label_list[f])
        
    ax.set_xlabel('Wavelength (nm)')
    ax.set_ylabel('Counts')
    ax.set_title(title)
    ax.set_ylim(y_range)
    if x_range:
        ax.set_xlim(x_range)
    ax.legend()    
   
    
def august_cap_noncap_plots():
    label_list = ['8/10/2020', 
                  #'8/11/2020', '8/12/2020', 
                  #'8/13/2020', 
                  '8/14/2020',
                  '8/21/2020', 
                  #'8/23/2020', 
                  '8/24/2020',
                  '8/25/2020',
                  '9/2/2020'
                  ]
    
    # capped
    title = 'Capped 5 nm Er'
    parent_folder = '2020_08_10 5 nm capped'
    file_list = ['2020_08_10-c-550','2020_08_11-c-550','2020_08_12-c-550',
                 '2020_08_13-c-550','2020_08_14-c-550','2020_08_21-c-550'] 
#    plot_spectra_list(parent_folder, file_list, title, label_list, y_range =[500,1500], x_range = [547, 580] )

    file_list = ['2020_08_10-c-670','2020_08_11-c-670','2020_08_12-c-670',
                 '2020_08_13-c-670','2020_08_14-c-670','2020_08_21-c-670'] 
#    plot_spectra_list(parent_folder, file_list, title, label_list, y_range =[580,750], x_range = [644, 692])
    
    # noncapped
    title = 'Noncapped 5 nm Er'
    parent_folder = '2020_08_10 5 nm noncapped'
    file_list = ['2020_08_10-nc-550',
                 #'2020_08_11-nc-550',
                 #'2020_08_12-nc-550',
                 #'2020_08_13-nc-550',
                 '2020_08_14-nc-550',
                 '2020_08_21-nc-550',
                 #'2020_08_23-nc-550',
                 '2020_08_24-nc-550',
                 '2020_08_25-alignment_test_3',
                 '2020_09_02-2'
                 ] 
    plot_spectra_list(parent_folder, file_list, title, label_list, 
                      y_range =[500,1700])
                      #x_range = [547, 580])

    file_list = ['2020_08_10-nc-670','2020_08_11-nc-670',
                 '2020_08_12-nc-670',
                 '2020_08_13-nc-670',
                 '2020_08_14-nc-670',
                 '2020_08_21-nc-670',
                 #'2020_08_23-nc-670','2020_08_24-nc-670'
                 ] 
#    plot_spectra_list(parent_folder, file_list, title, label_list, y_range =[580,750], x_range = [644, 692])
    
    
    
    
# %%
    
# graphene sheet with gating! take 1
folder_1= '2020_11_03-graphene_nanoribbons'

file_m01_550 = '2020_11_03-gnr-550-m01'
file_m02_550 = '2020_11_03-gnr-550-m02'
file_m03_550 = '2020_11_03-gnr-550-m03'
file_m04_550 = '2020_11_03-gnr-550-m04'
file_m05_550 = '2020_11_03-gnr-550-m05'
file_m06_550 = '2020_11_03-gnr-550-m06'
file_m07_550 = '2020_11_03-gnr-550-m07'
file_m08_550 = '2020_11_03-gnr-550-m08'
file_m09_550 = '2020_11_03-gnr-550-m09'
file_m10_550 = '2020_11_03-gnr-550-m10'
file_m11_550 = '2020_11_03-gnr-550-m11'
file_m12_550 = '2020_11_03-gnr-550-m12'
file_m13_550 = '2020_11_03-gnr-550-m13'
file_m14_550 = '2020_11_03-gnr-550-m14'
file_m15_550 = '2020_11_03-gnr-550-m15'
file_m16_550 = '2020_11_03-gnr-550-m16'
file_m17_550 = '2020_11_03-gnr-550-m17'
file_m18_550 = '2020_11_03-gnr-550-m18'

file_000_550_2 = '2020_11_03-gnr2-550-000'
file_m05_550_2 = '2020_11_03-gnr2-550-m05'
file_m10_550_2 = '2020_11_03-gnr2-550-m10'
file_m15_550_2 = '2020_11_03-gnr2-550-m15'

file_m10_550_3 = '2020_11_03-gnr3-550-m10'
file_m18_550_3 = '2020_11_03-gnr3-550-m18'
#
file_m01_670 = '2020_11_03-gnr-670-m01'
file_m02_670 = '2020_11_03-gnr-670-m02'
file_m03_670 = '2020_11_03-gnr-670-m03'
file_m04_670 = '2020_11_03-gnr-670-m04'
file_m05_670 = '2020_11_03-gnr-670-m05'
file_m06_670 = '2020_11_03-gnr-670-m06'
file_m07_670 = '2020_11_03-gnr-670-m07'
file_m08_670 = '2020_11_03-gnr-670-m08'
file_m09_670 = '2020_11_03-gnr-670-m09'
file_m10_670 = '2020_11_03-gnr-670-m10'
file_m11_670 = '2020_11_03-gnr-670-m11'
file_m12_670 = '2020_11_03-gnr-670-m12'
file_m13_670 = '2020_11_03-gnr-670-m13'
file_m14_670 = '2020_11_03-gnr-670-m14'
file_m15_670 = '2020_11_03-gnr-670-m15'
file_m16_670 = '2020_11_03-gnr-670-m16'
file_m17_670 = '2020_11_03-gnr-670-m17'
file_m18_670 = '2020_11_03-gnr-670-m18'

file_000_670_2 = '2020_11_03-gnr2-670-000'
file_m05_670_2 = '2020_11_03-gnr2-670-m05'
file_m10_670_2 = '2020_11_03-gnr2-670-m10'
file_m15_670_2 = '2020_11_03-gnr2-670-m15'

file_m10_670_3 = '2020_11_03-gnr3-670-m10'
file_m18_670_3 = '2020_11_03-gnr3-670-m18'

# file_550 = file_m18_550
# file_670 = file_m18_670

file_path_base = 'E:/Shared drives/Kolkowitz Lab Group/nvdata/spectra/Brar'
if __name__ == '__main__':
#    august_cap_noncap_plots()
    
    wvlngth_1, counts_1 = plot_spectra(file_000_550_2, folder_1)
    wvlngth_2, counts_2 = plot_spectra(file_m10_550_3, folder_1)
    wvlngth_3, counts_3 = plot_spectra(file_m18_550_3, folder_1)
    # wvlngth_4, counts_4 = plot_spectra(file_m05_550_2, folder_1)
    # wvlngth_5, counts_5 = plot_spectra(file_000_550_2, folder_1)    
    # wvlngth_6, counts_6 = plot_spectra(file_m18_550, folder_1)

    fig, ax= plt.subplots(1, 1, figsize=(10, 8))

    ax.set_xlabel('Wavelength (nm)')
    ax.set_ylabel('Counts')
    ax.set_title('Graphene Nanoribbons')
    ax.plot(wvlngth_1, numpy.array(counts_1), color= '#de6000', label = '0.0 V (CNP)')
    ax.plot(wvlngth_2, numpy.array(counts_2), color = '#00deaa', label = '-1.0 V')
    ax.plot(wvlngth_3, numpy.array(counts_3), color='#c800de', label = '-1.8 V')
    # ax.plot(wvlngth_4, numpy.array(counts_4), color='#1200de', label = '-0.5 V')
    # ax.plot(wvlngth_5, numpy.array(counts_5))
    # ax.plot(wvlngth_5, numpy.array(counts_5), label = '-1.8 V')
    ax.set_xlim([530, 620])
#    ax.set_ylim([530, 2200])
    ax.legend()

    # tool_belt.save_figure(fig, file_path_base + '/' + folder_1 + '/' + file_550)
    
    wvlngth_1, counts_1 = plot_spectra(file_m08_670, folder_1)
    wvlngth_2, counts_2 = plot_spectra(file_m09_670, folder_1)
    wvlngth_3, counts_3 = plot_spectra(file_m10_670, folder_1)
    wvlngth_4, counts_4 = plot_spectra(file_m11_670, folder_1)
    wvlngth_5, counts_5 = plot_spectra(file_m12_670, folder_1)    
    # wvlngth_6, counts_6 = plot_spectra(file_m18_670, folder_1)
    
#     fig2, ax= plt.subplots(1, 1, figsize=(10, 8))
    
#     ax.set_xlabel('Wavelength (nm)')
#     ax.set_ylabel('Counts')
#     ax.set_title('Graphene Nanoribbons')
#     ax.plot(wvlngth_1, numpy.array(counts_1), label = '-0.8 V')
#     ax.plot(wvlngth_2, numpy.array(counts_2), label = '-0.9 V')
#     ax.plot(wvlngth_3, numpy.array(counts_3), label = '-1.0 V')
#     ax.plot(wvlngth_4, numpy.array(counts_4), label = '-1.1 V')
#     ax.plot(wvlngth_5, numpy.array(counts_5), label = '-1.2 V')
#     # ax.plot(wvlngth_5, numpy.array(counts_5), label = '-1.8 V')
#     # ax.set_xlim([645, 695])
# #    ax.set_ylim([675, 1100])
#     ax.legend()
     
    # tool_belt.save_figure(fig2, file_path_base + '/' + folder_1 + '/' + file_670)
    
    
    