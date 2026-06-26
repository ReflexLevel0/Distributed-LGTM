#!/usr/bin/env python3
import sys
import math
from ruamel.yaml import YAML, CommentedMap, CommentedSeq
import ruamel.yaml
import os
from enum import Enum

class TempoDeployment(Enum):
    MONOLITHIC = 1
    MICROSERVICE = 2

class LokiDeployment(Enum):
    MONOLITHIC = 1
    SIMPLE_SCALABLE = 2
    MICROSERVICE = 3

def loki_deployment_mode_to_str(deployment_mode: int):
    match deployment_mode:
        case LokiDeployment.MONOLITHIC:
            return "SingleBinary"
        case LokiDeployment.SIMPLE_SCALABLE:
            return "SimpleScalable"
        case LokiDeployment.MICROSERVICE:
            return "Distributed"

yaml = YAML()
yaml.indent(mapping=2,sequence=4,offset=2)

def merge_data(a, b):
    for k, v in b.items():
        if k in a and isinstance(a[k], dict) and isinstance(v, dict):
            merge_data(a[k], v)
        else:
            a[k] = v
    return a

def update_yaml(data: CommentedMap, file_path: str) -> None:
    old_data = None
    combined_data = None
    if os.path.isfile(file_path):
        with(open(file_path, 'r') as file):
            old_data = yaml.load(file)

    if old_data is None:
        combined_data = data
    else:
        combined_data = merge_data(old_data, data)

    with open(file_path, 'w') as file:
        yaml.dump(combined_data, file)

def boolean_input(prompt: str, default: bool) -> bool:
    while True: 
        input_str = input("%s (%s/%s): " % (prompt, "Y" if default else "y", "n" if default else "N")).lower()
        if input_str == "y":
            return True
        elif input_str == "n":
            return False
        elif input_str == "":
            return default

def number_input(prompt: str, default: int, min_value: int = 1, max_value: int = 99999) -> int:
    while True:
        input_str = input("%s ([%s,%s],default=%s): " % (prompt, min_value, max_value, default))
        if input_str == "":
            return default
        elif input_str.isdigit():
            input_num = int(input_str)
            if input_num >= min_value and input_num <= max_value:
                return input_num

def yaml_disable_affinity(data: CommentedMap, components):
    for c in components:
        data[c]['affinity'] = None

def yaml_enable_affinity(data: CommentedMap, components):
    for c in components:
        if 'affinity' in data[c]:
            del data[c]['affinity']

def configure_mimir(disable_affinity: bool):
    manual_replicas = boolean_input("Manually configure replicas", False)
    
    ingester_replicas = 3
    querier_replicas = 3
    query_frontend_replicas = 2
    query_scheduler_replicas = 2
    store_gateway_replicas = 2
    distributor_replicas = 3
    gateway_replicas = 1
    compactor_replicas = 1 # only 1 compactor is ran in order to avoid conflicts

    if manual_replicas:
        ingester_replicas = number_input("Ingester replicas", ingester_replicas)
        querier_replicas = number_input("Querier replicas", querier_replicas)
        query_frontend_replicas = number_input("Query frotend replicas", query_frontend_replicas)
        query_scheduler_replicas = number_input("Query scheduler replicas", query_scheduler_replicas)
        store_gateway_replicas = number_input("Store gateway replicas", store_gateway_replicas)
        distributor_replicas = number_input("Distributor replicas", distributor_replicas)
        gateway_replicas = number_input("Gateway replicas", gateway_replicas)
 
    data: CommentedMap = yaml.load(f"""
distributor:
  replicas: {ingester_replicas}
ingester:
  replicas: {ingester_replicas}
querier:
  replicas: {querier_replicas}
query_frontend:
  replicas: {query_frontend_replicas}
query_scheduler:
  replicas: {query_scheduler_replicas}
store_gateway:
  replicas: {store_gateway_replicas}
gateway:
  replicas: {gateway_replicas}
compactor:
  replicas: 1
""")

    components = ['distributor' ,'ingester', 'querier', 'query_frontend', 'query_scheduler', 'store_gateway', 'gateway', 'compactor']
    if disable_affinity:
        yaml_disable_affinity(data, components)
    else:
        yaml_enable_affinity(data, components)

    update_yaml(data, '../config/mimir-values.yaml') 
    return f"helm install --create-namespace -n mimir-monitoring -f ../config/mimir-values.yaml mimir grafana/mimir-distributed --version 6.0.6"


