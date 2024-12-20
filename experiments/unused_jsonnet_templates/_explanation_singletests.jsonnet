// singleExperiments1.jsonnet
// Template for single experiments chaos mesh test!

// Importing all Chaos experiments and making them configurable with:
// CronJobs, Scheduled runs, and Workflow runs

// @Author: Florian Schlösser @stu240349

// Experiment templates
local NetworkChaos = import 'helpers/network-chaos.jsonnet';
local PodChaos = import 'helpers/pod-chaos.jsonnet';
local TimeChaos = import 'helpers/time-chaos.jsonnet';

// Network Chaos has the following single experiments:
// 1. singleNetworkChaos(apiVersion, experimentName, kind, action, mode, selector, params, duration)
// where kind can be: delay, loss, duplicate, corrupt, bandwidth, partition
// and params are the specific parameters for the kind of chaos
// e.g. for delay: { latency: '30s', correlation: '0', jitter: '90ms' }
// Read more: https://chaos-mesh.org/docs/simulate-network-chaos-on-kubernetes/

// Pod Chaos has the following single experiments:
// 1. singlePodChaos(apiVersion, experimentName, namespace, kind, mode, selector, duration)
// where kind can be: pod-failure, pod-kill,
// 
// 2. singleConainterKill(apiVersion, PodChaosName, namespace, mode, selector, containerNames, duration)
// where containerNames is a list of container names to kill

// Time Chaos has the following single experiments:
// 1. singleTimeChaos(apiVersion, experimentName, namespace, mode, selector, timeOffset, duration)
// where timeOffset is the time to offset the clock by

// General Configuration

// API version for Chaos Mesh is fixed

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

// Duration is the time to run the chaos experiment for

/* Following is a single experiment example for a pod failure */

// Constants
local apiVersion = 'chaos-mesh.org/v1alpha1';
local name = 'network-chaos-delay-1';
local namespace = 'default';
local kind = 'pod-failure';
local mode = 'all';

// Duration
local duration = '30s';

// Pods & namespaces to target
local selector = {
    namespaces: ['default'],
    labelSelectors: {
        'app': 'myapp',
    },
};

// Single pod chaos
local singlePodChaos = PodChaos.singlePodChaos(
    apiVersion,
    name,
    namespace,
    kind,
    mode,
    selector,
    duration='', // Optional
);

{
    singlePodChaos: singlePodChaos,
}