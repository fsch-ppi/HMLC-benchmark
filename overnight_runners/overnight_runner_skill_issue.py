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
from chaos_lib_utils.clean_run import cleanup_containers, delete_running_chaos_tests, wait_for_pods_ready, probe_all_pods_ready
from chaos_lib_utils.prometheus_utils import get_logs, adjust_prometheus_fetch_interval, restart_prometheus
from chaos_lib_utils.file_utils import get_log_path
from chaos_lib_utils.chaos_logging import monitor_chaos_tests, apply_chaos_tests_at_good_time
from chaos_lib_utils.constants import NUMBER_OF_RUNS, OFFSET_IN_SECONDS, DATA_FETCH_INTERVAL_SECONDS, logfile_path, monitoring_start_time, YAML_FOLDER, JSONNET_FOLDER, PROMETHEUS_NAMESPACE 
import time
import threading
from datetime import datetime
import re

# Testing for those latencies
tests = [ 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360, 380, 400]
yaml_folder = os.path.join(os.getcwd(), YAML_FOLDER)

single_pod_failure_yaml = os.path.join(yaml_folder, 'single_pod_failure.yaml')

# Network template is in single_delay.yaml
# We will create a new yaml file for each test, with the delay set to the value
# the filename will be single_{delay}.yaml
for test in tests:
    with open(os.path.join(single_pod_failure_yaml), 'r') as f:
        content = f.read()
        # replace network-delay with network-delay-{test}
        content = re.sub(r"name: pod-failure", f"name: pod-failure-{test}ms", content)
        # Replace "latency: '20ms' -> latency: '{DELAY_VALUE}ms'"
        # use regex
        content = re.sub(r"latency: '\d+ms'", f"latency: '{test}ms'", content)
        
        # if the file already exists, delete it,
        # then write the new content to the file
        if os.path.exists(os.path.join(yaml_folder, f"single_{test}.yaml")):
            os.remove(os.path.join(yaml_folder, f"single_{test}.yaml"))
        with open(os.path.join(yaml_folder, f"single_{test}.yaml"), 'w') as f:
            f.write(content)
            

yaml_files = [f for f in os.listdir(yaml_folder) if f.endswith('.yaml') and f.startswith('single')]
yaml_files.remove('single_pod_failure.yaml')
yaml_files.remove('single_delay.yaml')
yaml_files = sorted(yaml_files, key=lambda x: int(x.split('_')[1].split('.')[0]))
print(yaml_files)

# To keep track of failed runs, to be processed later
failed_runs = []

# make sure the pod_chaos is first in the list
yaml_files = sorted(yaml_files, key=lambda x: "pod_failure" in x)

def run_chaos_tests(yaml_file,run_counter):
    run_counter += 1
    print(f"Starting run {run_counter}")
    print("Deleting running chaos tests")
    
    # check if prometheus is ready, if not wait for it to be ready
    if not probe_all_pods_ready(namespace=PROMETHEUS_NAMESPACE):
        restart_prometheus(namespace=PROMETHEUS_NAMESPACE)
        wait_for_pods_ready(namespace=PROMETHEUS_NAMESPACE)
    # Adjust the prometheus fetch interval, so we get more data points
    adjust_prometheus_fetch_interval()
    
    # Delete any network & pod failures - the only thing used for the paper
    os.system(f'kubectl delete podchaos --all')
    os.system(f'kubectl delete networkchaos --all')
    # Cleanup containers for a clean start
    print("Re-creating deployments")
    cleanup_containers()
    wait_for_pods_ready()
    print("All pods are ready, starting chaos tests, and monitoring")

    # Get a name for the logfile and initialize with headers (csv)
    logfile_path = get_log_path(yaml_file)
    with open(logfile_path, 'w') as f:
        f.write("Metric,Time,Value\n")


    # apply the network delay instantly
    os.system(f'kubectl apply -f {yaml_file}')
    
    # apply the pod failure at a good time
    apply_chaos_tests_at_good_time(single_pod_failure_yaml)
    
    # Mark a start and run our offset for chaos tests
    monitoring_start_time = time.time()
    time.sleep(OFFSET_IN_SECONDS)
    


    # Designate a stop event, to forcefully terminate in case prometheus is not responding
    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=monitor_chaos_tests, args=(yaml_file, stop_event))
    monitor_thread.start()

    start_time = monitoring_start_time
    # Get logs in a set interval to not make the requests too large
    # If this fails we can always get the logs via the prometheus dashboard
    while monitor_thread.is_alive():
        time.sleep(DATA_FETCH_INTERVAL_SECONDS)
        end_time = time.time()
        try:
            get_logs(logfile_path, start_time=start_time, end_time=end_time)
        except Exception as e:
            # On a failed run, delete the logfile 
            os.remove(logfile_path)
            # Add remaining runs to the failed runs list
            failed_runs.append([yaml_file, NUMBER_OF_RUNS - (run_counter - 1)])
            # Stop this iteration, kill the monitor thread and move on to the next run
            stop_event.set()
            monitor_thread.join()
            return  
            
            
        start_time = end_time
        print("Logs fetched")

        
    # Wait for the monitor thread to finish, get missing logs if there are any
    monitor_thread.join()
    get_logs(logfile_path, start_time=start_time, end_time=end_time)
    print("Finished run {run_counter} of chaos tests")



for yaml_file in yaml_files:
    try:
        yaml_file = os.path.join(yaml_folder, yaml_file)
    except Exception as e:
        print(f"Error loading yaml file: {e}")
        continue
    print("-"*20, f"\nRunning chaos tests for {yaml_file}\n", "-"*20)
    for i in range(3):
        run_chaos_tests(yaml_file,i)


# Complete failed runs, until there are no more 
while len(failed_runs) > 0:
    run_to_repeat = failed_runs[0]
    run_chaos_tests(run_to_repeat[0], run_to_repeat[1])
    run_to_repeat[1] -= 1
    if run_to_repeat[1] <= 0:
        failed_runs.pop(0)