def configure_loki(disable_affinity: bool):
    single_binary_replicas = 0
    read_replicas = 0
    write_replicas = 0
    backend_replicas = 0
    ingester_replicas = 0
    querier_replicas = 0
    query_frontend_replicas = 0
    query_scheduler_replicas = 0
    distributor_replicas = 0
    compactor_replicas = 0
    index_gateway_replicas = 0
    gateway_replicas = 0
    max_concurrent_queries = None

    loki_deploy_mode: LokiDeployment = LokiDeployment(number_input("Loki deployment mode (1=monolithic,2=simple scalable,3=MICROSERVICE)", default=3, max_value=3))
    
    loki_replication_factor = number_input("Replication factor", 3)
    manual_replicas = boolean_input("Manually configure replicas", False)

    if loki_deploy_mode == LokiDeployment.MONOLITHIC:
        single_binary_replicas = 1
        gateway_replicas = 1
        if manual_replicas:
            single_binary_replicas = number_input("Number of replicas", loki_replication_factor, loki_replication_factor)
    
    elif loki_deploy_mode == LokiDeployment.SIMPLE_SCALABLE:
        read_replicas = 3
        write_replicas = loki_replication_factor
        backend_replicas = 2
        gateway_replicas = 2
        if manual_replicas:
            read_replicas = number_input("Read replicas", read_replicas)
            write_replicas = number_input("Write replicas", write_replicas, loki_replication_factor)
            backend_replicas = number_input("Backend replicas", backend_replicas)
    
    elif loki_deploy_mode == LokiDeployment.MICROSERVICE:
        ingester_replicas = 3
        querier_replicas = 3
        query_frontend_replicas = 2
        query_scheduler_replicas = 2
        distributor_replicas = 3
        index_gateway_replicas = 2
        gateway_replicas = 2
        compactor_replicas = 1 # only 1 compactor is ran in order to avoid conflicts
        if manual_replicas:
            ingester_replicas = number_input("Ingester replicas", ingester_replicas, loki_replication_factor)
            querier_replicas = number_input("Querier replicas", querier_replicas)
            query_frontend_replicas = number_input("Query frotend replicas", query_frontend_replicas)
            query_scheduler_replicas = number_input("Query scheduler replicas", query_scheduler_replicas)
            distributor_replicas = number_input("Distributor replicas", distributor_replicas)
            index_gateway_replicas = number_input("Ingex gateway replicas", index_gateway_replicas)

    if manual_replicas:
        gateway_replicas = number_input("Gateway replicas", gateway_replicas)

    if loki_deploy_mode in [LokiDeployment.SIMPLE_SCALABLE, LokiDeployment.MICROSERVICE]:
        max_concurrent_queries = number_input("Max concurrent queries processed by queriers", 4, 1)

    chunks_cache_mb = number_input("Chunk cache size [MB] (if 0, cache is disabled)", 2048)

    data: CommentedMap = yaml.load(f"""
loki:
  commonConfig:
    replication_factor: {loki_replication_factor}
  
chunksCache:
  enabled: {True if chunks_cache_mb > 0 else False}
  allocatedMemory: {chunks_cache_mb}

deploymentMode: {loki_deployment_mode_to_str(loki_deploy_mode)}

gateway:
  replicas: {gateway_replicas}
ingester:
  replicas: {ingester_replicas}
  zoneAwareReplication:
    enabled: {False if disable_affinity else True}
querier:
  replicas: {querier_replicas}
queryFrontend:
  replicas: {query_frontend_replicas}
queryScheduler:
  replicas: {query_scheduler_replicas}
distributor:
  replicas: {distributor_replicas}
compactor:
  replicas: {compactor_replicas}
indexGateway:
  replicas: {index_gateway_replicas}

backend:
  replicas: {backend_replicas}
read:
  replicas: {read_replicas}
write:
  replicas: {write_replicas}

singleBinary:
  replicas: {single_binary_replicas}
""")

    if max_concurrent_queries is not None:
        if 'querier' in data['loki']:
            data['loki']['querier']['max_concurrent'] = max_concurrent_queries
        else:
            data['loki']['querier'] = CommentedMap([
                ('max_concurrent', max_concurrent_queries)
            ])

    components = ['ingester', 'querier', 'queryFrontend', 'queryScheduler', 'distributor', 'compactor', 'indexGateway', 'gateway', 'backend', 'read', 'write', 'singleBinary']
    if disable_affinity:
        yaml_disable_affinity(data, components)
    else:
        yaml_enable_affinity(data, components)

    update_yaml(data, '../config/loki-values.yaml')
    return f"helm install --create-namespace -n loki-monitoring --values ../config/loki-values.yaml loki grafana-community/loki --version 13.6.1"


