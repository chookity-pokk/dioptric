# -*- coding: utf-8 -*-
"""
Created on Wed Nov 10 10:46:28 2021

@author: agardill
"""


import numpy
import utils.tool_belt as tool_belt
import time
import labrad
import majorroutines.optimize_digital as optimize
import majorroutines.image_sample as image_sample
import matplotlib.pyplot as plt
  
def xy_scan_voltages(x_center, y_center, x_range, y_range, num_steps):
    
        if x_range != y_range:
            raise ValueError("x_range must equal y_range for now")

        x_num_steps = num_steps
        y_num_steps = num_steps

        # Force the scan to have square pixels by only applying num_steps
        # to the shorter axis
        half_x_range = x_range / 2
        half_y_range = y_range / 2

        x_low = x_center - half_x_range
        x_high = x_center + half_x_range
        y_low = y_center - half_y_range
        y_high = y_center + half_y_range

        # Apply scale and offset to get the voltages we'll apply to the stage
        # Note that the polar/azimuthal angles, not the actual x/y positions
        # are linear in these voltages. For a small range, however, we don't
        # really care.
        x_positions_1d = numpy.linspace(x_low, x_high, num_steps)
        y_positions_1d = numpy.linspace(y_low, y_high, num_steps)

        ######### Works for any x_range, y_range #########

        # Winding cartesian product
        # The x values are repeated and the y values are mirrored and tiled
        # The comments below shows what happens for [1, 2, 3], [4, 5, 6]

        # [1, 2, 3] => [1, 2, 3, 3, 2, 1]
        x_inter = numpy.concatenate((x_positions_1d, numpy.flipud(x_positions_1d)))
        # [1, 2, 3, 3, 2, 1] => [1, 2, 3, 3, 2, 1, 1, 2, 3]
        if y_num_steps % 2 == 0:  # Even x size
            x_postions = numpy.tile(x_inter, int(y_num_steps / 2))
        else:  # Odd x size
            x_postions = numpy.tile(x_inter, int(numpy.floor(y_num_steps / 2)))
            x_postions = numpy.concatenate((x_postions, x_positions_1d))

        # [4, 5, 6] => [4, 4, 4, 5, 5, 5, 6, 6, 6]
        y_postions = numpy.repeat(y_positions_1d, x_num_steps)

        return x_postions, y_postions, x_positions_1d, y_positions_1d
# %% Main
    

def main(nv_sig, x_range, y_range, num_steps, apd_indices,
         save_data=True, plot_data=True, 
         um_scaled=False):

    with labrad.connect() as cxn:
        img_array, x_voltages, y_voltages = main_with_cxn(cxn, nv_sig, x_range,
                      y_range, num_steps, apd_indices, save_data, plot_data, 
                      um_scaled)

    return img_array, x_voltages, y_voltages

