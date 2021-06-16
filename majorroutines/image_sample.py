# -*- coding: utf-8 -*-
"""
Scan the galvos over the designated area, collecting counts at each point.
Generate an image of the sample.

Includes a replotting routine to show the data with axes in um instead of V.

Includes a replotting routine to replot rw data to manipulate again.

6/1 added a function that does two pulses at each pixel. Not included in control panel

Created on Tue Apr  9 15:18:53 2019

@author: mccambria
"""

import numpy
import utils.tool_belt as tool_belt
import time

import json
import matplotlib.pyplot as plt
import labrad

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

        # %%


def reformat_plot(colorMap, save_file_type,centered_coords  =False):
    """
    Recreates the scan from an image_sample file. The plot will have axes in
    microns

    The function will open a window to select the file. This window may appear
    behind Spyder, so just minimize Spyder to select a file.

    """

    # Select a file
    fileName = tool_belt.ask_open_file("nvdata/image_sample")

    if fileName == '':
        print('No file selected')
    else:

        # remove the extension
        fileNameBase = fileName[:-4]

        # Add the .txt extension to the file naem base
        fileName = fileNameBase + '.txt'
        print('File selected: ' + fileNameBase + '.svg')

        # Open the specified file
        with open(fileName) as json_file:

            # Load the data from the file
            data = json.load(json_file)

            # Build the image array from the data
            imgArray = []

            for line in data["img_array"]:
                imgArray.append(line)

            counts_array = numpy.array(imgArray)
#            counts_array = numpy.flip(numpy.flip(imgArray, 0),1)

            # Get the readout
            readout = data['readout']

            # Read in the arrays of Center and Image Reoslution
            try:
                nv_sig = data['nv_sig']
                xyzCenters = nv_sig["coords"]
            except Exception:
                xyzCenters = data['xyzCenters']
            num_steps = data["num_steps"]

            # Read in the values for the scan ranges, centers, and resolution
            yScanRange = data["y_range"]
            yCenter = xyzCenters[1]
            yImgResolution = yScanRange / num_steps

            xScanRange = data["x_range"]
            xCenter = xyzCenters[0]
            xImgResolution = xScanRange / num_steps
        if centered_coords:
            xCenter = 0
            yCenter = 0
        # define the readout in seconds
        readout_sec = float(readout) / 10**9

        # Define the scale from the voltso on the Galvo to microns
        # Currently using 35 microns per volt
        scale = 35

        # Calculate various values pertaining to the positions in the image
        xScanCenterPlusMinus = xScanRange / 2
        xMin = xCenter - xScanCenterPlusMinus
        xMax = xCenter + xScanCenterPlusMinus

        yScanCenterPlusMinus = yScanRange / 2
        yMin = yCenter - yScanCenterPlusMinus
        yMax = yCenter + yScanCenterPlusMinus

        # Calculate the aspect ratio between y and x , to be used in the figsize
        aspRatio = yImgResolution / xImgResolution

        # Create the figure, specifying only one plot. x and y label inputs are self-
        # explanatory. cmap allows a choice of color mapping.
        fig, ax = plt.subplots(figsize=(8, 8 * aspRatio))


        plt.xlabel('Position ($\mu$m)')
        plt.ylabel('Position ($\mu$m)')
#        plt.set_title('WeS2')

        # Telling matplotlib what to plot, and what color map to include
        img = ax.imshow(counts_array / 1000 / readout_sec, cmap=colorMap, interpolation='none',
                        extent = (scale*xMin, scale*xMax, scale*yMin, scale*yMax))

        # Add the color bar
        cbar = plt.colorbar(img)
        cbar.ax.set_title('kcts/sec')

        # Create the image
        fig.canvas.draw()
        fig.canvas.flush_events()

        # Save the file in the same file directory
        fig.savefig(fileNameBase + '_replot.' + save_file_type)

def create_figure(file_name, sub_folder = None):
#    if sub_folder:
    data = tool_belt.get_raw_data('', file_name)
#    else:
#        data = tool_belt.get_raw_data('image_sample', file_name)
    x_range = data['x_range']
    y_range = data['y_range']
    num_steps = data['num_steps']
    x_voltages = numpy.linspace(-x_range/2, +x_range/2, num_steps)
