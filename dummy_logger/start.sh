trap 'kill 0' SIGINT SIGTERM
for i in $(seq 1 $1); do
    ./dummy_logger.py $i $2 $3 &
done
wait