def main_with_cxn(cxn, nv_sig, x_range, y_range, num_steps,
                  apd_indices, save_data=True, plot_data=True, 
                  um_scaled=False):

    # %% Some initial setup
    
    startFunctionTime = time.time()
    
    tool_belt.reset_cfm(cxn)
    
    laser_key = 'imaging_laser'

    drift = tool_belt.get_drift() 
    coords = nv_sig['coords']
    adjusted_coords = (numpy.array(coords) + numpy.array(drift)).tolist() 
    x_center, y_center, z_center = adjusted_coords
    optimize.prepare_microscope(cxn, nv_sig, adjusted_coords)
    
    readout = nv_sig['imaging_readout_dur']
    readout_us = readout / 10**3
    readout_sec = readout / 10**9

    laser_name = nv_sig[laser_key]
    tool_belt.set_filter(cxn, nv_sig, laser_key)
    laser_power = tool_belt.set_laser_power(cxn, nv_sig, laser_key)
    # print(laser_power)
    
    if x_range != y_range:
        raise RuntimeError('x and y resolutions must match for now.')

    xy_server = tool_belt.get_xy_server(cxn)
    z_server = tool_belt.get_z_server(cxn)
    
    # Get a couple registry entries
    # See if this setup has finely specified delay times, else just get the 
    # one-size-fits-all value.
    dir_path = ['', 'Config', 'Positioning']
    
    
    cxn.registry.cd(*dir_path)
    _, keys = cxn.registry.dir()
    

    total_num_samples = num_steps**2  
    
    
    
    
    # %% calculate x y positions

    ret_vals = xy_scan_voltages(x_center, y_center,
                                       x_range, y_range, num_steps)
    x_positions, y_positions, x_positions_1d, y_positions_1d = ret_vals
    
    # return
    x_num_steps = len(x_positions_1d)
    x_low = x_positions_1d[0]
    x_high = x_positions_1d[x_num_steps-1]
    y_num_steps = len(y_positions_1d)
    y_low = y_positions_1d[0]
    y_high = y_positions_1d[y_num_steps-1]

    pixel_size = x_positions_1d[1] - x_positions_1d[0]
    
    
    # %% Set up our raw data objects

    # Initialize imgArray and set all values to NaN so that unset values
    # are not interpreted as 0 by matplotlib's colobar
    img_array = numpy.empty((x_num_steps, y_num_steps))
    img_array[:] = numpy.nan
    img_write_pos = []
    #make an array to save information if the piezo did not reach it's target
    flag_img_array = numpy.empty((x_num_steps, y_num_steps))
    flag_img_write_pos = []
    #array for dx values
    dx_img_array = numpy.empty((x_num_steps, y_num_steps))
    dx_img_write_pos = []
    #array for dy values
    dy_img_array = numpy.empty((x_num_steps, y_num_steps))
    dy_img_write_pos = []


    # %% Set up the image display

    if plot_data:

        img_array_kcps = numpy.copy(img_array)

        # For the image extent, we need to bump out the min/max x/y by half the
        # pixel size in each direction so that the center of each pixel properly
        # lies at its x/y voltages.
        half_pixel_size = pixel_size / 2
        img_extent = [x_high + half_pixel_size, x_low - half_pixel_size,
                      y_low - half_pixel_size, y_high + half_pixel_size]
        title = r'Confocal scan, {}, {} us readout'.format(laser_name, readout_us)
        fig = tool_belt.create_image_figure(img_array, img_extent,
                        clickHandler=image_sample.on_click_image, color_bar_label='kcps',
                        title=title, um_scaled=um_scaled)
        
    # %% Collect the data
    populate_img_array = image_sample.populate_img_array
    update_image_figure = tool_belt.update_image_figure
    tool_belt.init_safe_stop()
    
    cxn.apd_tagger.start_tag_stream(apd_indices) #move outside of sequence
    
    dx_list = []
    dy_list = []
    x_center1, y_center1, z_center1 = coords
    #ret_vals = xy_scan_voltages(x_center1, y_center1,
     #                                  x_range, y_range, num_steps)
    #x_positions1, y_positions1, _, _ = ret_vals
    time_start= time.time()
    opti_interval=2
    for i in range(total_num_samples): 
        #time_now = time.time()
        #if (time_now - time_start)/60 >= opti_interval:
       #     optimize.main_with_cxn(cxn, nv_sig, apd_indices)
       #     drift = tool_belt.get_drift() 
       #     time_start= time.time()
       #     cur_z_pos = z_center1 +drift[2]
       #     z_server.write_z(cur_z_pos)

        
        
        #cxn.apd_tagger.start_tag_stream(apd_indices)
        
        cur_x_pos = x_positions[i]
        cur_y_pos = y_positions[i]
        
        if tool_belt.safe_stop():
            break
        
        
        flag = xy_server.write_xy(cur_x_pos, cur_y_pos)
            
            
            
        # Some diagnostic stuff - checking how far we are from the target pos
        actual_x_pos, actual_y_pos = xy_server.read_xy()
        dx_list.append((actual_x_pos-cur_x_pos)*1e3)
        dy_list.append((actual_y_pos-cur_y_pos)*1e3)
        
        # read the counts at this location
        seq_args = [0, readout, apd_indices[0], laser_name, laser_power]
        seq_args_string = tool_belt.encode_seq_args(seq_args)
        cxn.pulse_streamer.stream_immediate('simple_readout.py',1,
                                                  seq_args_string)
        new_samples = cxn.apd_tagger.read_counter_simple(1) 
        
        # update the image arrays
        populate_img_array(new_samples, img_array, img_write_pos)
        populate_img_array([flag], flag_img_array, flag_img_write_pos)
        
        populate_img_array([(actual_x_pos-cur_x_pos)*1e3], dx_img_array, dx_img_write_pos)
        populate_img_array([(actual_y_pos-cur_y_pos)*1e3], dy_img_array, dy_img_write_pos)
        
        # Either include this in loop so it plots data as it takes it (takes about 2x as long)
        # or put it ourside loop so it plots after data is complete
    if plot_data: ###########################################################
            img_array_kcps[:] = (img_array[:] / 1000) / readout_sec
            update_image_figure(fig, img_array_kcps)
        
    do_analysis=False
    if do_analysis:
       tool_belt.create_image_figure(dx_img_array, img_extent,
                        clickHandler=image_sample.on_click_image, color_bar_label='nm',
                        title = "positional accuracy (dx)", um_scaled=um_scaled,
                        color_map = 'bwr')
       tool_belt.create_image_figure(dy_img_array, img_extent,
                        clickHandler=image_sample.on_click_image, color_bar_label='nm',
                        title = "positional accuracy (dy)", um_scaled=um_scaled,
                        color_map = 'bwr')
        
        
    
    
    
    
       print(numpy.std(abs(numpy.array(dx_list))))
       print(numpy.std(abs(numpy.array(dy_list))))
       fig_pos, axes = plt.subplots(1,2)
       ax = axes[0]
       ax.plot(dx_list)
       ax.set_xlabel('data point')
       ax.set_ylabel('Difference between set values and actual value (nm)')
       ax.set_title('X')
       ax = axes[1]
       ax.plot(dy_list)
       ax.set_xlabel('data point')
       ax.set_ylabel('Difference between set values and actual value (nm)')
       ax.set_title('Y')

    # %% Clean up

    tool_belt.reset_cfm(cxn)
    
    # %% Save the data

    endFunctionTime = time.time()
    time_elapsed = endFunctionTime - startFunctionTime
    timestamp = tool_belt.get_time_stamp()

    rawData = {'timestamp': timestamp,
               'time_elapsed': time_elapsed,
               'nv_sig': nv_sig,
               'nv_sig-units': tool_belt.get_nv_sig_units(),
               'x_range': x_range,
               'x_range-units': 'um',
               'y_range': y_range,
               'y_range-units': 'um',
               'num_steps': num_steps,
               'readout': readout,
               'readout-units': 'ns',
               'dx_list': dx_list,
               'dx_list-units': 'nm',
               'dy_list': dy_list,
               'dy_list-units': 'nm',
               'x_positions_1d': x_positions_1d.tolist(),
               'x_positions_1d-units': 'um',
               'y_positions_1d': y_positions_1d.tolist(),
               'y_positions_1d-units': 'um',
               'img_array': img_array.astype(int).tolist(),
               'img_array-units': 'counts',
               'flag_img_array': flag_img_array.tolist(),}

    if save_data:

        filePath = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
        tool_belt.save_raw_data(rawData, filePath)

        if plot_data:

            tool_belt.save_figure(fig, filePath)


    
    return img_array, x_positions_1d, y_positions_1d
 

