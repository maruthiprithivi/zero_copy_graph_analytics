#!/bin/bash

# Schema initialization script for PuppyGraph
# This script waits for PuppyGraph to be healthy, then verifies schemas are loaded

set -e

PUPPYGRAPH_HOST="${PUPPYGRAPH_HOST:-localhost}"
PUPPYGRAPH_PORT="${PUPPYGRAPH_PORT:-8081}"
PUPPYGRAPH_URL="http://${PUPPYGRAPH_HOST}:${PUPPYGRAPH_PORT}"
MAX_WAIT_TIME=300  # 5 minutes
WAIT_INTERVAL=10   # 10 seconds

echo "=================================================="
echo "PuppyGraph Schema Initialization"
echo "=================================================="
echo "PuppyGraph URL: ${PUPPYGRAPH_URL}"
echo ""

# Function to check if PuppyGraph is healthy
check_puppygraph_health() {
    curl -f -s "${PUPPYGRAPH_URL}" > /dev/null 2>&1
    return $?
}

# Function to check if schemas are loaded
check_schemas_loaded() {
    local response=$(curl -s "${PUPPYGRAPH_URL}/api/v1/graphs" 2>/dev/null || echo "")

    if echo "$response" | grep -q "customer360_graph"; then
        echo "✓ customer360_graph schema is loaded"
        return 0
    else
        echo "✗ customer360_graph schema not found"
        return 1
    fi
}

# Function to upload schema
upload_schema() {
    local schema_file="deployments/local/puppygraph/config/schema.json"
    local puppygraph_user="puppygraph"
    local puppygraph_password="${PUPPYGRAPH_PASSWORD:-puppygraph123}"

    echo "Uploading schema from ${schema_file}..."

    if [ ! -f "$schema_file" ]; then
        echo "✗ ERROR: Schema file not found: $schema_file"
        return 1
    fi

    local http_code=$(curl -XPOST \
        -H "content-type: application/json" \
        --data-binary @"$schema_file" \
        --user "$puppygraph_user:$puppygraph_password" \
        -w "%{http_code}" \
        -o /tmp/schema_upload_response.txt \
        -s \
        "${PUPPYGRAPH_URL}/schema")

    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
        echo "✓ Schema uploaded successfully (HTTP $http_code)"
        return 0
    else
        echo "✗ Schema upload failed (HTTP $http_code)"
        cat /tmp/schema_upload_response.txt
        return 1
    fi
}

# Wait for PuppyGraph to be healthy
echo "Waiting for PuppyGraph to be healthy..."
elapsed=0
while [ $elapsed -lt $MAX_WAIT_TIME ]; do
    if check_puppygraph_health; then
        echo "✓ PuppyGraph is healthy"
        break
    fi

    echo "  Waiting... (${elapsed}s/${MAX_WAIT_TIME}s)"
    sleep $WAIT_INTERVAL
    elapsed=$((elapsed + WAIT_INTERVAL))
done

if [ $elapsed -ge $MAX_WAIT_TIME ]; then
    echo "✗ ERROR: PuppyGraph did not become healthy within ${MAX_WAIT_TIME} seconds"
    exit 1
fi

echo ""
echo "Checking schema status..."
sleep 5  # Give PuppyGraph a moment to fully initialize

# Check if schemas are loaded
if check_schemas_loaded; then
    echo ""
    echo "=================================================="
    echo "✓ Schema initialization complete!"
    echo "=================================================="
    echo ""
    echo "Available graphs:"
    curl -s "${PUPPYGRAPH_URL}/api/v1/graphs" 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | sed 's/^/  - /'
    echo ""
    exit 0
else
    echo ""
    echo "⚠ Schemas not loaded - attempting automatic upload..."
    echo ""

    if upload_schema; then
        echo ""
        echo "Waiting 5 seconds for schema to initialize..."
        sleep 5

        if check_schemas_loaded; then
            echo ""
            echo "=================================================="
            echo "✓ Schema initialization complete!"
            echo "=================================================="
            exit 0
        else
            echo "✗ ERROR: Schema uploaded but not visible yet"
            echo "Please wait a moment and check the UI manually"
            exit 1
        fi
    else
        echo "✗ ERROR: Failed to upload schema automatically"
        echo "Please upload manually via http://${PUPPYGRAPH_HOST}:${PUPPYGRAPH_PORT}"
        exit 1
    fi
fi
