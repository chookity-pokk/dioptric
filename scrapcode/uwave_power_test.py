# -*- coding: utf-8 -*-
"""
Test script for setting microwave power/frequency

Created on Wed May  1 13:52:35 2019

@author: mccambria
"""

import labrad
import numpy
import matplotlib.pyplot as plt

def check_power():
    with labrad.connect() as cxn:
        cxn.signal_generator_tsg4104a.set_freq(2.87)
        cxn.signal_generator_tsg4104a.set_amp(-20.0)
        cxn.signal_generator_tsg4104a.uwave_on()
        # 4 is the tektronix sig gen, 
        cxn.pulse_streamer.constant([3], 0.0, 0.0)

#        while True:
#            power = input('Enter a power or nothing to stop: ')
#
#            if power != '':
#                cxn.signal_generator_tsg4104a.set_amp(power)
#            else:
#                break
        input('Press enter to stop...')

        cxn.pulse_streamer.constant([], 0.0, 0.0)
        cxn.signal_generator_tsg4104a.uwave_off()

    # Setting / Measured / Accounting for attenuator / Switch loss
    # At 2.87 GHz after switch, with -20 dBm attenuator:
        # 0.0 / -24.4 / -4.6 / 4.6
        # 1.0 / -23.5 / -3.5 / 4.5
        # 2.0 / -22.5 / -2.5 / 4.5
        # 3.0 / -21.5 / -1.5 / 4.5
        # 4.0 / -20.5 / -0.5 / 4.5
        # 5.0 / -19.4 /  0.6 / 4.4
        # 10.5/ -14.2 /  5.8 / 4.7
        # 11.0/ -13.8 /  6.2 / 4.8
        # 11.5/ -13.3 /  6.7 / 4.8

def check_freq():
    with labrad.connect() as cxn:
        cxn.microwave_signal_generator.set_freq(2.87)
        cxn.microwave_signal_generator.set_amp(11.0)
        cxn.microwave_signal_generator.uwave_on()
        cxn.pulse_streamer.constant(2)

