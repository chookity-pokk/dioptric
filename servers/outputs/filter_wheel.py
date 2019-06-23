# -*- coding: utf-8 -*-
"""Output server for the 532 nm laser ND filter wheel. The arduino controlling
the wheel is running filter_wheel.ino, which is where all the hard work
happens. This just posts commands over serial. The commands are then picked
up on the arduino.

Created on Mon Apr  8 19:50:12 2019

@author: mccambria

### BEGIN NODE INFO
[info]
name = filter_wheel
version = 1.0
description =

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from labrad.server import LabradServer
from labrad.server import setting
from twisted.internet.defer import ensureDeferred
import serial
import logging


class FilterWheel(LabradServer):
    name = 'filter_wheel'
    logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(levelname)-8s %(message)s',
                datefmt='%y-%m-%d_%H-%M-%S',
                filename='E:/Shared drives/Kolkowitz Lab Group/nvdata/labrad_logging/{}.log'.format(name))

    def initServer(self):
        self.task = None
        config = ensureDeferred(self.get_config())
        config.addCallback(self.on_get_config)

    async def get_config(self):
        p = self.client.registry.packet()
        p.cd(['Config'])
        p.get('filter_wheel_usb_address')
        p.cd(['FilterWheelIndexing'])
        p.dir()
        result = await p.send()
        return result

    def on_get_config(self, config):
        # Connect to the USB port
        self.arduino = serial.Serial(config['get'], 9600, timeout=5)
        # Get the dictionary mapping ND values to the indices on the wheel
        reg_keys = config['dir'][1]  # dir returns subdirs followed by keys
        indexing = ensureDeferred(self.get_mapping(reg_keys))
        indexing.addCallback(self.on_get_mapping, reg_keys)

    def get_mapping(self, reg_keys)
        p = self.client.registry.packet()
        for reg_key in reg_keys:
            p.get(reg_key, key=reg_key)  # Return as a dictionary
        result = await p.send()
        return result

    def on_get_mapping(self, mapping, reg_keys):
        self.filter_mapping = {}
        for reg_key in reg_keys:
            self.filter_mapping[reg_key] = mapping[reg_key]
        # Wait until the arduino lets us know it completed setup
        msg = self.arduino.read_until(b'#').split(b'#')[0]
        logging.debug(msg)

    @setting(0, filter_name='s')
    def set_filter(filter_name):
        filter_ind = filter_mapping[filter_name]
        self.arduino.write(b'FILTER{}#'.format(filter_ind))

__server__ = FilterWheel()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
