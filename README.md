# PuppyGraph + ClickHouse Demo

Demo repository showcasing graph analytics on OLAP data using PuppyGraph and ClickHouse for two real-world use cases: Customer 360 and Fraud Detection.

## Overview

**The Challenge:** Traditional OLAP databases excel at analytical queries but struggle with relationship-based queries (friend networks, fraud rings, recommendation paths).

**The Solution:** PuppyGraph provides a zero-ETL graph query layer on top of ClickHouse, enabling both analytical SQL queries and graph traversals (Cypher/Gremlin) on the same data without duplication.

**Performance:** Graph queries that would take minutes with traditional JOIN-heavy SQL execute in milliseconds using PuppyGraph's native graph traversal.

## Table of Contents

- [Use Cases](#use-cases)
- [Quick Start](#quick-start)
- [Dataset Overview](#dataset-overview)
- [Example Queries](#example-queries)
- [Available Commands](#available-commands)
- [Prerequisites](#prerequisites)
- [Technologies](#technologies)
- [Repository Structure](#repository-structure)
- [Troubleshooting](#troubleshooting)

## Use Cases

### 1. Customer 360
Unified view of customer behavior combining transactional data with relationship graphs:
- Product affinity networks and recommendations
- Customer segmentation and behavioral analysis
- Cross-sell recommendation paths
- Purchase pattern detection

**Scale**: 35.4M records (1M customers, 7.3M transactions, 27M interactions, 50K products)

**Queries**: 15 SQL + 20 Cypher queries

[View Customer 360 Documentation →](use-cases/customer-360/README.md)

### 2. Fraud Detection
Real-time fraud detection using graph pattern matching with embedded fraud scenarios:
- Fraud ring identification (account takeover, money laundering, card fraud)
- Suspicious transaction networks
- Shared attribute analysis (device, identity, address)
- Anomaly detection in relationships

**Scale**: 1.29M records (100K customers, 1M transactions, 50K devices, 10K merchants)

**Fraud Scenarios**: 5 embedded patterns (account takeover, money laundering, credit card fraud, synthetic identity, merchant collusion)

**Queries**: 10 SQL + 10 Cypher queries

[View Fraud Detection Documentation →](use-cases/fraud-detection/README.md)

## Quick Start

### Option 1: Local Deployment (Everything in Docker)

Run ClickHouse and PuppyGraph locally:

```bash
# Start services
make local

# Generate data (runs inside ClickHouse container)
make generate-local

# Check status
make status
```

**Access:**
- PuppyGraph Web UI: http://localhost:8081
- ClickHouse HTTP: http://localhost:8123

### Option 2: Hybrid Deployment (PuppyGraph Local + ClickHouse Cloud)

Run PuppyGraph locally, connect to ClickHouse Cloud:

**Prerequisites:**
1. ClickHouse Cloud instance running and accessible
2. Python dependencies: `pip install -r requirements.txt`
3. Network connectivity to ClickHouse Cloud

```bash
# Install dependencies
pip install -r requirements.txt

# Configure ClickHouse Cloud connection
cp deployments/hybrid/.env.example deployments/hybrid/.env
# Edit .env with your credentials:
#   CLICKHOUSE_HOST: your-instance.clickhouse.cloud
#   CLICKHOUSE_PORT: 9440
#   CLICKHOUSE_USER: default
#   CLICKHOUSE_PASSWORD: your-password
#   CLICKHOUSE_SECURE: true

# Start PuppyGraph
make hybrid

# Generate data (runs locally, ingests to cloud)
make generate-hybrid

# Check status
make status
```

**Access:**
- PuppyGraph Web UI: http://localhost:8081
- ClickHouse Cloud: Your cloud console

## Dataset Overview

**Total Dataset**: 36.7M records across both use cases

### Customer 360 Dataset (35.4M records)
- 1M customers (5 segments: VIP, Premium, Regular, Basic, New)
- 7.3M transactions ($10-$5,000 range, 8-12 per customer)
- 27M interactions (25 per customer: view, cart, wishlist, review, share)
- 50K products (10 categories)

**SQL Performance**: 15 queries, 10-1,609ms, avg 285ms
**Cypher Performance**: 20 queries, 10-1000x faster for relationship queries

### Fraud Detection Dataset (1.29M records)
- 100K customers (3% fraudulent, 97% legitimate)
- 170K accounts (5% involved in fraud)
- 50K devices (10% suspicious)
- 10K merchants (8% fraudulent)
- 1M transactions (100K fraudulent, 900K legitimate)

**Embedded Fraud Scenarios**:
1. Account Takeover (390 accounts) - Star pattern with 1 device accessing many accounts
2. Money Laundering (390 accounts) - Circular transfer patterns
3. Credit Card Fraud (390 accounts) - Bipartite pattern with stolen cards
4. Synthetic Identity (390 accounts) - Clique pattern with shared fake identities
5. Merchant Collusion (390 accounts) - Dense network of colluding merchants

**SQL Performance**: 10 queries, 11-293ms, avg 60ms
**Cypher Performance**: 10 queries, 10-100x faster for fraud ring detection

## Example Queries

### Customer 360 - SQL (ClickHouse)
```sql
-- Top customers by lifetime value
SELECT
    customer_id,
    name,
    segment,
    ltv as lifetime_value
FROM customers
WHERE segment = 'VIP'
ORDER BY ltv DESC
LIMIT 10;
```

### Customer 360 - Cypher (PuppyGraph)
```cypher
// Find product recommendations via collaborative filtering
MATCH (target:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p1:Product)
MATCH (other:Customer)-[:PURCHASED]->(p1)
MATCH (other)-[:PURCHASED]->(p2:Product)
WHERE target.segment = other.segment
  AND NOT (target)-[:PURCHASED]->(p2)
  AND target <> other
WITH p2, COLLECT(DISTINCT other) as similar_customers
RETURN DISTINCT p2.name as recommended_product,
       p2.category,
       SIZE(similar_customers) as recommendation_strength
ORDER BY recommendation_strength DESC
LIMIT 10;
```

### Fraud Detection - Cypher (PuppyGraph)
```cypher
// Detect account takeover rings (devices accessing many accounts)
MATCH (a1:Account)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(a2:Account)
WHERE a1.account_id <> a2.account_id
WITH d, collect(DISTINCT a1.account_id) + collect(DISTINCT a2.account_id) as connected_accounts
WHERE size(connected_accounts) >= 5
RETURN d.device_id,
       d.device_fingerprint,
       d.location,
       connected_accounts,
       size(connected_accounts) as account_count
ORDER BY account_count DESC
LIMIT 10;
```

## Available Commands

```bash
# Deployment
make local           # Start local deployment
make hybrid          # Start hybrid deployment

# Data Generation
make generate-local  # Generate data for local deployment
make generate-hybrid # Generate data for hybrid deployment

# Operations
make status          # Check deployment status
make logs            # View container logs
make clean           # Stop containers and clean up

# Quick start (deploy + generate + status)
make local-quick     # Complete local setup
make hybrid-quick    # Complete hybrid setup
```

## Data Generation Options

```bash
# Using defaults (1M customers, both use cases)
python3 generate_data.py

# Custom configuration
python3 generate_data.py \
  --customers 500000 \
  --seed 42 \
  --use-case both \
  --output-dir data \
  --compression snappy \
  --verbose
```

**Available options:**
- `--customers`: Number of customers (100K, 1M, 10M, 100M)
- `--seed`: Random seed for reproducibility
- `--use-case`: customer360, fraud-detection, or both
- `--output-dir`: Output directory for data files
- `--compression`: Parquet compression (snappy, gzip, lz4)
- `--verbose`: Enable debug logging

**Data Scales:**

| Scale      | Customers | Total Records | Generation Time | RAM Required | Disk Space |
|------------|-----------|---------------|-----------------|--------------|------------|
| Small      | 100K      | ~1.3M         | 5-10 min        | 4GB          | 2GB        |
| Medium     | 1M        | ~35M          | 30-45 min       | 8GB          | 10GB       |
| Large      | 10M       | ~350M         | 4-6 hours       | 16GB         | 50GB       |
| Enterprise | 100M+     | ~3.5B+        | 1-2 days        | 32GB+        | 500GB+     |

## Prerequisites

### Local Deployment
- Docker and Docker Compose
- 8GB+ RAM recommended (16GB for large datasets)
- 10GB+ free disk space

### Hybrid Deployment
- Docker and Docker Compose (for PuppyGraph)
- Python 3.8+ with pip: `pip install -r requirements.txt`
- ClickHouse Cloud account with instance running
- 4GB+ RAM recommended (8GB for large datasets)
- 10GB+ free disk space

## Technologies

- **ClickHouse**: OLAP database for analytical queries
- **PuppyGraph**: Zero-ETL graph query engine
- **Docker**: Containerization
- **Python**: Data generation and pipeline
- **Cypher/Gremlin**: Graph query languages
- **Parquet**: Columnar data format with Snappy compression

## Repository Structure

```
.
├── README.md                  # This file
├── use-cases/
│   ├── customer-360/
│   │   ├── README.md          # Customer 360 documentation
│   │   ├── generator.py       # Customer 360 data generator
│   │   ├── queries.sql        # 15 SQL queries
│   │   └── queries.cypher     # 20 Cypher queries
│   └── fraud-detection/
│       ├── README.md          # Fraud Detection documentation
│       ├── generator.py       # Fraud Detection data generator
│       ├── queries.sql        # 10 SQL queries
│       └── queries.cypher     # 10 Cypher queries
│
├── app/
│   ├── database/              # ClickHouse client
│   ├── graph/queries.py       # Cypher query wrapper
│   └── pipeline/              # Data ingestion pipeline
│
├── config/puppygraph/         # PuppyGraph schema definitions
├── deployments/
│   ├── local/                 # Local Docker deployment configs
│   └── hybrid/                # Hybrid deployment configs
│
├── generate_data.py           # Data generation CLI
├── Makefile                   # Deployment commands
├── CONFIG.yaml                # Project configuration
└── requirements.txt           # Python dependencies
```

## Troubleshooting

### Quick Diagnostics
```bash
# Check container status
make status
docker ps

# View logs
make logs
docker logs clickhouse-local
docker logs puppygraph-local
```

### Common Issues

#### 1. ClickHouse Authentication Errors (Local)
**Symptom:** `Authentication failed` or `SSL record layer failure`

**Solution:**
```bash
# Reset containers with clean state
make clean
docker-compose -f deployments/local/docker-compose.yml down -v
make local

# Verify authentication
docker exec clickhouse-local clickhouse-client --password=clickhouse123 --query "SELECT 1"
```

#### 2. ClickHouse Cloud Connection Issues (Hybrid)
**Symptom:** `Connection refused` when running `make generate-hybrid`

**Checklist:**
- ClickHouse Cloud instance is running
- `.env` file has correct credentials (no quotes around values)
- `CLICKHOUSE_PORT=9440` (secure port for cloud)
- `CLICKHOUSE_SECURE=true` is set
- Firewall allows outbound connections to port 9440

**Solution:**
```bash
# Test connection manually
clickhouse-client \
  --host=your-instance.clickhouse.cloud \
  --port=9440 \
  --user=default \
  --password=your-password \
  --secure \
  --query="SELECT 1"
```

#### 3. Port Conflicts
**Symptom:** `Error starting container: port is already allocated`

**Solution:**
```bash
# Check what's using the ports
lsof -i :8081  # PuppyGraph Web UI
lsof -i :8123  # ClickHouse HTTP
lsof -i :9000  # ClickHouse Native

# Stop conflicting processes
docker stop $(docker ps -q)
```

#### 4. Data Generation Out of Memory
**Symptom:** Process killed by OS or taking too long

**Solution:**
```bash
# Start with smallest scale
python generate_data.py --customers 10000 --use-case customer360

# Monitor memory
docker stats

# Reduce batch size if needed
python generate_data.py --customers 100000 --batch-size 50000
```

#### 5. Missing Python Dependencies
**Symptom:** `ModuleNotFoundError`

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt
```

#### 6. "Table does not exist" Errors
**Symptom:** `Table customer360.customers doesn't exist`

**Solution:**
```bash
# Check databases and tables
docker exec clickhouse-local clickhouse-client --query "SHOW DATABASES"
docker exec clickhouse-local clickhouse-client --query "SHOW TABLES FROM customer360"

# Regenerate data if missing
make generate-local  # or make generate-hybrid
```

### Clean Restart
If nothing else works, start completely fresh:
```bash
# Stop everything
make clean

# Remove all Docker resources
docker-compose -f deployments/local/docker-compose.yml down -v
docker-compose -f deployments/hybrid/docker-compose.yml down -v

# Remove generated data
rm -rf data/

# Start fresh
make local  # or make hybrid
make generate-local  # or make generate-hybrid
```

## Key Benefits

- **Zero-ETL**: No data duplication between OLAP and graph stores
- **Dual Query Support**: Run both SQL and graph queries on same data
- **Real-time Analytics**: Graph queries execute in milliseconds
- **Scalability**: Handles billions of edges efficiently
- **Flexibility**: Choose local or cloud deployment
