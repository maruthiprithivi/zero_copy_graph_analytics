# Architecture

Complete architecture documentation for the PuppyGraph + ClickHouse demonstration platform, including system design, data models, deployment patterns, and integration strategies.

---

## Documentation Index

### 1. [System Overview](./system-overview.md)

Comprehensive system architecture covering:

- **Architecture Overview:** Visual diagrams of components and data flow
- **Component Architecture:** Detailed breakdown of each system layer:
  - Data Generation Layer (generators, personas, configuration)
  - ClickHouse OLAP Database (schemas, storage, access patterns)
  - PuppyGraph Graph Query Engine (mappings, traversal, performance)
  - Application Query Layer (SQL and graph execution)

- **Deployment Patterns:** Three deployment models:
  - Local Deployment: Complete Docker-based local setup
  - Hybrid Deployment: ClickHouse Cloud + Local PuppyGraph
  - Cloud-Native (Future): Fully cloud-hosted solution roadmap

- **Data Flow Architectures:** Visual pipelines for:
  - Customer 360 analytics workflow
  - Fraud Detection processing pipeline
  - Data generation, ingestion, and analysis stages

- **Integration Points:** Technical details on:
  - Data ingestion interfaces and formats
  - Query execution endpoints
  - Configuration management and environment variables

- **Performance Characteristics:** Benchmarks and latency metrics

- **Security Architecture:** Authentication, encryption, and best practices

- **Monitoring and Operations:** Health checks and common tasks

- **Technology Stack:** Complete tool inventory

- **Troubleshooting Guide:** Common issues and solutions

---

### 2. [Data Model](./data-model.md)

Comprehensive data modeling documentation with mermaid ER diagrams:

#### Customer 360 Model
- **ER Diagram:** Visual entity relationships (CUSTOMER, PRODUCT, TRANSACTION, INTERACTION)
- **Table Specifications:** Complete schema for each table with:
  - Column definitions (type, constraints, indices)
  - Business logic and constraints
  - Typical queries and use cases
  - Sample data examples

- **Table Descriptions:**
  - CUSTOMER: Customer demographics, segmentation, lifetime value
  - PRODUCT: Product catalog, categorization, pricing
  - TRANSACTION: Purchase records, channels, completion status
  - INTERACTION: Customer engagement (views, clicks, support)

- **Relationship Definitions:** One-to-Many and derived Many-to-Many relationships

- **Graph Schema:** PuppyGraph vertex and edge mappings

#### Fraud Detection Model
- **ER Diagram:** Visual entity relationships (CUSTOMER, ACCOUNT, TRANSACTION, DEVICE, MERCHANT)
- **Table Specifications:** Complete schema for fraud-specific tables:
  - CUSTOMER: Identity information with SSN/phone/address
  - ACCOUNT: Customer accounts with status tracking
  - TRANSACTION: Detailed transaction records with fraud scoring
  - DEVICE: Device information with geolocation
  - MERCHANT: Merchant details and risk levels
  - DEVICE_ACCOUNT_USAGE: Device-account correlation junction table

- **Relationship Definitions:** Account ownership, transaction chains, device usage patterns

- **Graph Schema:** PuppyGraph vertices and edges for fraud patterns

#### Data Management
- **Index Strategy:** ClickHouse and PuppyGraph indexing approaches
- **Data Volumes:** Cardinality and storage metrics by scale
- **Data Quality Rules:** Integrity constraints and validation
- **Partitioning Strategy:** Time-based partitioning and sharding
- **Backup and Recovery:** Procedures and best practices
- **Audit and Compliance:** Data access logging and PII protection
- **Future Schema Evolution:** Planned enhancements and roadmap

---

## Quick Navigation

### By Use Case

