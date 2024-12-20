"""
This module contains functions for tracking the chaos experiments.
This involves a thread that runs in the background an keeps track of time and the state of the experiment.
"""
import time
import os
from chaos_lib_utils.constants import NUMBER_OF_RUNS, OFFSET_IN_SECONDS, OFFSET_IN_MINUTES
import threading
import re
from datetime import datetime, timedelta

def monitor_chaos_tests(yaml_file: str, stop_event: threading.Event, number_of_runs: int = NUMBER_OF_RUNS, time_per_run: int = OFFSET_IN_SECONDS)->None:
    """
    Monitor the chaos tests by counting number of runs and waiting for the full duration!

    Returns:
    None
    """
    runs = 0
    while runs < number_of_runs:
        time.sleep(time_per_run)
        runs += 1
    
    time.sleep(time_per_run)
    print("All runs completed, waiting for a bit to be in sync with logs")
    
def has_cron_schedule(yaml_file: str)->bool:
    """
    Check if the yaml file has a cron schedule
    
    Parameters:
    yaml_file (str): The path to the yaml file
    
    Returns:
    bool: True if the yaml file has a cron schedule, False otherwise
    """
    with open(yaml_file, 'r') as f:
        yaml_content = f.read()
        if "schedule" in yaml_content and "concurrencyPolicy" in yaml_content:
            return True
        else:
            return False

def round_time_to_next_cron(current_time: time.struct_time, minutes: int) -> time.struct_time:
    """
    Round the time to the next cron schedule.
    
    Parameters:
    current_time (time.struct_time): The current time.
    minutes (int): The cron schedule in minutes, e.g., 5 minutes, 10 minutes, etc.
    
    Returns:
    time.struct_time: The rounded time.
    """
    # conv to datetime to manipulate
    dt = datetime.fromtimestamp(time.mktime(current_time))
    dt = dt.replace(second=0, microsecond=0)

    # Calculate how many minutes to add to reach the next interval
    minute_dt = dt.minute
    while not minute_dt % minutes == 0:
        minute_dt += 1
    minute_increment = minute_dt - dt.minute

    new_dt = dt + timedelta(minutes=minute_increment)
    return new_dt.timetuple()

def apply_chaos_tests_at_good_time(yaml_file: str) -> None:
    """
    Normally the chaos includes a cron schedule.
    This function will check if that is actually the case and either:
    - Apply the chaos tests at a time immediately after the cron schedule
    or just apply the chaos tests - if it holds no cron schedule.

    Parameters:
    yaml_file (str): The path to the yaml file.

    Returns:
    None.
    """
    if has_cron_schedule(yaml_file):
        print("Waiting for cron schedule to be over so we have a clean start")

        current_time = time.localtime()
        time_to_wait_until = round_time_to_next_cron(current_time, OFFSET_IN_MINUTES)
        dt_to_wait_until = datetime.fromtimestamp(time.mktime(time_to_wait_until))

        while datetime.now() < dt_to_wait_until:
            time.sleep(5)
        # Wait for a safety time of 2 seconds -> that way checking seconds becomes irrelevant
        time.sleep(2)
    else:
        print("No cron schedule detected, applying chaos tests immediately")

    # Run the chaos tests
    os.system(f'kubectl apply -f {yaml_file}')
    print("Chaos tests started")
    
