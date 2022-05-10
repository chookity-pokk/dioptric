# -*- coding: utf-8 -*-
"""
Functions, etc to be referenced only by other utils. If you're running into
a circular reference in utils, put the function or whatever here. 

Created 2021_09_10

@author: mccambria
"""

import platform
from pathlib import Path


def get_nvdata_dir():
    """Returns the directory for nvdata as appropriate for the OS. Returns
    a Path.
    """
    os_name = platform.system()
    if os_name == "Windows":
        nvdata_dir = Path("C:/Users/student/Documents/LAB_DATA")
    elif os_name == "Linux":
        nvdata_dir = Path.home() / "E/nvdata"

    return nvdata_dir