#    x_voltages = data['x_voltages']'
#    coords = data['coords']
#    nv_sig = data['nv_sig']
#    coords = nv_sig['coords']
#    nv_sig = data['nv_sig']
#    coords = nv_sig['coords']
    try:
        nv_sig = data['nv_sig']
        coords = nv_sig['coords']
    except Exception as e:
        print(e)
        coords = data['coords']
    coords = [0,0,5.0]
    img_array = numpy.array(data['img_array'])
    # print(numpy.average(img_array))
    readout = data['readout']

    x_coord = coords[0]
    half_x_range = x_range / 2
    x_low = x_coord - half_x_range
    x_high = x_coord + half_x_range
    y_coord = coords[1]
    half_y_range = y_range / 2
    y_low = y_coord - half_y_range
    y_high = y_coord + half_y_range

    img_array_kcps = (img_array / 1000) / (readout / 10**9)

    pixel_size = x_voltages[1] - x_voltages[0]
    half_pixel_size = pixel_size / 2
    img_extent = [x_low - half_pixel_size, x_high + half_pixel_size,
                  y_low - half_pixel_size, y_high + half_pixel_size]

#    color_ind =  data['color_ind']
    readout_us = readout / 10**3
    title = 'Confocal scan.\nReadout {} us'.format(readout_us)
    fig = tool_belt.create_image_figure(img_array_kcps, numpy.array(img_extent)*35*10**3,
                                        clickHandler=on_click_image,
                                        title = title,
                                        color_bar_label = 'kcps',
                                        um_scaled = True
                                        )
    # Redraw the canvas and flush the changes to the backend
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig


# %% Mains

def two_pulse_image_sample(nv_sig, x_range, y_range, num_steps,  apd_indices, init_pulse_time, readout,
                           init_color_ind, read_color_ind,
         save_data=True, plot_data=True, continuous=False):

    with labrad.connect() as cxn:
        img_array, x_voltages, y_voltages = two_pulse_image_sample_with_cxn(cxn, nv_sig, x_range,
                      y_range, num_steps,
                      apd_indices,  init_pulse_time,readout,
                           init_color_ind, read_color_ind, save_data, plot_data, continuous)

    return img_array, x_voltages, y_voltages

def two_pulse_image_sample_with_cxn(cxn, nv_sig, x_range, y_range, num_steps,
                  apd_indices, init_pulse_time, readout,
                           init_color_ind, read_color_ind,  save_data=True,
                  plot_data=True, continuous=False):

    # %% Some initial setup
    tool_belt.reset_cfm(cxn)
    color_filter = nv_sig['color_filter']
    cxn.filter_slider_ell9k_color.set_filter(color_filter)



    shared_params = tool_belt.get_shared_parameters_dict(cxn)
#    readout = shared_params['continuous_readout_dur']
#    init_pulse_time = 10**5

    if init_color_ind == 532:
        init_delay = shared_params['515_DM_laser_delay']
    elif init_color_ind == 589:
        init_delay = shared_params['589_aom_delay']
    elif init_color_ind == 638:
        init_delay = shared_params['638_DM_laser_delay']
    else:
        init_delay = 0

    if read_color_ind == 532:
        read_delay = shared_params['515_DM_laser_delay']
    elif read_color_ind == 589:
        read_delay = shared_params['589_aom_delay']
    elif read_color_ind == 638:
        read_delay = shared_params['638_DM_laser_delay']

    aom_ao_589_pwr = nv_sig['am_589_power']

    adj_coords = (numpy.array(nv_sig['coords']) + \
                  numpy.array(tool_belt.get_drift())).tolist()
    x_center, y_center, z_center = adj_coords


    if x_range != y_range:
        raise RuntimeError('x and y resolutions must match for now.')

    # The galvo's small angle step response is 400 us
    # Let's give ourselves a buffer of 500 us (500000 ns)
    galvo_delay = int(0.5 * 10**6)

    total_num_samples = num_steps**2

    # %% Load the PulseStreamer
    seq_args = [galvo_delay, init_delay, read_delay, init_pulse_time,  readout, aom_ao_589_pwr, apd_indices[0],
            init_color_ind, read_color_ind]
#    print(seq_args)
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    ret_vals = cxn.pulse_streamer.stream_load('simple_readout_two_pulse.py',
                                              seq_args_string)
    period = ret_vals[0]

    # %% Initialize at the passed coordinates

    tool_belt.set_xyz(cxn, [x_center, y_center, z_center])

    # %% Set up the galvo

    x_voltages, y_voltages = cxn.galvo.load_sweep_scan(x_center, y_center,
                                                       x_range, y_range,
                                                       num_steps, period)
