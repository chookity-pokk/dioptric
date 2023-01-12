# -*- coding: utf-8 -*-
"""
Output server for the MadCityLabs piezo stage

Created on Mon Apr  8 19:50:12 2019

@author: mccambria

### BEGIN NODE INFO
[info]
name = piezo_stage_mcl_3d200ft_analog
version = 1.1
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
import nidaqmx
from nidaqmx.constants import AcquisitionType
import nidaqmx.stream_writers as stream_writers
import numpy
import logging
import socket


class PosXyzMcl3d200ftAnalog(LabradServer):
    name = "pos_xyz_MCL_3d200ft_analog"
    pc_name = socket.gethostname()

    def initServer(self):
        filename = ('C:/Users/student/Documents/labrad_logging/{}.log' )
        filename = filename.format(self.name)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%y-%m-%d_%H-%M-%S",
            filename=filename,
        )
        self.task = None
        self.sub_init_server_xyz()

    def sub_init_server_xyz(self):
        """Sub-routine to be called by xyz server"""
        config = ensureDeferred(self.get_config_xyz())
        logging.info('loaded config')
        config.addCallback(self.on_get_config_xyz)

    async def get_config_xyz(self):
        p = self.client.registry.packet()
        p.cd(["", "Config", "Wiring", "Daq"])
        p.get("ao_piezo_x")
        p.get("ao_piezo_y")
        p.get("ao_piezo_z")
        p.get("di_clock")
        result = await p.send()
        return result["get"]

    def on_get_config_xyz(self, config):
        self.daq_ao_piezo_x = config[0]
        self.daq_ao_piezo_y = config[1]
        self.daq_ao_piezo_z = config[2]
        self.daq_di_clock = config[3]
        # logging.debug(self.daq_di_clock)
        logging.info("Init complete")

    def stopServer(self):
        self.close_task_internal()

# %%
        
    def load_stream_writer_xy(self, c, task_name, voltages, period, 
                              continuous=False):

        # Close the existing task if there is one
        if self.task is not None:
            self.close_task_internal()

        # Write the initial voltages and stream the rest
        num_voltages = voltages.shape[1]
        self.write_xy(c, voltages[0, 0], voltages[1, 0])
        stream_voltages = voltages[:, 1:num_voltages]
        stream_voltages = numpy.ascontiguousarray(stream_voltages)
        num_stream_voltages = num_voltages - 1
        # Create a new task
        task = nidaqmx.Task(task_name)
        self.task = task

        # Set up the output channels
        task.ao_channels.add_ao_voltage_chan(
            self.daq_ao_piezo_x, min_val=0.0, max_val=10.0
        )
        task.ao_channels.add_ao_voltage_chan(
            self.daq_ao_piezo_y, min_val=0.0, max_val=10.0
        )

        # Set up the output stream
        output_stream = nidaqmx.task.OutStream(task)
        writer = stream_writers.AnalogMultiChannelWriter(output_stream)

        # Configure the sample to advance on the rising edge of the PFI input.
        # The frequency specified is just the max expected rate in this case.
        # We'll stop once we've run all the samples.
        freq = float(1 / (period * (10 ** -9)))  # freq in seconds as a float
        if continuous:
            task.timing.cfg_samp_clk_timing(
                freq, source=self.daq_di_clock, 
                samps_per_chan=num_stream_voltages,
                sample_mode=AcquisitionType.CONTINUOUS,
            )
        else:
            task.timing.cfg_samp_clk_timing(
                freq, source=self.daq_di_clock, 
                samps_per_chan=num_stream_voltages
            )

        writer.write_many_sample(stream_voltages)

        # Close the task once we've written all the samples
        task.register_done_event(self.close_task_internal)

        task.start()
        
    def load_stream_writer_z(self, c, task_name, voltages, period, 
                              continuous=False):

        # Close the existing task if there is one
        if self.task is not None:
            self.close_task_internal()

        # Make sure the voltages are an array
        voltages = numpy.array(voltages)
        
        # Write the initial voltages and stream the rest
        num_voltages = len(voltages)
        self.write_z(c, voltages[0])
        stream_voltages = voltages[1:num_voltages]
        stream_voltages = numpy.ascontiguousarray(stream_voltages)
        stream_voltages = numpy.array([stream_voltages])
        
        num_stream_voltages = num_voltages - 1
        
        # Create a new task
        task = nidaqmx.Task(task_name)
        self.task = task

        # Set up the output channels
        task.ao_channels.add_ao_voltage_chan(
            self.daq_ao_piezo_z, min_val=0.0, max_val=10.0
        )
        
        # Set up the output stream
        output_stream = nidaqmx.task.OutStream(task)
        writer = stream_writers.AnalogMultiChannelWriter(output_stream)

        # Configure the sample to advance on the rising edge of the PFI input.
        # The frequency specified is just the max expected rate in this case.
        # We'll stop once we've run all the samples.
        freq = float(1 / (period * (10 ** -9)))  # freq in seconds as a float
        if continuous:
            task.timing.cfg_samp_clk_timing(
                freq, source=self.daq_di_clock, 
                samps_per_chan=num_stream_voltages,
                sample_mode=AcquisitionType.CONTINUOUS,
            )
        else:
            task.timing.cfg_samp_clk_timing(
                freq, source=self.daq_di_clock, 
                samps_per_chan=num_stream_voltages
            )

        writer.write_many_sample(stream_voltages)

        # Close the task once we've written all the samples
        task.register_done_event(self.close_task_internal)

        task.start()


    def load_stream_writer_xyz(self, c, task_name, voltages, period):

        # Close the existing task if there is one
        if self.task is not None:
            self.close_task_internal()

        # Write the initial voltages and stream the rest
        num_voltages = voltages.shape[1]
        self.write_xy(c, voltages[0, 0], voltages[1, 0])
        self.write_z(c, voltages[2, 0])
        stream_voltages = voltages[:, 1:num_voltages]
        stream_voltages = numpy.ascontiguousarray(stream_voltages)
        num_stream_voltages = num_voltages - 1

        # Create a new task
        task = nidaqmx.Task(task_name)
        self.task = task

        # Set up the output channels
        task.ao_channels.add_ao_voltage_chan(
            self.daq_ao_piezo_x, min_val=0.0, max_val=10.0
        )
        task.ao_channels.add_ao_voltage_chan(
            self.daq_ao_piezo_y, min_val=0.0, max_val=10.0
        )
        task.ao_channels.add_ao_voltage_chan(
            self.daq_ao_piezo_z, min_val=0.0, max_val=10.0
        )

        # Set up the output stream
        output_stream = nidaqmx.task.OutStream(task)
        writer = stream_writers.AnalogMultiChannelWriter(output_stream)

        # Configure the sample to advance on the rising edge of the PFI input.
        # The frequency specified is just the max expected rate in this case.
        # We'll stop once we've run all the samples.
        freq = float(1 / (period * (10 ** -9)))  # freq in seconds as a float
        task.timing.cfg_samp_clk_timing(
            freq, source=self.daq_di_clock, samps_per_chan=num_stream_voltages
        )

        writer.write_many_sample(stream_voltages)

        # Close the task once we've written all the samples
        task.register_done_event(self.close_task_internal)

        task.start()
        
    def close_task_internal(self, task_handle=None, status=None, callback_data=None):
        task = self.task
        if task is not None:
            task.close()
            self.task = None
        return 0
# %%
    @setting(0, xVoltage="v[]", yVoltage="v[]")
    def write_xy(self, c, xVoltage, yVoltage):
        """Write the specified voltages to the galvo.

        Params
            xVoltage: float
                Voltage to write to the x channel
            yVoltage: float
                Voltage to write to the y channel
        """

        # Close the stream task if it exists
        # This can happen if we quit out early
        if self.task is not None:
            self.close_task_internal()

        with nidaqmx.Task() as task:
            # Set up the output channels
            task.ao_channels.add_ao_voltage_chan(
                self.daq_ao_piezo_x, min_val=0.0, max_val=10.0
            )
            task.ao_channels.add_ao_voltage_chan(
                self.daq_ao_piezo_y, min_val=0.0, max_val=10.0
            )
            task.write([xVoltage, yVoltage])

    @setting(1, returns="*v[]")
    def read_xy(self, c):
        """Return the current voltages on the x and y channels.

        Returns
            list(float)
                Current voltages on the x and y channels

        """
        with nidaqmx.Task() as task:
            # Set up the internal channels - to do: actual parsing...
            if self.daq_ao_piezo_x == "PXI1Slot3_2/AO0":
                chan_name = "PXI1Slot3_2/_ao0_vs_aognd"
            elif self.daq_ao_piezo_x == "PXI1Slot3_2/AO1":
                chan_name = "PXI1Slot3_2/_ao1_vs_aognd"
            elif self.daq_ao_piezo_x == "PXI1Slot3_2/AO2":
                chan_name = "PXI1Slot3_2/_ao2_vs_aognd"
            elif self.daq_ao_piezo_x == "PXI1Slot3_2/AO3":
                chan_name = "PXI1Slot3_2/_ao3_vs_aognd"
            task.ai_channels.add_ai_voltage_chan(chan_name, min_val=0.0, max_val=10.0)
            if self.daq_ao_piezo_y == "PXI1Slot3_2/AO0":
                chan_name = "PXI1Slot3_2/_ao0_vs_aognd"
            elif self.daq_ao_piezo_y == "PXI1Slot3_2/AO1":
                chan_name = "PXI1Slot3_2/_ao1_vs_aognd"
            elif self.daq_ao_piezo_y == "PXI1Slot3_2/AO2":
                chan_name = "PXI1Slot3_2/_ao2_vs_aognd"
            elif self.daq_ao_piezo_y == "PXI1Slot3_2/AO3":
                chan_name = "PXI1Slot3_2/_ao3_vs_aognd"
            task.ai_channels.add_ai_voltage_chan(chan_name, min_val=0.0, max_val=10.0)
            voltages = task.read()

        return voltages[0], voltages[1]

    @setting(
        2,
        x_center="v[]",
        y_center="v[]",
        x_range="v[]",
        y_range="v[]",
        num_steps="i",
        period="i",
        returns="*v[]*v[]",
    )
    def load_sweep_scan_xy(
        self, c, x_center, y_center, x_range, y_range, num_steps, period
    ):
        """Load a scan that will wind through the grid defined by the passed
        parameters. Samples are advanced by the clock. Currently x_range
        must equal y_range.

        Normal scan performed, starts in bottom right corner, and starts
        heading left

        Params
            x_center: float
                Center x voltage of the scan
            y_center: float
                Center y voltage of the scan
            x_range: float
                Full scan range in x
            y_range: float
                Full scan range in y
            num_steps: int
                Number of steps the break the ranges into
            period: int
                Expected period between clock signals in ns

        Returns
            list(float)
                The x voltages that make up the scan
            list(float)
                The y voltages that make up the scan
        """

        ######### Assumes x_range == y_range #########

        if x_range != y_range:
            raise ValueError("x_range must equal y_range for now")

        x_num_steps = num_steps
        y_num_steps = num_steps

        # Force the scan to have square pixels by only applying num_steps
        # to the shorter axis
        half_x_range = x_range / 2
        half_y_range = y_range / 2

        x_low = x_center - half_x_range
        x_high = x_center + half_x_range
        y_low = y_center - half_y_range
        y_high = y_center + half_y_range

        # Apply scale and offset to get the voltages we'll apply to the galvo
        # Note that the polar/azimuthal angles, not the actual x/y positions
        # are linear in these voltages. For a small range, however, we don't
        # really care.
        x_voltages_1d = numpy.linspace(x_low, x_high, num_steps)
        y_voltages_1d = numpy.linspace(y_low, y_high, num_steps)

        ######### Works for any x_range, y_range #########

        # Winding cartesian product
        # The x values are repeated and the y values are mirrored and tiled
        # The comments below shows what happens for [1, 2, 3], [4, 5, 6]

        # [1, 2, 3] => [1, 2, 3, 3, 2, 1]
        x_inter = numpy.concatenate((x_voltages_1d, numpy.flipud(x_voltages_1d)))
        # [1, 2, 3, 3, 2, 1] => [1, 2, 3, 3, 2, 1, 1, 2, 3]
        if y_num_steps % 2 == 0:  # Even x size
            x_voltages = numpy.tile(x_inter, int(y_num_steps / 2))
        else:  # Odd x size
            x_voltages = numpy.tile(x_inter, int(numpy.floor(y_num_steps / 2)))
            x_voltages = numpy.concatenate((x_voltages, x_voltages_1d))

        # [4, 5, 6] => [4, 4, 4, 5, 5, 5, 6, 6, 6]
        y_voltages = numpy.repeat(y_voltages_1d, x_num_steps)

        voltages = numpy.vstack((x_voltages, y_voltages))

        self.load_stream_writer_xy(c, "PiezoMCL-load_sweep_scan_xy", voltages, period)

        return x_voltages_1d, y_voltages_1d

    @setting(
        3,
        x_center="v[]",
        y_center="v[]",
        xy_range="v[]",
        num_steps="i",
        period="i",
        returns="*v[]*v[]",
    )
    def load_cross_scan_xy(self, c, x_center, y_center, xy_range, num_steps, period):
        """Load a scan that will first step through xy_range in x keeping y
        constant at its center, then step through xy_range in y keeping x
        constant at its center.

        Params
            x_center: float
                Center x voltage of the scan
            y_center: float
                Center y voltage of the scan
            xy_range: float
                Full scan range in x/y
            num_steps: int
                Number of steps the break the x/y range into
            period: int
                Expected period between clock signals in ns

        Returns
            list(float)
                The x voltages that make up the scan
            list(float)
                The y voltages that make up the scan
        """

        half_xy_range = xy_range / 2

        x_low = x_center - half_xy_range
        x_high = x_center + half_xy_range
        y_low = y_center - half_xy_range
        y_high = y_center + half_xy_range

        x_voltages_1d = numpy.linspace(x_low, x_high, num_steps)
        y_voltages_1d = numpy.linspace(y_low, y_high, num_steps)

        x_voltages = numpy.concatenate([x_voltages_1d, numpy.full(num_steps, x_center)])
        y_voltages = numpy.concatenate([numpy.full(num_steps, y_center), y_voltages_1d])

        voltages = numpy.vstack((x_voltages, y_voltages))

        self.load_stream_writer_xy(c, "PiezoMCL-load_cross_scan_xy", voltages, period)

        return x_voltages_1d, y_voltages_1d

    @setting(
        7,
        radius="v[]",
        num_steps="i",
        period="i",
        returns="*v[]*v[]",
    )
    def load_circle_scan_xy(self, c, radius, num_steps, period):
        """Load a circle scan centered about 0,0. Useful for testing cat's eye
        stationary point. For this reason, the scan runs continuously, not
        just until it makes it through all the samples once. 

        Params
            radius: float
                Radius of the circle in V
            num_steps: int
                Number of steps the break the x/y range into
            period: int
                Expected period between clock signals in ns

        Returns
            list(float)
                The x voltages that make up the scan
            list(float)
                The y voltages that make up the scan
        """
        
        angles = numpy.linspace(0, 2*numpy.pi, num_steps)

        x_voltages = radius * numpy.sin(angles)

        y_voltages = radius * numpy.cos(angles)
        # y_voltages = numpy.zeros(len(angles))

        voltages = numpy.vstack((x_voltages, y_voltages))

        self.load_stream_writer_xy(c, "PiezoMCL-load_circle_scan_xy", voltages, 
                                   period, True)

        return x_voltages, y_voltages

    @setting(
        4,
        x_center="v[]",
        y_center="v[]",
        scan_range="v[]",
        num_steps="i",
        period="i",
        returns="*v[]",
    )
    def load_scan_x(self, c, x_center, y_center, scan_range, num_steps, period):
        """Load a scan that will step through scan_range in x keeping y
        constant at its center.

        Params
            x_center: float
                Center x voltage of the scan
            y_center: float
                Center y voltage of the scan
            scan_range: float
                Full scan range in x/y
            num_steps: int
                Number of steps the break the x/y range into
            period: int
                Expected period between clock signals in ns

        Returns
            list(float)
                The x voltages that make up the scan
        """

        half_scan_range = scan_range / 2

        x_low = x_center - half_scan_range
        x_high = x_center + half_scan_range

        x_voltages = numpy.linspace(x_low, x_high, num_steps)
        y_voltages = numpy.full(num_steps, y_center)

        voltages = numpy.vstack((x_voltages, y_voltages))

        self.load_stream_writer_xy(c, "PiezoMCL-load_scan_x", voltages, period)

        return x_voltages

    @setting(
        5,
        x_center="v[]",
        y_center="v[]",
        scan_range="v[]",
        num_steps="i",
        period="i",
        returns="*v[]",
    )
    def load_scan_y(self, c, x_center, y_center, scan_range, num_steps, period):
        """Load a scan that will step through scan_range in y keeping x
        constant at its center.

        Params
            x_center: float
                Center x voltage of the scan
            y_center: float
                Center y voltage of the scan
            scan_range: float
                Full scan range in x/y
            num_steps: int
                Number of steps the break the x/y range into
            period: int
                Expected period between clock signals in ns

        Returns
            list(float)
                The y voltages that make up the scan
        """

        half_scan_range = scan_range / 2

        y_low = y_center - half_scan_range
        y_high = y_center + half_scan_range

        x_voltages = numpy.full(num_steps, x_center)
        y_voltages = numpy.linspace(y_low, y_high, num_steps)

        voltages = numpy.vstack((x_voltages, y_voltages))

        self.load_stream_writer_xy(c, "PiezoMCL-load_scan_y", voltages, period)

        return y_voltages

    @setting(6, x_points="*v[]", y_points="*v[]", period="i")
    def load_arb_scan_xy(self, c, x_points, y_points, period):
        """Load a scan that goes between points. E.i., starts at [1,1] and
        then on a clock pulse, moves to [2,1]. Can work for arbitrarily large
        number of points 
        (previously load_two_point_xy_scan)

        Params
            x_points: list(float)
                X values correspnding to positions in x
                y_points: list(float)
                Y values correspnding to positions in y
            period: int
                Expected period between clock signals in ns

        """

        voltages = numpy.vstack((x_points, y_points))

        self.load_stream_writer_xy(c, "PiezoMCL-load_arb_scan_xy", voltages, period)

        return
 
# %%
    @setting(22, voltage="v[]")
    def write_z(self, c, voltage):
        """Write the specified voltage to the piezo"""

        # Close the stream task if it exists
        # This can happen if we quit out early
        if self.task is not None:
            self.close_task_internal()

        with nidaqmx.Task() as task:
            # Set up the output channels
            task.ao_channels.add_ao_voltage_chan(
                self.daq_ao_piezo_z, min_val=0.0, max_val=10.0
            )
            task.write(voltage)
        
        
    @setting(21, returns="v[]")
    def read_z(self, c):
        """Return the current voltages on the piezo's DAQ channel"""
        with nidaqmx.Task() as task:
            # Set up the internal channels - to do: actual parsing...                
            if self.daq_ao_piezo_z == "PXI1Slot3_2/AO0":
                chan_name = "PXI1Slot3_2/_ao0_vs_aognd"
            elif self.daq_ao_piezo_z == "PXI1Slot3_2/AO1":
                chan_name = "PXI1Slot3_2/_ao1_vs_aognd"
            elif self.daq_ao_piezo_z == "PXI1Slot3_2/AO2":
                chan_name = "PXI1Slot3_2/_ao2_vs_aognd"
            elif self.daq_ao_piezo_z == "PXI1Slot3_2/AO3":
                chan_name = "PXI1Slot3_2/_ao3_vs_aognd"
            task.ai_channels.add_ai_voltage_chan(chan_name, min_val=0.0, max_val=10.0)
            voltage = task.read()
        return voltage
    

    @setting(
        23, center="v[]", scan_range="v[]", num_steps="i", period="i", returns="*v[]"
    )
    def load_scan_z(self, c, center, scan_range, num_steps, period):
        """Load a linear sweep with the DAQ"""

        half_scan_range = scan_range / 2
        low = center - half_scan_range
        high = center + half_scan_range
        voltages = numpy.linspace(low, high, num_steps)
        self.load_stream_writer_z(c, "PiezoMCL-load_scan_z", voltages, period)
        return voltages

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    @setting(24, z_voltages="*v[]", period="i", returns="*v[]")
    def load_arb_scan_z(self, c, z_voltages, period):
        """Load a list of voltages with the DAQ"""

        self.load_stream_writer_z(
            c, "PiezoMCL-load_arb_scan_z", numpy.array(z_voltages), period
        )
        return z_voltages
    
    
