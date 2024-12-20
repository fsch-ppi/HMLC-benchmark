// random_pod_failure_60s.jsonnet
// Test for a pod failure on a random kafka worker pod for 30s

// @Author: Florian Schlösser @stu240349

// Experiment templates
local PodChaos = import 'helpers/pod-chaos.jsonnet';


/* Following is a single experiment example for a pod failure */

// Constants
local apiVersion = 'chaos-mesh.org/v1alpha1';
local name = 'random-pod-failure-30s';
local namespace = 'kafka';
local kind = 'pod-failure';
local mode = 'one';

// Duration
local duration = '60s';

// Pods & namespaces to target
local selector = {
    namespaces: ['kafka'],
    labelSelectors: {
    app: 'heuristics-miner-flink',
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
    duration=duration, // Optional
);

{
    singlePodChaos: singlePodChaos,
}