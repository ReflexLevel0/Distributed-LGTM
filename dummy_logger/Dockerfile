FROM python:latest

WORKDIR /usr/app/src
COPY dummy_logger.py ./
COPY dataset.log ./

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV ID=""
ENV LOGS_PER_SECOND=""
CMD [ "sh", "-c", "python ./dummy_logger.py ${ID} ${LOGS_PER_SECOND} dataset.log" ]


