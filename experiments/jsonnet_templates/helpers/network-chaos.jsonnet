// network-chaos.jsonnet

// JSONnet structure for Chaos Mesh pod failure experiment.
// @Author: Florian Schlösser @stu240349

/* Helper functions */

// Helper function to conditionally include fields for different network chaos experiments
local conditionalFieldsNetworkChaos(kind, params) = 
    if kind == 'delay' then { delay: params }
    else if kind == 'loss' then { loss: params }
    else if kind == 'duplicate' then { duplicate: params }
    else if kind == 'corrupt' then { corrupt: params }
    else if kind == 'bandwidth' then { bandwidth: params }
    else if kind == 'partition' then { partition: params }
    else {};

// Helper function to fill out the common fields
local commonSpec(action, mode, selector, kind, params) = {
    action: action,
    mode: mode,
    selector: selector,
} + conditionalFieldsNetworkChaos(kind, params);

/* Single experiments */
local singleNetworkChaos(apiVersion, expermimentName, kind, action, mode, selector, duration, params) = {
    apiVersion: apiVersion,
    kind: 'NetworkChaos',
    metadata: {
        name: kind,
    },
    spec: commonSpec(action, mode, selector, kind, params)
        + if duration != '' then { duration: duration } else {},

};

/* For orchestration in a workflow */
local wfNetworkChaos(experimentName, deadline, kind, mode, selector, params) = {
    templateType: 'NetworkChaos',
    name: experimentName,
    deadline: deadline,
    networkChaos: commonSpec(kind, mode, selector, kind, params),
};


// Export 
{
    singleNetworkChaos: singleNetworkChaos,
    wfNetworkChaos: wfNetworkChaos,
}
