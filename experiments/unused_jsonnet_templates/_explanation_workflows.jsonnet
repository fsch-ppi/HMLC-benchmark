// networkFailure1.jsonnet 

// Template for chaos mesh test!


// Importing all Chaos experiments and making them configurable with:
// CronJobs, Scheduled runs, and Workflow runs

// @Author: Florian Schlösser @stu240349

// Experiment templates
local NetworkChaos = import 'helpers/network-chaos.jsonnet';
local PodChaos = import 'helpers/pod-chaos.jsonnet';
local TimeChaos = import 'helpers/time-chaos.jsonnet';

// Network Chaos has the following orchestrable experiments:
// 1. wfNetworkChaos(experimentName, deadline, kind, mode, selector, params)
// where kind can be: delay, loss, duplicate, corrupt, bandwidth, partition
// and params are the specific parameters for the kind of chaos
// e.g. for delay: { latency: '30s', correlation: '0', jitter: '90ms' }
// Read more: https://chaos-mesh.org/docs/simulate-network-chaos-on-kubernetes/

// Pod Chaos has the following single experiments:
// 1. wfPodChaos(experimentName, deadline, kind, mode, selector)
// where kind can be: pod-failure, pod-kill,
// 
// 2. wfContainerKill(experimentName, deadline, mode, selector, containerNames)
// where containerNames is a list of container names to kill

// Time Chaos has the following single experiments:
// 1. wfTimeChaos(experimentName, deadline, mode, selector, timeOffset)
// where timeOffset is the time to offset the clock by

// General Experiment Configuration:
// Name of the experiment - the name of the chaos experiment
// Namespace for the experiment - the namespace to run the chaos experiment in
// MODE refers to the mode of the chaos: all, one, fixed, fixed-percent, random-max-percent
// - all: all pods in the selector
// - one: one pod in the selector
// - fixed: fixed number of pods in the selector
// - fixed-percent: fixed percentage of pods in the selector
// - random-max-percent: random number of pods in the selector

// Selector is a JSON object with the following fields:
// - namespaces: a list of namespaces to target
// - labelSelectors: a map of labels to select pods by
// e.g. { namespaces: ['default'], labelSelectors: { 'app': ' myapp' } }



// Workflow template
// Parses the workflow together when called
local workflowFn = import 'helpers/workflow.jsonnet';
// General Configuration for a workflow:
// - apiVersion: the API version for the chaos experiment (fixed)
// - name: name of the orchestrated chaos experiment
// - entryName - the name of the entry point for the workflow
// - templateType - the type of the template (e.g. Parallel, Serial) execution
// (see https://chaos-mesh.org/docs/run-serial-or-parallel-experiments/)
// - deadline - the time to run the experiment for
// - children - the list of experiments to run in the workflow

// General Configuration
local apiVersion = 'chaos-mesh.org/v1alpha1';
local netChaosKind = 'network-chaos';

// Pods & namespaces to target
local selector = {
    namespaces: ['default'],
    labelSelectors: {
        'app': 'myapp',
    },
};

// Examples for network chaos experiments
local delay = {
    latency: '30s',
    correlation: '0',
    jitter: '90ms',
};

local bandwidth = {
    rate: '10mbps',
    buffer: 1000,
    limit: 1000,
};

// Define Network Chaos Experiments as JSON objects
// Also add each experiment to the workflow down in the exported function
local networkChaosExp1 = NetworkChaos.wfNetworkChaos(
    'network-chaos-delay-1',
    '30s',
    'delay',
    'all',
    selector,
    delay,
);

local podfailureExp2 = PodChaos.wfPodChaos(
    'podfailure-2',
    '30s',
    'pod-failure',
    'one',
    selector,
);

local containerkill1 = PodChaos.wfContainerKill(
    'container-kill-1',
    '30s',
    'one',
    selector,
    ['mycontainer'],
);

local clockSkewExp = TimeChaos.wfTimeChaos(
    'time-chaos-clock-skew',
    '30s',
    'all',
    selector,
    '-10m100ns'
);

// Export the workflow, so it can be parsed
{
    chaosWorkflow: workflowFn.workflow(
        apiVersion,
        'network-chaos-workflow',
        'network-chaos-entry',
        'Parallel',
        '240s',
        [
            { name: 'network-chaos-delay-1', config: networkChaosExp1 },
            { name: 'podfailure-2', config: podfailureExp2 },
            { name: 'container-kill-1', config: containerkill1 },
            { name: 'time-chaos-clock-skew', config: clockSkewExp },
        ]
    ),
}
