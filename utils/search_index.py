# -*- coding: utf-8 -*-
"""
Here are functions for our search index, which allows us to quickly look up
data files without specifying the file path. All you need is the file name!
You probably just need one of the end-user facing functions in tool_belt.
If you're here to call a function, check out the public functions at the bottom

Created September 10th, 2021

@author: mccambria
"""

# region Imports and constants

import utils.common as common
import os
from pathlib import PurePath
import sqlite3
import time

search_index_file_name = "search_index.db"
nvdata_dir = common.get_nvdata_dir()
nvdata_dir_str = str(nvdata_dir)
date_glob = "[0-9][0-9][0-9][0-9]_[0-9][0-9]"
search_index_glob = f"{nvdata_dir_str}/pc_*/branch_*/*/{date_glob}/*.txt"

# endregion
# region Private functions


def process_full_path(full_path):
    """Return just what we want for writing to the database. Expects a string
    containing the entire path to the file, including nvdata, the file
    name, the extension...
    """

    # Make sure we have a PurePath to manipulate
    full_path = PurePath(full_path)

    # Get the path to the file separated from the file name itself and nvdata
    path_to_file = full_path.parent
    path_to_file_parts = path_to_file.parts
    
    instructional_lab_pc_name = True
        
    if instructional_lab_pc_name != None:
        nvdata_ind = path_to_file_parts.index("LAB_DATA")
    else:
        nvdata_ind = path_to_file_parts.index("nvdata")
    
    index_path_parts = path_to_file_parts[nvdata_ind + 1 :]
    index_path = PurePath(index_path_parts[0]).joinpath(*index_path_parts[1:])
    # Save the path string in the posix format
    index_path = str(index_path.as_posix())

    # Get the file name, no extension
    index_file_name = full_path.stem

    return (index_file_name, index_path)


def add_to_search_index(data_full_path):
    db_vals = process_full_path(data_full_path)
    search_index = sqlite3.connect(nvdata_dir / search_index_file_name)
    cursor = search_index.cursor()
    cursor.execute("INSERT INTO search_index VALUES (?, ?)", db_vals)
    search_index.commit()
    search_index.close()
    # Sleep for 1 second so that every file name from the same PC should be unique
    time.sleep(1)
    return db_vals[1]


def get_data_path_from_nvdata(data_file_name):
    try:
        search_index = sqlite3.connect(nvdata_dir / search_index_file_name)
        cursor = search_index.cursor()
        cursor.execute(
            "SELECT * FROM search_index WHERE file_name = '{}'".format(data_file_name)
        )
        res = cursor.fetchone()
        return res[1]
    except Exception as exc:
        print(f"Failed to find file {data_file_name} in search index.")
        print("Attempting on-the-fly indexing.")
        index_path = index_on_the_fly(data_file_name)
        if index_path is None:
            msg = f"File {data_file_name} does not appear to exist in data" " folders."
            raise RuntimeError(msg)
        return index_path


def index_on_the_fly(data_file_name):
    """If a file fails to be indexed for whatever reason and we subsequently
    unsuccesfully attempt to look it up, we'll just index it on the fly
    """

    data_file_name_w_ext = f"{data_file_name}.txt"
    data_full_path = None
    yyyy_mm = data_file_name[0:7]

    for root, _, files in os.walk(nvdata_dir):
        path_root = PurePath(root)
        # Before looping through all the files make sure the folder fits
        # the glob
        test_path_root = path_root / "test.txt"
        if not test_path_root.match(search_index_glob):
            continue
        # Make sure the folder matches when the file was created
        if not root.endswith(yyyy_mm):
            continue
        if data_file_name_w_ext in files:
            # for f in files:
            data_full_path = f"{root}/{data_file_name_w_ext}"
            break

    if data_full_path is None:
        print(f"Failed to index file {data_file_name} on the fly.")
        return None
    else:
        index_path = add_to_search_index(data_full_path)
        return index_path


# endregion
# region Public functions
"""See also get_raw_data and get_raw_data_path in tool_belt"""


def gen_search_index():
    """Create the search index from scratch. This will take several minutes.
    Once complete, delete the old index file and remove the "new_" prefix
    from the fresh index.
    """

    # Create the table
    temp_name = "new_" + search_index_file_name
    search_index = sqlite3.connect(nvdata_dir / temp_name)
    cursor = search_index.cursor()
    cursor.execute(
        """CREATE TABLE search_index (file_name text, path_from_nvdata text)"""
    )

    for root, _, files in os.walk(nvdata_dir):
        path_root = PurePath(root)
        # Before looping through all the files make sure the folder fits
        # the glob
        test_path_root = path_root / "test.txt"
        if not test_path_root.match(search_index_glob):
            continue
        for f in files:
            if f.split(".")[-1] == "txt":
                db_vals = process_full_path(f"{root}/{f}")
                cursor.execute("INSERT INTO search_index VALUES (?, ?)", db_vals)

    search_index.commit()
    search_index.close()


# endregion


if __name__ == "__main__":

    # gen_search_index()
    # index_on_the_fly("2022_07_06-16_38_20-hopper-search")

    root = nvdata_dir / "pc_hahn/branch_master/pulsed_resonance/2022_12"
    file_list = [
        "2022_12_13-10_24_13-15micro-nv1_zfs_vs_t.txt",
        "2022_12_13-11_35_43-15micro-nv1_zfs_vs_t.txt",
        "2022_12_13-13_04_58-15micro-nv1_zfs_vs_t.txt",
        "2022_12_13-12_35_43-15micro-nv1_zfs_vs_t.txt",
        "2022_12_13-12_06_41-15micro-nv1_zfs_vs_t.txt",
    ]
    paths = [root / el for el in file_list]
    for el in paths:
        add_to_search_index(el)
