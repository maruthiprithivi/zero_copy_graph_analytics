# Fraud Detection Use Case

Network analysis for detecting fraud patterns using SQL and Cypher queries on financial transaction data.

## What It Does

- **SQL Pattern Detection**: Shared devices, transaction chains, synthetic identities
- **Cypher Network Analysis**: Account takeover rings, money laundering cycles, fraud networks
- **Zero-ETL**: Graph queries run directly on ClickHouse data

## Data Model

**Tables**: fraud_customers, fraud_accounts, fraud_transactions, fraud_devices, fraud_merchants

**Relationship Tables**: account_takeover_device_account_usage, money_laundering_account_relationships

**Graph Relationships**: Account → TRANSACTED_WITH → Account, Device → ACCESSED → Account

## Documentation

- **[Complete Investigation Guide](../../docs/demos/fraud-detection/README.md)** - Full fraud detection walkthrough
- **[SQL Detection Queries (10)](../../docs/demos/fraud-detection/SQL-QUERIES.md)** - Pattern detection queries
- **[Cypher Network Queries (10)](../../docs/demos/fraud-detection/CYPHER-QUERIES.md)** - Graph traversal queries

## Fraud Patterns Detected

1. **Account Takeover**: Single device accessing multiple accounts
2. **Money Laundering**: Circular money flows through account networks
3. **Credit Card Fraud**: Multiple cards at same merchants
4. **Synthetic Identity**: Accounts with similar PII patterns
5. **Merchant Collusion**: Connected merchant networks

## Quick Start

```bash
# Generate fraud data
docker exec -it clickhouse-local bash -c \
  "cd /app && python3 generate_data.py --use-case fraud --customers 100000"

# SQL pattern detection
docker exec -it clickhouse-local clickhouse-client
SELECT device_id, COUNT(DISTINCT account_id) as accounts
FROM account_takeover_device_account_usage
GROUP BY device_id
HAVING accounts > 5;

# Cypher network analysis (PuppyGraph UI: http://localhost:8081)
MATCH path = (a1:Account)-[:TRANSACTED_WITH*3..5]->(a1)
WHERE ALL(r IN relationships(path) WHERE r.amount > 9000)
RETURN path LIMIT 10;
```

## Query Examples

**SQL** - Find shared devices (account takeover):
```sql
SELECT
    device_id,
    COUNT(DISTINCT account_id) as account_count,
    SUM(login_count) as total_logins
FROM account_takeover_device_account_usage
GROUP BY device_id
HAVING account_count > 5
ORDER BY account_count DESC;
```

**Cypher** - Detect money laundering cycles:
```cypher
MATCH path = (a1:Account)-[:TRANSACTED_WITH*3..5]->(a1)
WHERE ALL(r IN relationships(path) WHERE r.amount > 9000)
  AND length(path) >= 3
RETURN
    [n IN nodes(path) | n.account_id] as cycle,
    length(path) as hops,
    reduce(total = 0, r IN relationships(path) | total + r.amount) as total_amount
LIMIT 50;
```