#    print(x_voltages)

    x_num_steps = len(x_voltages)
    x_low = x_voltages[0]
    x_high = x_voltages[x_num_steps-1]
    y_num_steps = len(y_voltages)
    y_low = y_voltages[0]
    y_high = y_voltages[y_num_steps-1]

    pixel_size = x_voltages[1] - x_voltages[0]

    # If we want to spend the same amount of time on an NV, regardless of the
    # scan range or pixel size, we will scale the readout time so that we spend
    # the same amount of time scanning over an NV, regardless of the relative
    #size of the pixel sizes and NV size.
#    readout = int((pixel_size/nv_size)**2 * base_readout)
#    print(pixel_size)
#    print(str(readout /10**3) + 'us')

    readout_us = float(readout) / 10**3

    # %% Set up the APD

    cxn.apd_tagger.start_tag_stream(apd_indices)

    # %% Set up our raw data objects

    # Initialize imgArray and set all values to NaN so that unset values
    # are not interpreted as 0 by matplotlib's colobar
    img_array = numpy.empty((x_num_steps, y_num_steps))
    img_array[:] = numpy.nan
    img_write_pos = []

    # %% Set up the image display

    if plot_data:
#        img_array_kcps = numpy.copy(img_array)

        # For the image extent, we need to bump out the min/max x/y by half the
        # pixel size in each direction so that the center of each pixel properly
        # lies at its x/y voltages.
        half_pixel_size = pixel_size / 2
        img_extent = [x_high + half_pixel_size, x_low - half_pixel_size,
                      y_low - half_pixel_size, y_high + half_pixel_size]
        title = 'Confocal scan with {} nm init, {} nm readout.\nReadout {} us'.format(init_color_ind, read_color_ind, readout_us)
        fig = tool_belt.create_image_figure(img_array, img_extent,
                                            clickHandler=on_click_image,
                                            title = title)

    # %% Collect the data
    cxn.apd_tagger.clear_buffer()
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
        new_samples = cxn.apd_tagger.read_counter_simple()
#        print(new_samples)
        num_new_samples = len(new_samples)
        if num_new_samples > 0:
            populate_img_array(new_samples, img_array, img_write_pos)
            # This is a horribly inefficient way of getting kcps, but it
            # is easy and readable and probably fine up to some resolution
            if plot_data:
#                img_array_kcps[:] = (img_array[:] / 1000) / readout_sec
                tool_belt.update_image_figure(fig, img_array)
            num_read_so_far += num_new_samples

    # %% Clean up

    tool_belt.reset_cfm(cxn)

    # Return to center
    cxn.galvo.write(x_center, y_center)
#    cxn.galvo.write(0.5, 0.5)

    # %% Read the optical power for either yellow or green light

#    if color_ind == 532:
#        optical_power_pd = tool_belt.opt_power_via_photodiode(color_ind)
#    elif color_ind == 589:
#        optical_power_pd = tool_belt.opt_power_via_photodiode(color_ind,
#           AO_power_settings = aom_ao_589_pwr, nd_filter = nv_sig['nd_filter'])
#    elif color_ind == 638:
#        optical_power_pd = tool_belt.opt_power_via_photodiode(color_ind)

    # Convert V to mW optical power
