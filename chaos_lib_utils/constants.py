"""
This module holds all shared constants and provides a function to load the comstans from a file (config.env)
"""
import os
from dotenv import load_dotenv

# Load the config file
# Get the namespace from the config file
load_dotenv('config.env')

# helper function to get the environment variables
def get_env_var(name, default=None, cast_type=None):
    value = os.getenv(name, default)
    if value is not None and cast_type:
        try:
            return cast_type(value)
        except ValueError:
            raise ValueError(f"Invalid value for {name}. Expected type {cast_type.__name__}.")
    return value

def get_csv_list_env_var(name, default=None):
    value = os.getenv(name, default)
    if value:
        return [item.strip() for item in value.split(",") if item.strip()]
    return []

# Load constants from env, if not found use default values
NUMBER_OF_RUNS = get_env_var("NUMBER_OF_RUNS", 2, int)
OFFSET_IN_MINUTES = get_env_var("OFFSET_IN_MINUTES", 3, float)
OFFSET_IN_SECONDS = OFFSET_IN_MINUTES * 60

PROMETHEUS_URL = get_env_var("PROMETHEUS_URL", "http://localhost:9090")
TIME_GRANULARITY = get_env_var("TIME_GRANULARITY", 1, float)
LOG_FOLDER = os.path.join(os.getcwd(), get_env_var("LOG_FOLDER", "experiments/runs"))
DATA_FETCH_INTERVAL_SECONDS = get_env_var("DATA_FETCH_INTERVAL_SECONDS", 60, float)
NAMESPACE_ENV = get_env_var("CHAOS_TESTING_NAMESPACE", "kafka")
JSONNET_FOLDER = get_env_var("JSONNET_FOLDER", "experiments/jsonnet_templates")
YAML_FOLDER = get_env_var("YAML_FOLDER", "experiments")
MAX_POD_RECREATION_TIME_SECONDS = get_env_var("MAX_POD_RECREATION_TIME_SECONDS", 300, float)
PROMETHEUS_CUSTOM_RESOURCE_NAME = get_env_var("PROMETHEUS_CUSTOM_RESOURCE_NAME", "prometheus-kube-prometheus-prometheus")
PROMETHEUS_TIME_GRANULARITY = get_env_var("PROMETHEUS_TIME_GRANULARITY", 5, int)
PROMETHEUS_NAMESPACE = get_env_var("PROMETHEUS_NAMESPACE", "monitoring")
# runtime vars
logfile_path = None
monitoring_start_time = None

# Create the log folder if it does not exist
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)