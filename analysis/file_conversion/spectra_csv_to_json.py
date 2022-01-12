# -*- coding: utf-8 -*-
"""
Specify folders and run to produce json files containing the wavelengths and
counts within each csv-formatted text file in the folder.

Created on Tue Mar 3 11:26:49 2020

@author: agardill
"""

import os
import utils.tool_belt as tool_belt
import csv

def convert_single_file(folder, file):

    with open('{}/{}.csv'.format(folder, file)) as csv_file:
        wavelength_list = []
        counts_list = []
        
        reader = csv.reader(csv_file)
        data = list(reader)


    for line in range(2, len(data)):
        wavelength_list.append(float(data[line][0]))
        counts_list.append(int(data[line][1]))

    json_dict = {'wavelengths': wavelength_list,
                 'wavelengths-units': 'nm',
                 'counts': counts_list
                    }

    # Save as a json
    file_path = folder + '/' + file
    tool_belt.save_raw_data(json_dict, file_path)
        
def convert_folder_items(folder_name):

    folder_items = os.listdir(folder_name)

    for csv_file_name in folder_items:

        # Only process txt files, which we assume to be json files
        if not csv_file_name.endswith('.csv'):
            continue

        with open('{}/{}'.format(folder_name, csv_file_name)) as csv_file:
            wavelength_list = []
            counts_list = []
            try:
                reader = csv.reader(csv_file)
                data = list(reader)

            except Exception:
                # Skip txt files that are evidently not data files
                print('skipped {}'.format(csv_file_name))
                continue

        for line in range(2, len(data)):
            wavelength_list.append(float(data[line][0]))
            counts_list.append(int(data[line][1]))

        json_dict = {'wavelengths': wavelength_list,
                     'wavelengths-units': 'nm',
                     'counts': counts_list
                        }

        # Save as a json
        file_path = top_folder_name + '/' + csv_file_name[:-4]
        tool_belt.save_raw_data(json_dict, file_path)

if __name__ == '__main__':

    top_folder_name = 'E:/Shared drives/Kolkowitz Lab Group/nvdata/horiba_spectrometer/2021_05'

    convert_folder_items(top_folder_name)

#    top_folder_name = 'E:/Shared drives/Kolkowitz Lab Group/nvdata/spectra/Brar/2020_09_02 5 nm MM tests'
#
#    convert(top_folder_name)