#    optical_power_mW = tool_belt.calc_optical_power_mW(color_ind, optical_power_pd)
    optical_power_pd = None
    optical_power_mW = None


    # %% Save the data

    # measure laser powers:
    green_optical_power_pd, green_optical_power_mW, \
            red_optical_power_pd, red_optical_power_mW, \
            yellow_optical_power_pd, yellow_optical_power_mW = \
            tool_belt.measure_g_r_y_power(
                              nv_sig['am_589_power'], nv_sig['nd_filter'])

    timestamp = tool_belt.get_time_stamp()

    rawData = {'timestamp': timestamp,
               'nv_sig': nv_sig,
               'nv_sig-units': tool_belt.get_nv_sig_units(),
               'init_color_ind': init_color_ind,
               'read_color_ind': read_color_ind,
               'optical_power_pd': optical_power_pd,
               'optical_power_pd-units': 'V',
               'optical_power_mW': optical_power_mW,
               'optical_power_mW-units': 'mW',
               'aom_ao_589_pwr': aom_ao_589_pwr,
               'aom_ao_589_pwr-units': 'V',
               'x_range': x_range,
               'x_range-units': 'V',
               'y_range': y_range,
               'y_range-units': 'V',
               'num_steps': num_steps,
               'readout': readout,
               'readout-units': 'ns',
               'init_pulse_time': init_pulse_time,
               'init_pulse_time-units': 'ns',

            'green_optical_power_pd': green_optical_power_pd,
            'green_optical_power_pd-units': 'V',
            'green_optical_power_mW': green_optical_power_mW,
            'green_optical_power_mW-units': 'mW',
            'red_optical_power_pd': red_optical_power_pd,
            'red_optical_power_pd-units': 'V',
            'red_optical_power_mW': red_optical_power_mW,
            'red_optical_power_mW-units': 'mW',
            'yellow_optical_power_pd': yellow_optical_power_pd,
            'yellow_optical_power_pd-units': 'V',
            'yellow_optical_power_mW': yellow_optical_power_mW,
            'yellow_optical_power_mW-units': 'mW',
               'x_voltages': x_voltages.tolist(),
               'x_voltages-units': 'V',
               'y_voltages': y_voltages.tolist(),
               'y_voltages-units': 'V',
               'img_array': img_array.astype(int).tolist(),
               'img_array-units': 'counts'}

    if save_data:

        filePath = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
        tool_belt.save_raw_data(rawData, filePath)

        if plot_data:

            tool_belt.save_figure(fig, filePath)

    return img_array, x_voltages, y_voltages

# %%

def main(nv_sig, x_range, y_range, num_steps,  apd_indices,
         color_ind, save_data=True, plot_data=True, readout = 10**7 , flip = False, um_scaled = False, continuous=False):

    with labrad.connect() as cxn:
        img_array, x_voltages, y_voltages = main_with_cxn(cxn, nv_sig, x_range,
                      y_range, num_steps,
                      apd_indices,  color_ind,  save_data, plot_data, readout, flip, um_scaled ,  continuous)

    return img_array, x_voltages, y_voltages

def main_with_cxn(cxn, nv_sig, x_range, y_range, num_steps,
                  apd_indices,  color_ind, save_data=True,
                  plot_data=True, readout = 10**7, flip = False, um_scaled = False, continuous=False):

    # %% Some initial setup
    tool_belt.reset_cfm_wout_uwaves(cxn)

    color_filter = nv_sig['color_filter']
    cxn.filter_slider_ell9k_color.set_filter(color_filter)
    
    nd_filter = nv_sig['nd_filter']
    cxn.filter_slider_ell9k.set_filter(nd_filter)

    aom_ao_589_pwr = nv_sig['am_589_power']
    ao_515_pwr = nv_sig['ao_515_pwr']

    adj_coords = (numpy.array(nv_sig['coords']) + \
                  numpy.array(tool_belt.get_drift())).tolist()
    x_center, y_center, z_center = adj_coords

    if x_range != y_range:
        raise RuntimeError('x and y resolutions must match for now.')

    # The galvo's small angle step response is 400 us
    # Let's give ourselves a buffer of 500 us (500000 ns)
    delay = int(0.5 * 10**6)

    total_num_samples = num_steps**2

    # %% Load the PulseStreamer
    seq_args = [delay, readout, aom_ao_589_pwr, ao_515_pwr, apd_indices[0], color_ind]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    ret_vals = cxn.pulse_streamer.stream_load('simple_readout.py',
                                              seq_args_string)
#    print(seq_args)
    period = ret_vals[0]


    # %% Initialize at the starting point

    tool_belt.set_xyz(cxn, [x_center, y_center, z_center])