# %%

    @setting(11, x_points="*v[]", y_points="*v[]", z_points="*v[]", period="i")
    def load_arb_scan_xyz(self, c, x_points, y_points, z_points, period):
        """
        Load a scan around a seuqence of arbitrary xyz points 

        Params
            x_points: list(float)
                X values correspnding to positions in x
            y_points: list(float)
                Y values correspnding to positions in y
            z_points: list(float)
                Z values correspnding to positions in z
            period: int
                Expected period between clock signals in ns

        """

        voltages = numpy.vstack((x_points, y_points, z_points))

        self.load_stream_writer_xyz(
            c, "PiezoMCL-load_arb_scan_xyz", voltages, period
        )

        return
    
    @setting(
        12,
        x_center="v[]",
        z_center="v[]",
        x_range="v[]",
        z_range="v[]",
        num_steps="i",
        period="i",
        returns="*v[]*v[]",
    )
    def load_sweep_scan_xz(
        self, c, x_center, y_center, z_center, x_range, z_range, num_steps, period
    ):
        """Load a scan that will wind through the grid defined by the passed
        parameters. Samples are advanced by the clock.

        Normal scan performed, starts in bottom right corner, and starts
        heading left
        

        Params
            x_center: float
                Center x voltage of the scan
            y_center: float
                Center position y voltage (won't change in y)
            z_center: float
                Center z voltage of the scan
            x_range: float
                Full scan range in x
            z_range: float
                Full scan range in z
            num_steps: int
                Number of steps the break the ranges into
            period: int
                Expected period between clock signals in ns

        Returns
            list(float)
                The x voltages that make up the scan
            list(float)
                The z voltages that make up the scan
        """

        # Must use same number of steps right now
        x_num_steps = num_steps
        z_num_steps = num_steps

        # Force the scan to have square pixels by only applying num_steps
        # to the shorter axis
        half_x_range = x_range / 2
        half_z_range = z_range / 2

        x_low = x_center - half_x_range
        x_high = x_center + half_x_range
        z_low = z_center - half_z_range
        z_high = z_center + half_z_range

        # Apply scale and offset to get the voltages we'll apply.
        x_voltages_1d = numpy.linspace(x_low, x_high, num_steps)
        z_voltages_1d = numpy.linspace(z_low, z_high, num_steps)
    

        ######### Works for any x_range, y_range #########

        # Winding cartesian product
        # The x values are repeated and the z values are mirrored and tiled
        # The comments below shows what happens for [1, 2, 3], [4, 5, 6]

        # [1, 2, 3] => [1, 2, 3, 3, 2, 1]
        x_inter = numpy.concatenate((x_voltages_1d, numpy.flipud(x_voltages_1d)))
        # [1, 2, 3, 3, 2, 1] => [1, 2, 3, 3, 2, 1, 1, 2, 3]
        if z_num_steps % 2 == 0:  # Even x size
            x_voltages = numpy.tile(x_inter, int(z_num_steps / 2))
        else:  # Odd x size
            x_voltages = numpy.tile(x_inter, int(numpy.floor(z_num_steps / 2)))
            x_voltages = numpy.concatenate((x_voltages, x_voltages_1d))

        # [4, 5, 6] => [4, 4, 4, 5, 5, 5, 6, 6, 6]
        z_voltages = numpy.repeat(z_voltages_1d, x_num_steps)
        
        y_voltages = numpy.empty(len(z_voltages))
        y_voltages.fill(y_center)

        voltages = numpy.vstack((x_voltages,y_voltages, z_voltages))

        self.load_stream_writer_xyz(c, "PiezoMCL-load_sweep_scan_xz", voltages, period)

        return x_voltages_1d, z_voltages_1d

        
# %%

__server__ = PosXyzMcl3d200ftAnalog()

if __name__ == "__main__":
    from labrad import util

    util.runServer(__server__)
