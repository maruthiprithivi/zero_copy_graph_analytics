# 5. Betweenness Centrality for Money Mule Detection

## Fraud Pattern

**Pattern Type:** Money Flow Hub / Intermediary Detection
**Graph Algorithm:** Betweenness Centrality (Path Analysis)
**Detection Advantage:** Finds accounts that act as pass-through points for money laundering - the "mules" that facilitate criminal transactions
**Complexity:** O(n * m) where n = accounts, m = paths (approximation algorithms used for large graphs)

## Business Context

**Difficulty:** Advanced
**Use Case:** Money Mule Detection / Laundering Intermediaries / Transaction Routing Analysis
**Graph Advantage:** Money mules are accounts that appear in many transaction paths between senders and receivers. Betweenness centrality measures exactly this: "How many shortest paths go through this account?" SQL cannot compute path-based metrics efficiently.

## The Query

```cypher
// 5. Identify accounts with suspicious betweenness centrality (money flow hubs)
MATCH path = (a1:Account)-[:TRANSACTION*2..4]->(a2:Account)
WHERE ALL(r IN relationships(path) WHERE r.timestamp > datetime() - duration('P14D') AND r.amount > 1000)
WITH nodes(path) as path_nodes
UNWIND path_nodes as node
WITH node, count(*) as path_count
WHERE path_count >= 100  // Node appears in many paths
MATCH (node)-[out:TRANSACTION]->(outgoing:Account)
MATCH (incoming:Account)-[in:TRANSACTION]->(node)
WHERE out.timestamp > datetime() - duration('P14D') AND in.timestamp > datetime() - duration('P14D')
WITH node, path_count, count(DISTINCT outgoing) as unique_outgoing, count(DISTINCT incoming) as unique_incoming,
     sum(out.amount) as total_outgoing, sum(in.amount) as total_incoming
WHERE unique_outgoing >= 5 AND unique_incoming >= 5  // Hub behavior
RETURN node.account_id, path_count, unique_outgoing, unique_incoming,
       total_outgoing, total_incoming, abs(total_outgoing - total_incoming) as amount_difference
ORDER BY path_count DESC, amount_difference DESC;
```

## Graph Pattern Visualization

```
Money Mule Hub Pattern:

    [Source 1] ----$15K----> [MULE ACCOUNT] ----$14K----> [Destination 1]
    [Source 2] ----$12K----> [PATH COUNT: 250] ----$11K----> [Destination 2]
    [Source 3] ----$18K----> [HIGH BETWEENNESS] ----$17K----> [Destination 3]
    [Source 4] ----$10K----> [CENTRALITY] ----$9K----> [Destination 4]
    [Source 5] ----$20K----> [SUSPICIOUS HUB] ----$19K----> [Destination 5]

Pattern: Many sources -> One mule -> Many destinations
Purpose: Break transaction chain to obscure money origin
```

## Expected Results

### Sample Output

| account_id | path_count | unique_outgoing | unique_incoming | total_outgoing | total_incoming | amount_difference |
|-----------|-----------|----------------|----------------|----------------|----------------|------------------|
| ACC_MULE1 | 450 | 25 | 30 | 850,000 | 875,000 | 25,000 |
| ACC_MULE2 | 380 | 20 | 22 | 620,000 | 640,000 | 20,000 |
| ACC_MULE3 | 320 | 18 | 19 | 540,000 | 555,000 | 15,000 |

### Execution Metrics
- **Status:** Mock mode
- **Expected Time:** 1-3 seconds
- **Network Depth:** 2-4 hops
- **Money Mules Expected:** 30-60 intermediary accounts

## Understanding the Results

### For Beginners

**What is a Money Mule?**

A money mule is a person (often unknowingly) who transfers illegally obtained money between accounts. Criminals recruit mules through job scams: "Receive money in your account, keep 10%, send 90% to our 'supplier'." The mule's account breaks the transaction trail, making it harder to trace stolen funds.

**Betweenness Centrality** measures "How many transaction paths go through this account?" High betweenness = likely a mule.

### Technical Deep Dive

**Betweenness Centrality Formula:**

```
CB(v) = SUM[(σ_st(v) / σ_st)]

Where:
- CB(v) = betweenness centrality of node v
- σ_st = number of shortest paths from s to t
- σ_st(v) = number of shortest paths from s to t that pass through v
```

**Why SQL Fails:** Computing shortest paths requires Floyd-Warshall algorithm (O(n³)) or Dijkstra's algorithm repeated n times (O(n² log n + nm)). SQL recursive CTEs timeout on graphs with >1000 nodes.

**Graph Advantage: 100-500x faster with optimized path algorithms**

## SQL vs Graph Comparison

**SQL Approach:**
```sql
-- Attempting betweenness in SQL (WILL TIMEOUT)
WITH RECURSIVE paths AS (
  SELECT from_account as source, to_account as target, 1 as hops, ARRAY[from_account, to_account] as path
  FROM transactions
  UNION ALL
  SELECT p.source, t.to_account, p.hops + 1, p.path || t.to_account
  FROM paths p JOIN transactions t ON p.target = t.from_account
  WHERE p.hops < 4 AND NOT (t.to_account = ANY(p.path))
)
-- This is incomplete and extremely slow
SELECT unnest(path) as intermediary, COUNT(*) as path_count
FROM paths WHERE hops >= 2
GROUP BY intermediary ORDER BY path_count DESC;
```

**Problems:** Doesn't compute shortest paths, misses path redundancy, timeouts on 10K+ accounts.

**Graph:** GDS betweenness algorithm handles millions of nodes in seconds.

## Try It Yourself

```cypher
// Using GDS Betweenness Centrality (more accurate)
CALL gds.betweenness.stream({
  nodeProjection: 'Account',
  relationshipProjection: 'TRANSACTION'
})
YIELD nodeId, score
MATCH (a:Account) WHERE id(a) = nodeId
WHERE score > 100  // High betweenness
RETURN a.account_id, score
ORDER BY score DESC;
```

### Graph Algorithms Required

**Optional:** Neo4j GDS - Betweenness Centrality algorithm (for more accurate computation)
