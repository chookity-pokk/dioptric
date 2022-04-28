# -*- coding: utf-8 -*-
"""
Scan the galvos over the designated area, collecting counts at each point.
Generate an image of the sample.

Created on Tue Apr  9 15:18:53 2019

@author: mccambria
"""


import numpy
import utils.tool_belt as tool_belt
import time
import labrad
import majorroutines.optimize as optimize


def populate_img_array_bottom_left(valsToAdd, imgArray, writePos):
    """
    We scan the sample in a winding pattern. This function takes a chunk
    of the 1D list returned by this process and places each value appropriately
    in the 2D image array. This allows for real time imaging of the sample's
    fluorescence.

    Note that this function could probably be much faster. At least in this
    context, we don't care if it's fast. The implementation below was
    written for simplicity.

    Params:
        valsToAdd: numpy.ndarray
            The increment of raw data to add to the image array
        imgArray: numpy.ndarray
            The xDim x yDim array of fluorescence counts
        writePos: tuple(int)
            The last x, y write position on the image array. [] will default
            to the bottom right corner.
    """

    yDim = imgArray.shape[0]
    xDim = imgArray.shape[1]

    if len(writePos) == 0:
        writePos[:] = [xDim , yDim - 1]

    xPos = writePos[0]
    yPos = writePos[1]

    # Figure out what direction we're heading
    headingLeft = ((yDim - 1 - yPos) % 2 == 0)

    for val in valsToAdd:
        if headingLeft:
            # Determine if we're at the left x edge
            if (xPos == 0):
                yPos = yPos - 1
                imgArray[yPos, xPos] = val
                headingLeft = not headingLeft  # Flip directions
            else:
                xPos = xPos - 1
                imgArray[yPos, xPos] = val
        else:
            # Determine if we're at the right x edge
            if (xPos == xDim - 1):
                yPos = yPos - 1
                imgArray[yPos, xPos] = val
                headingLeft = not headingLeft  # Flip directions
            else:
                xPos = xPos + 1
                imgArray[yPos, xPos] = val
#    print([xPos, yPos])
    writePos[:] = [xPos, yPos]

def populate_img_array(valsToAdd, imgArray, writePos):
    """
    We scan the sample in a winding pattern. This function takes a chunk
    of the 1D list returned by this process and places each value appropriately
    in the 2D image array. This allows for real time imaging of the sample's
    fluorescence.

    Note that this function could probably be much faster. At least in this
    context, we don't care if it's fast. The implementation below was
    written for simplicity.

    Params:
        valsToAdd: numpy.ndarray
            The increment of raw data to add to the image array
        imgArray: numpy.ndarray
            The xDim x yDim array of fluorescence counts
        writePos: tuple(int)
            The last x, y write position on the image array. [] will default
            to the bottom right corner.
    """
    yDim = imgArray.shape[0]
    xDim = imgArray.shape[1]

    if len(writePos) == 0:
        writePos[:] = [xDim, yDim - 1]

    xPos = writePos[0]
    yPos = writePos[1]

    # Figure out what direction we're heading
    headingLeft = ((yDim - 1 - yPos) % 2 == 0)

    for val in valsToAdd:
        if headingLeft:
            # Determine if we're at the left x edge
            if (xPos == 0):
                yPos = yPos - 1
                imgArray[yPos, xPos] = val
                headingLeft = not headingLeft  # Flip directions
            else:
                xPos = xPos - 1
                imgArray[yPos, xPos] = val
        else:
            # Determine if we're at the right x edge
            if (xPos == xDim - 1):
                yPos = yPos - 1
                imgArray[yPos, xPos] = val
                headingLeft = not headingLeft  # Flip directions
            else:
                xPos = xPos + 1
                imgArray[yPos, xPos] = val
    writePos[:] = [xPos, yPos]

    return imgArray


def on_click_image(event):
    """
    Click handler for images. Prints the click coordinates to the console.

    Params:
        event: dictionary
            Dictionary containing event details
    """

    try:
        print('{:.3f}, {:.3f}'.format(event.xdata, event.ydata))
#        print('[{:.3f}, {:.3f}, 50.0],'.format(event.xdata, event.ydata))
    except TypeError:
        # Ignore TypeError if you click in the figure but out of the image
        pass
    
    
# %% Main
    

def main(nv_sig, x_range, z_range, num_steps, apd_indices,
         save_data=True, plot_data=True, 
         um_scaled=False):

    with labrad.connect() as cxn:
        img_array, x_voltages, z_voltages = main_with_cxn(cxn, nv_sig, x_range,
                      z_range, num_steps, apd_indices, save_data, plot_data, 
                      um_scaled)

    return img_array, x_voltages, z_voltages

