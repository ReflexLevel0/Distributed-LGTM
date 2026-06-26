FROM python:latest

WORKDIR /usr/app/src
COPY dummy_sensor.py ./
COPY dataset.csv ./

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV ID=""
CMD [ "sh", "-c", "python ./dummy_sensor.py ${ID} dataset.csv" ]
