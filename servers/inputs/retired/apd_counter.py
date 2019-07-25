# -*- coding: utf-8 -*-
"""
Input server for the LASER COMPONENTS COUNT-100C APD. Communicates via the DAQ.

Created on Tue Apr  9 08:52:34 2019

@author: mccambria

### BEGIN NODE INFO
[info]
name = apd_counter
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
import nidaqmx.stream_readers as stream_readers
from nidaqmx.constants import TriggerType
from nidaqmx.constants import Level


class ApdCounter(LabradServer):
    name = 'apd_counter'

    def initServer(self):
        config = ensureDeferred(self.get_config())
        config.addCallback(self.on_get_config)
        self.tasks = {}
        self.stream_reader_state = {}

    async def get_config(self):
        p = self.client.registry.packet()
        p.cd(['Config', 'Wiring', 'Daq'])
        p.get('di_clock')
        p.dir()
        result = await p.send()
        return result

    def on_get_config(self, config):
        # The counters share a clock, but everything else is distinct
        self.daq_di_clock = config['get']
        # Determine how many APDs we're supposed to set up
        apd_sub_dirs = []
        apd_indices = []
        sub_dirs = config['dir'][0]
        for sub_dir in sub_dirs:
            if sub_dir.startswith('Apd_'):
                apd_sub_dirs.append(sub_dir)
                apd_indices.append(int(sub_dir.split('_')[1]))
        if len(apd_sub_dirs) > 0:
            wiring = ensureDeferred(self.get_wiring(apd_sub_dirs))
            wiring.addCallback(self.on_get_wiring, apd_indices)

    async def get_wiring(self, apd_sub_dirs):
        p = self.client.registry.packet()
        for sub_dir in apd_sub_dirs:
            p.cd(['', 'Config', 'Wiring', 'Daq', sub_dir])
            p.get('ctr_apd')
            p.get('ci_apd')
            p.get('di_apd_gate')
        result = await p.send()
        return result['get']

    def on_get_wiring(self, wiring, apd_indices):
        self.daq_ctr_apd = {}
        self.daq_ci_apd = {}
        self.daq_di_apd_gate = {}
        # Loop through the possible counters
        for loop_index in range(len(apd_indices)):
            apd_index = apd_indices[loop_index]
            wiring_index = 3 * loop_index
            self.daq_ctr_apd[apd_index] = wiring[wiring_index]
            self.daq_ci_apd[apd_index] = wiring[wiring_index+1]
            self.daq_di_apd_gate[apd_index] = wiring[wiring_index+2]

    def stopServer(self):
        for apd_index in self.tasks:
            self.close_task_internal(apd_index)

    def close_task_internal(self, apd_index):
        task = self.tasks[apd_index]
        task.close()
        self.tasks.pop(apd_index)
        self.stream_reader_state.pop(apd_index)

    def try_load_stream_reader(self, c, apd_index, period, total_num_to_read):

        # Close the stream task if it exists
        # This can happen if we quit out early
        if apd_index in self.tasks:
            self.close_task_internal(apd_index)

        task = nidaqmx.Task('ApdCounter-load_stream_reader_{}'.format(apd_index))
        self.tasks[apd_index] = task

        chan_name = self.daq_ctr_apd[apd_index]
        chan = task.ci_channels.add_ci_count_edges_chan(chan_name)
        chan.ci_count_edges_term = self.daq_ci_apd[apd_index]

        # Set up the input stream
        input_stream = nidaqmx.task.InStream(task)
        input_stream.read_all_avail_samp = True
        reader = stream_readers.CounterReader(input_stream)
        # Just collect whatever data is available when we read
        reader.verify_array_shape = False

        # Set up the gate ('pause trigger')
        # Pause when low - i.e. read only when high
        task.triggers.pause_trigger.trig_type = TriggerType.DIGITAL_LEVEL
        task.triggers.pause_trigger.dig_lvl_when = Level.LOW
        gate_chan_name = self.daq_di_apd_gate[apd_index]
        task.triggers.pause_trigger.dig_lvl_src = gate_chan_name

        # Configure the sample to advance on the rising edge of the PFI input.
        # The frequency specified is just the max expected rate in this case.
        # We'll stop once we've run all the samples.
        freq = float(1/(period*(10**-9)))  # freq in seconds as a float
        task.timing.cfg_samp_clk_timing(freq, source=self.daq_di_clock,
                                        samps_per_chan=total_num_to_read)

        # Initialize the state dictionary for this stream
        self.stream_reader_state[apd_index] = {}
        state_dict = self.stream_reader_state[apd_index]
        state_dict['reader'] = reader
        state_dict['num_read_so_far'] = 0
        state_dict['total_num_to_read'] = total_num_to_read
        # Something funny is happening if we get more
        # than 1000 samples in one read
        state_dict['buffer_size'] = min(total_num_to_read, 1000)
        state_dict['last_value'] = 0  # Last cumulative value we read

        # Start the task. It will start counting immediately so we'll have to
        # discard the first sample.
        task.start()

    @setting(0, apd_index='i', period='i', total_num_to_read='i')
    def load_stream_reader(self, c, apd_index, period, total_num_to_read):
        """Open a stream to count clicks from the specified APD. The
        stream can be read with read_stream.

        Params
            apd_index: int
                Index of the APD to use
            period: int
                Expected between sample clocks in ns
            total_num_to_read: int
                Total number of samples that the stream will record. Due to a
                bug this value must currently be > 1.
        """
        self.try_load_stream_reader(c, apd_index, period, total_num_to_read)

    @setting(1, apd_index='i', num_to_read='i', returns='*w')
    def read_stream(self, c, apd_index, num_to_read=None):
        """Read the stream loaded by load_stream_reader.

        Params
            apd_index: int
                Index of the APD to use
            num_to_read: int
                Number of samples to read. This will not return until there
                are num_to_read samples available. Default is None, in which
                case we simply read what is available. This is useful for
                polling on a loop.

        Returns
            list(int)
                The samples that were read
        """

        # Unpack the state dictionary
        state_dict = self.stream_reader_state[apd_index]

        reader = state_dict['reader']
        num_read_so_far = state_dict['num_read_so_far']
        total_num_to_read = state_dict['total_num_to_read']
        buffer_size = state_dict['buffer_size']

        # Read the samples currently in the DAQ memory
        if num_to_read == None:
            # Read whatever is in the buffer
            new_samples_cum = numpy.zeros(buffer_size, dtype=numpy.uint32)
            read_all_available = nidaqmx.constants.READ_ALL_AVAILABLE
            num_new_samples = reader.read_many_sample_uint32(new_samples_cum,
                     number_of_samples_per_channel=read_all_available)
        else:
            # Read the specified number of samples
            new_samples_cum = numpy.zeros(buffer_size, dtype=numpy.uint32)
            wait_inf = nidaqmx.constants.WAIT_INFINITELY
            num_new_samples = reader.read_many_sample_uint32(new_samples_cum,
                                             num_to_read, timeout=wait_inf)
            if num_new_samples != num_to_read:
                raise Warning('Read more/less samples than specified.')

        # Check if we collected more samples than we need, which may happen
        # if the pulser runs longer than necessary. If so, just to throw out
        # excess samples.
        if num_read_so_far + num_new_samples > total_num_to_read:
            num_new_samples = total_num_to_read - num_read_so_far
        new_samples_cum = new_samples_cum[0: num_new_samples]

        # The DAQ counter reader returns cumulative counts, which is not what
        # we want. So we have to calculate the difference between samples
        # n and n-1 in order to get the actual count for the nth sample.
        new_samples_diff = numpy.zeros(num_new_samples)
        for index in range(num_new_samples):
            if index == 0:
                last_value = state_dict['last_value']
            else:
                last_value = new_samples_cum[index-1]

            new_samples_diff[index] = new_samples_cum[index] - last_value

        if num_new_samples > 0:
            state_dict['last_value'] = new_samples_cum[num_new_samples-1]

        # Update the current count and check if we're done with the task
        num_read_so_far += num_new_samples
        if num_read_so_far == total_num_to_read:
            self.close_task_internal(apd_index)
        else:
            state_dict['num_read_so_far'] = num_read_so_far

        return new_samples_diff


__server__ = ApdCounter()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
