# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 12:13:01 2019

@author: Aedan
"""
import numpy
import json
import matplotlib.pyplot as plt

    
# %%

def main():
    directory_mar = 'E:/Shared Drives/Kolkowitz Lab Group/nvdata/lifetime_v2/2020_03'
    
    directory_aug = 'E:/Shared Drives/Kolkowitz Lab Group/nvdata/lifetime_v2/branch_hopper_disable_opt/2020_08'
    
    file_sample_removed_aug = '2020_08_03-15_38_07-5nmEr-search'
    with open(directory_aug + '/'+ file_sample_removed_aug + '.txt') as json_file:
        data = json.load(json_file)
        background_counts = numpy.array(data["binned_samples"])
        
    # No filter
#    file_mar = '2020_03_09-15_46_02-Y2O3_no_graphene_no_IG_2'
#    file_aug = '2020_08_03-13_41_11-5nmEr-search'
    
    # 550 Shortpass
#    file_mar = '2020_03_09-15_56_14-Y2O3_no_graphene_no_IG_2'
#    file_aug = '2020_08_03-14_03_43-5nmEr-search'
    
    # 630 longpass
    file_mar = '2020_03_09-16_05_16-Y2O3_no_graphene_no_IG_2'
    file_aug = '2020_08_03-14_36_05-5nmEr-search'
    
    dir_list = [directory_mar, directory_aug]
    file_list = [file_mar, file_aug]
    # Make list for the data
    
    start_num = [9, 29]
    counts_list = []
    bin_center_list =[]
    data_fmt_list = ['bo','ko']
#    fit_fmt_list=['b--','k--']
    label_list = ['pre anneal (3/2020)', 'post anneal (8/2020)']
    
    fig_fit, ax= plt.subplots(1, 1, figsize=(10, 8))
    
    # Open the specified file
    for i in range(len(file_list)):
        file = file_list[i]
        directory = dir_list[i]
        with open(directory + '/'+ file + '.txt') as json_file:
        
            # Load the data from the file
            data = json.load(json_file)
            counts = numpy.array(data["binned_samples"])
            bin_centers = numpy.array(data["bin_centers"])/10**3
            
        counts_list.append(counts)
        bin_center_list.append(bin_centers)
        
        bin_centers = bin_center_list[i]
        bin_centers_norm = numpy.array(bin_centers)-bin_centers[start_num[i]]
        
        counts = numpy.array(counts_list[i])
        sub_counts = counts - background_counts
        
        first_point = counts[start_num[i]]
        last_point = counts[-1]
        norm_counts = (counts - last_point) / (first_point - last_point)
        ax.plot(bin_centers_norm[start_num[i]:], norm_counts[start_num[i]:], data_fmt_list[i],label=label_list[i])
    ax.set_xlabel('Time (us)')
    ax.set_ylabel('Counts (arb.)')
    ax.set_title('5 nm Er implanted Y2O3 lifetime, 660 longpass filter')
    ax.legend()
#    ax.set_xlim([0,500])
    ax.set_yscale("log", nonposy='clip')

#%%
    
if __name__ == '__main__':
#    subtract()
    main()