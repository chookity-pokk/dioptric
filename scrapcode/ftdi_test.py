# -*- coding: utf-8 -*-
"""Template for scripts that should be run directly from the files themselves
(as opposed to from the control panel, for example).

Created on Sun Jun 16 11:22:40 2019

@author: mccambria
"""


# %% Imports

from pyftdi.ftdi import Ftdi
from pyftdi.usbtools import UsbTools
import time

# %% Constants


# %% Functions


# %% Main


def main(dev):
    """When you run the file, we'll call into main, which should contain the
    body of the script.
    """
    
    # This setup sequence is adapted straight from section 2.1 (USB Interface
    # adapter) of the Elliptec communication protocol manual
    dev.set_baudrate(9600)
    dev.set_line_property(8, 1, 'N')
    time.sleep(0.1)
    dev.purge_buffers()
    time.sleep(0.1)
    # Reset - not supported by pyftdi apparently
    dev.set_flowctrl('')
    
    print(dev.poll_modem_status())
    print(dev.read_pins())
    print('writing...')
    print(dev.write_data('hello'.encode()))
    print('written')
    print(dev.read_data(5))


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here

    # Run the script
    try:
        tools = UsbTools()
        dev = Ftdi()
        # SN 'DM014SW8'
        dev = tools.get_device(0x0403, 0x6015)
#        dev.open_from_url('ftdi://::DM014SW8/1')
        main(dev)
    except Exception as e:
        print(e)
        dev.close()
        tools.release_device(dev)
        tools.flush_cache()
        