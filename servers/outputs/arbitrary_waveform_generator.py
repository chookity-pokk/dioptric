# -*- coding: utf-8 -*-
"""
Output server for the arbitrary waveform generator.

Created on Wed Apr 10 12:53:38 2019

@author: mccambria

### BEGIN NODE INFO
[info]
name = arbitrary_waveform_generator
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
import logging


class ArbitraryWaveformGenerator(LabradServer):
    name = 'arbitrary_waveform_generator'
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
        p.get('arb_wave_gen_visa_address')
        result = await p.send()
        return result['get']

    def on_get_config(self, config):
        resource_manager = visa.ResourceManager()
        self.wave_gen = resource_manager.open_resource(config)
        self.reset(None)
        logging.debug('init complete')

    @setting(0, i_voltages='*v[]', q_voltages='*v[]')
    def load_iq_waveform(self, c, i_voltages, q_voltages):
        """Loads the passed I and Q voltages for the IQ modulation of an
        external source. Triggered off the rising edge of an external
        trigger input.
        """

        # Clear the memory so we can load waveforms with existing names
        self.wave_gen.write('SOUR1:DATA:VOL:CLE')
        self.wave_gen.write('SOUR2:DATA:VOL:CLE')

        # Load the set of voltages to trigger through as arbitrary waveforms
        # if i_voltages = [1.1, 2.2, 3.3] then i_voltages_str = '1.1, 2.2, 3.3'
        i_voltages_str = ', '.join([str(float(el)) for el in i_voltages])
        self.wave_gen.write('SOUR1:DATA:ARB i_voltages, {}'.format(i_voltages_str))
        q_voltages_str = ', '.join([str(float(el)) for el in q_voltages])
        self.wave_gen.write('SOUR2:DATA:ARB q_voltages, {}'.format(q_voltages_str))

        # Set both channels to zero
        self.wave_gen.write('SOUR1:FUNC DC')
        self.wave_gen.write('SOUR1:VOLT:OFFS 0.0')
        self.wave_gen.write('OUTP1 ON')
        self.wave_gen.write('SOUR2:FUNC DC')
        self.wave_gen.write('SOUR2:VOLT:OFFS 0.0')
        self.wave_gen.write('OUTP2 ON')

        # Set to arbitrary mode
        self.wave_gen.write('SOUR1:FUNC ARB')
        self.wave_gen.write('SOUR2:FUNC ARB')

        # Load the waveforms we just set up
        self.wave_gen.write('SOUR1:FUNC:ARB i_voltages')
        self.wave_gen.write('SOUR2:FUNC:ARB q_voltages')

        # Set the amplitude to the full 2.0 V range
        self.wave_gen.write('SOUR1:FUNC:ARB:PTP 2.0')
        self.wave_gen.write('SOUR2:FUNC:ARB:PTP 2.0')

        # Turn off the filter so we can use an external trigger
        self.wave_gen.write('SOUR1:FUNC:ARB:FILT OFF')
        self.wave_gen.write('SOUR2:FUNC:ARB:FILT OFF')

        # Set the trigger to the rising edge of an external source
        self.wave_gen.write('TRIG:SOUR EXT')
        self.wave_gen.write('TRIG:SLOP POS')

        # Advance through waveform points based on the trigger
        self.wave_gen.write('SOUR1:FUNC:ARB:ADV TRIG')
        self.wave_gen.write('SOUR2:FUNC:ARB:ADV TRIG')

        # Be sure the waveforms are set to the beginning
        self.wave_gen.write('FUNC:ARB:SYNC')

    @setting(4)
    def test_sin(self, c):
        for chan in [1, 2]:
            source_name = 'SOUR{}:'.format(chan)
            self.wave_gen.write('{}FUNC SIN'.format(source_name))
            self.wave_gen.write('{}FREQ 10000'.format(source_name))
            self.wave_gen.write('{}VOLT:HIGH +2.0'.format(source_name))
            self.wave_gen.write('{}VOLT:LOW 0.0'.format(source_name))
        self.wave_gen.write('OUTP1 ON')
        self.wave_gen.write('SOUR2:PHAS 90')
        self.wave_gen.write('OUTP2 ON')

    @setting(5)
    def wave_off(self, c):
        self.wave_gen.write('OUTP1 OFF')
        self.wave_gen.write('OUTP2 OFF')

    @setting(6)
    def reset(self, c):
        self.wave_off(None)


__server__ = ArbitraryWaveformGenerator()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
