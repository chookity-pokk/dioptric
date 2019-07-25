# -*- coding: utf-8 -*-
"""
Input server for APDs running into the Time Tagger.

Created on Wed Apr 24 22:07:25 2019

@author: mccambria

### BEGIN NODE INFO
[info]
name = apd_tagger
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
import TimeTagger
import numpy
import logging
import re


class ApdTagger(LabradServer):
    name = 'apd_tagger'
    logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s %(levelname)-8s %(message)s',
                datefmt='%y-%m-%d_%H-%M-%S',
                filename='E:/Shared drives/Kolkowitz Lab Group/nvdata/labrad_logging/{}.log'.format(name))

    def initServer(self):
        self.reset_tag_stream_state()
        config = ensureDeferred(self.get_config())
        config.addCallback(self.on_get_config)
    
    async def get_config(self):
        p = self.client.registry.packet()
        p.cd('Config')
        p.get('time_tagger_serial')
        p.cd(['Wiring', 'Tagger'])
        p.get('di_clock')
        p.dir()
        result = await p.send()
        return result
            
    def on_get_config(self, config):
        get_result = config['get']
        tagger_serial = get_result[0]
        self.tagger = TimeTagger.createTimeTagger(tagger_serial)
        self.tagger.reset()
        # The APDs share a clock, but everything else is distinct
        self.tagger_di_clock = get_result[1]
        # Create a mapping from tagger channels to semantic channel names
        self.channel_mapping = {self.tagger_di_clock: 'di_clock'}
        # Determine how many APDs we're supposed to set up
        apd_sub_dirs = []
        apd_indices = []
        sub_dirs = config['dir'][0]
        for sub_dir in sub_dirs:
            if re.fullmatch(r'Apd_[0-9]+', sub_dir):
                apd_sub_dirs.append(sub_dir)
                apd_indices.append(int(sub_dir.split('_')[1]))
        if len(apd_sub_dirs) > 0:
            wiring = ensureDeferred(self.get_wiring(apd_sub_dirs))
            wiring.addCallback(self.on_get_wiring, apd_indices)
    
    async def get_wiring(self, apd_sub_dirs):
        p = self.client.registry.packet()
        for sub_dir in apd_sub_dirs:
            p.cd(['', 'Config', 'Wiring', 'Tagger', sub_dir])
            p.get('di_apd')
            p.get('di_gate')
        result = await p.send()
        return result['get']

    def on_get_wiring(self, wiring, apd_indices):
        self.tagger_di_apd = {}
        self.tagger_di_gate = {}
        # Loop through the available APDs
        for loop_index in range(len(apd_indices)):
            apd_index = apd_indices[loop_index]
            wiring_index = 2 * loop_index
            di_apd = wiring[wiring_index]
            self.tagger_di_apd[apd_index] = di_apd
            self.channel_mapping[di_apd] = 'di_apd_{}'.format(apd_index)
            di_gate = wiring[wiring_index+1]
            self.tagger_di_gate[apd_index] = di_gate
            # APDs can share gates so make that apparent in the channel mapping
            if di_gate in self.channel_mapping:
                prev_val = self.channel_mapping[di_gate]
                new_val = '{}-{}'.format(prev_val, apd_index)
                self.channel_mapping[di_gate] = new_val
                prev_val = self.channel_mapping[-di_gate]
                new_val = '{}-{}'.format(prev_val, apd_index)
                self.channel_mapping[-di_gate] = new_val
            else:
                val = 'di_gate_open_{}'.format(apd_index)
                self.channel_mapping[di_gate] = val
                val = 'di_gate_close_{}'.format(apd_index)
                self.channel_mapping[-di_gate] = val
        self.reset_tag_stream_state()  # Initialize state variables
        self.reset(None)
        logging.debug('init complete')

    def read_raw_stream(self):
        if self.stream is None:
            logging.error('read_raw_stream attempted while stream is None.')
            return
        
        buffer = self.stream.getData()
        timestamps = buffer.getTimestamps()
        channels = buffer.getChannels()
        return timestamps, channels
    
    def read_counter_setting_internal(self, num_to_read):
        if self.stream is None:
            logging.error('read_counter attempted while stream is None.')
            return
        if num_to_read is None:
            # Poll once and return the result
            counts =  self.read_counter_internal(None)
        else:
            # Poll until we've read the requested number of samples
            counts = []
            while len(counts) < num_to_read:
                counts.extend(self.read_counter_internal(num_to_read))
            if len(counts) > num_to_read:
                msg = 'Read {} samples, only requested {}'.format(len(counts),
                            num_to_read)
                logging.error(msg)
                
        return counts
        
    def read_counter_internal(self, num_to_read):
        if self.stream is None:
            logging.error('read_counter_internal attempted while stream ' \
                          'is None.')
            return
        
        timestamps, channels = self.read_raw_stream()

        # Find clock clicks (sample breaks)
        result = numpy.nonzero(channels == self.tagger_di_clock)
        clock_click_inds = result[0].tolist()

        previous_sample_end_ind = None
        sample_end_ind = None

        # Counts will be a list of lists - the first dimension will divide
        # samples and the second will divide gatings within samples
        return_counts = []

        for clock_click_ind in clock_click_inds:

            # Clock clicks end samples, so they should be included with the
            # sample itself
            sample_end_ind = clock_click_ind + 1

            if previous_sample_end_ind is None:
                sample_timestamps = self.leftover_timestamps
                sample_timestamps.extend(timestamps[0: sample_end_ind])
                sample_channels = self.leftover_channels
                sample_channels.extend(channels[0: sample_end_ind])
            else:
                sample_timestamps = timestamps[previous_sample_end_ind:
                    sample_end_ind]
                sample_channels = channels[previous_sample_end_ind:
                    sample_end_ind]
                
            # Make sure we've got arrays or else comparison won't produce
            # the boolean array we're looking for when we find gate clicks
            sample_timestamps = numpy.array(sample_timestamps)
            sample_channels = numpy.array(sample_channels)
            
            sample_counts = []
            
            # Loop through the APDs
            for apd_index in self.stream_apd_indices:
                
                apd_channel = self.tagger_di_apd[apd_index]
                gate_open_channel = self.tagger_di_gate[apd_index]
                gate_close_channel = -gate_open_channel
            
                # Find gate open clicks
                result = numpy.nonzero(sample_channels == gate_open_channel)
                gate_open_click_inds = result[0].tolist()
    
                # Find gate close clicks
                # Gate close channel is negative of gate open channel,
                # signifying the falling edge
                result = numpy.nonzero(sample_channels == gate_close_channel)
                gate_close_click_inds = result[0].tolist()
    
                # The number of APD clicks is simply the number of items in the
                # buffer between gate open and gate close clicks
                channel_counts = []
                
                for ind in range(len(gate_open_click_inds)):
                    gate_open_click_ind = gate_open_click_inds[ind]
                    gate_close_click_ind = gate_close_click_inds[ind]
                    gate_window = sample_channels[gate_open_click_ind:
                        gate_close_click_ind]
                    gate_window = gate_window.tolist()
                    gate_count = gate_window.count(apd_channel)
                    channel_counts.append(gate_count)
                    
                sample_counts.append(channel_counts)

            return_counts.append(sample_counts)
            previous_sample_end_ind = sample_end_ind
        
        if sample_end_ind is None:
            # No samples were clocked - add everything to leftovers
            self.leftover_timestamps.extend(timestamps.tolist())
            self.leftover_channels.extend(channels.tolist())
        else:
            # Reset leftovers from the last sample clock
            self.leftover_timestamps = timestamps[sample_end_ind:].tolist()
            self.leftover_channels = channels[sample_end_ind:].tolist()

        return return_counts
    
    def stop_tag_stream_internal(self):
        if self.stream is not None:
            self.stream.stop()
        self.reset_tag_stream_state()
    
    def reset_tag_stream_state(self):
        self.stream = None
        self.stream_apd_indices = []
        self.stream_channels = []
        self.leftover_timestamps = []
        self.leftover_channels = []

    @setting(0, returns='*s')
    def get_channel_mapping(self, c):
        """As a regexp, the order is:
        [+APD, *[gate open, gate close], ?clock]
        Whether certain channels will be present/how many channels of a given
        type will be present is based on the channels passed to
        start_tag_stream.
        """
        
        return [self.channel_mapping[chan] for chan in self.stream_channels]

    @setting(1, apd_indices='*i', gate_indices='*i', clock='b')
    def start_tag_stream(self, c, apd_indices, gate_indices=None, clock=True):
        """Expose a raw tag stream which can be read with read_tag_stream and
        closed with stop_tag_stream.
        """
        
        # Make sure the existing stream is stopped and we have fresh state
        if self.stream is not None:
            logging.warning('New stream started before existing stream was ' \
                            'stopped. Stopping existing stream.')
            self.stop_tag_stream_internal()
        else:
            self.reset_tag_stream_state()
        
        channels = []
        for ind in apd_indices:
            channels.append(self.tagger_di_apd[ind])
        # If gate_indices is unspecified, add gates for all the 
        # passed APDs by default
        if gate_indices is None:
            gate_indices = apd_indices
        for ind in gate_indices:
            gate_channel = self.tagger_di_gate[ind]
            channels.append(gate_channel)  # rising edge
            channels.append(-gate_channel)  # falling edge
        if clock:
            channels.append(self.tagger_di_clock)
        # Store in state before de-duplication to preserve order
        self.stream_channels = channels
        # De-duplicate the channels list
        channels = list(set(channels))
        # Hardware-limited max buffer is a million total samples
        buffer_size = int(10**6 / len(channels))  
        self.stream = TimeTagger.TimeTagStream(self.tagger,
                                               buffer_size, channels)
        # When you set up a measurement, it will not start recording data
        # immediately. It takes some time for the tagger to configure the fpga,
        # etc. The sync call waits until this process is complete. 
        self.tagger.sync()
        self.stream_apd_indices = apd_indices
        
    @setting(2)
    def stop_tag_stream(self, c):
        """Closes the stream started with start_tag_stream. Resets
        leftovers.
        """
        self.stop_tag_stream_internal()

    @setting(3, returns='*s*s')
    def read_tag_stream(self, c):
        """Read the stream started with start_tag_stream. Returns two lists,
        each as long as the number of counts that have occurred since the
        buffer was refreshed. First list is timestamps in ps, second is apd
        indices.
        """
        if self.stream is None:
            logging.error('read_tag_stream attempted while stream is None.')
            return
        timestamps, channels = self.read_raw_stream()
        # Convert timestamps to strings since labrad does not support int64s
        # It must be converted to int64s back on the client
        timestamps = timestamps.astype(str).tolist()
        # Map channels to semantic channels
        semantic_channels = [self.channel_mapping[chan] for chan in channels]
        return timestamps, semantic_channels

    @setting(4, num_to_read='i', returns='*3w')
    def read_counter_complete(self, c, num_to_read=None):
        return self.read_counter_setting_internal(num_to_read)

    @setting(5, num_to_read='i', returns='*w')
    def read_counter_simple(self, c, num_to_read=None):
        
        complete_counts = self.read_counter_setting_internal(num_to_read)
        
        # To combine APDs we assume all the APDs have the same gate
        gate_channels = list(self.tagger_di_gate.values())
        first_gate_channel = gate_channels[0]
        if not all(val == first_gate_channel for val in gate_channels):
            logging.critical('Combined counts from APDs with ' \
                             'different gates.')
        
        # Just find the sum of each sample in complete_counts
        return_counts = [numpy.sum(sample, dtype=int) for sample
                         in complete_counts]
            
        return return_counts

    @setting(6, num_to_read='i', returns='*2w')
    def read_counter_separate_gates(self, c, num_to_read=None):
        
        complete_counts = self.read_counter_setting_internal(num_to_read)
        
        # To combine APDs we assume all the APDs have the same gate
        gate_channels = list(self.tagger_di_gate.values())
        first_gate_channel = gate_channels[0]
        if not all(val == first_gate_channel for val in gate_channels):
            logging.critical('Combined counts from APDs with ' \
                             'different gates.')
        
        # Add the APD counts as vectors for each sample in complete_counts
        return_counts = [numpy.sum(sample, 0, dtype=int).tolist() for sample
                         in complete_counts]
            
        return return_counts

    @setting(7, num_to_read='i', returns='*2w')
    def read_counter_separate_apds(self, c, num_to_read=None):
        
        complete_counts = self.read_counter_setting_internal(num_to_read)
        
        # Just find the sum of the counts for each APD for each
        # sample in complete_counts
        return_counts = [[numpy.sum(apd_counts, dtype=int) for apd_counts
                          in sample] for sample in complete_counts]
            
        return return_counts

    @setting(8)
    def reset(self, c):
        self.stop_tag_stream_internal()

__server__ = ApdTagger()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