def configure_tempo(disable_affinity: bool):
    tempo_deploy_mode: TempoDeployment = TempoDeployment(number_input("Tempo deployment mode (1=monolithic,2=MICROSERVICE)", default=2, max_value=2))
    manual_replicas = boolean_input("Manually configure replicas", False)

    single_binary_replicas = 0
    ingester_replicas = 0
    querier_replicas = 0
    query_frontend_replicas = 0
    distributor_replicas = 0
    compactor_replicas = 0
    tempo_replication_factor = None

    if tempo_deploy_mode == TempoDeployment.MONOLITHIC:
        single_binary_replicas = 1
        if manual_replicas:
            single_binary_replicas = number_input("Replicas", 1)
    else:
        compactor_replicas = 1
        tempo_replication_factor = 3
        ingester_replicas = tempo_replication_factor
        querier_replicas = 3
        query_frontend_replicas = 2
        distributor_replicas = 3
        if manual_replicas:
            tempo_replication_factor = number_input("Replication factor", tempo_replication_factor)
            ingester_replicas = number_input("Ingester replicas", ingester_replicas)
            querier_replicas = number_input("Querier replicas", querier_replicas)
            query_frontend_replicas = number_input("Query frontend replicas", query_frontend_replicas)
            distributor_replicas = number_input("Distributor replicas", distributor_replicas)

    data: CommentedMap = yaml.load(f"""
ingester:
  replicas: {ingester_replicas}
  config:
    replication_factor: {tempo_replication_factor}
  zoneAwareReplication:
    enabled: {False if disable_affinity else True}

querier:
  replicas: {querier_replicas}
queryFrontend:
  replicas: {query_frontend_replicas}
distributor:
  replicas: {distributor_replicas}
compactor:
  replicas: {compactor_replicas}

replicas: {single_binary_replicas}
""")

    components = ['ingester', 'querier', 'queryFrontend', 'distributor', 'compactor']
    if disable_affinity:
        yaml_disable_affinity(data, components)
    else:
        yaml_enable_affinity(data, components)

    update_yaml(data, '../config/tempo-values.yaml')
    return f"helm install --create-namespace -n tempo-monitoring -f ../config/tempo-values.yaml tempo grafana-community/{"tempo --version 2.1.0" if tempo_deploy_mode == 1 else "tempo-distributed --version 2.18.0"}"


def configure_sensors():
    sensor_count = number_input("Number of sensors", 3, 0)
    replica_count = number_input("Replicas per sensor", 1)
    
    sensors_seq = CommentedSeq() 
    for i in range(0, sensor_count):
        sensors_seq.append(CommentedMap([('id', i + 1)]))
    
    data = CommentedMap([
        ('replicaCount', replica_count),
        ('sensors', sensors_seq)
    ])

    update_yaml(data, '../config/sensor-values.yaml')
    return f"helm install --create-namespace -n sensor-monitoring -f ../config/sensor-values.yaml sensors ../charts/dummy-sensor-chart"


