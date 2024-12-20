"""
This module defines the data "stream" obtained from the Prometheus API
It defines a function for reading the data stream and writing it to a file
It also defines all used metrics (obtained from the Prometheus API)

The module contains the following functions:
- get_metric_queries: Returns the metric queries (defined by prometheus) to fetch from the data source 
- get_logs: This function will get logs from the data source (Prometheus) for a defined time range
"""
import requests
import time
import subprocess
import re


from chaos_lib_utils.constants import monitoring_start_time, TIME_GRANULARITY, PROMETHEUS_URL, PROMETHEUS_NAMESPACE, PROMETHEUS_CUSTOM_RESOURCE_NAME, PROMETHEUS_TIME_GRANULARITY

def get_metric_queries() -> list[list[str]]:
    """
    Returns the metric queries to fetch from the data source
    
    Parameters:
    None
    
    Returns:
    list[list[str]]: A list of lists containing the metric name and the query to fetch the metric in Prometheus
    """
    metric_queries = [["Lag_Input_Topic","sum by(consumergroup, topic) (kafka_consumergroup_lag >= 0)"]]
    return metric_queries

def restart_prometheus(namespace: str = PROMETHEUS_NAMESPACE) -> None:
    """
    Runs a little script to re install the prometheus namespace fully!
    
    kubectl delete namespace monitoring
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm uninstall prometheus
    helm install prometheus prometheus-community/kube-prometheus-stack --create-namespace --namespace monitoring
    """
    cmd = f"kubectl delete namespace {namespace}"
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error deleting namespace {namespace}: {e}")
        
    cmd = f"helm install prometheus prometheus-community/kube-prometheus-stack --create-namespace --namespace {namespace}"
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error installing prometheus: {e}")
    
def adjust_prometheus_fetch_interval(interval: str = PROMETHEUS_TIME_GRANULARITY, namespace: str = PROMETHEUS_NAMESPACE, prometheus_process_name: str = PROMETHEUS_CUSTOM_RESOURCE_NAME)-> None:
    """
    This function will load the prometheus configuration and adjust the fetch interval in which the data is fetched
    It will collect the current promethues configuartion, save it to a file, while modifying the fetch interval, then apply the new configuration
    
    Parameters:
    interval: str: The new interval to fetch the data
    -> Defaults to the TIME_GRANULARITY
    namespace: str: The namespace in which the prometheus is running
    -> Defaults to the NAMESPACE_ENV
    """
    # Get the current prometheus configuration
    cmd = f"kubectl get prometheus {prometheus_process_name} -n {namespace} -o yaml"
    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
        prometheus_config = result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error getting prometheus configuration: {e}")
    
    # Find "scrapeInterval: 30s" and replace it with the new interval
    old_prometheus_config = prometheus_config
    prometheus_config = re.sub(r'scrapeInterval: \d+s', f'scrapeInterval: {interval}s', prometheus_config)
    
    # check if we evne have changes to apply!
    if old_prometheus_config == prometheus_config:
        return
    
    # Save the configuration to a file, to apply it
    with open("prometheus_config.yaml", "w") as f:
        f.write(prometheus_config)
        
    # Apply the new configuration
    cmd = f"kubectl apply -f prometheus_config.yaml"
    
    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run("rm prometheus_config.yaml", shell=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error applying new prometheus configuration: {e}")
        
def get_logs(logfile_path :str, start_time: int = monitoring_start_time, end_time: int = time.time(), data_source_url: str = PROMETHEUS_URL, time_granularity: int = TIME_GRANULARITY, retries=0) -> None:
    """
    This function will get logs from the data source
    (Prometheus in this case) for a defined time range

    Parameters:
    logfile_path: str: Path to the logfile to write the data to
    start_time: int: Start time for the logs (defaults to the start of the monitoring)
    end_time: int: End time for the logs (defaults to the current time)
    data_source_url: str: URL of the data source (Prometheus)

    Output:
    Writes data to the logfile
    Returns:
    None
    """
    url = data_source_url

    metrics = get_metric_queries()
    # Append to file
    with open(logfile_path, 'a') as f:

        for query in metrics:
            response = requests.get(f"{url}/api/v1/query_range", params={"query": query[1], "start": start_time, "end": end_time, "step": time_granularity})
            if response.status_code == 200:
                data = response.json()['data']['result']

                # If we recieve data write it to the file in csv format
                if not data == []:
                    values = data[0]['values']
                    for val in values:
                        f.write(f"{query[0]},{val[0]},{val[1]}\n")
            else:
                # Sleep for a bit and retry
                time.sleep(5)
                if retries < 3:
                    get_logs(logfile_path, start_time, end_time, data_source_url, time_granularity, retries+1)
                else:
                    raise Exception(f"Error fetching logs: {response.text}")
                