# Hybrid Deployment

Hybrid deployment with local PuppyGraph and ClickHouse Cloud. Data generation and ingestion scripts run on your local machine (not in containers).

## Architecture

```
┌─────────────────────────────────────────┐
│     Your Local Machine                  │
│  - Python environment                   │
│  - Data generator scripts               │
│  - Data ingestion scripts               │
└─────────────────────────────────────────┘
             │
             │ Connection via .env
             ▼
┌─────────────────────────────────────────┐
│     ClickHouse Cloud (Remote)           │
│  - ClickHouse Database                  │
│  - Stores all data                      │
└─────────────────────────────────────────┘
             ▲
             │ Connection
             │
┌─────────────────────────────────────────┐
│     PuppyGraph Container (Local)        │
│  - PuppyGraph Engine                    │
│  - Queries ClickHouse Cloud             │
└─────────────────────────────────────────┘
```

## Prerequisites

1. ClickHouse Cloud account and instance
2. Python 3.8+ installed on your local machine
3. Docker installed

## Setup

### 1. Configure ClickHouse Cloud Connection

```bash
cd deployments/hybrid

# Copy the environment template
cp .env.example .env

# Edit .env with your ClickHouse Cloud credentials
nano .env  # or use your preferred editor
```

Required environment variables in `.env`:
```env
CLICKHOUSE_HOST=your-instance.clickhouse.cloud
CLICKHOUSE_PORT=9440
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your-password-here
CLICKHOUSE_DATABASE=default
CLICKHOUSE_SECURE=true
```

### 2. Install Python Dependencies

```bash
# From the root of the repository
pip install -r requirements.txt
```

### 3. Start PuppyGraph

```bash
cd deployments/hybrid
docker-compose --env-file .env up -d
```

This starts PuppyGraph locally, configured to connect to your ClickHouse Cloud instance.

## Generate and Ingest Data

Data generation runs on your local machine and connects to ClickHouse Cloud:

### Option 1: Using the .env file

```bash
# From the root of the repository
python generate_data.py --env-file deployments/hybrid/.env
```

### Option 2: Using environment variables

```bash
# Export the environment variables
export $(cat deployments/hybrid/.env | grep -v '^#' | xargs)

# Generate data
python generate_data.py --customers 100000 --use-case both
```

### Option 3: Inline environment variables

```bash
CLICKHOUSE_HOST=your-instance.clickhouse.cloud \
CLICKHOUSE_PORT=9440 \
CLICKHOUSE_USER=default \
CLICKHOUSE_PASSWORD=your-password \
CLICKHOUSE_DATABASE=default \
CLICKHOUSE_SECURE=true \
python generate_data.py --customers 100000
```

## Access Services

- **PuppyGraph Web UI**: http://localhost:8081
- **PuppyGraph Cypher (Bolt)**: bolt://localhost:7687
- **PuppyGraph Gremlin**: ws://localhost:8182
- **ClickHouse Cloud**: Access via your ClickHouse Cloud console

## Query the Data

### Using ClickHouse Cloud Console
Log into your ClickHouse Cloud console and run SQL queries:
```sql
SELECT COUNT(*) FROM customers;
SELECT * FROM customers LIMIT 10;
```

### Using PuppyGraph Web UI
1. Open http://localhost:8081
2. Run Cypher queries:
```cypher
MATCH (c:Customer) RETURN c LIMIT 10;
```

### Using Python Scripts
```python
from app.database.clickhouse import ClickHouseClient

# Load environment
from dotenv import load_dotenv
load_dotenv('deployments/hybrid/.env')

# Connect and query
client = ClickHouseClient()
result = client.execute("SELECT COUNT(*) FROM customers")
print(result)
```

## Stop Services

```bash
docker-compose down
```

## Configuration Details

### Data Generator Configuration

The data generator reads ClickHouse connection settings from:
1. Environment variables (highest priority)
2. `.env` file specified with `--env-file`
3. Default values

Connection settings used:
- `CLICKHOUSE_HOST`: ClickHouse Cloud hostname
- `CLICKHOUSE_PORT`: 9440 (ClickHouse Cloud secure port)
- `CLICKHOUSE_USER`: Database user
- `CLICKHOUSE_PASSWORD`: Database password
- `CLICKHOUSE_DATABASE`: Database name
- `CLICKHOUSE_SECURE`: Set to "true" for SSL connection

### PuppyGraph Configuration

PuppyGraph uses the same ClickHouse Cloud connection via environment variables in `docker-compose.yml`:
- Reads from the `.env` file
- Constructs JDBC URL automatically
- Enables SSL for secure connection

## Troubleshooting

### Check PuppyGraph Status
```bash
docker-compose ps
docker-compose logs puppygraph
```

### Test ClickHouse Cloud Connection
```bash
# Using clickhouse-client (if installed)
clickhouse-client \
  --host=your-instance.clickhouse.cloud \
  --port=9440 \
  --user=default \
  --password=your-password \
  --secure \
  --query="SELECT 1"
```

### Python Connection Test
```python
import os
from dotenv import load_dotenv
from app.database.connections import get_clickhouse_connection

load_dotenv('deployments/hybrid/.env')
conn = get_clickhouse_connection()
print("Connection successful!")
```

### Common Issues

1. **Connection refused**: Check your ClickHouse Cloud instance is running and firewall allows connections
2. **Authentication failed**: Verify credentials in `.env` file
3. **SSL errors**: Ensure `CLICKHOUSE_SECURE=true` is set
4. **PuppyGraph can't connect**: Check that environment variables are properly loaded in docker-compose

## Data Files

Generated data is stored locally in the `../../data` directory. The data generation script:
1. Generates data locally
2. Connects to ClickHouse Cloud
3. Ingests data into your cloud database
4. Saves backup files to `data/` directory