#    time.sleep(1)
    # %% Set up the galvo
    if flip==1: # instead of starting scan at lowest x and y point, instead
        #starts at y_max. So y direction is flipped
        x_voltages, y_voltages = cxn.galvo.load_sweep_scan_flip(x_center, y_center,
                                                       x_range, y_range,
                                                       num_steps, period)
    elif flip == 2: # starts in bottom left corner (max x, min y)

        x_voltages, y_voltages = cxn.galvo.load_sweep_scan_bl(x_center, y_center,
                                                       x_range, y_range,
                                                       num_steps, period)
    elif flip == 3: # starts in upper left corner (max x, max y)

        x_voltages, y_voltages = cxn.galvo.load_sweep_scan_ul(x_center, y_center,
                                                       x_range, y_range,
                                                       num_steps, period)
    elif flip == 4: # starts in upper right corner (min x, max y)

        x_voltages, y_voltages = cxn.galvo.load_sweep_scan_ur(x_center, y_center,
                                                       x_range, y_range,
                                                       num_steps, period)
    else:  # normal scan, starts in bottom right corner (min x, min y)
        x_voltages, y_voltages = cxn.galvo.load_sweep_scan(x_center, y_center,
                                                       x_range, y_range,
                                                       num_steps, period)

    x_num_steps = len(x_voltages)
    x_low = x_voltages[0]
    x_high = x_voltages[x_num_steps-1]
    y_num_steps = len(y_voltages)
    y_low = y_voltages[0]
    y_high = y_voltages[y_num_steps-1]

    pixel_size = x_voltages[1] - x_voltages[0]


    readout_us = float(readout) / 10**3


    # %% Set up the APD

    cxn.apd_tagger.start_tag_stream(apd_indices)

    # %% Set up our raw data objects

    # Initialize imgArray and set all values to NaN so that unset values
    # are not interpreted as 0 by matplotlib's colobar
    img_array = numpy.empty((x_num_steps, y_num_steps))
    img_array[:] = numpy.nan
    img_write_pos = []

    # %% Set up the image display

    if plot_data:

#        img_array_kcps = numpy.copy(img_array)

        # For the image extent, we need to bump out the min/max x/y by half the
        # pixel size in each direction so that the center of each pixel properly
        # lies at its x/y voltages.
        half_pixel_size = pixel_size / 2
        img_extent = [x_high + half_pixel_size, x_low - half_pixel_size,
                      y_low - half_pixel_size, y_high + half_pixel_size]
        if um_scaled:
            img_extent = [(x_high + half_pixel_size)*35, (x_low - half_pixel_size)*35,
                      (y_low - half_pixel_size)*35, (y_high + half_pixel_size)*35]
        title = 'Confocal scan with {} nm.\nReadout {} us'.format(color_ind, readout_us)
        fig = tool_belt.create_image_figure(img_array, img_extent,
                                            clickHandler=on_click_image,
                                            title = title, um_scaled = um_scaled)

    # %% Collect the data
    cxn.apd_tagger.clear_buffer()
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
        new_samples = cxn.apd_tagger.read_counter_simple()
#        print(new_samples)
        num_new_samples = len(new_samples)
        if num_new_samples > 0:
            if flip==1: # if we flipped the scan, start to fill in the points 
                # on the left side
                populate_img_array_bottom_left(new_samples, img_array, img_write_pos)
                # This is a horribly inefficient way of getting kcps, but it
                # is easy and readable and probably fine up to some resolution
                if plot_data:
    #                img_array_kcps[:] = (img_array[:] / 1000) / readout_sec
                    tool_belt.update_image_figure(fig, img_array)
                num_read_so_far += num_new_samples
            else:
                populate_img_array(new_samples, img_array, img_write_pos)
                # This is a horribly inefficient way of getting kcps, but it
                # is easy and readable and probably fine up to some resolution
                if plot_data:
    #                img_array_kcps[:] = (img_array[:] / 1000) / readout_sec
                    tool_belt.update_image_figure(fig, img_array)
                num_read_so_far += num_new_samples


    # %% Clean up

    tool_belt.reset_cfm_wout_uwaves(cxn)

    # Return to center
    cxn.galvo.write(x_center, y_center)

    # %% Save the data
    if plot_data: # for all the different starting points of the scans, generate
        # a second image that is positioned "normally" in space (just as if
        #nothing was flipped)
        if flip == 1:
            fig = tool_belt.create_image_figure(numpy.fliplr(img_array), img_extent,
                                                clickHandler=on_click_image,
                                                title = title)
        elif flip == 2:
            fig = tool_belt.create_image_figure(numpy.rot90(img_array,3), img_extent,
                                                clickHandler=on_click_image,
                                                title = title)
        elif flip == 3:
            fig = tool_belt.create_image_figure(numpy.rot90(img_array,2), img_extent,
                                                clickHandler=on_click_image,
                                                title = title)
        elif flip == 4:
            fig = tool_belt.create_image_figure(numpy.rot90(img_array,1), img_extent,
                                                clickHandler=on_click_image,
                                                title = title)

    # measure laser powers:
