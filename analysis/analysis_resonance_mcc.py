# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 10:42:07 2019

This script plots ESR data to a Gaussian fit. It guesses the frequencies of the
resonances, and uses those to curve fit to two gaussians.

It will not fit if it does not find one or two minimums.

To fix: fine tuning the width parameter. Scale the width parameter with the
frequency range

@author: gardill
"""
# %% Imports

import numpy
import json
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from numpy import exp

# %% Open the file with JSON


def fit_resonance(save_file_type):

    minFreqGuess = numpy.empty([2])

#    minFreqGuess[0] = 2.81
    minFreqGuess[0] = 2.93
    second_freq_guess = 'n'  # 'n' if none

#    folder_dir = 'E:/Shared drives/Kolkowitz Lab Group/nvdata/resonance/'
    folder_dir = 'E:/Shared drives/Kolkowitz Lab Group/nvdata/pulsed_resonance/branch_ramsey2/'
    file_name = '2019-07-12_09-33-07_johnson1.txt'
#    file_name = '2019-06-19_18-41-28_ayrton12.txt'
    open_file_name = '{}{}'.format(folder_dir, file_name)

    with open(open_file_name) as json_file:
        data = json.load(json_file)

        # Get information about the frequency
        freq_center = data["freq_center"]
        freq_range = data["freq_range"]
        num_steps = data["num_steps"]

        # Get the averaged, normalized counts from the ESR
        norm_avg_counts = numpy.array(data["norm_avg_sig"])
#        sig_counts = numpy.array(data['sig_counts'])
#        ref_counts = numpy.array(data['ref_counts'])
#        norm_avg_counts = sig_counts[1,:] / ref_counts[1,:]

# %% Frequency array

    # Calculate some of the necessary values about the frequency scanned
    half_freq_range = freq_range / 2
    freq_low = freq_center - half_freq_range
    freq_high = freq_center + half_freq_range
    freqs = numpy.linspace(freq_low, freq_high, num_steps)

# %% Define the gaussian function

    def double_gaus(x,offset,a1,center1,sigma1, a2, center2, sigma2):
            return offset - a1*exp(-(x-center1)**2/(2*sigma1**2)) - a2*exp(-(x-center2)**2/(2*sigma2**2))

    def single_gaus(x,offset,a1,center1,sigma1):
        return offset - a1*exp(-(x-center1)**2/(2*sigma1**2))

    # Guess the st dev, contrast, and veritcal offset for the fitting
    sigma = 0.01
    contrast = 0.1
    offset = 1

## %% Guess the locations of the minimums
#
#    minFreqGuess = []
#
#    findPeaks = find_peaks(-norm_avg_counts + 1, width = 8, prominence = (0.07, None))
#
#    minGuess = findPeaks[0]
#
#    print(minGuess)
#
#    if len(minGuess) < 1:
#        print("No local minimums found, cannot fit automatically")
#
#    elif len(minGuess) > 2:
#        print("Too many minimums found, cannot fit automatically")
#
#    else:
#        for i in minGuess:
#
#            minFreqGuess.append(freq[i])
#
#        print(minFreqGuess)

# %% Ask user input for guesses on the two resonances.

#    msg_first_resonance = 'Need two init params for resonance centers.  ' \
#        'First resonance = '
#    minFreqGuess[0] = input(msg_first_resonance)
#
#    msg_second_resonance = '(if one resonance, input \'n\')  ' \
#        'Second resonance = '
#
#    second_freq_guess = input(msg_second_resonance)

    if second_freq_guess == 'n':
        guess_params = [offset, contrast, minFreqGuess[0], sigma]
        minFreqGuess[1] = minFreqGuess[0]

        try:
            popt,pcov = curve_fit(single_gaus, freqs, norm_avg_counts,
                          p0=guess_params)
        except Exception:
            print('Something went wrong!')
            popt = guess_params

        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        ax.plot(freqs, norm_avg_counts,'b',label='data')
        ax.plot(freqs, single_gaus(freqs,*popt),'r-',label='fit')
        ax.set_xlabel('Frequency (GHz)')
        ax.set_ylabel('Contrast (arb. units)')
    #    ax.set_title('ESR (60\N{DEGREE SIGN})')
        ax.legend()
        text1 = "\n".join(("Fluorescent Contrast=" + "%.3f"%(popt[1]),
                          "Center Frequency=" + "%.4f"%(popt[2]) + " GHz",
                          "Std Deviation=" + "%.4f"%(popt[3]) + " GHz"))
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)

        ax.text(0.05, 0.15, text1, transform=ax.transAxes, fontsize=12,
                                verticalalignment="top", bbox=props)

    else:
        minFreqGuess[1] = second_freq_guess
        guess_params=[offset, contrast, minFreqGuess[0], sigma,
                              contrast, minFreqGuess[1], sigma]

        try:
            popt,pcov = curve_fit(double_gaus, freqs, norm_avg_counts,
                          p0=guess_params)
        except Exception:
            print('Something went wrong!')
            popt = guess_params

        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        ax.plot(freqs, norm_avg_counts,'b',label='data')
        smooth_freqs = numpy.linspace(freqs[0], freqs[-1], 1000)
        ax.plot(smooth_freqs, double_gaus(smooth_freqs,*popt),'r-',label='fit')
        ax.set_xlabel('Frequency (GHz)')
        ax.set_ylabel('Contrast (arb. units)')
    #    ax.set_title('ESR (60\N{DEGREE SIGN})')
        ax.legend()
        text1 = "\n".join(("Fluorescent Contrast=" + "%.3f"%(popt[1]),
                          "Center Frequency=" + "%.4f"%(popt[2]) + " GHz",
                          "Std Deviation=" + "%.4f"%(popt[3]) + " GHz"))
        text2 = "\n".join(("Fluorescent Contrast=" + "%.3f"%(popt[4]),
                          "Center Frequency=" + "%.4f"%(popt[5]) + " GHz",
                          "Std Deviation=" + "%.3f"%(popt[6]) + " GHz"))
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)

        ax.text(0.05, 0.15, text1, transform=ax.transAxes, fontsize=12,
                                verticalalignment="top", bbox=props)
        ax.text(0.55, 0.15, text2, transform=ax.transAxes, fontsize=12,
                                verticalalignment="top", bbox=props)


# %% If there are 1 or 2 guesses for the minimum, then fit a curve


#    if len(minGuess) == 1:
#        popt,pcov = curve_fit(gaus, freq, norm_avg_counts,
#                      p0=[offset, contrast, minFreqGuess[0], sigma,
#                          contrast, minFreqGuess[0], sigma])
#    elif len(minGuess) == 2:



# %% Plot the data itself and the fitted curve

    fig.canvas.draw()
    fig.set_tight_layout(True)
    fig.canvas.flush_events()

    # Save the file in the same file directory
    no_ext = open_file_name.split('.')[0]
    fig.savefig('{}_fit.{}'.format(no_ext, save_file_type))

# %%

if __name__ == "__main__":

    fit_resonance('svg')
