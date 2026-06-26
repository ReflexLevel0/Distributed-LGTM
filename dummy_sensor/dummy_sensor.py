#!/usr/bin/env python3
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Summary
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
import logging
import http.server
import time
import csv
import json
import time
import requests
import sys 
import os
import random

def push_logs(
    labels: dict[str, str],
    entries: list[tuple[str, str]],
    headers: dict[str, str] | None = None,
    auth: tuple[str, str] | None = None,
    verify: bool | str = False) -> None:
    payload = {
        'streams': [
            {
                'stream': labels,
                'values': [list(e) for e in entries],
            }
        ]
    }
    req_headers = {**(headers or {}), 'Content-Type': 'application/json'}
    resp = requests.post(
        f'{os.environ['ALLOY_URL']}:{os.environ['ALLOY_LOGS_PORT']}/loki/api/v1/push',
        headers=req_headers,
        data=json.dumps(payload),
        auth=auth,
        verify=verify,
    )
    resp.raise_for_status()

GAUGE_TEMP = Gauge('temperature', 'Sensor temperature reading (celsius)')
GAUGE_HUMIDITY = Gauge('humidity', 'Sensor humidity reading (percentage)')
GAUGE_PRESSURE = Gauge('pressure', 'Sensor pressure reading (pascals)')
GAUGE_CO2 = Gauge('co2', 'Sensor CO2 reading (ppm)')
GAUGE_PM2_5 = Gauge('pm2.5', 'Sensor PM2.5 reading (ppm)')
GAUGE_PM10 = Gauge('pm10', 'Sensor PM10 reading (ppm)')
GAUGE_DAYTIME = Gauge('daytime', 'Sensor reading describing if its day (1) or night (0)')

if __name__ == '__main__':
    now_ns = str(int(time.time() * 1e9))

    if(len(sys.argv) != 3):
        push_logs(
            labels={'job': 'dummy-sensor', 'env': 'dev'},
            entries=[(now_ns, 'ERROR: 3 arguments expected but got ' + str(len(sys.argv)) + '; usage: ./sensor_data_transmitter.py [sensorID] [datasetFilePath]')],
            headers={'X-Scope-OrgId': 'foo'}
        )
        exit()
    
    sensor_id = int(sys.argv[1])
    dataset_file_path = sys.argv[2]

    start_http_server(8000)
    push_logs(
        labels={'job': 'dummy-sensor', 'env': 'dev'},
        entries=[
            (now_ns, 'INFO: logger ' + sys.argv[1] + ' started'),
        ],
        headers={'X-Scope-OrgId': 'foo'}
    )
    
    resource = Resource(attributes={
        SERVICE_NAME: 'dummy-sensor'
    })
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=f'{os.environ['ALLOY_URL']}:{os.environ['ALLOY_TRACES_GRPC_PORT']}')
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span(f'calculate_line_count'):
        with open(dataset_file_path, 'r') as file:
            lineCount = sum(1 for line in file)
    
    skip_readings_count = int(random.random() * sensor_id) # will skip every n-th reading when reading sensor data
    sleep_amount = 0.5 + random.random() / 2 # will sleep between 0.5 and 1 seconds between every reading

    while True: # constantly reads and transmits sensor data, looping after reading the whole file
        line_counter = 0
        with tracer.start_as_current_span(f'read_file'):
            with open(dataset_file_path, 'r') as file:
                csv_file = csv.reader(file)
                
                for line in csv_file:
                    # skipping over header row
                    if line[0] == 'ID':
                        continue

                    # skipping n readings (defined by skip_readings_count)
                    line_counter = line_counter + 1
                    if skip_readings_count > 0 and line_counter % skip_readings_count != 0:
                        continue
                    
                    # parsing the reading and readings
                    with tracer.start_as_current_span(f'parse_reading') as span:
                        now_ns = str(int(time.time() * 1e9))

                        if line[2] != '':
                            GAUGE_TEMP.set(float(line[2]))

                        if line[3] != '':
                            GAUGE_HUMIDITY.set(float(line[3]))

                        if line[4] != '':
                            GAUGE_PRESSURE.set(float(line[4]))

                        if line[5] != '':
                            GAUGE_CO2.set(float(line[5]))

                        if line[6] != '':
                            GAUGE_PM2_5.set(float(line[6]))

                        if line[7] != '':
                            GAUGE_PM10.set(float(line[7]))

                        if line[8] == 'Day':
                            GAUGE_DAYTIME.set(1)
                        elif line[8] == 'Night':
                            GAUGE_DAYTIME.set(0)

                        time.sleep(sleep_amount)
                        span.set_attribute('line_id', line[0])
