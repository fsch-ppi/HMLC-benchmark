// time-chaos.jsonnet

// JSONnet structure for Chaos Mesh Time skew experiment
// @Author: Florian Schlösser @stu240349

/* Helper functions to fill out common fields */
local commonTimeChaos(mode, selector, timeOffset) = {
    mode: mode,
    selector: selector,
    timeOffset: timeOffset
};

/* Single experiments */
local singleTimeChaos(apiVersion, experimentName, namespace, mode, selector, timeOffset, duration) = {
    apiVersion: apiVersion,
    kind: 'TimeChaos',
    metadata: {
        name: experimentName,
        namespace: namespace,
    },
    spec: commonTimeChaos(mode, selector, timeOffset)
        + if duration != '' then { duration: duration } else {},
};

/* For orchestration in a workflow */
local wfTimeChaos(experimentName, deadline, mode, selector, timeOffset) = {
    templateType: 'TimeChaos',
    name: experimentName,
    deadline: deadline,
    timeChaos: commonTimeChaos(mode, selector, timeOffset),
};

// Export 
{
    singleTimeChaos: singleTimeChaos,
    wfTimeChaos: wfTimeChaos,
}
