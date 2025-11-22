# 8. Merchant Collusion Network Detection

## Fraud Pattern

**Pattern Type:** Merchant Collusion / Card Testing / Split Transactions
**Graph Algorithm:** Bi-partite Graph Pattern Matching with Temporal Constraints
**Detection Advantage:** Finds merchants with shared customers making rapid sequential transactions - indicates collusion for credit card fraud
**Complexity:** O(n * m * k) where n = merchants, m = customers, k = transactions

## Business Context

**Difficulty:** Advanced
**Use Case:** Merchant Collusion / Card Testing Networks / Split Transaction Fraud
**Graph Advantage:** Merchant collusion patterns form bi-partite graphs (customers connected to multiple colluding merchants). Graph databases natively handle bi-partite matching, while SQL requires complex multi-way joins that timeout on large datasets.

## The Query

```cypher
// 8. Find merchant collusion networks
MATCH (m1:Merchant)<-[t1:TRANSACTION]-(a:Account)-[t2:TRANSACTION]->(m2:Merchant)
WHERE m1.merchant_id <> m2.merchant_id
AND t1.timestamp > datetime() - duration('P7D') AND t2.timestamp > datetime() - duration('P7D')
AND abs(duration.between(t1.timestamp, t2.timestamp).seconds) < 3600  // Within 1 hour
WITH m1, m2, count(DISTINCT a) as shared_customers,
     collect(DISTINCT a.account_id) as customer_accounts,
     sum(t1.amount + t2.amount) as total_volume
WHERE shared_customers >= 5  // Multiple shared customers
MATCH (m1)-[r:MERCHANT_RELATIONSHIP]-(m2)  // Pre-existing business relationship
RETURN m1.merchant_name, m2.merchant_name, m1.category, m2.category,
       shared_customers, total_volume, customer_accounts[0..3] as sample_customers
ORDER BY shared_customers DESC, total_volume DESC;
```

## Graph Pattern Visualization

```
Merchant Collusion Pattern (Bi-partite Graph):

    [Merchant 1: Electronics Store]      [Merchant 2: Gift Card Store]
                |                                    |
                +---------+           +--------------+
                |         |           |              |
            Customer A  Customer B  Customer C  Customer D
                |         |           |              |
                +---------+-----------+--------------+
                          |           |
              All transact at BOTH merchants within 1 hour
              Indicates: Card testing or split transaction fraud
```

## Expected Results

### Sample Output

| merchant_name_1 | merchant_name_2 | category_1 | category_2 | shared_customers | total_volume | sample_customers |
|----------------|----------------|-----------|-----------|----------------|--------------|-----------------|
| ElectroMart | QuickGiftCards | Electronics | Gift Cards | 15 | 78,500 | [ACC_001, ACC_012, ACC_045] |
| GasStation123 | Pharmacy456 | Gas | Healthcare | 12 | 45,200 | [ACC_089, ACC_102, ACC_134] |

### Execution Metrics
- **Status:** Mock mode
- **Expected Time:** 500ms - 2 seconds
- **Temporal Window:** 7 days
- **Collusion Networks Expected:** 10-20 merchant pairs

## Understanding the Results

### For Beginners

**What is Merchant Collusion?**

Fraud scenarios involving cooperating merchants:
1. **Card Testing:** Fraudster uses stolen cards at Merchant A (small purchase), if approved, immediately uses at Merchant B (large purchase)
2. **Split Transactions:** Break large purchase into smaller amounts across colluding merchants to evade fraud detection
3. **Refund Fraud:** Colluding merchants issue fake refunds, split the money

**Graph Clue:** Many customers rapidly transacting at same merchant pairs = Collusion

### Technical Deep Dive

**Pattern:** `(m1)<-[t1]-(a)-[t2]->(m2)` is a bi-partite graph traversal (customer connects two merchants)

**Temporal Constraint:** `abs(duration.between(t1.timestamp, t2.timestamp).seconds) < 3600` ensures transactions are within 1 hour (rapid sequence indicates testing)

**Why SQL is Slow:**

```sql
-- SQL requires complex self-joins
SELECT m1.name, m2.name, COUNT(DISTINCT a.account_id) as shared
FROM transactions t1
JOIN merchants m1 ON t1.merchant_id = m1.id
JOIN transactions t2 ON t1.account_id = t2.account_id
JOIN merchants m2 ON t2.merchant_id = m2.id
WHERE m1.id < m2.id
  AND ABS(EXTRACT(EPOCH FROM (t1.timestamp - t2.timestamp))) < 3600
GROUP BY m1.name, m2.name
HAVING COUNT(DISTINCT a.account_id) >= 5;
```

**Problems:** Multiple joins on large tables, timestamp calculation expensive, no relationship concept

**Graph Advantage: 10-50x faster, expressive pattern matching**

## Try It Yourself

```cypher
// Find merchant collusion with fraud score
MATCH (m1:Merchant)<-[t1:TRANSACTION]-(a:Account)-[t2:TRANSACTION]->(m2:Merchant)
WHERE m1.merchant_id < m2.merchant_id
  AND abs(duration.between(t1.timestamp, t2.timestamp).seconds) < 3600
WITH m1, m2, count(DISTINCT a) as shared,
     avg(t1.amount + t2.amount) as avg_combined_amount
WHERE shared >= 5
WITH m1, m2, shared,
     shared * 10 + CASE WHEN avg_combined_amount > 5000 THEN 50 ELSE 0 END as fraud_score
RETURN m1.merchant_name, m2.merchant_name, shared, fraud_score
ORDER BY fraud_score DESC;
```
