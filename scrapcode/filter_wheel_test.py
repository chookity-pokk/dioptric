# -*- coding: utf-8 -*-
"""Test file for Philip's filer wheel project

Created on Mon Jun 24 09:44:39 2019

@author: mccambria
"""


# %% Imports


import labrad


# %% Constants


# %% Functions


# %% Main


def main(cxn):
    """When you run the file, we'll call into main, which should contain the
    body of the script.
    """

    cxn.filter_wheel.set_filter('nd_1.5')


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here

    # Run the script
    with labrad.connect() as cxn:
        main(cxn)
