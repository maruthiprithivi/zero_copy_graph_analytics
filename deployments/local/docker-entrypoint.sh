#!/bin/bash
set -e

# Fix ownership of data directory
chown -R clickhouse:clickhouse /var/lib/clickhouse /app/data 2>/dev/null || true

# Set ClickHouse password if provided
if [ -n "$CLICKHOUSE_PASSWORD" ]; then
    echo "Setting ClickHouse password..."
    cat > /etc/clickhouse-server/users.d/default-password.xml <<EOF
<clickhouse>
    <users>
        <default>
            <password>$CLICKHOUSE_PASSWORD</password>
        </default>
    </users>
</clickhouse>
EOF
    chown clickhouse:clickhouse /etc/clickhouse-server/users.d/default-password.xml
fi

# Start ClickHouse server in the background as clickhouse user
echo "Starting ClickHouse server..."
su -s /bin/bash clickhouse -c "/usr/bin/clickhouse-server --config-file=/etc/clickhouse-server/config.xml" &

# Wait for ClickHouse to be ready
echo "Waiting for ClickHouse to be ready..."
if [ -n "$CLICKHOUSE_PASSWORD" ]; then
    until clickhouse-client --password "$CLICKHOUSE_PASSWORD" --query "SELECT 1" > /dev/null 2>&1; do
        echo "ClickHouse is not ready yet. Waiting..."
        sleep 2
    done
else
    until clickhouse-client --query "SELECT 1" > /dev/null 2>&1; do
        echo "ClickHouse is not ready yet. Waiting..."
        sleep 2
    done
fi

echo "ClickHouse is ready!"
echo "Data generator and ingestion scripts are available at /app"
echo "To generate data, exec into this container and run: python3 generate_data.py"

# Keep container running
tail -f /dev/null
