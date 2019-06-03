# -*- coding: utf-8 -*-
"""
This file contains functions, classes, and other objects that are useful
in a variety of contexts. Since they are expected to be used in many
files, I put them all in one place so that they don't have to be redefined
in each file.

Created on Fri Nov 23 14:57:08 2018

@author: mccambria
"""


# %% Imports


# User modules
import PulseStreamer.pulse_streamer_jrpc
from PulseStreamer.pulse_streamer_jrpc import PulseStreamer
from PulseStreamer.pulse_streamer_jrpc import Start
from PulseStreamer.pulse_streamer_jrpc import Mode
from PulseStreamer.Sequence import Sequence

# Library modules
import nidaqmx
import matplotlib.pyplot as plt
import visa  # Docs here: https://pyvisa.readthedocs.io/en/master/
import threading
import os
import datetime
import numpy
import json
import time
import labrad
import csv
from scipy import asarray as ar, exp
from tkinter import Tk
from tkinter import filedialog
from git import Repo


# %% xyz sets


def set_xyz(cxn, coords):
    cxn.galvo.write(coords[0], coords[1])
    cxn.objective_piezo.write_voltage(coords[2])


def set_xyz_zero(cxn):
    cxn.galvo.write(0.0, 0.0)
    cxn.objective_piezo.write_voltage(50.0)


# %% Matplotlib plotting utils


def create_image_figure(imgArray, imgExtent, clickHandler=None):
    """
    Creates a figure containing a single grayscale image and a colorbar.

    Params:
        imgArray: numpy.ndarray
            Rectangular numpy array containing the image data.
            Just zeros if you're going to be writing the image live.
        imgExtent: list(float)
            The extent of the image in the form [left, right, bottom, top]
        clickHandler: function
            Function that fires on clicking in the image

    Returns:
        matplotlib.figure.Figure
    """

    # Tell matplotlib to generate a figure with just one plot in it
    fig, ax = plt.subplots()

    # Tell the axes to show a grayscale image
    img = ax.imshow(imgArray, cmap='inferno',
                    extent=tuple(imgExtent))

    # Check if we should clip or autoscale
    clipAtThousand = False
    if clipAtThousand:
        if numpy.all(numpy.isnan(imgArray)):
            imgMax = 0  # No data yet
        else:
            imgMax = numpy.nanmax(imgArray)
        if imgMax > 1000:
            img.set_clim(None, 1000)
        else:
            img.autoscale()
    else:
        img.autoscale()

    # Add a colorbar
    plt.colorbar(img)

    # Wire up the click handler to print the coordinates
    if clickHandler is not None:
        fig.canvas.mpl_connect('button_press_event', clickHandler)

    # Draw the canvas and flush the events to the backend
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig


def update_image_figure(fig, imgArray):
    """
    Update the image with the passed image array and redraw the figure.
    Intended to update figures created by create_image_figure.

    The implementation below isn't nearly the fastest way of doing this, but
    it's the easiest and it makes a perfect figure every time (I've found
    that the various update methods accumulate undesirable deviations from
    what is produced by this brute force method).

    Params:
        fig: matplotlib.figure.Figure
            The figure containing the image to update
        imgArray: numpy.ndarray
            The new image data
    """

    # Get the image - Assume it's the first image in the first axes
    axes = fig.get_axes()
    ax = axes[0]
    images = ax.get_images()
    img = images[0]

    # Set the data for the image to display
    img.set_data(imgArray)

    # Check if we should clip or autoscale
    clipAtThousand = False
    if clipAtThousand:
        if numpy.all(numpy.isnan(imgArray)):
            imgMax = 0  # No data yet
        else:
            imgMax = numpy.nanmax(imgArray)
        if imgMax > 1000:
            img.set_clim(None, 1000)
        else:
            img.autoscale()
    else:
        img.autoscale()

    # Redraw the canvas and flush the changes to the backend
    fig.canvas.draw()
    fig.canvas.flush_events()


def create_line_plot_figure(vals, xVals=None):
    """
    Creates a figure containing a single line plot

    Params:
        vals: numpy.ndarray
            1D numpy array containing the values to plot
        xVals: numpy.ndarray
            1D numpy array with the x values to plot against
            Default is just the index of the value in vals

    Returns:
        matplotlib.figure.Figure
    """

    # Tell matplotlib to generate a figure with just one plot in it
    fig, ax = plt.subplots()

    if xVals is not None:
        ax.plot(xVals, vals)
        ax.set_xlim(xVals[0], xVals[len(xVals) - 1])
    else:
        ax.plot(vals)
        ax.set_xlim(0, len(vals)-1)

    # Draw the canvas and flush the events to the backend
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig


def create_line_plots_figure(vals, xVals=None):
    """
    Creates a figure containing a single line plot

    Params:
        vals: tuple(numpy.ndarray)
            1D numpy array containing the values to plot
        xVals: numpy.ndarray
            1D numpy array with the x values to plot against
            Default is just the index of the value in vals

    Returns:
        matplotlib.figure.Figure
    """

    # Tell matplotlib to generate a figure with len(vals) plots
    fig, ax = plt.subplots(len(vals))

    if xVals is not None:
        ax.plot(xVals, vals)
        ax.set_xlim(xVals[0], xVals[len(xVals) - 1])
    else:
        ax.plot(vals)
        ax.set_xlim(0, len(vals) - 1)

    # Draw the canvas and flush the events to the backend
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig


def update_line_plot_figure(fig, vals):
    """
    Updates a figure created by create_line_plot_figure

    Params:
        vals: numpy.ndarray
            1D numpy array containing the values to plot
    """

    # Get the line - Assume it's the first line in the first axes
    axes = fig.get_axes()
    ax = axes[0]
    lines = ax.get_lines()
    line = lines[0]

    # Set the data for the line to display and rescale
    line.set_ydata(vals)
    ax.relim()
    ax.autoscale_view(scalex=False)

    # Redraw the canvas and flush the changes to the backend
    fig.canvas.draw()
    fig.canvas.flush_events()


# %% Math functions


def gaussian(x, *params):
    """
    Calculates the value of a gaussian for the given input and parameters

    Params:
        x: float
            Input value
        params: tuple
            The parameters that define the Gaussian
            0: coefficient that defines the peak height
            1: mean, defines the center of the Gaussian
            2: standard deviation, defines the width of the Gaussian
            3: constant y value to account for background
    """

    coeff, mean, stdev, offset = params
    var = stdev**2  # variance
    centDist = x-mean  # distance from the center
    return offset + coeff**2*numpy.exp(-(centDist**2)/(2*var))


def sinexp(t, offset, amp, freq, decay):
    two_pi = 2*numpy.pi
    half_pi = numpy.pi / 2
    return offset + (amp * numpy.sin((two_pi * freq * t) + half_pi)) * exp(-decay**2 * t)

# This cosexp includes a phase that will be 0 in the ideal case. 
#def cosexp(t, offset, amp, freq, phase, decay):
#    two_pi = 2*numpy.pi
#    return offset + (numpy.exp(-t / abs(decay)) * abs(amp) * numpy.cos((two_pi * freq * t) + phase))


def cosexp(t, offset, amp, freq, decay):
    two_pi = 2*numpy.pi
    return offset + (numpy.exp(-t / abs(decay)) * abs(amp) * numpy.cos((two_pi * freq * t)))

# %% File Open utils
    
def ask_open_file(file_path):
    """
    Open a file by selecting it through a file window. File window usually 
    opens behind Spyder, may need to minimize Spyder to see file number
    
    file_path: input the file path to the folder of the data, starting after
    the Kolkowitz Lab Group folder
    
    Returns:
        string: file name of the file to use in program
    """
    
    root = Tk()
    root.withdraw()
    root.focus_force()
    directory = str("E:/Team Drives/Kolkowitz Lab Group/" + file_path)
    file_name = filedialog.askopenfilename(initialdir = directory,
                                          title = 'choose file to replot', filetypes = (("svg files","*.svg"),("all files","*.*")) ) 
    return file_name
    
# %%  Save utils
    

def get_branch_name():
    """Return the name of the active branch of kolkowitz-nv-experiment-v1.0"""
    repo_path = 'C:\\Users\\kolkowitz\\Documents\\' \
        'GitHub\\kolkowitz-nv-experiment-v1.0'
    repo = Repo(repo_path)
    return repo.active_branch.name


def get_time_stamp():
    """
    Get a formatted timestamp for file names and metadata.

    Returns:
        string: <year>-<month>-<day>_<hour>-<minute>-<second>
    """

    timestamp = str(datetime.datetime.now())
    timestamp = timestamp.split('.')[0]  # Ditch microseconds
    timestamp = timestamp.replace(':', '-')  # Replace colon with dash
    timestamp = timestamp.replace(' ', '_')  # Replace space with underscore
    return timestamp


