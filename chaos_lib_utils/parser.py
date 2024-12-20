"""
This module contains parsing function to convert jsonnet files to yaml files for the chaos experiments
"""
import json
import yaml
import re 
import os
from chaos_lib_utils.constants import JSONNET_FOLDER, YAML_FOLDER


def convert_jsonnet_single_to_yaml(jsonnet_content):
    """
    This function converts a jsonnet single experiment to a yaml.
    Generate the yaml file using ugly parsing!
    Parsing steps explained:
    1. Load the jsonnet file by using "jsonnet filename.jsonnet"
    2. Parse the output:
       a) omit the outermost brackets "workflow = { ... }"
       
    Parameters:
    jsonnet_content (str): The content of the jsonnet file
    Returns:
    str: The content of the yaml file
    """
    # Load jsonnet as json
    data = json.loads(jsonnet_content)
    
    # Extract the key (e.g., "networkChaosWorkflow")
    key = next(iter(data))
    workflow_data = data[key]
    yaml_dump = yaml.dump(workflow_data, sort_keys=False)
    # Attatch quotes to the selector!
    yaml_dump = add_quotes_to_relevant_selectors(yaml_dump)
    return yaml_dump

def add_quotes_to_relevant_selectors(yaml_content):
    """

    This function adds quotes to the selectors in the yaml content that need quotes.
    Refer to (https://chaos-mesh.org/docs/define-chaos-experiment-scope/) for more information.

    Example:
    fieldSelectors:
      metadata.name: power-kafka-
    This function will convert this to:
    fieldSelectors:
      "metadata.name": "power-kafka-"
    
    Parameters:
    yaml_content (str): The content of the yaml file
    Returns:
    str: The content of the yaml file with the quotes added
    """
    # fieldSelectors
    yaml_dump = re.sub(r'(?<=fieldSelectors:\n)(\s+)(.*): (.*)', r'\1"\2": "\3"', yaml_content)
    # annotationSelectors
    yaml_dump = re.sub(r'(?<=annotationSelectors:\n)(\s+)(.*): (.*)', r'\1"\2": "\3"', yaml_dump)
    # nodeSelectors
    yaml_dump = re.sub(r'(?<=nodeSelectors:\n)(\s+)(.*): (.*)', r'\1"\2": "\3"', yaml_dump)
    # labelSelectors
    yaml_dump = re.sub(r'(?<=labelSelectors:\n)(\s+)(.*): (.*)', r'\1"\2": "\3"', yaml_dump)
    return yaml_dump
      
    
def convert_jsonnet_workflow_to_yaml(jsonnet_content):
    """
    This function converts a jsonnet workflow to a yaml workflow.
    Generate the yaml file using ugly parsing!
    This was sadly necessary as the jsonnet lib cannot specify "-" lists in yaml
    Thus - since this is well defined, we have some "constant" markers in the jsonnet files,
    which we can use to parse the jsonnet workflows into yaml

    Parsing steps explained:
    1. Load the jsonnet file by using "jsonnet filename.jsonnet"
    2. Parse the output:
       a) omit the outermost brackets "workflow = { ... }"
       b) find "spec": "parent": and replace parent content with:
         childreen:
           - name1: "..."
           - name2: "..."
       c) find "spec": "childConfigs": and replace childConfigs and the array entries
          with the similar format:
         - name1: "..." where name1 is the name of the child1 etc. (make sure to replace the inner "config" and just take the contents)
          
    3. Write the output to a yaml file
    
    Parameters:
    jsonnet_content (str): The content of the jsonnet file
    Returns:
    str: The content of the yaml file
    """
    # JSONify content
    data = json.loads(jsonnet_content)
    
    # Extract the key (e.g., "networkChaosWorkflow")
    key = next(iter(data))
    workflow_data = data[key]
    
    # reformat structure
    yaml_content = {
        'apiVersion': workflow_data['apiVersion'],
        'kind': workflow_data['kind'],
        'metadata': workflow_data['metadata'],
        'spec': {
            'entry': workflow_data['spec']['entry'],
            'templates': []
        }
    }
    # extract parent
    parent = workflow_data['spec']['templates']['parent']
    parent_yaml = {
        'name': parent['name'],
        'templateType': parent.get('templateType', ''),
        'deadline': parent['deadline'],
        'children': parent['children']
    }
    yaml_content['spec']['templates'].append(parent_yaml)
    
    # extract children
    for child in workflow_data['spec']['templates']['childConfigs']:
        config = child['config']
        child_yaml = {
            'name': child['name'],
            'templateType': config.get('templateType', ''),
        }
        
        # We do not always have a deadline, if we have a cron schedule
        if config.get('deadline') is None:
            pass
        else:
            child_yaml['deadline'] = config['deadline']
        # get other vals by iterating over the keys
        additional_keys = {k: v for k, v in config.items() if k not in ['templateType', 'deadline']}
        child_yaml.update(additional_keys)
        
        
        yaml_content['spec']['templates'].append(child_yaml)
    
    yaml_dump = yaml.dump(yaml_content, sort_keys=False)
    # Attatch quotes to the selector!
    yaml_dump = add_quotes_to_relevant_selectors(yaml_dump)
    return yaml_dump


def parse_all_jsonnet_files(jsonnet_folder:str = JSONNET_FOLDER, yaml_folder: str = YAML_FOLDER)-> None:
    """
    This function takes two folder paths and parses all jsonnet files
    in the first folder to yaml files in the second folder.
    
    Note: The paths are expected to be relative paths!
    
    Parameters:
    jsonnet_folder (str): The folder path containing the jsonnet files
    yaml_folder (str): The folder path to save the yaml files
    
    Returns:
    None
    """
    jsonnet_folder = os.path.join(os.getcwd(), jsonnet_folder)
    yaml_folder = os.path.join(os.getcwd(), yaml_folder)
    
    # Find all jsonnet files in the folder
    for f in os.listdir(jsonnet_folder):
        if f.endswith('.jsonnet'):
            
            # Gerate jsonnet output to parse for correct yaml
            jsonnet_file_path = os.path.join(jsonnet_folder, f)
            yaml_file_path = os.path.join(os.getcwd(), yaml_folder, f.replace('.jsonnet', '.yaml'))
            os.system(f'jsonnet {jsonnet_file_path} > {yaml_file_path}')
            # Parse jsonnet output to correct yaml
            parsed_yaml_content = None 
            with open(yaml_file_path, 'r') as yaml_file:
                yaml_content = yaml_file.read()
                if 'Workflow' in yaml_content:
                    parsed_yaml_content = convert_jsonnet_workflow_to_yaml(yaml_content)
                else:
                    parsed_yaml_content = convert_jsonnet_single_to_yaml(yaml_content)
            with open(yaml_file_path, 'w') as yaml_file:
                yaml_file.write(parsed_yaml_content)