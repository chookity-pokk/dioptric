# -*- coding: utf-8 -*-
"""
Output server for the Berkeley Nucleonics 835 microwave signal generator.

Created on Wed Apr 10 12:53:38 2019

@author: mccambria

### BEGIN NODE INFO
[info]
name = signal_generator_bnc835
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


class SignalGeneratorBnc835(LabradServer):
    name = 'signal_generator_bnc835'
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
        p.get('signal_generator_bnc835_visa_address')
        result = await p.send()
        return result['get']

    def on_get_config(self, visa_address):
        resource_manager = visa.ResourceManager()
        self.sig_gen = resource_manager.open_resource(visa_address)
        logging.debug(self.sig_gen)
        # Note that this instrument works with pyvisa's default
        # termination assumptions
        self.reset(None)
        logging.debug('init complete')

    @setting(0)
    def uwave_on(self, c):
        """Turn on the signal. This is like opening an internal gate on
        the signal generator.
        """

        self.sig_gen.write('OUTP 1')

    @setting(1)
    def uwave_off(self, c):
        """Turn off the signal. This is like closing an internal gate on
        the signal generator.
        """

        self.sig_gen.write('OUTP 0')

    @setting(2, freq='v[]')
    def set_freq(self, c, freq):
        """Set the frequency of the signal.

        Params
            freq: float
                The frequency of the signal in GHz
        """

        self.sig_gen.write('FREQ:MODE FIX')
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

        self.sig_gen.write('POW:MODE FIX')
        # Determine how many decimal places we need
        precision = len(str(amp).split('.')[1])
        self.sig_gen.write('POW {0:.{1}f}DBM'.format(amp, precision))

    @setting(4, freqs='*v[]')
    def load_freq_list(self, c, freqs):
        # Configure the list itself
        freqs_hz_str = ', '.join([str(int(freq * 10**9)) for freq in freqs])
        self.sig_gen.write('LIST:FREQ {}'.format(freqs_hz_str))
        
        # Set the rising edge of an external trigger source to advance the
        # frequency to the next point in the sweep
        self.sig_gen.write('TRIG:TYPE POIN')
        self.sig_gen.write('TRIG:SOUR EXT')
        self.sig_gen.write('INIT:CONT 1')
        
        # Set the mode last as it assumes everything else
        self.sig_gen.write('FREQ:MODE LIST')

    @setting(5, start_freq='v[]', end_freq='v[]', num_steps='i')
    def load_freq_sweep(self, c, start_freq, end_freq, num_steps):
        
        # Configure the sweep itself
        precision = len(str(start_freq).split('.')[1])
        self.sig_gen.write('FREQ:STAR {0:.{1}f}GHZ'.format(start_freq, precision))
        precision = len(str(end_freq).split('.')[1])
        self.sig_gen.write('FREQ:STOP {0:.{1}f}GHZ'.format(end_freq, precision))
        self.sig_gen.write('SWE:POIN {}'.format(num_steps))
        self.sig_gen.write('SWE:SPAC LIN')
        
        # Set the rising edge of an external trigger source to advance the
        # frequency to the next point in the sweep
        self.sig_gen.write('TRIG:TYPE POIN')
        self.sig_gen.write('TRIG:SOUR EXT')
        self.sig_gen.write('INIT:CONT 1')
        
        # Set the mode last as it assumes everything else
        self.sig_gen.write('FREQ:MODE SWE')

    @setting(6)
    def reset(self, c):
        self.sig_gen.write('*RST')
        self.uwave_off(c)
        # Default to a continuous wave at 2.87 GHz and 0.0 dBm
        self.set_freq(c, 2.87)
        self.set_amp(c, 0.0)


__server__ = SignalGeneratorBnc835()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
