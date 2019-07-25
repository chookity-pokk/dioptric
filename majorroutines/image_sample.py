# -*- coding: utf-8 -*-
"""
Scan the galvos over the designated area, collecting counts at each point.
Generate an image of the sample.

Includes a replotting routine to show the data with axes in um instead of V.

Includes a replotting routine to replot rw data to manipulate again.

Created on Tue Apr  9 15:18:53 2019

@author: mccambria
"""

import numpy
import utils.tool_belt as tool_belt
import time

import json
import matplotlib.pyplot as plt
import labrad


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

def reformat_plot(colorMap, save_file_type):
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
            xyzCenters = data["coords"]
            imgResolution = data["num_steps"]

            # Read in the values for the scan ranges, centers, and resolution
            yScanRange = data["y_range"]
            yCenter = xyzCenters[1]
            yImgResolution = imgResolution

            xScanRange = data["x_range"]
            xCenter = xyzCenters[0]
            xImgResolution = imgResolution

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

def create_figure(file_name, folder_name='E:/Shared drives/Kolkowitz Lab Group/nvdata/image_sample'):

    with open('{}/{}'.format(folder_name, file_name)) as file:
        data = json.load(file)
        x_range = data['x_range']
        y_range = data['y_range']
        x_voltages = data['x_voltages']
        coords = data['coords']
        img_array = numpy.array(data['img_array'])
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
    img_extent = [x_high + half_pixel_size, x_low - half_pixel_size,
                  y_low - half_pixel_size, y_high + half_pixel_size]

    fig = tool_belt.create_image_figure(img_array_kcps, img_extent)
    # Redraw the canvas and flush the changes to the backend
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig


# %% Mains


def main(nv_sig, x_range, y_range, num_steps, apd_indices,
         continuous=False, save_data=True, plot_data=True):

    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig, x_range, y_range, num_steps, apd_indices,
                      continuous, save_data, plot_data)

def main_with_cxn(cxn, nv_sig, x_range, y_range, num_steps, apd_indices,
                  continuous=False, save_data=True, plot_data=True):

    # %% Some initial setup
    
    tool_belt.reset_cfm(cxn)

    shared_params = tool_belt.get_shared_parameters_dict(cxn)
    readout = shared_params['continuous_readout_dur']

    adj_coords = (numpy.array(nv_sig['coords']) + \
                  numpy.array(tool_belt.get_drift())).tolist()
    x_center, y_center, z_center = adj_coords

    readout_sec = float(readout) / 10**9

    if x_range != y_range:
        raise RuntimeError('x and y resolutions must match for now.')

    # The galvo's small angle step response is 400 us
    # Let's give ourselves a buffer of 500 us (500000 ns)
    delay = int(0.5 * 10**6)

    total_num_samples = num_steps**2

    # %% Load the PulseStreamer

    seq_args = [delay, readout, apd_indices[0]]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    ret_vals = cxn.pulse_streamer.stream_load('simple_readout.py',
                                              seq_args_string)
    period = ret_vals[0]

    # %% Initialize at the passed coordinates

    tool_belt.set_xyz(cxn, [x_center, y_center, z_center])

    # %% Set up the galvo

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

        img_array_kcps = numpy.copy(img_array)

        # For the image extent, we need to bump out the min/max x/y by half the
        # pixel size in each direction so that the center of each pixel properly
        # lies at its x/y voltages.
        half_pixel_size = pixel_size / 2
        img_extent = [x_high + half_pixel_size, x_low - half_pixel_size,
                      y_low - half_pixel_size, y_high + half_pixel_size]

        fig = tool_belt.create_image_figure(img_array, img_extent,
                                            clickHandler=on_click_image)

    # %% Collect the data

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
        num_new_samples = len(new_samples)
        if num_new_samples > 0:
            populate_img_array(new_samples, img_array, img_write_pos)
            # This is a horribly inefficient way of getting kcps, but it
            # is easy and readable and probably fine up to some resolution
            # we likely will never try
            if plot_data:
                img_array_kcps[:] = (img_array[:] / 1000) / readout_sec
                tool_belt.update_image_figure(fig, img_array_kcps)
            num_read_so_far += num_new_samples

    # %% Clean up
    
    tool_belt.reset_cfm(cxn)

    # Return to center
    cxn.galvo.write(x_center, y_center)

    # %% Save the data

    timestamp = tool_belt.get_time_stamp()

    rawData = {'timestamp': timestamp,
               'nv_sig': nv_sig,
               'nv_sig-units': tool_belt.get_nv_sig_units(),
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

    return rawData


# %% Run the file


if __name__ == '__main__':
    file_name = '2019-06-27_16-02-37_ayrton14.txt'
    create_figure(file_name)