# %% Run the file


if __name__ == '__main__':


    path = 'pc_rabi/branch_CFMIII/image_sample_digital/2021_12'
    file_name = '2021_12_21-10_24_48-johnson-nv0_2021_12_2021'

    data = tool_belt.get_raw_data( file_name, path)
    nv_sig = data['nv_sig']
    timestamp = data['timestamp']
    img_array = data['img_array']
    x_range= data['x_range']
    y_range= data['y_range']
    x_voltages = data['x_positions_1d']
    y_voltages = data['y_positions_1d']
    
    
    x_low = -x_range/2
    x_high = x_range/2
    y_low = -y_range/2
    y_high = y_range/2
    
    pixel_size = x_voltages[1] - x_voltages[0]
    half_pixel_size = pixel_size / 2
    img_extent = [x_low - half_pixel_size,x_high + half_pixel_size,
                  y_low - half_pixel_size, y_high + half_pixel_size]
    
    # csv_name = '{}_{}'.format(timestamp, nv_sig['name'])
    
    
    tool_belt.create_image_figure(img_array, numpy.array(img_extent), 
                                  clickHandler=image_sample.on_click_image,
                        title=None, color_bar_label='Counts', 
                        min_value=None, um_scaled=True)
    
    
    # tool_belt.save_image_data_csv(img_array, x_voltages, y_voltages,  path, 
    #                               csv_name)   