#        freqs = numpy.linspace(2.72, 3.02, 31)
#
#        for freq in freqs:
#            cxn.microwave_signal_generator.set_freq(freq)
#            print(freq)
#            if input('Press enter to continue...') == 'stop':
#                break

        while True:
            freq = input('Enter a frequency or nothing to stop: ')

            if freq != '':
                cxn.microwave_signal_generator.set_freq(freq)
            else:
                break

        cxn.pulse_streamer.constant(0)
        cxn.microwave_signal_generator.uwave_off()

    # Freq setting / Measured power / Power accounting for attenuator
    # At 5.0 dBm after switch, with -20 dBm attenuator:
        # 2.71 / -19.4 /  0.6
        # 2.73 / -19.3 /  0.7
        # 2.75 / -19.2 /  0.8
        # 2.77 / -19.9 /  0.1
        # 2.79 / -19.2 /  0.8
        # 2.81 / -19.6 /  0.4
        # 2.83 / -20.3 / -0.3
        # 2.85 / -19.8 /  0.2
        # 2.87 / -19.7 /  0.3
        # 2.89 / -19.3 /  0.7
        # 2.91 / -19.7 /  0.3
        # 2.93 / -19.8 /  0.2
        # 2.95 / -19.9 /  0.1
        # 2.97 / -20.2 / -0.3
        # 2.99 / -20.2 / -0.2
        # 3.01 / -20.5 / -0.5

    # Freq setting / Measured power / Power accounting for attenuator
    # At 10.5 dBm after switch, with -20 dBm attenuator:
        # 2.75 / -13.7 / 6.3
        # 2.79 / -14.4 / 5.6
        # 2.87 / -14.2 / 5.8
        # 3.01 / -15.1 / 4.9

    # Freq setting / Measured power / Power accounting for attenuator
    # At 11.0 dBm after switch, with -20 dBm attenuator:
        # 2.75 / -13.2 / 6.8
        # 2.87 / -13.8 / 6.2

    # The amplifier should add 40 dBm. The amp can handle 7.0 dBm input so
    # we will run at 11.0 dBm max to account for the gate
    # With 40 dBm of attentuation in place and the amp on, the post-gate
    # input should match the output.

    # Freq setting / Measured power / Power accounting for attenuator
    # At 10.5 dBm after switch, with -20 dBm attenuator:
        # 2.75 / -13.7 / 6.3
        # 2.79 / -14.4 / 5.6
        # 2.87 / -14.2 / 5.8
        # 3.01 / -15.1 / 4.9

    # Measured attenuator performance, 2.87 GHz, 11.0 dBm into gate, amp on:
    # With all three (50 dB): -9.9 -> 49.8
    # measured -> actual attentuation
    # 1810MCLVAT-10W2: -0.1 -> 9.8
    # PE7005-20: 9.9 -> 19.8
    # 2082-6194-20: 10.3 -> 20.2

    # Calculating amplifier gain (46 dB nominally)
    # 2.87 GHz, 11.0 dBm into gate, 6.2 dBm into amp
    # 6.2 + gain - 49.8 = meas
    # meas + atten = gain
    # -9.6 + 43.6 = 34.0...

    # -30.0 attenuation, 2.87 GHz
    # set power / input power / measured power / calculated gain
    # set_power - gate_atten + amp_gain - atten = meas_power
    # amp_gain = meas_power - set_power + gate_atten + atten
    # set power / measured power
    # -10.0 / -0.2
    # -9.0 / 0.8
    # -8.0 / 1.8
    # -7.0 / 2.8
    # -6.0 / 3.7
    # -5.0 / 4.6
    # -4.0 / 5.4
    # -3.0 / 6.1
    # -2.0 / 6.8
    # -1.0 / 7.4
    # 0.0 / 8.0
    # 1.0 / 8.3
    # 2.0 / 8.7
    # 3.0 / 9.0
    # 4.0 / 9.3
    # 5.0 / 9.5
    # 6.0 / 9.7
    # 7.0 / 9.8
    # 8.0 / 9.9
    # 9.0 / 10.0
    # 10.0 / 10.0
    # 11.0 / 10.1

def plot_data():
    # input power vs output power
    step = 1.0
    in_powers = numpy.arange(-10.0, 11.0+step, step)
    out_powers = [-0.2, 0.8, 1.8, 2.8, 3.7, 4.6, 5.4, 6.1, 6.8, 7.4,
          8.0, 8.3, 8.7, 9.0, 9.3, 9.5, 9.7, 9.8, 9.9, 10.0, 10.0, 10.1]
    # amp_gain = meas_power - set_power + gate_atten + atten
    power_diffs = out_powers - in_powers
    gains = power_diffs + 4.5 + 30.0
    # fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    fig, axes_pack = plt.subplots(1, 2, figsize=(12, 6))
    ax = axes_pack[0]
    ax.plot(in_powers, out_powers) 
    ax.set_title('Measured Power Versus Set Power At 2.87 GHz')
    ax.set_xlabel('Set Power (dBm)')
    ax.set_ylabel('Measured Power (dBm)')
    ax = axes_pack[1]
    ax.plot(in_powers, gains)
    ax.set_title('Measured Amplifier Gain Versus Set Power At 2.87 GHz')
    ax.set_xlabel('Set Power (dBm)')
    ax.set_ylabel('Measured Amplifier Gain (dB)')
    fig.tight_layout()


if __name__ == '__main__':
     check_power()
#     check_freq()
#    plot_data()
    
    # Turn on the green
#    with labrad.connect() as cxn:
#        cxn.pulse_streamer.constant([3], 0.0, 0.0)
#        input('Press enter to stop...')
#        cxn.pulse_streamer.constant([], 0.0, 0.0)
        