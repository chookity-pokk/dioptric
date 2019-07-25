# -*- coding: utf-8 -*-
"""
Output server for the Thorlabs ELL9K filter slider.

Created on Thu Apr  4 15:58:30 2019

@author: mccambria

### BEGIN NODE INFO
[info]
name = filter_slider_ell9k
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
import time
import logging


class FilterSliderEll9k(LabradServer):
    name = 'filter_slider_ell9k'
    logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s %(levelname)-8s %(message)s',
                datefmt='%y-%m-%d_%H-%M-%S',
                filename='E:/Shared drives/Kolkowitz Lab Group/nvdata/labrad_logging/{}.log'.format(name))

    def initServer(self):
        config = ensureDeferred(self.get_config())
        config.addCallback(self.on_get_config)

    async def get_config(self):
        p = self.client.registry.packet()
        p.cd('Config')
        p.get('filter_slider_ell9k_address')
        p.cd('FilterSliderEll9kFilterMapping')
        p.dir()
        result = await p.send()
        return result

    def on_get_config(self, config):
        # Get the slider
        try:
            self.slider = serial.Serial(config['get'], 9600, serial.EIGHTBITS,
                                serial.PARITY_NONE, serial.STOPBITS_ONE)
        except Exception as e:
            logging.debug(e)
            del self.slider
        time.sleep(0.1)
        self.slider.flush()
        time.sleep(0.1)
        filter_mapping_keys = config['dir'][1]
        config = ensureDeferred(self.get_mapping(filter_mapping_keys))
        config.addCallback(self.on_get_mapping, filter_mapping_keys)
        
    async def get_mapping(self, filter_mapping_keys):
        # Set up the mapping from filter name to slider position
        p = self.client.registry.packet()
        for key in filter_mapping_keys:
            p.get(key)
        result = await p.send()
        return result['get']
            
    def on_get_mapping(self, mapping, keys):
        self.slider_positions = {}
        for key_ind in range(len(keys)):
            key = keys[key_ind]
            pos = mapping[key_ind]
            self.slider_positions[key] = pos
        # Set up the mapping from filter position to move command
        self.move_commands = {0: '0ma00000000'.encode(),
                              1: '0ma00000020'.encode(),
                              2: '0ma00000040'.encode(),
                              3: '0ma00000060'.encode()}
        logging.debug('Init complete')

    @setting(0, filter_name='s')
    def set_filter(self, c, filter_name):
        pos = self.slider_positions[filter_name]
        cmd = self.move_commands[pos]
        self.slider.write(cmd)
        self.slider.readline()


__server__ = FilterSliderEll9k()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
