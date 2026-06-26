#!/usr/bin/env python3
from ruamel.yaml import YAML, CommentedSeq, CommentedMap
import os

def number_input(prompt: str, default: int, min_value: int = 1, max_value: int = 99999) -> int:
    while True:
        input_str = input("%s ([%s,%s],default=%s): " % (prompt, min_value, max_value, default))
        if input_str == "":
            return default
        elif input_str.isdigit():
            input_num = int(input_str)
            if input_num >= min_value and input_num <= max_value:
                return input_num

logger_count = number_input("Number of loggers", 3, 0)

logger_yaml = YAML()
logger_yaml.indent(mapping=2,sequence=4,offset=2)
with open("../config/logger-values.yaml", "r") as f:
    data = logger_yaml.load(f)

loggers_seq = CommentedSeq()
for i in range(0, logger_count):
    loggers_seq.append(CommentedMap([('id', i + 1)]))
data['loggers'] = loggers_seq

with open('../config/logger-values.yaml', 'w') as file:
    logger_yaml.dump(data, file)

os.system("helm upgrade -n logger-monitoring -f ../config/logger-values.yaml loggers ../charts/dummy-logger-chart")
