// random_delay_20ms.jsonnet
// Template for single experiments introducing random delay of 20ms to all pods 

// @Author: Florian Schlösser @stu240349

// Experiment templates
local NetworkChaos = import 'helpers/network-chaos.jsonnet';

local apiVersion = 'chaos-mesh.org/v1alpha1';
local name = 'network-chaos-delay-1';
local namespace = 'default';
local kind = 'delay';
local action = 'delay';
local mode = 'one';

// Duration
local duration = '60s';
local params = {
    latency: '20ms',
    correlation: '0',
    jitter: '0',
};

// Pods & namespaces to target
local selector = {
    namespaces: ['kafka'],
    labelSelectors: {
    app: 'heuristics-miner-flink',
    },
};

// Single pod chaos
local singlePodChaos = NetworkChaos.singleNetworkChaos(
    apiVersion,
    name,
    kind,
    action,
    mode,
    selector,
    duration,
    params,
);

{
    singlePodChaos: singlePodChaos,
}