# -*- coding: utf-8 -*-
"""
Specify folders and run to produce csv files containing the taus and
norm_avg_sigs within each json-formatted text file in the folder.

The csv files are named as:
<init state>_to_<read state>_<max relaxation time in us>.csv

Created on Mon May 27 11:26:49 2019

@author: mccambria
"""

import os
import json
import numpy
import csv

def convert(folder_name):
    
    folder_items = os.listdir(folder_name)

    for json_file_name in folder_items:
    
        # Only process txt files, which we assume to be json files
        if not json_file_name.endswith('.txt'):
            continue
    
        with open('{}/{}'.format(folder_name, json_file_name)) as json_file:
    
            try:
                data = json.load(json_file)
                binned_samples = data['binned_samples']
                bin_centers = data['bin_centers']
            except Exception:
                # Skip txt files that are evidently not data files
                print('skipped {}'.format(json_file_name))
                continue
    
#        # Calculate the taus
#        taus = numpy.linspace(relaxation_time_range[0], relaxation_time_range[1],
#                              num=num_steps, dtype=numpy.int32)
    
        # Populate the data to save
        csv_data = []
        for bin_ind in range(len(bin_centers)):
            row = []
            row.append(bin_centers[bin_ind])
            row.append(binned_samples[bin_ind])
            csv_data.append(row)
    
        max_relaxation_us = relaxation_time_range[1] // 1000
    
        csv_file_name = '{}_to_{}_{}'.format(init_state, read_state,
                         max_relaxation_us)
    
        with open('{}/{}.csv'.format(folder_name, csv_file_name),
                  'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',',
                                    quoting=csv.QUOTE_NONE)
            csv_writer.writerows(csv_data)
            
if __name__ == '__main__':
    
    top_folder_name = 'E:/Shared drives/Kolkowitz Lab Group/nvdata/lifetime_v2/2020_02'
        
#    sub_folder_names = ['2019-08-22-07_55_36-ayrton12-nv1_2019_05_10.txt',
#                         '2019-08-23-17_36_12-ayrton12-nv1_2019_05_10.txt',
#                         '2019-08-23-23_20_27-ayrton12-nv1_2019_05_10.txt',
#                         '2019-08-24-06_51_38-ayrton12-nv1_2019_05_10.txt',
#                         '2019-08-24-08_38_20-ayrton12-nv1_2019_05_10.txt',
#                         '2019-08-24-14_22_27-ayrton12-nv1_2019_05_10.txt']
#    
#    for el in sub_folder_names:
#        
#        convert(top_folder_name.format(el))
        
    convert(top_folder_name.format('relaxation rate paper data'))
