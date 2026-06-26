# pre-requisites
minikube
docker (non-rootless)/docker desktop
helm
python3
"pip install ruamel.yaml"

# starting minikube
minikube start --extra-config=kubelet.max-pods=500
minikube addons enable metrics-server
minikube dashboard

# Installation
To install pre-requisite programs needed to run the LGTM stack, execute all of the following steps:
1) install minikube/docker desktop/any other kubernetes cluster
2) install docker (non-rootless)
3) install helm
4) install python3
5) "pip install ruamel.yaml"

# Setup
Run "scripts/setup.sh" script from inside the scripts directory

IMPORTANT: choose "yes" when asked whether "Disable affinity" if running locally (on one computer, with no other computers available to the cluster), otherwise deployments will fail.

# Deployment
1a) If using minikube, run:
"minikube start"

1b) If using another kubernetes cluster, start it.

2) run "scripts/start.sh" script from inside the scripts directory

# Deletion
run "scripts/stop.sh" script from inside the scripts directory

# Adding/reducing sensor count
run "scripts/change_sensor_count.sh" script from inside the scripts directory

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
