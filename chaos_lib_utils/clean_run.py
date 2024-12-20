""""
This module defines functions for
- deleting specific containers based on a config.env file
- deleting all chaos tests running in the cluster specified in the config.env file
"""
import subprocess
import re
import time
from chaos_lib_utils.constants import NAMESPACE_ENV, MAX_POD_RECREATION_TIME_SECONDS

def get_namespace_deployment_yaml(namespace: str = NAMESPACE_ENV) -> str:
    """
    Gets all deployments in the namespace as a yaml file and returns it as a string
    If there is an error getting the deployments, an exception is raised
    
    Parameters:
    namespace: str: Name of the namespace to get the deployments from
    -> This is provided by the config.env file
    
    Returns:
    str: The yaml file containing all deployments as a string
    """
    cmd = f"kubectl get deployments -n {namespace} -o yaml"
    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error getting deployments in namespace {namespace}: {e}")

def cleanup_containers(namespace:str = NAMESPACE_ENV)-> None:
    """
    Deletes and re-create all deployments that are in the specified namespace to clean up in between different chaos tests.
    First gets a yaml containing all deployments in the namespace, then deletes all deployments and re-creates them using that yaml file.
    
    This raises an exception if there is an error deleting or re-creating the deployments.
    
    Parameters:
    namespace: str: Name of the namespace to clean up
    -> This is also defined in the config.env file
    
    Returns:
    None
    """
    all_deployments_yaml = get_namespace_deployment_yaml()
    
    # write this yaml to a file and apply it to the cluster
    with open("all_deployments.yaml", "w") as f:
        f.write(all_deployments_yaml)
    
    # Delete all deployments
    cmd = f"kubectl delete deployments --all -n {namespace}"
    try:
        subprocess.run(cmd, shell=True, check=True)
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error deleting deployments in namespace {namespace}: {e}")
    
    # Re-create all deployments    
    cmd = f"kubectl apply -f all_deployments.yaml"
    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error re-creating deployments in namespace {namespace}: {e}")
    
def probe_all_pods_ready(namespace: str = NAMESPACE_ENV) -> bool:
    """
    Checks if all pods in the namespace are ready using JsonPath
    
    Parameters:
    namespace: str: Name of the namespace to check the pods in
    -> This is also defined in the config.env file
    
    Returns:
    bool: True if all pods are ready, False otherwise
    """
    cmd = f"kubectl get deployments -n {namespace} -o jsonpath=\"{{range .items[*]}}{{.metadata.name}}{{'\\n'}}{{.status.replicas}}{{'-'}}{{.status.readyReplicas}}{{'\\n'}}{{end}}\""
    # This command will return a string with the following format:
    # deployment_name_1
    # replicas-ready_replicas
    # ...
    
    try: 
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error getting deployments in namespace {namespace}: {e}")

    # Split output and check for readiness of all deployments
    statuses = output.splitlines()
    for i, status in enumerate(statuses):
        if (i + 1) % 2 == 0:
            # If we do not even get information - the pods cannot be ready
            if len(status) > 2:
                replicas, ready_replicas = status.split("-")
                if not replicas == ready_replicas:
                    return False
            else:
                return False
    return True
    
def wait_for_pods_ready(namespace: str = NAMESPACE_ENV, waiting_treshhold: str = MAX_POD_RECREATION_TIME_SECONDS) -> None:
    """
    This function probes pods in the defined namespace all 5 seconds until all are ready.
    If the waiting exceeds a defined threshold, an exception is raised.
    
    Parameters:
    namespace: str: Name of the namespace to check the pods in
    -> This is also defined in the config.env file
    treehold: int: Threshold in seconds to wait for all pods to be ready
    -> This is also defined in the config.env file
    
    Returns:
    None
    
    Raises:
    Exception: If the threshold is exceeded
    """
    start_waiting_time = time.time()
    while not probe_all_pods_ready(namespace):
        # If the waiting time exceeds the threshold, raise an exception
        if time.time() - start_waiting_time > 300:
            raise Exception(f"Waiting for pods to be ready exceeded threshold of {waiting_treshhold} seconds")
        time.sleep(5)
    return None
        
def delete_running_chaos_tests(namespace: str = NAMESPACE_ENV) -> None:
    """
    Delete all chaos tests running in the cluster

    First all chaos tests are listed by cluster, then all deleted that are in 
    Parameter: namespace: str: Name of the cluster to delete the chaos tests from
    """

    # Get all chaos tests from chaos mesh, with "kubectl get apiresources"
    # filter for lines that have chaos-mesh.org in them
    cmd = "kubectl api-resources"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8')
    # Get types of chaos tests
    chaos_test_types = [line.split(" ")[0] for line in output.split('\n') if "chaos-mesh.org" in line]

    # Holds tuples of (type, name, namespace), for easy dekltion
    chaos_tests_in_cluster = []
    for chaos_test_type in chaos_test_types:
        cmd = f"kubectl get {chaos_test_type} -A"
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
    
        if output.startswith("No resources found"):
            continue
        # Parse the output
        # Append tuples of (type, name, namespace) to the list
        # omiting header line, filter empty lines
        for line in filter(lambda x: x != '', output.split('\n')[1:]):
            # Split line using regex into three non whitespace words 
            # and append to the list
            # Safety check for unpacking
            if not len(re.findall(r'\S+', line)) == 3:
                continue
            _, name, _ = re.findall(r'\S+', line)
            if namespace in line:
                chaos_tests_in_cluster.append((chaos_test_type, name, namespace))

    # Delete old chaos tests in cluster
    for chaos_test_type, name, _ in chaos_tests_in_cluster:
        cmd = f"kubectl delete {chaos_test_type} {name} -n {namespace}"
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
        print(f"Deleted old chaos test {name} in {namespace}")


