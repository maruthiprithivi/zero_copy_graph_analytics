# Local Deployment

Fully local deployment with ClickHouse and PuppyGraph running in Docker containers. Data generation and ingestion scripts run inside the ClickHouse container.

## Architecture

```
┌─────────────────────────────────────────┐
│     ClickHouse Container                │
│  - ClickHouse Server                    │
│  - Python environment                   │
│  - Data generator scripts               │
│  - Data ingestion scripts               │
└─────────────────────────────────────────┘
             │
             │ Connection
             ▼
┌─────────────────────────────────────────┐
│     PuppyGraph Container                │
│  - PuppyGraph Engine                    │
│  - Connects to ClickHouse               │
└─────────────────────────────────────────┘
```

## Quick Start

### 1. Start Services

```bash
cd deployments/local
docker-compose up -d
```

This will start:
- ClickHouse on ports 8123 (HTTP) and 9000 (Native)
- PuppyGraph on ports 8081 (Web UI), 7687 (Cypher), 8182 (Gremlin)

### 2. Generate and Ingest Data

The data generator and ingestion scripts are installed inside the ClickHouse container. To run them:

```bash
# Enter the ClickHouse container
docker exec -it clickhouse-local bash

# Inside the container, generate data
cd /app
python3 generate_data.py --customers 100000 --use-case both

# The data will be generated and automatically ingested into ClickHouse
```

### 3. Access Services

- **ClickHouse HTTP**: http://localhost:8123
- **ClickHouse Native**: localhost:9000
- **PuppyGraph Web UI**: http://localhost:8081
- **PuppyGraph Cypher (Bolt)**: bolt://localhost:7687
- **PuppyGraph Gremlin**: ws://localhost:8182

### 4. Query the Data

#### Using ClickHouse CLI (inside container)
```bash
docker exec -it clickhouse-local clickhouse-client

# Run SQL queries
SELECT COUNT(*) FROM customers;
```

#### Using PuppyGraph Web UI
1. Open http://localhost:8081
2. Run Cypher or Gremlin queries

## Data Generation Options

Inside the ClickHouse container:

```bash
# Default (1M customers, both use cases)
python3 generate_data.py

# Custom scale
python3 generate_data.py --customers 500000

# Specific use case only
python3 generate_data.py --use-case customer360
python3 generate_data.py --use-case fraud-detection

# With configuration file
cp data.env.example data.env
# Edit data.env with your preferences
python3 generate_data.py --env-file data.env

# All options
python3 generate_data.py --help
```

## Stop Services

```bash
docker-compose down

# To also remove volumes (deletes data)
docker-compose down -v
```

## Configuration

### ClickHouse
- Username: `default`
- Password: `clickhouse123`
- Database: `default`

### PuppyGraph
- Password: `puppygraph123`
- Graph catalog: `clickhouse_local`
- Graph name: `customer360_graph`

## Troubleshooting

### Check Container Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f clickhouse
docker-compose logs -f puppygraph
```

### Check ClickHouse Health
```bash
docker exec clickhouse-local clickhouse-client --query "SELECT 1"
```

### Access Data Files
Generated data files are stored in the `../../data` directory on your host machine and mounted into the container at `/app/data`.
