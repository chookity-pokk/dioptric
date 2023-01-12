# -*- coding: utf-8 -*-
"""
Functions, etc to be referenced only by other utils. If you're running into
a circular reference in utils, put the function or whatever here. 

Created 2021_09_10

@author: mccambria
"""

import platform
from pathlib import Path
import socket


def get_nvdata_dir():
    """Returns the directory for nvdata as appropriate for the OS. Returns
    a Path.
    """
    
    # Check if we're in the instructional lab
    pc_name = socket.gethostname()
    os_name = platform.system()
    if pc_name == "DESKTOP-OQNODDN":
        nvdata_dir = Path("C:/Users/student/Documents/LAB_DATA")
    elif os_name == "Windows":
        nvdata_dir = Path("E:/Shared drives/Kolkowitz Lab Group/nvdata")
    elif os_name == "Linux":
        nvdata_dir = Path.home() / "E/nvdata"

    return nvdata_dir
