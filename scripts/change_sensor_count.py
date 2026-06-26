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

sensor_count = number_input("Number of sensors", 3, 0)

sensors_yaml = YAML()
sensors_yaml.indent(mapping=2,sequence=4,offset=2)
with open("../config/sensor-values.yaml", "r") as f:
    data = sensors_yaml.load(f)

sensors_seq = CommentedSeq()
for i in range(0, sensor_count):
    sensors_seq.append(CommentedMap([('id', i + 1)]))
data['sensors'] = sensors_seq

with open('../config/sensor-values.yaml', 'w') as file:
    sensors_yaml.dump(data, file)

os.system("helm upgrade -n sensor-monitoring -f ../config/sensor-values.yaml sensors ../charts/dummy-sensor-chart")
