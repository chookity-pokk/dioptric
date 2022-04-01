# -*- coding: utf-8 -*-
"""
Timing server for the Swabian Pulse Stream 8/2.

Created on Tue Apr  9 17:12:27 2019

@author: mccambria

### BEGIN NODE INFO
[info]
name = pulse_streamer
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
from pulsestreamer import PulseStreamer as Pulser
from pulsestreamer import TriggerStart
from pulsestreamer import OutputState
import importlib
import os
import sys
import utils.tool_belt as tool_belt
import json
import logging
import socket
from pathlib import Path


class PulseStreamer(LabradServer):
    name = 'pulse_streamer'
    pc_name = socket.gethostname()

    def initServer(self):
        filename = 'C:/Users/student/Documents/labrad_logging/{}.log' 
        filename = filename.format(self.name)
        logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%y-%m-%d_%H-%M-%S', filename=filename)
        config = ensureDeferred(self.get_config())
        config.addCallback(self.on_get_config)

    async def get_config(self):
        p = self.client.registry.packet()
        p.cd(['', 'Config', 'DeviceIDs'])
        p.get('pulse_streamer_ip')
        p.dir()
        result = await p.send()
        return result

    def on_get_config(self, config):
        self.pulser = Pulser(config['get'])
        sequence_library_path = Path.home() / 'Documents/GitHub/kolkowitz-nv-experiment-v1.0/servers/timing/sequencelibrary'
        sys.path.append(str(sequence_library_path))
        self.get_config_dict()

    def get_config_dict(self):
        """
        Get the config dictionary on the registry recursively. Very similar
        to the function of the same name in tool_belt.
        """
        config_dict = {}
        _ = ensureDeferred(self.populate_config_dict(['', 'Config'],
                                                     config_dict))
        _.addCallback(self.on_get_config_dict, config_dict)
    
    async def populate_config_dict(self, reg_path, dict_to_populate):
        """Populate the config dictionary recursively"""

        # Sub-folders
        p = self.client.registry.packet()
        p.cd(reg_path)
        p.dir()
        result = await p.send()
        sub_folders, keys = result['dir']
        for el in sub_folders:
            sub_dict = {}
            sub_path = reg_path + [el]
            await self.populate_config_dict(sub_path, sub_dict)
            dict_to_populate[el] = sub_dict
    
        # Keys
        if len(keys) == 1:
            p = self.client.registry.packet()
            p.cd(reg_path)
            key = keys[0]
            p.get(key)
            result = await p.send()
            val = result['get']
            dict_to_populate[key] = val
        
        elif len(keys) > 1:
            p = self.client.registry.packet()
            p.cd(reg_path)
            for key in keys:
                p.get(key)
            result = await p.send()
            vals = result['get']
        
            for ind in range(len(keys)):
                key = keys[ind]
                val = vals[ind]
                dict_to_populate[key] = val

    def on_get_config_dict(self, _, config_dict):
        self.config_dict = config_dict
        self.pulser_wiring = self.config_dict['Wiring']['PulseStreamer']
        self.feedthrough_lasers = []
        optics_dict = config_dict["Optics"]
        for key in optics_dict:
            optic = optics_dict[key]
            feedthrough_str = optic["feedthrough"]
            if eval(feedthrough_str):
                self.feedthrough_lasers.append(key)
        logging.info(self.feedthrough_lasers)
        # Initialize state variables and reset
        self.seq = None
        self.loaded_seq_streamed = False
        self.reset(None)
        logging.info('Init complete')

    def get_seq(self, seq_file, seq_args_string):
        seq = None
        file_name, file_ext = os.path.splitext(seq_file)
        if file_ext == '.py':  # py: import as a module
            seq_module = importlib.import_module(file_name)
            
            ########### labrad did not like trying to import utils.tool_belt. This is only place tool_belt is used. Let's just put in the function here? 4/1/22
#            if seq_args_string == "":
#                args = []
#            else:
#                args = json.loads(seq_args_string)
            args = tool_belt.decode_seq_args(seq_args_string)
                
            seq, final, ret_vals = seq_module.get_seq(self, self.config_dict, 
                                                      args)
        return seq, final, ret_vals

    @setting(0, seq_file='s', num_repeat='i',
             seq_args_string='s', returns='*?')
    def stream_immediate(self, c, seq_file, num_repeat=1, seq_args_string=''):
        """Load the sequence from seq_file and immediately run it for
        the specified number of repitions. End in the specified
        final output state.

        Params
            seq_file: str
                A sequence file from the sequence library
            num_repeat: int
                Number of times to repeat the sequence. Default is 1
            args: list(any)
                Arbitrary list used to modulate a sequence from the sequence
                library - see simple_readout.py for an example. Default is
                None. All values in list must have same type.

        Returns
            list(any)
                Arbitrary list returned by the sequence file
        """

        ret_vals = self.stream_load(c, seq_file, seq_args_string)
        self.stream_start(c, num_repeat)
        return ret_vals

    @setting(1, seq_file='s', seq_args_string='s', returns='*?')
    def stream_load(self, c, seq_file, seq_args_string=''):
        """Load the sequence from seq_file. Set it to end in the specified
        final output state. The sequence will not run until you call
        stream_start.

        Params
            seq_file: str
                A sequence file from the sequence library
            args: list(any)
                Arbitrary list used to modulate a sequence from the sequence
                library - see simple_readout.py for an example. Default is
                None

        Returns
            list(any)
                Arbitrary list returned by the sequence file
        """
        
        self.pulser.setTrigger(start=TriggerStart.SOFTWARE)
        seq, final, ret_vals = self.get_seq(seq_file, seq_args_string)
        if seq is not None:
            self.seq = seq
            self.loaded_seq_streamed = False
            self.final = final
        return ret_vals

    @setting(2, num_repeat='i')
    def stream_start(self, c, num_repeat=1):
        """Run the currently loaded stream for the specified number of
        repitions.

        Params
            num_repeat: int
                Number of times to repeat the sequence. Default is 1
        """
        
        # Make sure the lasers that require it are set to feedthrough
        for laser in self.feedthrough_lasers:
            self_client = self.client
            if hasattr(self_client, laser):
                yield self_client[laser].load_feedthrough()

        if self.seq == None:
            raise RuntimeError('Stream started with no sequence.')
        if not self.loaded_seq_streamed:
            self.pulser.stream(self.seq, num_repeat, self.final)
            self.loaded_seq_streamed = True
        self.pulser.startNow()

    @setting(3, digital_channels='*i',
             analog_0_voltage='v[]', analog_1_voltage='v[]')
    def constant(self, c, digital_channels=[],
                 analog_0_voltage=0.0, analog_1_voltage=0.0):
        """Set the PulseStreamer to a constant output state."""

        digital_channels = [int(el) for el in digital_channels]
        state = OutputState(digital_channels,
                            analog_0_voltage, analog_1_voltage)
        self.pulser.constant(state)

    @setting(4)
    def force_final(self, c):
        """Force the PulseStreamer its current final output state.
        Essentially a stop command.
        """

        self.pulser.forceFinal()

    @setting(6)
    def reset(self, c):
        # Probably don't need to force_final right before constant but...
        self.force_final(c)
        self.constant(c, digital_channels = [],
                      analog_0_voltage = 0.0, analog_1_voltage = 0.0)
        self.seq = None
        self.loaded_seq_streamed = False


__server__ = PulseStreamer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
