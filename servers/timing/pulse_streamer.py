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
import logging


class PulseStreamer(LabradServer):
    name = 'pulse_streamer'
    logging.basicConfig(level=logging.WARNING, 
                format='%(asctime)s %(levelname)-8s %(message)s',
                datefmt='%y-%m-%d_%H-%M-%S',
                filename='E:/Shared drives/Kolkowitz Lab Group/nvdata/labrad_logging/{}.log'.format(name))

    def initServer(self):
        config = ensureDeferred(self.get_config())
        config.addCallback(self.on_get_config)

    async def get_config(self):
        p = self.client.registry.packet()
        p.cd('Config')
        p.get('pulse_streamer_ip')
        p.get('sequence_library_path')
        p.cd(['Wiring', 'Pulser'])
        p.dir()
        result = await p.send()
        return result

    def on_get_config(self, config):
        get_result = config['get']
        self.pulser = Pulser(get_result[0])
        sys.path.append(get_result[1])
        reg_keys = config['dir'][1]  # dir returns subdirs followed by keys
        wiring = ensureDeferred(self.get_wiring(reg_keys))
        wiring.addCallback(self.on_get_wiring, reg_keys)

    async def get_wiring(self, reg_keys):
        p = self.client.registry.packet()
        for reg_key in reg_keys:
            p.get(reg_key, key=reg_key)  # Return as a dictionary
        result = await p.send()
        return result

    def on_get_wiring(self, wiring, reg_keys):
        self.pulser_wiring = {}
        for reg_key in reg_keys:
            self.pulser_wiring[reg_key] = wiring[reg_key]
        # Initialize state variables and reset
        self.seq = None
        self.loaded_seq_streamed = False
        self.reset(None)
        logging.debug('Init complete')

    def get_seq(self, seq_file, seq_args_string):
        seq = None
        file_name, file_ext = os.path.splitext(seq_file)
        if file_ext == '.py':  # py: import as a module
            seq_module = importlib.import_module(file_name)
            args = tool_belt.decode_seq_args(seq_args_string)
            seq, final, ret_vals = seq_module.get_seq(self.pulser_wiring, args)
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
        self.constant(c, [self.pulser_wiring['do_532_aom']])
        self.seq = None
        self.loaded_seq_streamed = False


__server__ = PulseStreamer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
