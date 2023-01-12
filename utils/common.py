# -*- coding: utf-8 -*-
"""
Functions, etc to be referenced only by other utils. If you're running into
a circular reference in utils, put the function or whatever here. 

Created September 10th, 2021

@author: mccambria
"""

import platform
from pathlib import Path
import utils.tool_belt as tool_belt
### Lab-specific stuff here

shared_email = "kolkowitznvlab@gmail.com"
windows_nvdata_dir = Path("E:/Shared drives/Kolkowitz Lab Group/nvdata")
linux_nvdata_dir = Path.home() / "E/nvdata"

###


def get_nvdata_dir():
    """Returns an OS-dependent Path to the nvdata directory (configured above)"""
    
    check_if_instructional_lab_pc_name = tool_belt.check_if_instructional_lab()
    
    if check_if_instructional_lab_pc_name != None:
        nvdata_dir = Path("C:/Users/student/Documents/LAB_DATA")
    else:
        os_name = platform.system()
        if os_name == "Windows":
            nvdata_dir = windows_nvdata_dir
        elif os_name == "Linux":
            nvdata_dir = linux_nvdata_dir

    return nvdata_dir


def get_registry_entry(cxn, key, directory):
    """Return the value for the specified key. Directory as a list,
    where an empty string indicates the top of the registry
    """

    p = cxn.registry.packet()
    p.cd("", *directory)
    p.get(key)
    return p.send()["get"]


def get_server(cxn, server_type):
    """Helper function for server getters in tool_belt. Return None if we can't
    make the connection for whatever reason (e.g. the key does not exist in 
    the registry
    """
    try:
        server_name = get_registry_entry(cxn, server_type, ["", "Config", "Servers"])
        server = getattr(cxn, server_name)
    except Exception as exc:
        # print(f"Could not get server type {server_type}")
        server = None
    return server
