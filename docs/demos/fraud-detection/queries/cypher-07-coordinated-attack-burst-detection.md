# 7. Coordinated Attack Pattern Detection

## Fraud Pattern

**Pattern Type:** Burst Activity / Coordinated Fraud Attack
**Graph Algorithm:** Temporal Aggregation with Star Pattern Matching
**Detection Advantage:** Detects when multiple accounts simultaneously attack a single target - credential stuffing, DDoS, account takeover
**Complexity:** O(n * m) where n = target accounts, m = attacker accounts

## Business Context

**Difficulty:** Intermediate
**Use Case:** Account Takeover Detection / Credential Stuffing / DDoS Attack / Coordinated Fraud
**Graph Advantage:** Coordinated attacks show as burst patterns: many accounts targeting one account simultaneously. Graph databases aggregate temporal patterns in real-time, while SQL requires complex window functions that are slow and error-prone.

## The Query

```cypher
// 7. Detect coordinated attack patterns (burst activity)
MATCH (a:Account)-[t:TRANSACTION]->(target:Account)
WHERE t.timestamp > datetime() - duration('PT1H')  // Last hour
WITH target, collect({account: a.account_id, amount: t.amount, timestamp: t.timestamp}) as attackers,
     count(t) as attack_count, sum(t.amount) as total_attack_amount
WHERE attack_count >= 10  // Multiple attackers
AND size([x IN attackers WHERE x.amount > 1000]) >= 5  // High value attacks
MATCH (target)-[:OWNED_BY]->(victim:Customer)
RETURN target.account_id, victim.name, attack_count, total_attack_amount,
       attackers[0..5] as sample_attackers  // Show first 5 attackers
ORDER BY attack_count DESC, total_attack_amount DESC;
```

## Graph Pattern Visualization

```
Coordinated Attack (Star Pattern):

              [Attacker 1] --$1500--> [TARGET ACCOUNT]
              [Attacker 2] --$2000--> [Victim: John Doe]
              [Attacker 3] --$1800--> [Attack Count: 25]
                    ...                    ^
              [Attacker 10] --$1200--------|

All within 1 hour = Coordinated attack (credential stuffing, account takeover)
```

## Expected Results

### Sample Output

| target_account | victim_name | attack_count | total_attack_amount | sample_attackers |
|---------------|-------------|-------------|-------------------|-----------------|
| ACC_VICTIM1 | John Doe | 45 | 67,500 | [{account: ACC_ATK1, amount: 1500, timestamp: 2025-11-22T14:05}, ...] |
| ACC_VICTIM2 | Jane Smith | 32 | 48,000 | [{account: ACC_ATK5, amount: 2000, timestamp: 2025-11-22T14:12}, ...] |

### Execution Metrics
- **Status:** Mock mode
- **Expected Time:** 100-300ms (real-time detection)
- **Temporal Window:** Last 1 hour (adjustable)
- **Attacks Expected:** 10-20 coordinated attacks per day

## Understanding the Results

### For Beginners

**What is a Coordinated Attack?**

Criminals use botnets or stolen credentials to simultaneously attack accounts. Examples:
1. **Credential Stuffing:** Test 10,000 stolen passwords against one account
2. **Account Takeover:** Multiple devices log into victim's account simultaneously
3. **DDoS-style Fraud:** Flood target with transactions to overwhelm fraud detection

**Graph Clue:** Many accounts -> One target within minutes = Attack

### Technical Deep Dive

**Algorithm:**

1. **Temporal Filter:** `WHERE t.timestamp > datetime() - duration('PT1H')` (last hour only)
2. **Star Pattern Matching:** `(a:Account)-[t]->(target:Account)` (many -> one)
3. **Aggregation:** Collect all attackers, count transactions, sum amounts
4. **Threshold Filter:** >= 10 attackers, >= 5 high-value transactions

**Why SQL is Adequate But Slower:**

```sql
-- SQL can do this with window functions
SELECT
  target_account,
  COUNT(DISTINCT from_account) as attack_count,
  SUM(amount) as total_amount,
  JSON_AGG(JSON_BUILD_OBJECT('account', from_account, 'amount', amount, 'timestamp', timestamp) LIMIT 5) as sample
FROM transactions
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY target_account
HAVING COUNT(DISTINCT from_account) >= 10
  AND COUNT(CASE WHEN amount > 1000 THEN 1 END) >= 5
ORDER BY attack_count DESC;
```

**Graph Advantage:** 2-5x faster due to relationship indexes, cleaner syntax

## Try It Yourself

```cypher
// Real-time monitoring (run every 5 minutes)
MATCH (a:Account)-[t:TRANSACTION]->(target:Account)
WHERE t.timestamp > datetime() - duration('PT5M')
WITH target, count(DISTINCT a) as attacker_count, collect(a.account_id) as attackers
WHERE attacker_count >= 5
RETURN target.account_id, attacker_count, attackers;
```
