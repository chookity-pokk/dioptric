# -*- coding: utf-8 -*-
"""Template for minor routines. Minor routines are routines for which we will
probably not want to save the data or routines that are used infrequently.

Created on Sun Jun 16 11:38:17 2019

@author: mccambria
"""


# %% Imports


import utils.tool_belt as tool_belt
import labrad


# %% Functions


def clean_up(cxn):

    tool_belt.reset_cfm()


# %% Main


def main():
    """When you run the file, we'll call into main, which should contain the
    body of the routine.
    """

    with labrad.connect() as cxn:
        main_with_cxn(cxn)
    
    
def main_with_cxn(cxn):

    # %% Initial set up here
    
    tool_belt.reset_cfm(cxn)

    # %% Collect the data

    # %% Wrap up

    clean_up(cxn)


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':
    
    pass
