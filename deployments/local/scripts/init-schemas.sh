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
    curl -f -s "${PUPPYGRAPH_URL}/health" > /dev/null 2>&1
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
    echo "⚠ WARNING: Schemas not automatically loaded"
    echo "This may be due to PuppyGraph version or configuration"
    echo ""
    echo "The schema is defined in:"
    echo "  /puppygraph/config/puppygraph.json"
    echo ""
    echo "Please verify the schema manually via:"
    echo "  1. Open http://${PUPPYGRAPH_HOST}:${PUPPYGRAPH_PORT}"
    echo "  2. Check the graphs in the UI"
    echo ""
    exit 1
fi
