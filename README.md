### 🎛️Code and Data for the "Chaos Engineering for Process mining Paper"

This repository is from code developed in the Seminars work in my University and the accompanying paper public.

I benchmarked the Heuristics Miner with Lossy counting - a process streaming process mining algorithm using chaos tests with the framework proposed by me.

#### 📝 Paper
The related can be found [here](/paper/ChaosEngineeringStreamingProcessMining.pdf). It provides an introduction into the topic and will explain better what is actually going on here.

#### 🧩 Framework
The paper proposes [ChaosMeshWizard](https://github.com/fsch-ppi/ChaosMeshWizard), a framework based on [ChaosMesh](https://chaos-mesh.org/). It provides a cli to quickly deploy, monitor and analyze chaos tests run using ChaosMesh in Kubernetes enviroments.

#### 🛠️ Setup
For the setup I used Apache Kafka and Flink as well as Prometheus as a monitoring service. The implementation also gives access to a grafana dashboard, in which the prometheus metrics can be observed.

The main enviroment is based on the [KubernetesEnvironmentBuilder](https://github.com/HenryWedge/KubernetesEnvironmentBuilder) by my supervisor.
I forked this repository for this setup, so everything remains stable

1. Make sure you are using a Unix-based system with at least 16GB RAM. 

**NOTE**: WSL will **NOT** work, since some used chaos tests need access to the kernel network module.

2. Make sure you have the following programm installed 
- [minikube](https://kubernetes.io/de/docs/tasks/tools/install-minikube/)
- [helm](https://helm.sh/docs/intro/install/) 
- [kubectl](https://kubernetes.io/docs/tasks/tools/)

3. Clone the following repository and cd into it
```shell
git clone https://github.com/fsch-ppi/k8HeuristicsMiner.git
```
4. Start minikube with as much memory and processor cores as you can spare
``` shell
minikube start  --cpus=8 --memory 25384
```

Create a dns name for minikube.
```shell
sudo -- sh -c -e "echo '$(minikube ip) minikube' >> /etc/hosts"
```

Build the environment with all helm charts and 
```shell
chmod +x build-examples.sh
./build-examples.sh
```

Apply the Kafka files and wait until all components get into the `Running` state
```shell
kubectl apply -f examples/kafka
kubectl get pods -n kafka -w
```

Create the kafka topics and build the heuristics miner
```shell
./build-k8s.sh
kubectl apply -f build/kafka/input-topic.json -n kafka
kubectl apply -f build/kafka/model-topic.json -n kafka
kubectl apply -f build/flink/flink-deployment.json
```

Create datasource and start the execution of messages!
```shell
./build-k8s.sh
kubectl create cm def-datasource --from-file=build/load-config/datasource -n kafka
kubectl create cm def-load --from-file=build/load-config/load -n kafka
kubectl create cm def-sink --from-file=build/load-config/sink -n kafka
./start-load.sh
```

If you want to use grafana, start the dashboard using:
```shell
source ./interact.sh
grafana
```

Install Chaos Mesh
```shell
helm repo add chaos-mesh https://charts.chaos-mesh.org
kubectl create ns chaos-mesh
helm install chaos-mesh chaos-mesh/chaos-mesh -n=chaos-mesh --version 2.7.0
```
Additionally if you want to use the dashboard without generating a RBaC key for yourself, you can disable permission authentification.

**NOTE**: If others have access to the same machine, or the Chaos Mesh Dashboard will be exposed to the internet, this is a bad idea. However when using minikube you would have to manually do numerous steps to create the risk of exposing the service to the internet.
```shell
# Disable permission authentification
helm upgrade chaos-mesh chaos-mesh/chaos-mesh --namespace=chaos-mesh --version 2.7.0 --set dashboard.securityMode=false
```

Set up port forewarding for all services you want to examine.
The implementation only need prometheus!
```shell
# Fist one is mandatory
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring

# Others can be used if you want to examine them
kubectl port-forward -n chaos-mesh svc/chaos-dashboard 2333:2333  
kubectl port-forward svc/kafka-ui 8080:80 -n kafka
kubectl port-forward service/grafana-nodeport-service 9091:80 -n monitoring
```

Finally, install the python requirments
```shell
pip install -r requirements.txt
```

Now you are ready to go!

#### 🔍 Defining Chaos Tests
You can define chaos tests in two main ways:
1. Use the Chaos Dashboard (UI of Chaos mesh), download YAML and paste it in the [/experiments](/experiments) folder.

2. Create a Jsonnet template in [/experiments/jsonnet_templates](/experiments/jsonnet_templates/).
Examples can be found [here](/experiments/unused_jsonnet_templates/_explanation_workflows.jsonnet) for workflows and [here](/experiments/unused_jsonnet_templates/_explanation_singletests.jsonnet) for single experiments.

When you run the main [CLI application](/chaos_wizard_cli.py), Jsonnet templates will be automatically converted to valid yaml. 


The [helpers](/experiments/jsonnet_templates/helpers/) folder holds all basic definitions for the currently supported tests. As of now this are only NetworkChaos, PodChaos and TimeChaos [refer to](https://chaos-mesh.org/docs/simulate-pod-chaos-on-kubernetes/)
#### 🧪 Running single tests
Before running your first test, take a look into [config.env](/config.env). This holds test parameters, such as the interval in which the logging service fetches data and how long you want runs to be. Make sure this somewhat alligns with your Chaos Test definitions.


To run tests, start the main application with 
```shell
python3 chaos_wizard_cli.py
```
Select the tests you want to run.

#### 🌙 Running overnight
For running overnight, I have provided two scripts:
1. [overnight_runner.py](/overnight_runners/overnight_runner.py). When started it will just try to run all defined chaos tests three times.

Since I could not get orchestrated workflows, that used a cron schedule to work (weirldy) - I resorted to
2. [/overnight_runners/overnight_runner_skill_issue.py](/overnight_runners/overnight_runner_skill_issue.py)
This script will create a single network delay test for all defined latencies in its source code and run 3 iterations of each test.

If you want to use any of both scripts, make sure to move them into the main folder.

#### 📊 Data Analysis
I used a jupyter notebook for data analysis (so plots can be shown). Most of the functions used are, however defined in the python modules.

The notebook will scan & evaluate the whole [/experiments/runs](/experiments/runs/) folder.
There are two cherry-picked cases, which I used for my plots, the more general cases are found somewhere else.

### 🧩 Modularity
Helper functions and modules used for differen parts of the application, as well as unsused functions, that might be helpful for you can be found in [/chaos_lib_utils/](/chaos_lib_utils/).

### 🔧 Adjust Data Source
If you happen to want to use another monitoring service you can adjust the get_logs() function in [/chaos_lib_utils/prometheus_utils.py](/chaos_lib_utils/prometheus_utils.py) or just swap the calls to the get_logs() functions with your own.