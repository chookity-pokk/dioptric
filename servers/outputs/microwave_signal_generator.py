# -*- coding: utf-8 -*-
"""
Output server for the microwave signal generator.

Created on Wed Apr 10 12:53:38 2019

@author: mccambria

### BEGIN NODE INFO
[info]
name = microwave_signal_generator
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
import visa  # Docs here: https://pyvisa.readthedocs.io/en/master/
import nidaqmx
import nidaqmx.stream_writers as stream_writers
from nidaqmx.constants import AcquisitionType
import numpy


class MicrowaveSignalGenerator(LabradServer):
    name = 'microwave_signal_generator'

    def initServer(self):
        config = ensureDeferred(self.get_config())
        config.addCallback(self.on_get_config)

    async def get_config(self):
        p = self.client.registry.packet()
        p.cd('Config')
        p.get('uwave_sig_gen_visa_address')
        p.cd(['Wiring', 'Daq'])
        p.get('di_uwave_clock')
        p.get('ao_uwave_sig_gen_mod')
        result = await p.send()
        return result['get']

    def on_get_config(self, config):
        resource_manager = visa.ResourceManager()
        self.sig_gen = resource_manager.open_resource(config[0])
        # Set the VISA read and write termination. This is specific to the
        # instrument - you can find it in the instrument's programming manual
        self.sig_gen.read_termination = '\r\n'
        self.sig_gen.write_termination = '\r\n'
        # Set our channels for FM
        self.daq_di_pulser_clock = config[1]
        self.daq_ao_sig_gen_mod = config[2]
        self.task = None    # Initialize state variable
        self.reset(None)

    @setting(0)
    def uwave_on(self, c):
        """Turn on the signal. This is like opening an internal gate on
        the signal generator.
        """

        self.sig_gen.write('ENBR 1')

    @setting(1)
    def uwave_off(self, c):
        """Turn off the signal. This is like closing an internal gate on
        the signal generator.
        """

        self.sig_gen.write('ENBR 0')

    @setting(2, freq='v[]')
    def set_freq(self, c, freq):
        """Set the frequency of the signal.

        Params
            freq: float
                The frequency of the signal in GHz
        """

        # Determine how many decimal places we need
        precision = len(str(freq).split('.')[1])
        self.sig_gen.write('FREQ {0:.{1}f}GHZ'.format(freq, precision))

    @setting(3, amp='v[]')
    def set_amp(self, c, amp):
        """Set the amplitude of the signal.

        Params
            amp: float
                The amplitude of the signal in dBm
        """

        # Determine how many decimal places we need
        precision = len(str(amp).split('.')[1])
        self.sig_gen.write('AMPR {0:.{1}f}DBM'.format(amp, precision))

    def daq_write_to_mod(self, voltage):
        """Write the specified voltage."""

        # Close the stream task if it exists
        # This can happen if we quit out early
        if self.task is not None:
            self.close_task_internal()

        with nidaqmx.Task() as task:
            # Set up the output channels
            task.ao_channels.add_ao_voltage_chan(self.daq_ao_sig_gen_mod,
                                                 min_val=-1.0, max_val=1.0)
            task.write(voltage)
    
    def load_stream_writer(self, task_name, voltages, period=0.001*10**9):
        
        # Close the existing task
        if self.task is not None:
            self.close_task_internal()
        task = nidaqmx.Task(task_name)

        # Write the initial voltages and stream the rest
        num_voltages = len(voltages)
        self.daq_write_to_mod(voltages[0])
        stream_voltages = voltages[1:]
        stream_voltages = numpy.ascontiguousarray(stream_voltages)
        num_stream_voltages = num_voltages - 1
        
        # Create a new task
        self.task = task

        # Set up the output channels
        task.ao_channels.add_ao_voltage_chan(self.daq_ao_sig_gen_mod,
                                             min_val=-1.0, max_val=1.0)

        # Set up the output stream
        output_stream = nidaqmx.task.OutStream(task)
        writer = stream_writers.AnalogSingleChannelWriter(output_stream)

        # Configure the sample to advance on the rising edge of the PFI input.
        # The frequency specified is just the max expected rate in this case.
        # We'll stop once we've run all the samples.
        freq = float(1/(period*(10**-9)))  # freq in seconds as a float
        task.timing.cfg_samp_clk_timing(freq, source=self.daq_di_pulser_clock,
                                        samps_per_chan=num_stream_voltages)

        writer.write_many_sample(stream_voltages)

        # Close the task once we've written all the samples
        task.register_done_event(self.close_task_internal)

        task.start()


#    @setting(4, fm_range='v[]', voltages='*v[]', period='i')
#    def load_fm(self, c, fm_range, voltages, period):
    @setting(4, fm_range='v[]', voltages='*v[]', period='i')
    def load_fm(self, c, fm_range, voltages, period):
        """Set up frequency modulation via an external voltage. This has never
        been used or tested and needs work.
        """

        # Set up the DAQ AO that will control the modulation
        self.load_stream_writer('UwaveSigGen-load_fm', voltages, period)
        # Simple FM is type 1, subtype 0
        self.sig_gen.write('TYPE 1')
        self.sig_gen.write('STYP 0')
        # Set the range of the modulation
        precision = len(str(fm_range).split('.')[1])
        self.sig_gen.write('FDEV {0:.{1}f}GHZ'.format(fm_range, precision))
        # Set to an external source
        self.sig_gen.write('MFNC 5')
        # Turn on FM
        self.sig_gen.write('MODL 1')

    @setting(5)
    def mod_off(self, c):
        """Turn off the modulation."""

        self.sig_gen.write('MODL 0')
        task = self.task
        if task is not None:
            task.close()

    @setting(6)
    def reset(self, c):
        self.sig_gen.write('FDEV 0')
        self.uwave_off(c)
        self.mod_off(c)
        # Clean up the DAQ task!
        if self.task is not None:
            crash = 1/0
        # Set the DAQ AO to 0
        with nidaqmx.Task() as task:
            # Set up the output channels
            task.ao_channels.add_ao_voltage_chan(self.daq_ao_sig_gen_mod,
                                                 min_val=-1.0, max_val=1.0)
            task.write(0.0)


__server__ = MicrowaveSignalGenerator()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
