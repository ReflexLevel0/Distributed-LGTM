#!/bin/bash
kubectl delete namespace \
        grafana-monitoring \
        logger-monitoring \
        sensor-monitoring \
        alloy-monitoring \
        tempo-monitoring \
        loki-monitoring \
        mimir-monitoring \
        minio-monitoring \
        kafka \
        cadvisor \
        keda