def configure_loggers():
    logger_count = number_input("Number of loggers", 3, 0)
    replica_count = number_input("Replicas per logger", 1)
    
    loggers_seq = CommentedSeq() 
    for i in range(0, logger_count):
        loggers_seq.append(CommentedMap([('id', i + 1)]))
    
    data = CommentedMap([
        ('replicaCount', replica_count),
        ('loggers', loggers_seq)
    ])

    update_yaml(data, '../config/logger-values.yaml')
    return f"helm install --create-namespace -n logger-monitoring -f ../config/logger-values.yaml loggers ../charts/dummy-logger-chart"


def configure_minio(disable_affinity: bool):
    minio_replicas = number_input("Minio replicas", 5)

    data: CommentedMap = yaml.load(f"""
replicas: {minio_replicas}
    """)

    update_yaml(data, '../config/minio-values.yaml')
    return f"""helm install --create-namespace -n minio-monitoring -f ../config/minio-values.yaml minio minio/minio --version 5.4.0
kubectl apply -n minio-monitoring -f ../config/minio-retention-job.yaml"""


def configure_kafka(disable_affinity: bool):
    kafka_broker_replicas = number_input("Kafka broker replicas", 3)
    data: CommentedMap = yaml.load(f"""
spec:
  replicas: {kafka_broker_replicas}
    """)
    update_yaml(data, '../config/kafka-broker-values.yaml')

    kafka_controller_replicas = number_input("Kafka controller replicas", 3)
    data: CommentedMap = yaml.load(f"""
spec:
  replicas: {kafka_controller_replicas}
    """)
    update_yaml(data, '../config/kafka-controller-values.yaml')
    
    enable_kafka_ui = boolean_input("Enable Kafka UI", True)

    return f"""kubectl create namespace kafka --dry-run=client -o yaml | kubectl apply -f -
kubectl create -n kafka -f 'https://strimzi.io/install/latest?namespace=kafka'
kubectl apply -n kafka -f ../config/kafka-values.yaml -f ../config/kafka-broker-values.yaml -f ../config/kafka-controller-values.yaml
{"kubectl apply -n kafka -f ../config/kafka-ui.yaml" if enable_kafka_ui else ""}"""


disable_affinity = boolean_input("Disable affinity (should only be disabled for testing/development)", default=False)

minio_install_str = configure_minio(disable_affinity)
kafka_install_str = configure_kafka(disable_affinity)

enable_mimir = boolean_input("Enable Mimir", True)
if enable_mimir:
    mimir_install_str = configure_mimir(disable_affinity)

enable_loki = boolean_input("Enable Loki", True)
if enable_loki:
    loki_install_str = configure_loki(disable_affinity)

enable_tempo = boolean_input("Enable Tempo", True)
if enable_tempo:
    tempo_install_str = configure_tempo(disable_affinity)

enable_grafana = boolean_input("Enable Grafana", True)

enable_sensors = boolean_input("Enable dummy sensors", True)
if enable_sensors:
    sensors_install_str = configure_sensors()

enable_loggers = boolean_input("Enable dummy loggers", True)
if enable_loggers:
    loggers_install_str = configure_loggers()

with open("./start.sh", "w") as f:
    f.write("#!/bin/bash\n")
    f.write(f"""helm repo add grafana https://grafana.github.io/helm-charts
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm repo add minio https://charts.min.io/
helm repo add strimzi https://strimzi.io/charts/
kubectl create namespace grafana-monitoring --dry-run=client -o yaml | kubectl apply -f -
{kafka_install_str}
{minio_install_str}
helm install --create-namespace -n alloy-monitoring -f ../config/alloy-values.yaml alloy grafana/alloy --version 1.8.1
""")
    if enable_loki:
        f.write(f"{loki_install_str}\n")
    if enable_mimir:
        f.write(f"{mimir_install_str}\n")
    if enable_tempo:
        f.write(f"{tempo_install_str}\n")
    if enable_sensors:
        f.write(f"{sensors_install_str}\n")
    if enable_loggers:
        f.write(f"{loggers_install_str}\n")
    if enable_grafana:
        f.write("kubectl apply -n grafana-monitoring -f ../config/grafana-deploy.yaml\n")

with open("./delete.sh", "w") as f:
    f.write("""#!/bin/bash
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
""")
