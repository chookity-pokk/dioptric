# -*- coding: utf-8 -*-
"""
Input server for a thermistor. Communicates via the DAQ.

Created on Tue Apr  9 08:52:34 2019

@author: mccambria

### BEGIN NODE INFO
[info]
name = thermistor
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
import numpy
import nidaqmx


class Thermistor(LabradServer):
    name = 'thermistor'

    def initServer(self):
        config = ensureDeferred(self.get_config())
        config.addCallback(self.on_get_config)

    async def get_config(self):
        p = self.client.registry.packet()
        p.cd(['Config', 'Wiring', 'Daq'])
        p.get('ai_thermistor_sig')
        p.get('ai_thermistor_ref')
        result = await p.send()
        return result['get']

    def on_get_config(self, wiring):
        self.daq_ai_sig = wiring[0]
        self.daq_ai_ref = wiring[1]

    def stopServer(self):
        for apd_index in self.tasks:
            self.close_task_internal(apd_index)

    @setting(0, returns='*v[]')
    def read_temperature(self, c):
        """Return the temperature in V"""
        
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(self.daq_ai_sig,
                                                 min_val=0.0, max_val=5.0)
            sig = task.read()
            
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(self.daq_ai_ref,
                                                 min_val=0.0, max_val=5.0)
            ref = task.read()
        
        return [sig, ref]


__server__ = Thermistor()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
