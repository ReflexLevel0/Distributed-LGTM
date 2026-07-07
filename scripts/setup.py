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


def update_dict_list(dict_list, selector, setter, value):
    contains_value = False
    for v in dict_list:
        if selector(v) is False:
            continue
        setter(v)
        contains_value = True
        break
    if contains_value is False:
        dict_list.append(value)


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

    chunks_cache_mb = number_input("Chunk cache size [MB] (if 0, cache is disabled)", 2048, 0)

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

    # updating TEMPO_PUSH_URL in Alloy config based on chosen deployment mode
    if tempo_deploy_mode == TempoDeployment.MONOLITHIC:
        tempo_url = "http://tempo.tempo-monitoring.svc.cluster.local:4317"
    else:
        tempo_url = "http://tempo-distributor.tempo-monitoring.svc.cluster.local:4317"
    with open('../config/alloy-values.yaml', 'r') as f: 
        data: CommentedMap = yaml.load(f)
        extraEnv = data['alloy']['extraEnv']
        update_dict_list(extraEnv, lambda v: v['name'] == 'TEMPO_PUSH_URL', lambda v: v.update({'value': tempo_url}), {'name': 'TEMPO_PUSH_URL', 'value': tempo_url})
    update_yaml(data, '../config/alloy-values.yaml')

    # updating Tempo config
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
    return f"helm install --create-namespace -n tempo-monitoring -f ../config/tempo-values.yaml tempo grafana-community/{"tempo --version 2.1.0" if tempo_deploy_mode == TempoDeployment.MONOLITHIC else "tempo-distributed --version 2.18.0"}"


def configure_alloy():
    replica_count = number_input("Number of replicas", 3)
    data = yaml.load(f"""
controller:
  replicas: {replica_count}
""")
    update_yaml(data, '../config/alloy-values.yaml')
    return "helm install --create-namespace -n alloy-monitoring -f ../config/alloy-values.yaml alloy grafana/alloy --version 1.8.1"


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
    minio_replicas = number_input("Number of replicas", 5)
    minio_persistence = boolean_input("Persistence enabled", True)
    minio_persistence_size = 0
    if minio_persistence:
        minio_persistence_size = number_input("Persistence size (GiB)", 5)
    mimir_retention_days = number_input("Mimir data retention (days)", 90)
    loki_retention_days = number_input("Loki data retention (days)", 30)
    tempo_retention_days = number_input("Tempo data retention (days)", 30)

    with open('../config/minio-retention-job.yaml', 'r') as f:
        data = yaml.load(f)
    env = data['spec']['template']['spec']['containers'][0]['env']
    update_dict_list(env, lambda v: v['name'] == 'MIMIR_RETENTION_DAYS', lambda v: v.update({'value': str(mimir_retention_days)}), {'name': 'MIMIR_RETENTION_DAYS', 'value': str(mimir_retention_days)})
    update_dict_list(env, lambda v: v['name'] == 'LOKI_RETENTION_DAYS', lambda v: v.update({'value': str(loki_retention_days)}), {'name': 'LOKI_RETENTION_DAYS', 'value': str(loki_retention_days)})
    update_dict_list(env, lambda v: v['name'] == 'TEMPO_RETENTION_DAYS', lambda v: v.update({'value': str(tempo_retention_days)}), {'name': 'TEMPO_RETENTION_DAYS', 'value': str(tempo_retention_days)})
    update_yaml(data, '../config/minio-retention-job.yaml')

    data: CommentedMap = yaml.load(f"""
replicas: {minio_replicas}
persistence:
  enabled: {"true" if minio_persistence else "false"}
  size: {minio_persistence_size}Gi
    """)

    update_yaml(data, '../config/minio-values.yaml')
    return f"""helm install --create-namespace -n minio-monitoring -f ../config/minio-values.yaml minio minio/minio --version 5.4.0
kubectl apply -n minio-monitoring -f ../config/minio-retention-configmap.yaml
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

print("\nMINIO")
minio_install_str = configure_minio(disable_affinity)

print("\nKAFKA")
kafka_install_str = configure_kafka(disable_affinity)

print("\nMIMIR")
mimir_install_str = ""
enable_mimir = boolean_input("Enable Mimir", True)
if enable_mimir:
    mimir_install_str = configure_mimir(disable_affinity)

print("\nLOKI")
loki_install_str = ""
enable_loki = boolean_input("Enable Loki", True)
if enable_loki:
    loki_install_str = configure_loki(disable_affinity)

print("\nTEMPO")
tempo_install_str = ""
enable_tempo = boolean_input("Enable Tempo", True)
if enable_tempo:
    tempo_install_str = configure_tempo(disable_affinity)

print("\nALLOY")
alloy_install_str = ""
enable_alloy = boolean_input("Enable Alloy", True)
if enable_alloy:
    alloy_install_str = configure_alloy()

print("\nKEDA")
keda_install_str = ""
enable_keda = boolean_input("Enable KEDA & cAdvisor", True)
if enable_keda:
    keda_install_str = f"""helm install --create-namespace -n keda keda kedacore/keda
kubectl kustomize ../config/cadvisor | kubectl apply -f -"""

print("\nGRAFANA")
grafana_install_str = ""
enable_grafana = boolean_input("Enable Grafana", True)
if enable_grafana:
    grafana_install_str = f"""kubectl create namespace grafana-monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n grafana-monitoring -f ../config/grafana-deploy.yaml"""

print("\nSENSORS")
sensors_install_str = ""
enable_sensors = boolean_input("Enable dummy sensors", True)
if enable_sensors:
    sensors_install_str = configure_sensors()

print("\nLOGGERS")
loggers_install_str = ""
enable_loggers = boolean_input("Enable dummy loggers", True)
if enable_loggers:
    loggers_install_str = configure_loggers()

with open("./start.sh", "w") as f:
    f.write("#!/bin/bash\n")
    f.write(f"""helm repo add kedacore https://kedacore.github.io/charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm repo add minio https://charts.min.io/
helm repo add strimzi https://strimzi.io/charts/
helm repo update
{keda_install_str}\n
{kafka_install_str}\n
{minio_install_str}\n
{alloy_install_str}\n
{loki_install_str}\n
{mimir_install_str}\n
{tempo_install_str}\n
{sensors_install_str}\n
{loggers_install_str}\n
{grafana_install_str}\n
""")


with open("./delete.sh", "w") as f:
    f.write("""#!/bin/bash
kubectl delete namespace \\
        grafana-monitoring \\
        logger-monitoring \\
        sensor-monitoring \\
        alloy-monitoring \\
        tempo-monitoring \\
        loki-monitoring \\
        mimir-monitoring \\
        minio-monitoring \\
        kafka \\
        cadvisor \\
        keda
""")
