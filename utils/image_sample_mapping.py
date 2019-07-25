# -*- coding: utf-8 -*-
"""Saves the data necessary to relocate specific NVs. Also can probably (?)
illustrate a mapping from an NV list to an image_sample.

Created on Mon Jun 10 13:54:07 2019

@author: mccambria
"""


# %% Imports


import json
import majorroutines.image_sample as image_sample
import utils.tool_belt as tool_belt
import matplotlib.pyplot as plt
import os
import labrad


# %% Functions


def illustrate_mapping(file_name):
    
    folder_dir = tool_belt.get_folder_dir(__file__)
    file_path = os.path.abspath(os.path.join(folder_dir, file_name))
    with open(file_path) as file:
        data = json.load(file)
        image_sample_file_name = data['image_sample_file_name']
        nv_sig_list = data['nv_sig_list']
        
    fig = image_sample.create_figure(image_sample_file_name)
    axes = fig.get_axes()
    ax = axes[0]
    images = ax.get_images()
    im = images[0]
    im.set_clim(0, 100)
    fig.set_size_inches(8.5, 8.5)
    
    # Get the expected radius of an NV
    try:
        with labrad.connect() as cxn:
            shared_params = tool_belt.get_shared_parameters_dict(cxn)
        airy_radius_nm = shared_params['airy_radius_nm']
        galvo_nm_per_volt = shared_params['galvo_nm_per_volt']
        airy_radius_volts = airy_radius_nm / galvo_nm_per_volt
    except Exception:
        airy_radius_volts = 0.004

    for ind in range(len(nv_sig_list)):
        nv_sig = nv_sig_list[ind]
        circle = plt.Circle(tuple(nv_sig[0:2]), 2*airy_radius_volts,
                            ec='g', fill=False, lw=2.0)
        ax.add_patch(circle)
        
    return fig
    
def generate_mapping_files(sample_name, micrometer_coords,
                           image_sample_file_name, nv_sig_list):
    
    raw_data = {
            'sample_name': sample_name,
            'micrometer_coords': micrometer_coords,
            'micrometer_coords-units': 'mm',
            'image_sample_file_name': image_sample_file_name,
            'nv_sig_list': nv_sig_list,
            'nv_sig_list-units': tool_belt.get_nv_sig_units(),
            }
    
    folder_dir = tool_belt.get_folder_dir(__file__)
    file_name = '{}_mapping'.format(image_sample_file_name.split('.')[0])
    file_path = os.path.abspath(os.path.join(folder_dir, file_name))
    
    tool_belt.save_raw_data(raw_data, file_path)
    
    file_name_ext = '{}.txt'.format(file_name)
    fig = illustrate_mapping(file_name_ext)
    
    tool_belt.save_figure(fig, file_path)


# %% Run the file


if __name__ == '__main__':
    
    # Ignore this...
#    if False:
#        # Circle NVs from an existing mapping
#        file_name = '2019-06-10_15-26-39_ayrton12_mapping'
#        illustrate_mapping(file_name)
#    else:
    
    # Generate the mapping files
    sample_name = 'johnson1'
    micrometer_coords = [208.3, 277.3, 146.8]
    image_sample_file_name = '2019-07-23_17-37-01_johnson1'
    
#    generate_mapping_files(sample_name, micrometer_coords,
#                           image_sample_file_name, nv_sig_list)
