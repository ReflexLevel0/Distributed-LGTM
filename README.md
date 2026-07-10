# Installation
To install pre-requisite programs needed to run the LGTM stack, execute all of the following steps:
1) install minikube/docker desktop/any other Kubernetes cluster
2) install kubectl and make sure the configured cluster is accessible with it
3) install docker (non-rootless)
4) install helm
5) install python3
6) "pip install ruamel.yaml"

# Setup
Run "scripts/setup.sh" script from inside the scripts directory

IMPORTANT: choose "yes" when asked whether "Disable affinity" if running locally (on one computer, with no other computers available to the cluster), otherwise deployments will fail.

# Deployment
1. if using minikube run: "minikube start", otherwise start the non-minikube cluster

2. run "scripts/start.sh" script from inside the scripts directory

# Deletion
Run "scripts/delete.sh" script from inside the scripts directory in order to delete all the deployed applications.

# Change sensor/logger count
Run "scripts/change_sensor_count.sh" and "scripts/change_logger_count.sh" scripts from inside the scripts directory in order to change the number of running sensors or loggers.

# Upgrading
After manually changing helm files it is possible to update the running deployment by running "helm upgrade".

An example of upgrading the sensors deployment:
```helm upgrade -n sensor-monitoring -f values.yaml sensors ./charts/real-sensors-chart```

For a hint on how to upgrade other deployments, check the "script/start.sh" script.

# Accessing UI
Port forward services and access them in the browser using the following commands:

kubectl port-forward -n grafana-monitoring svc/grafana 3000:3000

kubectl port-forward -n alloy-monitoring svc/alloy 12345:12345

kubectl port-forward -n kafka svc/kafka-ui 8080:8080

kubectl port-forward -n minio-monitoring svc/minio-console 9001:9001
