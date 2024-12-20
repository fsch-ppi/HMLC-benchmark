"""
This script is meant to provide a CLI for running chaos tests using chaos mesh.

It is meant to integrate with the chaos mesh API and provide a simple way to run chaos tests.
The baisc notion of the workflows will be defined in the /expermients folder, as .jssonet files

This script has three main tasks:

1. Loading expermient files:
    - converting to valid yaml
    - validating the yaml

2. Running & monitoring the chaos tests:
    - running a selected chaos test

3. Generating reports & plots from the tests:
    From the data logged during tests:
    - generate a report
    - generate plots
"""

import os
from chaos_lib_utils.parser import convert_jsonnet_single_to_yaml, convert_jsonnet_workflow_to_yaml, parse_all_jsonnet_files
from chaos_lib_utils.clean_run import cleanup_containers, delete_running_chaos_tests, wait_for_pods_ready
from chaos_lib_utils.prometheus_utils import get_logs, adjust_prometheus_fetch_interval
from chaos_lib_utils.file_utils import get_log_path
from chaos_lib_utils.chaos_logging import monitor_chaos_tests, apply_chaos_tests_at_good_time
from chaos_lib_utils.constants import OFFSET_IN_SECONDS, DATA_FETCH_INTERVAL_SECONDS, logfile_path, monitoring_start_time, JSONNET_FOLDER, YAML_FOLDER
import dotenv   
import time
import threading
from datetime import datetime


"""
1. Loading expermient files & cleaning up old files

The user will be presented with a list of available experiments to choose from.
The user can either select a jsonnet file to compile a yaml file from (via the jsonnet templates)
or just use the chaos dashboard to define tests and inject the corresponding yaml file.

The system will then detect the needed options and make sure there is a yaml file to run the tests from.
HOWEVER a naming issue can arise if the user has a yaml file with the same name as a jsonnet file containing different tests.!
"""
# Parse all Jsonnet files to yaml before running anything
parse_all_jsonnet_files(JSONNET_FOLDER, YAML_FOLDER)


yaml_folder = os.path.join(os.getcwd(), YAML_FOLDER)
yaml_files = [f for f in os.listdir(yaml_folder) if f.endswith('.yaml')]
# Provide options to the user, make him select a file
print("Available experiments:")
for i, f in enumerate(yaml_files):
    print(f'({i}): {f}')

selected_file = input("Select a file: ")
try:
    yaml_file = os.path.join(yaml_folder, yaml_files[int(selected_file)])
except:
    print("Invalid selection")
    exit(1)
    
# Before each run we make sure, that no chaos tests are running in 
# Ask the user if they want to run the chaos tests
# Print the yaml file to the user
print("Chaos test yaml file:")
print("-"*20)
with open(yaml_file, 'r') as f:
    print(f.read())
print("-"*20,"\n",)
run_tests = input("Run tests? (y/n): ")
"""
2. Running the chaos tests & getting data

First the user will see the yaml file he is about to run.
Then he will be asked if he wants to run the tests!

Before actually running the tests, metrics are 

If the user selects he wants to run the chaos test, a few setup steps are done:
a) Before each delete all chaos tests running in the cluster (name specified in the config.env file)
b) Delete the specified containers in the config.env file so that we get a clean start
-> Depending on your kubernetes setup they will be re-created automatically
NOTE: My code assumes automatic re-creation 


"""
if run_tests.lower() == 'y':
    print("Starting soon, doing some cleanup first")
    
    # Adjust the prometheus fetch interval, so we get more data points
    adjust_prometheus_fetch_interval()
    
    # Delete all chaos thests running in the cluster
    print("Deleting running chaos tests")
    delete_running_chaos_tests()
    # Cleanup containers for a clean start
    print("Deleting an re-creating Pods so we get a clean start")
    cleanup_containers()
    wait_for_pods_ready()
    print("All pods are ready, starting chaos tests, and monitoring")

    # Get a name for the logfile and initialize with headers (csv)
    logfile_path = get_log_path(yaml_file)
    with open(logfile_path, 'w') as f:
        f.write("Metric,Time,Value\n")



    # Apply the chaos tests, dpending on wether we have a cron schedule or not
    apply_chaos_tests_at_good_time(yaml_file)
    
    # Mark a start and run our offset for chaos tests
    monitoring_start_time = time.time()
    time.sleep(OFFSET_IN_SECONDS)
    
else:
    print("Chaos tests not started")
    exit(0)

"""
3. Monitoring the chaos tests and injecting re-runs

The programm will spawn a thread, that will monitor time and re-start the chaos tests if there is more than one run
The thread will terminate after everything has run correclty.

The main thread will get logs in a set interval from prometheus or any other logging system configured 
(NOTE: prometheus is the standard, you would neet to define your own RestAPI)
and generate a report and plots from the data.
"""
stop_signal = threading.Event()
monitor_thread = threading.Thread(target=monitor_chaos_tests, args=(yaml_file, stop_signal))
monitor_thread.start()

start_time = monitoring_start_time
# Get logs in a set interval to not make the requests too large
# If this fails we can always get the logs via the prometheus dashboard
while monitor_thread.is_alive():
    time.sleep(DATA_FETCH_INTERVAL_SECONDS)
    end_time = time.time()
    get_logs(logfile_path, start_time=start_time, end_time=end_time)
    start_time = end_time

    
# Wait for the monitor thread to finish, get missing logs if there are any
monitor_thread.join()
get_logs(logfile_path, start_time=start_time, end_time=end_time)
print("Finished getting logs")

# Remove the chaos tests
delete_running_chaos_tests()



