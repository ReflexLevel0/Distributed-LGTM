# To start 5 loggers sending 100 log lines per second run:
ALLOY_URL=http://localhost ALLOY_LOGS_PORT=3100 ALLOY_TRACES_GRPC_PORT=4317 ./start.sh 5 100 web_server_logs/access.log