def main_with_cxn(cxn, nv_sig, x_range, z_range, num_steps,
                  apd_indices, save_data=True, plot_data=True, 
                  um_scaled=False):

    # %% Some initial setup
    
    tool_belt.reset_cfm(cxn)
    laser_key = 'imaging_laser'

    drift = tool_belt.get_drift()
    coords = nv_sig['coords']
    adjusted_coords = (numpy.array(coords) + numpy.array(drift)).tolist()
    x_center, y_center, z_center = adjusted_coords
    
    adjusted_coords_begin = (numpy.array(adjusted_coords) + [0,0,-z_range/2]).tolist()
    # print(adjusted_coords_begin)
    # return
    optimize.prepare_microscope(cxn, nv_sig, adjusted_coords_begin)
    laser_name = nv_sig[laser_key]
    tool_belt.set_filter(cxn, nv_sig, laser_key)
    laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)
    
    # if x_range != y_range:
    #     raise RuntimeError('x and y resolutions must match for now.')

    xyz_server = tool_belt.get_xyz_server(cxn)
    xy_delay = tool_belt.get_registry_entry(cxn, 'xy_small_response_delay', ['', 'Config', 'Positioning'])
    z_delay = tool_belt.get_registry_entry(cxn, 'z_delay', ['', 'Config', 'Positioning'])
    # use whichever delay is longer: 
    if z_delay > xy_delay:
        delay = z_delay
    else:
        delay = xy_delay
    # Get the scale in um per unit
    xy_scale = tool_belt.get_registry_entry(cxn, 'xy_nm_per_unit', ['', 'Config', 'Positioning'])
    z_scale = tool_belt.get_registry_entry(cxn, 'z_nm_per_unit', ['', 'Config', 'Positioning'])
    if xy_scale == -1:
        um_scaled = False
    else: 
        xy_scale *= 1000

    total_num_samples = num_steps**2

    # %% Load the PulseStreamer
    
    readout = nv_sig['imaging_readout_dur']
    
    readout_sec = readout / 10**9
    readout_us = readout / 10**3

    seq_args = [delay, readout, apd_indices[0], laser_name, laser_power]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    # print(seq_args_string)
    # return
    ret_vals = cxn.pulse_streamer.stream_load('simple_readout.py',
                                              seq_args_string)
    period = ret_vals[0]


    # %% Initialize at the starting point

    tool_belt.set_xyz(cxn, [x_center, y_center, z_center])
    
    # %% Set up the xy_server

    x_voltages, z_voltages = xyz_server.load_sweep_scan_xz(x_center,y_center,
                                                           z_center,
                                       x_range, z_range, num_steps, period)

    x_num_steps = len(x_voltages)
    x_low = x_voltages[0]
    x_high = x_voltages[x_num_steps-1]
    z_num_steps = len(z_voltages)
    z_low = z_voltages[0]
    z_high = z_voltages[z_num_steps-1]

    pixel_size_x = x_voltages[1] - x_voltages[0]
    pixel_size_z = z_voltages[1] - z_voltages[0]


    # %% Set up the APD

    apd_server = tool_belt.get_apd_server(cxn)
    apd_server_name = tool_belt.get_registry_entry(cxn, "apd_server", ["", "Config", "Counter"])
    if apd_server_name == 'apd_tagger':
        apd_server.start_tag_stream(apd_indices)
    elif apd_server_name == 'apd_daq':
        apd_server.load_stream_reader(apd_indices[0], period,  total_num_samples)


    # %% Set up our raw data objects

    # Initialize imgArray and set all values to NaN so that unset values
    # are not interpreted as 0 by matplotlib's colobar
    img_array = numpy.empty((x_num_steps, z_num_steps))
    img_array[:] = numpy.nan
    img_write_pos = []

    # %% Set up the image display

    if plot_data:

        img_array_kcps = numpy.copy(img_array)

        # For the image extent, we need to bump out the min/max x/y by half the
        # pixel size in each direction so that the center of each pixel properly
        # lies at its x/y voltages.
        half_pixel_size_x = pixel_size_x / 2
        half_pixel_size_z = pixel_size_z / 2
        img_extent = [x_high + half_pixel_size_x, x_low - half_pixel_size_x,
                      z_low - half_pixel_size_z, z_high + half_pixel_size_z]
        if um_scaled:
            img_extent = [(x_high + half_pixel_size_x)*xy_scale, (x_low - half_pixel_size_x)*xy_scale,
                      (z_low - half_pixel_size_z)*z_scale, (z_high + half_pixel_size_z)*z_scale]
        title = r'Confocal scan X and Z, {}, {} us readout'.format(laser_name, readout_us)
        fig = tool_belt.create_image_figure(img_array, img_extent,
                        clickHandler=on_click_image, color_bar_label='kcps',
                        title=title, um_scaled=um_scaled, aspect_ratio = "auto")

    # %% Collect the data
