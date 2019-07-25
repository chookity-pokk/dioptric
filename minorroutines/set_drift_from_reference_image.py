# -*- coding: utf-8 -*-
"""Determine the drift by taking an image using the same parameters as a
reference image and then comparing the reference image to the new image.
To calculate the drift we use opencv's template matching. Template matching
assumes your template is smaller than the image you're searching through so we
pad the reference image to double its size in each dimension. I think this
could bias the values to small shifts, but I'm not sure this actually happens
with the matching method we use (cv2.TM_CCOEFF_NORMED). I need to think more
about the formula for that method. In my tests at least, this works
consistently.

This needs some work to support non-square images yet.

Created on Sun Jun 16 11:38:17 2019

@author: mccambria
"""


# %% Imports


import majorroutines.image_sample as image_sample
import majorroutines.optimize as optimize
import utils.tool_belt as tool_belt
import cv2
import utils.image_processing as image_processing
from matplotlib import pyplot as plt
import numpy
import labrad


# %% Main


def main(cxn, ref_file_name, nv_sig, nd_filter, apd_indices):

        with labrad.connect() as cxn:
            main_with_cxn(cxn, ref_file_name, nv_sig, nd_filter, apd_indices)

def main_with_cxn(cxn, ref_file_name, nv_sig, nd_filter, apd_indices):
    """Main entry point."""

    # %% Get the reference image

    ref_data = tool_belt.get_raw_data('image_sample', ref_file_name)

    # %% Get a new image

    # Take a new image using the same parameters
    ref_coords = ref_data['coords']
    ref_x_range = ref_data['x_range']
    ref_y_range = ref_data['y_range']
    ref_num_steps = ref_data['num_steps']
    # Use the last known in-focus z
    current_drift = tool_belt.get_drift()
    coords = [*ref_coords[0:2], nv_sig[2] + current_drift[2]]
    new_data = image_sample.main_with_cxn(cxn, coords, nd_filter,
                           ref_x_range, ref_y_range,
                           ref_num_steps, apd_indices,
                           save_data=False, plot_data=False)

    # Test data
#    new_data = tool_belt.get_raw_data('image_sample',
#                                      '2019-06-14_16-36-48_ayrton12')
#    new_data = tool_belt.get_raw_data('image_sample',
#                                      '2019-06-02_13-39-23_ayrton12')

    # %% Calculate and set the x/y shift

    # Get the image arrays
    ref_img_array = numpy.array(ref_data['img_array'])
    new_img_array = numpy.array(new_data['img_array'])

    # Convert to 8 bit
    ref_img_array = image_processing.convert_to_8bit(ref_img_array)
    new_img_array = image_processing.convert_to_8bit(new_img_array)

    # Add a border to the reference image so that we can use template matching
    img_shape = ref_img_array.shape
    ver_border_size = img_shape[0] // 2
    hor_border_size = img_shape[1] // 2
    ref_img_array = cv2.copyMakeBorder(ref_img_array,
                       top=ver_border_size, bottom=ver_border_size,
                       left=hor_border_size, right=hor_border_size,
                       borderType=cv2.BORDER_CONSTANT, value=0)

    res = cv2.matchTemplate(ref_img_array, new_img_array,
                            cv2.TM_CCOEFF_NORMED)
    
    # Test plot
#    fig, ax = plt.subplots(figsize=(5,5))
#    ax.imshow(res)
    
    # Find where we best matched to determine the shift
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    # Adjust for the borders
    x_shift_pixels = max_loc[0] - hor_border_size
    y_shift_pixels = max_loc[1] - ver_border_size
    
    # Test print
#    print('x_shift_pixels: {}'.format(x_shift_pixels))
#    print('y_shift_pixels: {}'.format(y_shift_pixels))
    
    # Determine the pixel size in volts / pixel
    ref_x_voltages = ref_data['x_voltages']
    x_pixel_size = (ref_x_voltages[-1] - ref_x_voltages[0]) / ref_num_steps
    ref_y_voltages = ref_data['y_voltages']
    y_pixel_size = (ref_y_voltages[-1] - ref_y_voltages[0]) / ref_num_steps
    
    # Convert to volts
    x_shift_volts = x_shift_pixels * x_pixel_size
    y_shift_volts = y_shift_pixels * y_pixel_size
    
    # Make sure we have floats and set the drift
    tool_belt.set_drift([float(x_shift_volts),
                         float(y_shift_volts),
                         float(current_drift[2])])

    # %% Optimize to set drift more precisely
    
    optimize.main(cxn, nv_sig, nd_filter, apd_indices)
    

# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

#    main(None, '2019-06-14_16-28-13_ayrton12', None, None)
    main(None, '2019-06-03_09-50-45_ayrton12', None, None)
