# -*- coding: utf-8 -*-
"""Template for scripts that should be run directly from the files themselves
(as opposed to from the control panel, for example).

Created on Sun Jun 16 11:22:40 2019

@author: mccambria
"""


# %% Imports


import labrad


# %% Constants


# %% Functions


# %% Main


def main():
    """When you run the file, we'll call into main, which should contain the
    body of the script.
    """

    with labrad.connect() as cxn:
        cxn.objective_piezo.write(5.5)
        print(cxn.objective_piezo.read())
        print(cxn.objective_piezo.read_position())


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # Set up your parameters to be passed to main here

    # Run the script
    main()