**Customer 360 Analysis:**
1. Read: [System Overview - Customer 360 Data Pipeline](./system-overview.md#customer-360-data-pipeline)
2. Study: [Data Model - Customer 360](./data-model.md#customer-360-data-model)
3. Reference: [Data Model - Customer 360 ER Diagram](./data-model.md#er-diagram)

**Fraud Detection:**
1. Read: [System Overview - Fraud Detection Data Pipeline](./system-overview.md#fraud-detection-data-pipeline)
2. Study: [Data Model - Fraud Detection](./data-model.md#fraud-detection-data-model)
3. Reference: [Data Model - Fraud Detection ER Diagram](./data-model.md#er-diagram-1)

### By Role

**System Administrators:**
- [Deployment Patterns](./system-overview.md#deployment-patterns) - Choose deployment model
- [Monitoring and Operations](./system-overview.md#monitoring-and-operations) - Health checks
- [Troubleshooting Guide](./system-overview.md#troubleshooting-guide) - Common issues

**Data Engineers:**
- [Data Generation Layer](./system-overview.md#1-data-generation-layer) - Understand data sources
- [Component Architecture](./system-overview.md#component-architecture) - System design
- [Data Model](./data-model.md) - Complete schema documentation

**Analysts/Business Users:**
- [Component Architecture - Application Query Layer](./system-overview.md#4-application-query-layer) - Query capabilities
- [Data Model - Relationships](./data-model.md#relationship-definitions) - Understand connections
- [Performance Characteristics](./system-overview.md#performance-characteristics) - Query performance

**Architects/Designers:**
- [Architecture Overview](./system-overview.md#architecture-overview) - System design
- [Integration Points](./system-overview.md#integration-points) - Connectivity
- [Scalability Considerations](./system-overview.md#scalability-considerations) - Growth planning

---

## Key Diagrams

### System Architecture
![System Architecture Diagram](./system-overview.md#architecture-overview) - Shows all components and data flow

### Local Deployment
![Local Deployment Pattern](./system-overview.md#pattern-1-local-deployment-developmentdemo) - Docker-based local setup

### Hybrid Deployment
![Hybrid Deployment Pattern](./system-overview.md#pattern-2-hybrid-deployment-clickhouse-cloud--local-puppygraph) - Cloud + local combination

### Customer 360 Data Pipeline
![Data Pipeline Diagram](./system-overview.md#customer-360-data-pipeline) - Generation to analysis flow

### Customer 360 ER Diagram
![ER Diagram](./data-model.md#er-diagram) - Entity relationships for Customer360

### Fraud Detection ER Diagram
![ER Diagram](./data-model.md#er-diagram-1) - Entity relationships for fraud detection

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| OLAP Database | ClickHouse | Analytical queries and storage |
| Graph Engine | PuppyGraph | Graph pattern matching |
| Query Languages | SQL + Cypher | Analytics and graph patterns |
| Containerization | Docker | Deployment and isolation |
| Orchestration | Docker Compose | Multi-container management |
| Data Format | Parquet | Efficient columnar storage |
| Python Libraries | clickhouse-driver, neo4j, pandas | Integration and processing |
| Frontend | Streamlit | Interactive dashboard |

---

## Performance Metrics

### ClickHouse Query Performance
- Aggregation queries: 10ms - 1s
- Multi-table joins: 100ms - 5s
- Full table scans: <1s for OLAP workloads

### PuppyGraph Traversal Performance
- Single-hop traversal: <10ms
- 2-3 hop patterns: <100ms
- Deep traversals (4+ hops): <500ms

### Data Ingestion Performance
- Small scale (100K records): 5 minutes
- Medium scale (1M records): 30 minutes
- Large scale (10M records): 2-3 hours

---

## Scalability Path

| Stage | Customers | Database | PuppyGraph | Infrastructure |
|-------|-----------|----------|-----------|-----------------|
| Development | 100K | Local ClickHouse | Local Container | Laptop/Desktop |
| Testing | 1M | Local ClickHouse | Local Container | Workstation (8GB+ RAM) |
| Demo | 10M | Hybrid (Cloud) | Local Container | Cloud + Local |
| Production | 100M+ | Cloud Cluster | Cloud Deployment | Enterprise Infrastructure |

---

## Configuration Reference

### Environment Variables

**ClickHouse:**
```
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9440
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=password
CLICKHOUSE_DATABASE=customer360
```

**PuppyGraph:**
```
PUPPYGRAPH_URI=bolt://localhost:7687
PUPPYGRAPH_USER=neo4j
PUPPYGRAPH_PASSWORD=password
```

**Data Generation:**
```
CUSTOMERS_SCALE=100K
BATCH_SIZE=10000
RANDOM_SEED=42
COMPRESSION=snappy
```

---

## Common Tasks

### Deploy Local Environment
```bash
make local                 # Start Docker containers
make generate-local        # Generate test data
make status               # Verify deployment
```

### Deploy Hybrid Environment
```bash
make hybrid                # Start local PuppyGraph
make generate-hybrid       # Generate data for cloud
```

### Access Interfaces
- PuppyGraph Web UI: http://localhost:8081
- ClickHouse HTTP: http://localhost:8123

### Common Queries

**Customer 360 - SQL:**
```sql
SELECT segment, COUNT(*) as customers, AVG(ltv) as avg_ltv
FROM customers GROUP BY segment ORDER BY avg_ltv DESC
```

**Customer 360 - Cypher:**
```cypher
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
RETURN c.name, COUNT(p) as products_purchased ORDER BY products_purchased DESC
```

**Fraud Detection - Cypher:**
```cypher
MATCH (c1:Customer)-[:SHARES_EMAIL|SHARES_PHONE|SHARES_ADDRESS]-(c2:Customer)
RETURN c1, c2, COUNT(*) as shared_attributes ORDER BY shared_attributes DESC
```

---

## Document Versions

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-11-22 | Initial comprehensive documentation with mermaid diagrams |

---

## Related Documentation

- [Deployment Guide](../deployments/) - Detailed setup instructions
- [Query Examples](../demos/) - Use case-specific queries
- [Performance Benchmarks](../performance/) - Benchmark results and comparisons
