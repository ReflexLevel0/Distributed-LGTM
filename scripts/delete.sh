#!/bin/bash
kubectl delete deployment -n grafana-monitoring grafana
kubectl delete statefulsets -n grafana-monitoring postgres
helm delete -n logger-monitoring loggers
helm delete -n sensor-monitoring sensors
helm delete -n alloy-monitoring alloy
helm delete -n tempo-monitoring tempo
helm delete -n mimir-monitoring mimir
helm delete -n loki-monitoring loki
helm delete -n minio-monitoring minio
kubectl delete deployment -n kafka kafka-cluster-entity-operator kafka-ui strimzi-cluster-operator
kubectl delete -n kafka --all pods
