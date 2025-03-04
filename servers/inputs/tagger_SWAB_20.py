# -*- coding: utf-8 -*-
"""
Input server for APDs running into the Time Tagger.
Created on Wed Apr 24 22:07:25 2019
@author: mccambria
### BEGIN NODE INFO
[info]
name = tagger_SWAB_20
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
import numpy as np
import logging
import re
import socket
import servers.inputs.interfaces.tagger as tagger
from servers.inputs.interfaces.tagger import Tagger


class TaggerSwab20(Tagger, LabradServer):
    name = "tagger_SWAB_20"
    pc_name = socket.gethostname()

    def initServer(self):
        filename = (
            "E:/Shared drives/Kolkowitz Lab" " Group/nvdata/pc_{}/labrad_logging/{}.log"
        )
        filename = filename.format(self.pc_name, self.name)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%y-%m-%d_%H-%M-%S",
            filename=filename,
        )
        self.reset_tag_stream_state()
        config = ensureDeferred(self.get_config())
        config.addCallback(self.on_get_config)

    async def get_config(self):
        p = self.client.registry.packet()
        p.cd(["", "Config"])
        p.get("apd_indices")
        p.cd(["", "Config", "DeviceIDs"])
        p.get(f"{self.name}_serial")
        p.cd(["", "Config", "Wiring", "Tagger"])
        p.get("di_clock")
        p.get("di_apd_gate")
        p.dir()
        result = await p.send()
        return result

    def on_get_config(self, config):
        get_result = config["get"]
        self.config_apd_indices = get_result[0]
        tagger_serial = get_result[1]
        try:
            self.tagger = TimeTagger.createTimeTagger(tagger_serial)
        except Exception as e:
            logging.info(e)
        self.tagger.reset()
        # The APDs share a clock and gate
        self.tagger_di_clock = get_result[2]
        self.tagger_di_apd_gate = get_result[3]
        # Determine how many APDs we're supposed to set up
        apd_indices = []
        keys = config["dir"][1]
        for key in keys:
            if re.fullmatch(r"di_apd_[0-9]+", key):
                apd_indices.append(int(key.split("_")[2]))
        wiring = ensureDeferred(self.get_wiring(apd_indices))
        wiring.addCallback(self.on_get_wiring, apd_indices)

    async def get_wiring(self, apd_indices):
        p = self.client.registry.packet()
        for ind in apd_indices:
            p.get(f"di_apd_{ind}")
        result = await p.send()
        return result["get"]

    def on_get_wiring(self, wiring, apd_indices):
        self.tagger_di_apd = {}
        # Loop through the available APDs
        for loop_index in range(len(apd_indices)):
            apd_index = apd_indices[loop_index]
            di_apd = wiring[loop_index]
            self.tagger_di_apd[apd_index] = di_apd
        self.reset_tag_stream_state()  # Initialize state variables
        self.reset(None)
        logging.info("init complete")

    def read_raw_stream(self):
        if self.stream is None:
            logging.error("read_raw_stream attempted while stream is None.")
            return
        buffer = self.stream.getData()
        # Monitor overflows for both the Time Tagger's onboard buffer
        # and the software buffer that the stream feeds into on our PC
        num_hardware_overflows = self.tagger.getOverflowsAndClear()
        has_software_overflows = buffer.hasOverflows
        if (num_hardware_overflows > 0) or has_software_overflows:
            logging.info(f"Num hardware overflows: {num_hardware_overflows}")
            logging.info(f"Has software overflows: {has_software_overflows}")
        timestamps = buffer.getTimestamps()
        channels = buffer.getChannels()
        return timestamps, channels

    def read_counter_internal(self):
        if self.stream is None:
            logging.error("read_counter_internal attempted while stream is None.")
            return
        _, buffer_channels = self.read_raw_stream()

        # Do the hard work in the fast sub function
        apd_channels = [self.tagger_di_apd[val] for val in self.stream_apd_indices]
        return_counts, leftover_channels = tagger.tags_to_counts(
            buffer_channels,
            self.tagger_di_clock,
            self.tagger_di_apd_gate,
            apd_channels,
            self.leftover_channels,
        )
        # MCC: Bounce check
        # if 0 in np.array(return_counts):
        #     double_samples = [self.tagger_di_clock, self.tagger_di_clock]
        #     errors = [(buffer_times[i], buffer_times[i+1]) for i in range(len(buffer_channels)) if buffer_channels[i:i+2].tolist() == double_samples]
        #     logging.info(errors)
        self.leftover_channels = leftover_channels
        return return_counts

    def stop_tag_stream_internal(self):
        if self.stream is not None:
            self.stream.stop()
        self.reset_tag_stream_state()

    def reset_tag_stream_state(self):
        self.stream = None
        self.stream_apd_indices = []
        self.stream_channels = []
        self.leftover_channels = np.empty((0), dtype=np.int32)

    @setting(0, returns="*i")
    def get_channel_mapping(self, c):
        """As a regexp, the order is:
        [+APD, ?gate open, ?gate close, ?clock]
        Whether certain channels will be present/how many channels of a given
        type will be present is based on the channels passed to
        start_tag_stream.
        """
        return self.stream_channels

    @setting(1, apd_indices="*i", apd_gate="b", clock="b")
    def start_tag_stream(self, c, apd_indices=None, apd_gate=True, clock=True):
        """Expose a raw tag stream which can be read with read_tag_stream and
        closed with stop_tag_stream.
        """

        # Make sure the existing stream is stopped and we have fresh state
        if self.stream is not None:
            logging.warning(
                "New stream started before existing stream was "
                "stopped. Stopping existing stream."
            )
            self.stop_tag_stream_internal()
        else:
            self.reset_tag_stream_state()

        if apd_indices is None:
            apd_indices = self.config_apd_indices

        channels = []
        for ind in apd_indices:
            channels.append(self.tagger_di_apd[ind])
        if apd_gate:
            channels.append(self.tagger_di_apd_gate)
            channels.append(-self.tagger_di_apd_gate)
        if clock:
            channels.append(self.tagger_di_clock)
        # Store in state before de-duplication to preserve order
        self.stream_channels = channels
        # De-duplicate the channels list
        channels = list(set(channels))
        self.stream = TimeTagger.TimeTagStream(self.tagger, 10**8, channels)
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

    @setting(3)
    def clear_buffer(self, c):
        """Clear the hardware's internal buffer. Should be called before
        starting a pulse sequence."""
        buffer = self.stream.getData()
        # We also don't care about overflows here, so toss (but log) those
        num_hardware_overflows = self.tagger.getOverflowsAndClear()
        has_software_overflows = buffer.hasOverflows
        if (num_hardware_overflows > 0) or has_software_overflows:
            logging.info(f"Num hardware overflows: {num_hardware_overflows}")
            logging.info(f"Has software overflows: {has_software_overflows}")

    @setting(5)
    def reset(self, c):
        self.stop_tag_stream_internal()


__server__ = TaggerSwab20()

if __name__ == "__main__":
    from labrad import util

    util.runServer(__server__)
