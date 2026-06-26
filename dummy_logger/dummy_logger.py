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

if __name__ == '__main__':
    now_ns = str(int(time.time() * 1e9))

    if(len(sys.argv) != 4):
        push_logs(
            labels={'job': 'dummy-logger', 'env': 'dev'},
            entries=[(now_ns, 'ERROR: 3 arguments expected but got ' + str(len(sys.argv)) + '; usage: ./dummy_logger.py [loggerID] [linesPerSecond] [datasetFilePath]')],
            headers={'X-Scope-OrgId': 'foo'}
        )
        exit()
    
    logger_id = int(sys.argv[1])
    lines_per_second = sys.argv[2]
    dataset_file_path = sys.argv[3]

    push_logs(
        labels={'job': 'dummy-logger', 'env': 'dev'},
        entries=[
            (now_ns, 'INFO: logger ' + sys.argv[1] + ' started'),
        ],
        headers={'X-Scope-OrgId': 'foo'}
    )

    while True: # constantly reads and transmits log data, looping after reading the whole file
        start_ns = int(time.time() * 1e9)
        line_counter = 0
        with open(dataset_file_path, 'r') as file:
            batch = []
            for line in file:
                now_ns = int(time.time() * 1e9)

                while line_counter < (now_ns - start_ns) / 1e9 * float(lines_per_second):
                    batch.append((str(now_ns), json.dumps(line.strip())))
                    line_counter = line_counter + 1
                    now_ns = int(time.time() * 1e9)

                if len(batch) > 0:
                    push_logs(
                        labels={'job': 'dummy-logger', 'env': 'dev'},
                        entries=batch,
                        headers={'X-Scope-OrgId': 'foo'}
                    )
                    batch = []

                time.sleep(1)