def get_file_path(caller_file, timeStamp, name=''):
    """
    Get the file path to save to. This will be in a subdirectory of nvdata.

    Params:
        caller_file: file object
            __file__ of the caller - parsed to get the name of
            the subdirectory we will write to
        timeStamp: string
            Formatted timestamp to include in the file name
        name: string
            The file names consist of <timestamp>_<name>.<ext>
            Ext is supplied by the save functions
    """

    caller_file_name = os.path.basename(caller_file)
    sub_dir_name = os.path.splitext(caller_file_name)[0]

    # Set up a timestamp
    fileName = timeStamp + '_' + name
    
    branch_name = get_branch_name()
    
    # Check where we should save to
    if branch_name == 'master':
        # master should save without a branch sub-folder
        joined_path = os.path.join('E:/Team Drives/Kolkowitz Lab Group/nvdata',
                                   sub_dir_name)
    else:
        # Otherwise we want a branch sub-folder so that we know this data was
        # produced by code that's under development
        joined_path = os.path.join('E:/Team Drives/Kolkowitz Lab Group/nvdata',
                                   sub_dir_name,
                                   'branch_{}'.format(branch_name))
        
    folderDir = os.path.abspath(joined_path)

    # Make the required directory if it doesn't exist already
    if not os.path.isdir(folderDir):
        os.makedirs(folderDir)

    fileDir = os.path.abspath(os.path.join(folderDir, fileName))

    return fileDir


def save_figure(fig, filePath):
    """
    Save a matplotlib figure as a png.

    Params:
        fig: matplotlib.figure.Figure
            The figure to save
        filePath: string
            The file path to save to including the file name, excluding the
            extension
    """

    fig.savefig(filePath + '.svg')


def save_raw_data(rawData, filePath):
    """
    Save raw data in the form of a dictionary to a text file. New lines
    will be printed between entries in the dictionary.

    Params:
        rawData: dict
            The raw data as a dictionary - will be saved via JSON
        filePath: string
            The file path to save to including the file name, excluding the
            extension
    """

    with open(filePath + '.txt', 'w') as file:
        json.dump(rawData, file, indent=2)
        

# %% Safe stop (TM mccambria)


"""
Safe stop allows you to listen for a stop command while other things are
happening. This allows you to, say, stop a loop-based routine halfway
through. To use safe stop, call init_safe_stop() and then poll for the
stop command with safe_stop(). It's up to you to actually stop the
routine once you get the signal. Note that there's no way to programmatically
halt safe stop once it's running; the user must press enter.

Safe stop works by setting up a second thread alongside the main
thread. This thread listens for input, and sets a threading event after
the input. A threading event is just a flag used for communication between
threads. safe_stop() simply returns whether the flag is set.
"""


def safe_stop_input():
    """
    This is what the safe stop thread does.
    """

    global SAFESTOPEVENT
    input('Press enter to stop...')
    SAFESTOPEVENT.set()


def check_safe_stop_alive():
    """
    Checks if the safe stop thread is alive.
    """

    global SAFESTOPTHREAD
    try:
        SAFESTOPTHREAD
        return SAFESTOPTHREAD.isAlive()
    except NameError:
        return False


def init_safe_stop():
    """
    Initialize safe stop. Recycles the current instance of safe stop if
    there's one already running.
    """

    global SAFESTOPEVENT
    global SAFESTOPTHREAD
    needNewSafeStop = False

    # Determine if we need a new instance of safe stop or if there's
    # already one running
    try:
        SAFESTOPEVENT
        SAFESTOPTHREAD
        if not SAFESTOPTHREAD.isAlive():
            # Safe stop has already run to completion so start it back up
            needNewSafeStop = True
    except NameError:
        # Safe stop was never initialized so just get a new instance
        needNewSafeStop = True

    if needNewSafeStop:
        SAFESTOPEVENT = threading.Event()
        SAFESTOPTHREAD = threading.Thread(target=safe_stop_input)
        SAFESTOPTHREAD.start()


def safe_stop():
    """
    Check if the user has told us to stop. Call this whenever there's a safe
    break point after initializing safe stop.
    """

    global SAFESTOPEVENT

    try:
        return SAFESTOPEVENT.is_set()
    except Exception:
        print('Stopping. You have to intialize safe stop before checking it.')
        return True


def poll_safe_stop():
    """
    Polls safe stop continuously until the user says stop. Effectively a
    regular blocking input. The problem with just sticking input() in the main
    thread is that you can't have multiple threads looking for input.
    """

    init_safe_stop()
    while True:
        time.sleep(0.1)
        if safe_stop():
            break


# %% Resets and clean up

