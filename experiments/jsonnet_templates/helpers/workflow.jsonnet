// workflow.jsonnet
// This defines functions for creating a semi-valid workflow
// configuration for a network chaos experiment.
// @Author: Florian Schlösser @stu240349

local workflow(apiVersion, name, entryName, entryType, deadline, children) = {
    // children is a list of objects with:
    // name: name,
    // config: the configuration / result of the function call

    apiVersion: apiVersion,
    kind: 'Workflow',
    metadata: {
        name: name,
    },
    spec: {
        entry: entryName,
        templates : {
            parent: {
                name: entryName,
                templateType: entryType,
                deadline: deadline,
                // List all children
                children: [child.name for child in children],
            },

            // List children name and configuration
            childConfigs: [
                {
                    name: child.name,
                    config: child.config,
                } for child in children
            ],
        },
    },
};

{
    workflow: workflow,
}