#    green_optical_power_pd, green_optical_power_mW, \
#            red_optical_power_pd, red_optical_power_mW, \
#            yellow_optical_power_pd, yellow_optical_power_mW = \
#            tool_belt.measure_g_r_y_power(
#                              nv_sig['am_589_power'], nv_sig['nd_filter'])

    timestamp = tool_belt.get_time_stamp()

    rawData = {'timestamp': timestamp,
               'nv_sig': nv_sig,
               'nv_sig-units': tool_belt.get_nv_sig_units(),
               'color_filter': color_filter,
               'color_ind': color_ind,
               'aom_ao_589_pwr': aom_ao_589_pwr,
               'aom_ao_589_pwr-units': 'V',
#                'green_optical_power_pd': green_optical_power_pd,
#                'green_optical_power_pd-units': 'V',
#                'green_optical_power_mW': green_optical_power_mW,
#                'green_optical_power_mW-units': 'mW',
#                'red_optical_power_pd': red_optical_power_pd,
#                'red_optical_power_pd-units': 'V',
#                'red_optical_power_mW': red_optical_power_mW,
#                'red_optical_power_mW-units': 'mW',
#                'yellow_optical_power_pd': yellow_optical_power_pd,
#                'yellow_optical_power_pd-units': 'V',
#                'yellow_optical_power_mW': yellow_optical_power_mW,
#                'yellow_optical_power_mW-units': 'mW',
               'x_range': x_range,
               'x_range-units': 'V',
               'y_range': y_range,
               'y_range-units': 'V',
               'num_steps': num_steps,
               'readout': readout,
               'readout-units': 'ns',
               'x_voltages': x_voltages.tolist(),
               'x_voltages-units': 'V',
               'y_voltages': y_voltages.tolist(),
               'y_voltages-units': 'V',
               'img_array': img_array.astype(int).tolist(),
               'img_array-units': 'counts'}

    if save_data:

        filePath = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
        tool_belt.save_raw_data(rawData, filePath)

        if plot_data:

            tool_belt.save_figure(fig, filePath)

    return img_array, x_voltages, y_voltages


# %% Run the file


if __name__ == '__main__':

#    file_name = '2019-06-04_09-58-38_ayrton12'
#    create_figure(file_name)
#    reformat_plot('inferno', 'svg')

#    file_name = 'branch_Spin_to_charge/2020_10/2020_10_13-17_32_31-goeppert-mayer-ensemble'
    # file_name = 'pc_rabi/branch_Spin_to_charge/isolate_nv_charge_dynamics_moving_target/2020_12/2020_12_08-18_04_02-goeppert-mayer-nv1_2020_12_02-img'
    file_name = 'pc_rabi/branch_Spin_to_charge/image_sample/2020_12/2020_12_09-15_36_03-goeppert-mayer-nv1_2020_12_02'

#    file_name = 'pc_rabi/branch_Spin_to_charge/image_sample/2021_04/2021_04_02-09_41_46-goeppert-mayer' # bright
#    file_name = 'pc_rabi/branch_Spin_to_charge/image_sample/2021_04/2021_04_02-09_46_49-goeppert-mayer' # dark
#    file_name = 'pc_rabi/branch_Spin_to_charge/image_sample/2021_04/2021_04_02-09_46_49-goeppert-mayer' # dark
#    reformat_plot('inferno', 'png')
    create_figure(file_name)

#    sub_folder = 'branch_Spin_to_charge/2020_10/'
#    green_file = '2020_10_14-16_47_42-goeppert-mayer-nv1'
#    red_file = '2020_10_14-16_49_03-goeppert-mayer-nv1'
#
#    data = tool_belt.get_raw_data('image_sample', sub_folder+green_file)
#    green_img_array = numpy.array(data['img_array'])
#
#    data = tool_belt.get_raw_data('image_sample', sub_folder+red_file)
#    red_img_array = numpy.array(data['img_array'])
#    x_voltages = data['x_voltages']
#    y_voltages = data['y_voltages']
#
#    dif_img_array = green_img_array - red_img_array
#
#    x_num_steps = len(x_voltages)
#    x_low = x_voltages[0]
#    x_high = x_voltages[x_num_steps-1]
#    y_num_steps = len(y_voltages)
#    y_low = y_voltages[0]
#    y_high = y_voltages[y_num_steps-1]
#
#    pixel_size = x_voltages[1] - x_voltages[0]
#    half_pixel_size = pixel_size / 2
#    img_extent = [x_high + half_pixel_size, x_low - half_pixel_size,
#                  y_low - half_pixel_size, y_high + half_pixel_size]
#
#    title = 'Dif image yellow scan after green initialization and red initialization'
#    tool_belt.create_image_figure(numpy.fliplr(dif_img_array), img_extent,
#                                            clickHandler=on_click_image,
#                                            title = title)
