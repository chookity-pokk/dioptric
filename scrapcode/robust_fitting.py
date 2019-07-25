# -*- coding: utf-8 -*-
"""This script plots ESR data to a Gaussian fit. It guesses the frequencies of the
resonances, and uses those to curve fit to two gaussians.

Created on Thu Mar 21 10:42:07 2019

@author: mccambria
"""


# %% Imports


import numpy
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import utils.tool_belt as tool_belt


# %% Define the gaussian functions


def gaussian(freq, constrast, sigma, center):
    return constrast * numpy.exp(-((freq-center)**2) / (2 * (sigma**2)))

def double_gaussian_dip(freq, low_constrast, low_sigma, low_center,
                        high_constrast, high_sigma, high_center):
    low_gauss = gaussian(freq, low_constrast, low_sigma, low_center)
    high_gauss = gaussian(freq, high_constrast, high_sigma, high_center)
    return 1.0 - low_gauss - high_gauss
    
def single_gaussian_dip(freq, constrast, sigma, center):
    return 1.0 - gaussian(freq, constrast, sigma, center)


# %% Main


def fit_resonance(file):
    
    data = tool_belt.get_raw_data('pulsed_resonance.py', file)
        
    # Get information about the frequency
    freq_center = data['freq_center']
    freq_range = data['freq_range']
    num_steps = data['num_steps']
    
    # Get the averaged, normalized counts from the ESR 
    norm_avg_sig = numpy.array(data['norm_avg_sig'])  
       
    # %% Frequency array
    
    # Calculate some of the necessary values about the frequency scanned 
    half_freq_range = freq_range / 2
    freq_low = freq_center - half_freq_range
    freq_high = freq_center + half_freq_range
    freqs = numpy.linspace(freq_low, freq_high, num_steps)
    smooth_freqs = numpy.linspace(freq_low, freq_high, 1000)  # For plotting
        
    # %% Guess the locations of the minimums
            
    contrast = 0.2
    sigma = 0.005
    fwhm = 2.355 * sigma
    
    # Convert to index space
    fwhm_ind = fwhm * (num_steps / freq_range)
    
    inverted_norm_avg_sig = 1 - norm_avg_sig
    
    # Peaks must be separated from each other by a ~FWHM (rayleigh criteria),
    # have at least 75% of our estimated contrast, and be more than a single
    # point wide
    peak_inds, details = find_peaks(inverted_norm_avg_sig,
                                    distance=fwhm_ind,
                                    height=(0.75 * contrast, None),
                                    width=(2,None))
    peak_inds = peak_inds.tolist()
    peak_heights = details['peak_heights'].tolist()
    
    if len(peak_inds) > 1:
        # Find the location of the highest peak
        max_peak_peak_inds = peak_heights.index(max(peak_heights)) 
        max_peak_freqs = peak_inds[max_peak_peak_inds]
        
        # Remove what we just found so we can find the second highest peak
        peak_inds.pop(max_peak_peak_inds)
        peak_heights.pop(max_peak_peak_inds)
        
        # Find the location of the next highest peak
        next_max_peak_peak_inds = peak_heights.index(max(peak_heights))  # Index in peak_inds
        next_max_peak_freqs = peak_inds[next_max_peak_peak_inds]  # Index in freqs
    
        # Order from smallest to largest
        peaks = [max_peak_freqs, next_max_peak_freqs]
        peaks.sort()  
        
        low_freq_guess = freqs[peaks[0]]
        high_freq_guess = freqs[peaks[1]]
    
    elif len(peak_inds) == 1:
        low_freq_guess = freqs[peak_inds[0]]
        high_freq_guess = None
    else:
        print('Could not locate peaks for {}'.format(file))
        return None, None

    # %% Fit!
        
    contrast = 0.2  # Arb
    sigma = 0.005  # MHz
    
    if high_freq_guess is None:
        fit_func = single_gaussian_dip
        guess_params = [contrast, sigma, low_freq_guess]
    else:
        fit_func = double_gaussian_dip
        guess_params=[contrast, sigma, low_freq_guess,
                      contrast, sigma, high_freq_guess]
        
    try:
        popt, pcov = curve_fit(fit_func, freqs, norm_avg_sig, p0=guess_params)
    except Exception: 
        print('Something went wrong!')
        popt = guess_params
    
    do_plot = True
    if do_plot:
        
        fig, ax = plt.subplots(figsize=(8.5, 8.5))
        ax.plot(freqs, norm_avg_sig, 'b', label='data')
        ax.plot(smooth_freqs, fit_func(smooth_freqs, *popt), 'r-', label='fit')
        ax.set_xlabel('Frequency (GHz)')
        ax.set_ylabel('Contrast (arb. units)')
        ax.legend()
        
        text = '\n'.join(('Contrast = {:.3f}',
                          'Standard deviation = {:.4f} GHz',
                          'Frequency = {:.4f} GHz'))
        if fit_func == single_gaussian_dip:
            low_text = text.format(*popt[0:3])
            high_text = None
        elif fit_func == double_gaussian_dip:
            low_text = text.format(*popt[0:3])
            high_text = text.format(*popt[3:6])
            
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        ax.text(0.05, 0.15, low_text, transform=ax.transAxes, fontsize=12,
                verticalalignment="top", bbox=props)
        if high_text is not None:
            ax.text(0.55, 0.15, high_text, transform=ax.transAxes, fontsize=12,
                    verticalalignment="top", bbox=props)
        
        fig.canvas.draw()
        fig.set_tight_layout(True)
        fig.canvas.flush_events()
    
    # Return the resonant frequencies
    if fit_func == single_gaussian_dip:
        return popt[2], None
    elif fit_func == double_gaussian_dip:
        return popt[2], popt[5]
    
    
# %% Run the file
    
    
if __name__ == "__main__":
    
    files = ['2019-07-12_17-59-35_johnson1',
             '2019-07-12_17-47-06_johnson1',
             '2019-07-12_17-42-12_johnson1',
             '2019-07-12_17-33-50_johnson1',
             '2019-07-12_17-27-14_johnson1']
#    files = ['2019-07-12_17-15-01_johnson1',
#             '2019-07-12_17-12-20_johnson1',
#             '2019-07-12_16-58-54_johnson1',
#             '2019-07-08_17-21-38_johnson1']
#    files = ['2019-07-12_16-58-54_johnson1']
    
    for file in files:
        fit_resonance(file)
