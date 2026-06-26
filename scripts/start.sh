#!/bin/bash
helm repo add kedacore https://kedacore.github.io/charts  
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm repo add minio https://charts.min.io/
helm repo add strimzi https://strimzi.io/charts/
helm repo update

kubectl create namespace grafana-monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace kafka --dry-run=client -o yaml | kubectl apply -f -

helm install --create-namespace -n keda keda kedacore/keda
kubectl kustomize ../config/cadvisor | kubectl apply -f -
kubectl create -n kafka -f 'https://strimzi.io/install/latest?namespace=kafka'
kubectl apply -n kafka -f ../config/kafka-values.yaml -f ../config/kafka-broker-values.yaml -f ../config/kafka-controller-values.yaml
kubectl apply -n kafka -f ../config/kafka-ui.yaml
helm install --create-namespace -n minio-monitoring -f ../config/minio-values.yaml minio minio/minio --version 5.4.0
kubectl apply -n minio-monitoring -f ../config/minio-retention-job.yaml
helm install --create-namespace -n alloy-monitoring -f ../config/alloy-values.yaml alloy grafana/alloy --version 1.8.1
helm install --create-namespace -n loki-monitoring --values ../config/loki-values.yaml loki grafana-community/loki --version 13.6.1
helm install --create-namespace -n mimir-monitoring -f ../config/mimir-values.yaml mimir grafana/mimir-distributed --version 6.0.6
kubectl apply -f ../config/mimir-scaled-object-example.yaml
helm install --create-namespace -n tempo-monitoring -f ../config/tempo-values.yaml tempo grafana-community/tempo-distributed --version 2.18.0
helm install --create-namespace -n sensor-monitoring -f ../config/sensor-values.yaml sensors ../charts/dummy-sensor-chart
helm install --create-namespace -n logger-monitoring -f ../config/logger-values.yaml loggers ../charts/dummy-logger-chart
kubectl apply -n grafana-monitoring -f ../config/grafana-deploy.yaml
