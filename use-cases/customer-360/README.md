# Customer 360 Use Case

Unified customer analytics using SQL (ClickHouse) and Cypher (PuppyGraph) queries on the same data.

## What It Does

- **SQL Analytics**: Customer segmentation, transaction metrics, cohort analysis
- **Cypher Analytics**: Product recommendations, customer similarity, purchase patterns
- **Zero-ETL**: Both query types read from the same ClickHouse tables

## Data Model

**Tables**: customers, products, transactions, interactions

**Graph Relationships**: Customer → PURCHASED → Product

## Documentation

- **[Complete Demo Guide](../../docs/demos/customer-360/README.md)** - Full walkthrough with queries
- **[SQL Queries (15)](../../docs/demos/customer-360/SQL-QUERIES.md)** - All SQL queries with results
- **[Cypher Queries (20)](../../docs/demos/customer-360/CYPHER-QUERIES.md)** - All graph queries

## Quick Start

```bash
# Generate data
docker exec -it clickhouse-local bash -c \
  "cd /app && python3 generate_data.py --use-case customer360 --customers 100000"

# Run SQL query
docker exec -it clickhouse-local clickhouse-client
SELECT segment, COUNT(*) FROM customers GROUP BY segment;

# Run Cypher query (PuppyGraph UI: http://localhost:8081)
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
RETURN c.segment, COUNT(p) as products;
```

## Data Scales

| Scale | Customers | Transactions |
|-------|-----------|--------------|
| Small | 100K | ~800K |
| Medium | 1M | ~8M |
| Large | 10M | ~100M |

## Query Examples

**SQL** - Customer segments:
```sql
SELECT segment, COUNT(*) as count, AVG(lifetime_value) as avg_ltv
FROM customers
GROUP BY segment
ORDER BY avg_ltv DESC;
```

**Cypher** - Product recommendations:
```cypher
MATCH (target:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p1:Product)
MATCH (other:Customer)-[:PURCHASED]->(p1)
MATCH (other)-[:PURCHASED]->(p2:Product)
WHERE NOT (target)-[:PURCHASED]->(p2)
RETURN p2.name, COUNT(other) as score
ORDER BY score DESC
LIMIT 10;
```
