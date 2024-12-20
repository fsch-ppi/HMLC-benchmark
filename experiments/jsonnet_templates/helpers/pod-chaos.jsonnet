// chaos-mesh-pod-failure.jsonnet

// JSONnet structure for Chaos Mesh pod failure experiment.
// @Author: Florian Schlösser @stu240349

// To create PodChaos (one of either)
// - Pod failure
// - Pod kill
// - Container kill

/* Helper functions to fill out common fields */
local commonPodChaos(kind, mode, selector) = {
    action: kind,
    mode: mode,
    selector: selector,
};
local commonContainerKill(mode, selector, containerNames) = {
    mode: mode,
    selector: selector,
    containerNames: containerNames,
    action: 'container-kill',
};

/* Single experiments */
// pod failure or pod kill
local singlePodChaos(apiVersion, PodChaosName, namespace, kind, mode, selector, duration) = {
    apiVersion: apiVersion,
    kind: 'PodChaos',
    metadata: {
        name: PodChaosName,
        namespace: namespace,
    },
    spec: commonPodChaos(kind, mode, selector)
        + (if duration != '' then { duration: duration } else {}),
};
// container kill
local singleContainerKill(apiVersion, PodChaosName, namespace, mode, selector, containerNames, duration) = {
    apiVersion: apiVersion,
    kind: 'PodChaos',
    metadata: {
        name: PodChaosName,
        namespace: namespace,
    },
    spec: commonContainerKill(mode, selector, containerNames)
        + (if duration != '' then { duration: duration } else {}),
};

/* For orchestration in a workflow */
// pod failure or pod kill
local wfPodChaos(experimentName, deadline, kind, mode, selector) = {
    templateType: 'PodChaos',
    name: experimentName,
    deadline: deadline,
    podChaos: commonPodChaos(kind, mode, selector),
};


local wfScheduledPodChaos(experimentName, deadline, kind, mode, selector, cronSchedule, concurrencyPolicy) = {
    name: experimentName,
    deadline: deadline,
    templateType: 'Schedule',
    schedule: {
        concurrencyPolicy: concurrencyPolicy,
        schedule: cronSchedule,
        podChaos: commonPodChaos(kind, mode, selector),
    },
};


// container kill
local wfContainerKill(experimentName, deadline, mode, selector, containerNames) = {
    templateType: 'PodChaos',
    name: experimentName,
    deadline: deadline,
    podChaos: commonContainerKill(mode, selector, containerNames),
};

// Export 
{
    singlePodChaos: singlePodChaos,
    wfPodChaos: wfPodChaos,
    wfContainerKill: wfContainerKill,
    wfScheduledPodChaos: wfScheduledPodChaos,
}
