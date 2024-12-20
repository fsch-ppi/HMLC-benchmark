// Experiment templates
local NetworkChaos = import 'helpers/network-chaos.jsonnet';
local PodChaos = import 'helpers/pod-chaos.jsonnet';
local TimeChaos = import 'helpers/time-chaos.jsonnet';
local workflowFn = import 'helpers/workflow.jsonnet';

// Basic settings
local apiVersion = 'chaos-mesh.org/v1alpha1';
local netChaosKind = 'network-chaos';
########################################################################
// CHANGE THIS TO ADJUST
########################################################################
// Name of the experiment
local name = 'w150ms-network-and-pod';
// Delay Configuration = 0ms means no delay and just pod failure
local delay = {
    latency: '150ms',
    correlation: '0',
    jitter: '0',
};
// Take those two from your config file!
// Time to run experiment for -> should correspond to: (NUMBER_OF_RUNS + 1 ) * OFFSET_IN_SECONDS
local totalExperimentDuration = '360s';
// Cron schedule on when to inject the pod failure
local podFailureSchedule = '*/2 * * * *';


// 'Allow' or 'Forbid'
local podFailureConcurrencyPolicy = 'Allow';
########################################################################


// Pods to target for pod failure
local podSelector = {
            namespaces: ['kafka'],
    labelSelectors: {
    app: 'heuristics-miner-flink',
    },
};

// Pods to target for network delay
local namespaceSelector = {
    namespaces: ['kafka'],
};

// Network delay settings
local networkChaosExp1 = NetworkChaos.wfNetworkChaos(
    'network-delay-1',
    totalExperimentDuration,
    'delay',
    'all',
    namespaceSelector,
    delay,
);

// Pod failure
local podfailureExp1 = PodChaos.wfScheduledPodChaos(
    'podfailure-1',
    totalExperimentDuration,
    'pod-failure',
    'one',
    podSelector,
    podFailureSchedule,
    podFailureConcurrencyPolicy,
);

// Export full workflow
{
    chaosWorkflow: workflowFn.workflow(
        apiVersion,
        name,
        'parententry',
        'Parallel',
        totalExperimentDuration,
        [
            { name: 'podfailure-1', config: podfailureExp1 },
            { name: 'network-delay-1', config: networkChaosExp1 },
        ]
    ),
}