#    cxn.apd_tagger.clear_buffer()
    cxn.pulse_streamer.stream_start(total_num_samples)

    timeout_duration = ((period*(10**-9)) * total_num_samples) + 10
    timeout_inst = time.time() + timeout_duration

    num_read_so_far = 0

    tool_belt.init_safe_stop()

    while num_read_so_far < total_num_samples:

        if time.time() > timeout_inst:
            break

        if tool_belt.safe_stop():
            break

        # Read the samples and update the image
        new_samples = apd_server.read_counter_simple()
#        print(new_samples)
        num_new_samples = len(new_samples)
        if num_new_samples > 0:

            populate_img_array(new_samples, img_array, img_write_pos)
            # This is a horribly inefficient way of getting kcps, but it
            # is easy and readable and probably fine up to some resolution
            if plot_data:
                img_array_kcps[:] = (img_array[:] / 1000) / readout_sec
                tool_belt.update_image_figure(fig, img_array_kcps)
            num_read_so_far += num_new_samples

    # %% Clean up

    tool_belt.reset_cfm(cxn)

    # Return to center
    tool_belt.set_xyz(cxn, [x_center, y_center, z_center])

    # %% Save the data

    timestamp = tool_belt.get_time_stamp()

    rawData = {'timestamp': timestamp,
               'nv_sig': nv_sig,
               'nv_sig-units': tool_belt.get_nv_sig_units(),
               'drift': drift,
               'x_range': x_range,
               'x_range-units': 'V',
               'z_range': z_range,
               'z_range-units': 'V',
               'num_steps': num_steps,
               'readout': readout,
               'readout-units': 'ns',
               'x_voltages': x_voltages.tolist(),
               'x_voltages-units': 'V',
               'z_voltages': z_voltages.tolist(),
               'z_voltages-units': 'V',
               'img_array': img_array.astype(int).tolist(),
               'img_array-units': 'counts'}

#    if save_data:
#
#        filePath = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
#        tool_belt.save_raw_data(rawData, filePath)
#
#        if plot_data:
#
#            tool_belt.save_figure(fig, filePath)

    return img_array, x_voltages, z_voltages


# %% Run the file


if __name__ == '__main__':


    path = 'pc_rabi/branch_master/image_sample_xz/2021_08'
    file_name = '2021_08_27-15_58_12-johnson-nv2_2021_08_27'

    data = tool_belt.get_raw_data( file_name, path)
    nv_sig = data['nv_sig']
    readout = nv_sig['imaging_readout_dur']
    timestamp = data['timestamp']
    img_array = numpy.array(data['img_array'])
    x_voltages = data['x_voltages']
    z_voltages = data['z_voltages']
    num_steps = data['num_steps']
    half_num_steps = int(num_steps/2)
    print(z_voltages[half_num_steps])
    
    x_low = x_voltages[0]
    x_high = x_voltages[-1]
    z_low = z_voltages[0]
    z_high = z_voltages[-1]
    pixel_size_x = x_voltages[1] - x_voltages[0]
    pixel_size_z = z_voltages[1] - z_voltages[0]
    
    half_pixel_size_x = pixel_size_x / 2
    half_pixel_size_z = pixel_size_z / 2
    img_extent = [x_high + half_pixel_size_x, x_low - half_pixel_size_x,
                  z_low - half_pixel_size_z, z_high + half_pixel_size_z]
    
    
    
    
    readout_sec = readout / 10**9
    img_array_kcps = numpy.copy(img_array)
    img_array_kcps[:] = (img_array[:] / 1000) / readout_sec
    
    title = r'Confocal scan X and Z'
    tool_belt.create_image_figure(img_array_kcps, img_extent,
                        clickHandler=on_click_image, color_bar_label='kcps',
                        title=title, um_scaled=False, aspect_ratio = "auto")
    
    
    
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
    #
    # csv_name = '{}_{}'.format(timestamp, nv_sig['name'])
    
    # tool_belt.save_image_data_csv(img_array, x_voltages, y_voltages,  path, 
    #                               csv_name)
