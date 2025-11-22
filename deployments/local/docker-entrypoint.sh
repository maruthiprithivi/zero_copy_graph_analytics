#!/bin/bash
set -e

# Start ClickHouse server in the background
echo "Starting ClickHouse server..."
/usr/bin/clickhouse-server --config-file=/etc/clickhouse-server/config.xml &

# Wait for ClickHouse to be ready
echo "Waiting for ClickHouse to be ready..."
until clickhouse-client --query "SELECT 1" > /dev/null 2>&1; do
    echo "ClickHouse is not ready yet. Waiting..."
    sleep 2
done

echo "ClickHouse is ready!"
echo "Data generator and ingestion scripts are available at /app"
echo "To generate data, exec into this container and run: python3 generate_data.py"

# Keep container running
tail -f /dev/null
