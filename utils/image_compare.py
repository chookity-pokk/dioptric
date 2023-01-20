# -*- coding: utf-8 -*-
"""
Template matching.

Created on Fri Jan  20 08:30:00 2023

@author: carter fox 
"""

####################### Imports #######################

import cv2
import numpy as np
from matplotlib import pyplot as plt
import json
import sys

def convert_to_8bit(img, min_val=0, max_val=255):
    img = img.astype(np.float64)
    img -= np.nanmin(img)  # Set the lowest value to 0
    img *= (max_val/np.nanmax(img))
    img = img.astype(np.uint8)
    img += min_val
    return img

def get_img_extent(data):
    x_voltages = data['x_positions_1d']
    y_voltages = data['y_positions_1d']
    
    x_low = x_voltages[0]
    x_high = x_voltages[-1]
    y_low = y_voltages[0]
    y_high = y_voltages[-1]

    half_pixel_size = (x_voltages[1] - x_voltages[0]) / 2
    img_extent = [x_high + half_pixel_size, x_low - half_pixel_size,
                  y_low - half_pixel_size, y_high + half_pixel_size]
    return img_extent


def get_shift(directory, haystack_file, needle_file, plot=True):
    
    diff_lim_spot_diam = 0.015  # expected st dev of the gaussian in volts
    
    ####################### Process Haystack File #######################
    file_path = directory + haystack_file
    with open(file_path, 'r') as file:
        haystack_data = json.load(file)
        
    x_voltages = haystack_data['x_positions_1d']
    y_voltages = haystack_data['y_positions_1d']
    
    haystack_img_extent = get_img_extent(haystack_data)
    
    og_center_x_volts = (x_voltages[-1] + x_voltages[0])/2
    og_center_y_volts = (y_voltages[-1] + y_voltages[0])/2
    
    x_range = haystack_data['x_range']
    y_range = haystack_data['y_range']
    min_range = min(x_range, y_range)
    num_steps = haystack_data['num_steps']
    volts_per_pixel = min_range / num_steps
    
    haystack_img_array = np.array(haystack_data['img_array'])
    haystack_img_array = convert_to_8bit(haystack_img_array)
    
    haystack_img_array = cv2.GaussianBlur(haystack_img_array, (5, 5), 0)
    
    ####################### Initial calculations #######################
    
    # expected st dev of the gaussian in pixels - must be odd
    diff_lim_spot_pixels = int(diff_lim_spot_diam / volts_per_pixel)
    if diff_lim_spot_pixels % 2 == 1:
        diff_lim_spot_pixels += 1
    
    ####################### Process Needle File #######################
    
    file_path = directory + needle_file
    with open(file_path, 'r') as file:
        needle_data = json.load(file)
        
    template_img = np.array(needle_data['img_array'])
    needle_x = needle_data['x_positions_1d']
    needle_y = needle_data['y_positions_1d']
    needle_img_array = np.array(needle_data['img_array'])
    w, h = len(needle_x),len(needle_y)
    template_img = convert_to_8bit(template_img)
    
    needle_img_extent = get_img_extent(needle_data)
    
    
    ####################### Run the matching #######################
    
    method = eval('cv2.TM_CCOEFF_NORMED')
    res = cv2.matchTemplate(haystack_img_array, template_img, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    center_x = int(w/2 + top_left[0])
    center_y = int(h/2 + top_left[1])
    
    center_x_volts = x_voltages[center_x]
    center_y_volts = y_voltages[center_y]
    
    shift_x_volts = round(center_x_volts - og_center_x_volts,4)
    shift_y_volts = round(center_y_volts - og_center_y_volts,4)
    
    processed_img_array = np.copy(haystack_img_array)
    processed_img_array = cv2.cvtColor(processed_img_array, cv2.COLOR_GRAY2RGB)
    
    ####################### Plotting #######################
    
    if plot:
        fig, axes_pack = plt.subplots(1, 3, figsize=(15, 5))
        ax = axes_pack[0]
        ax.set_title('haystack')
        ax.set_xlabel('x [V]')
        ax.set_ylabel('y [V]')
        ax.imshow(haystack_img_array, extent=tuple(haystack_img_extent))
        ax = axes_pack[1]
        ax.set_xlabel('x [V]')
        ax.set_ylabel('y [V]')
        ax.imshow(needle_img_array, extent=tuple(needle_img_extent))
        ax.set_title('needle')
        ax = axes_pack[2]
        ax.set_xlabel('x [V]')
        ax.set_ylabel('y [V]')
        ax.imshow(processed_img_array, extent=tuple(haystack_img_extent))
        cv2.rectangle(haystack_img_array,top_left, bottom_right, 255, 1)
        cv2.circle(haystack_img_array, [center_x,center_y], 0, (255, 0, 0), 1)
        plt.imshow(haystack_img_array, extent=tuple(haystack_img_extent))
        ax.set_title('result: x_shift = {} V    y_shift = {} V'.format(shift_x_volts,shift_y_volts))
        fig.tight_layout()
        fig_manager = plt.get_current_fig_manager()
        
    return shift_x_volts, shift_y_volts

    
if __name__ == '__main__':
    
    ####################### Files #######################
    directory = "C:/Users/student/Documents/LAB_DATA/pc_nvcenter-pc/branch_instructional-lab-v2/image_sample/2023_01/"
    needle_file = '2023_01_20-09_41_50-E6test-nv1_XY.txt'
    haystack_file = '2023_01_20-08_28_56-E6test-nv1_XY.txt'
    
    shift_x_volts, shift_y_volts = get_shift(directory, haystack_file, needle_file,plot=True)
    print('x shift = {} V'.format(shift_x_volts))
    print('y shift = {} V'.format(shift_y_volts))