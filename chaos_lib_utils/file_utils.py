"""
This module contains functions for file operations used in the chaos experiments

The module contains the following functions:
- get_file_safe_datetime: Get a datetime string that can be used in a filename
- get_log_path: Get a log path and log name for the chaos test (subfolder is specified in config.env)
"""
from datetime import datetime
import os
from chaos_lib_utils.constants import LOG_FOLDER

def get_file_safe_datetime() -> str:
    """
    Get a datetime string that can be used in a filename
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def get_log_path(chaos_test_name: str, folder_path: str = LOG_FOLDER) -> str:
    """
    Get a log path and log name for the chaos test in the specified folder (config.env)
    
    This will work if the input is a full path or just the name of the chaos test
    This will also work for files that are not yaml.
    """
    chaos_test_name = chaos_test_name.split('/')[-1]
    chaos_test_name = chaos_test_name.split('.')[0]

    return os.path.join(folder_path, f"{chaos_test_name}_{get_file_safe_datetime()}.log") 