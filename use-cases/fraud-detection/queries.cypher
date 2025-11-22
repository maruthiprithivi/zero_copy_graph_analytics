// Fraud Detection Cypher Queries for PuppyGraph
// These queries leverage graph algorithms for superior fraud detection

// 1. Find connected components of accounts sharing devices (Account Takeover Rings)
MATCH (a1:Account)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(a2:Account)
WHERE a1.account_id <> a2.account_id
WITH d, collect(DISTINCT a1.account_id) + collect(DISTINCT a2.account_id) as connected_accounts
WHERE size(connected_accounts) >= 5  // Device used by 5+ accounts
RETURN d.device_id, d.device_fingerprint, d.location, connected_accounts, size(connected_accounts) as account_count
ORDER BY account_count DESC
LIMIT 10;

// 2. Detect money laundering cycles using graph traversal
MATCH cycle = (a1:Account)-[:TRANSACTION*3..6]->(a1)
WHERE ALL(r IN relationships(cycle) WHERE r.amount > 1000 AND r.timestamp > datetime() - duration('P7D'))
WITH cycle,
     [r IN relationships(cycle) | r.amount] as amounts,
     [r IN relationships(cycle) | r.timestamp] as timestamps
WHERE reduce(total = 0, amount IN amounts | total + amount) > 50000  // High value cycles
RETURN nodes(cycle) as accounts, amounts, timestamps,
       reduce(total = 0, amount IN amounts | total + amount) as total_amount,
       size(relationships(cycle)) as cycle_length
ORDER BY total_amount DESC, cycle_length ASC;

// 3. Find fraud rings using community detection
MATCH (a1:Account)-[t:TRANSACTION]->(a2:Account)
WHERE t.timestamp > datetime() - duration('P30D')
WITH a1, a2, count(t) as transaction_count, sum(t.amount) as total_amount
WHERE transaction_count >= 3 OR total_amount > 25000
// Use Louvain algorithm for community detection
CALL gds.louvain.stream({
  nodeProjection: ['Account'],
  relationshipProjection: {
    CONNECTED: {
      type: 'TRANSACTION',
      properties: ['amount', 'transaction_count']
    }
  },
  relationshipWeightProperty: 'transaction_count'
})
YIELD nodeId, communityId
MATCH (a:Account) WHERE id(a) = nodeId
WITH communityId, collect(a.account_id) as community_accounts, count(a) as community_size
WHERE community_size >= 5 AND community_size <= 50  // Suspicious community size
RETURN communityId, community_accounts, community_size
ORDER BY community_size DESC;

// 4. Calculate PageRank to identify key accounts in fraud networks
MATCH (a:Account)-[t:TRANSACTION]->(a2:Account)
WHERE t.timestamp > datetime() - duration('P30D') AND t.amount > 5000
CALL gds.pageRank.stream({
  nodeProjection: ['Account'],
  relationshipProjection: 'TRANSACTION',
  relationshipWeightProperty: 'amount',
  dampingFactor: 0.85,
  maxIterations: 20
})
YIELD nodeId, score
MATCH (a:Account) WHERE id(a) = nodeId
MATCH (a)-[t:TRANSACTION]->(other:Account)
WHERE t.timestamp > datetime() - duration('P30D')
WITH a, score, count(t) as outgoing_transactions, sum(t.amount) as outgoing_amount
WHERE outgoing_transactions >= 10 AND score > 0.01  // High PageRank accounts
RETURN a.account_id, a.customer_id, score, outgoing_transactions, outgoing_amount
ORDER BY score DESC
LIMIT 20;

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

// 6. Find synthetic identity clusters using similarity
MATCH (c1:Customer), (c2:Customer)
WHERE c1.customer_id < c2.customer_id  // Avoid duplicates
AND (
  c1.ssn_hash = c2.ssn_hash OR
  c1.phone = c2.phone OR
  c1.address = c2.address OR
  levenshtein(c1.name, c2.name) <= 2  // Similar names
)
AND (c1.created_at > datetime() - duration('P90D') OR c2.created_at > datetime() - duration('P90D'))
MATCH (c1)-[:OWNS]->(a1:Account), (c2)-[:OWNS]->(a2:Account)
WITH c1, c2, collect(a1.account_id) as accounts1, collect(a2.account_id) as accounts2,
     CASE
       WHEN c1.ssn_hash = c2.ssn_hash THEN 'SSN'
       WHEN c1.phone = c2.phone THEN 'PHONE'
       WHEN c1.address = c2.address THEN 'ADDRESS'
       ELSE 'NAME'
     END as similarity_type
RETURN c1.customer_id, c2.customer_id, c1.name, c2.name,
       similarity_type, accounts1, accounts2
ORDER BY similarity_type, c1.created_at DESC;

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

// 9. Trace money flow paths with temporal constraints
MATCH path = (source:Account)-[:TRANSACTION*1..5]->(sink:Account)
WHERE source.account_id = 'suspicious_account_123'  // Starting point
AND ALL(r IN relationships(path) WHERE
  r.timestamp > datetime() - duration('P3D') AND
  r.amount > 5000
)
// Ensure temporal ordering
AND ALL(i IN range(0, size(relationships(path))-2) WHERE
  relationships(path)[i].timestamp <= relationships(path)[i+1].timestamp
)
WITH path,
     [r IN relationships(path) | r.amount] as amounts,
     [r IN relationships(path) | r.timestamp] as timestamps,
     last(nodes(path)) as final_destination
WHERE reduce(total = 0, amount IN amounts | total + amount) > 50000
MATCH (final_destination)-[:OWNED_BY]->(end_customer:Customer)
RETURN nodes(path) as money_trail, amounts, timestamps,
       reduce(total = 0, amount IN amounts | total + amount) as total_amount,
       end_customer.name as final_recipient
ORDER BY total_amount DESC, size(relationships(path)) ASC;

// 10. Real-time fraud scoring using graph features
MATCH (a:Account {account_id: $account_id})
OPTIONAL MATCH (a)-[recent:TRANSACTION]->(others:Account)
WHERE recent.timestamp > datetime() - duration('PT24H')
WITH a, count(recent) as recent_transactions,
     count(DISTINCT others) as unique_recipients_24h,
     sum(recent.amount) as amount_24h,
     collect(DISTINCT others.account_id) as recent_recipients

// Calculate network degree
OPTIONAL MATCH (a)-[:TRANSACTION]-(connected:Account)
WITH a, recent_transactions, unique_recipients_24h, amount_24h, recent_recipients,
     count(DISTINCT connected) as total_network_degree

// Find if part of suspicious clusters
OPTIONAL MATCH (a)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(other_accounts:Account)
WHERE other_accounts.account_id <> a.account_id
WITH a, recent_transactions, unique_recipients_24h, amount_24h, recent_recipients,
     total_network_degree, count(DISTINCT other_accounts) as device_shared_accounts

// Calculate risk score (0-100)
WITH a, recent_transactions, unique_recipients_24h, amount_24h, recent_recipients,
     total_network_degree, device_shared_accounts,
     // Risk factors weighted scoring
     CASE WHEN recent_transactions > 50 THEN 25 ELSE recent_transactions * 0.5 END +
     CASE WHEN unique_recipients_24h > 20 THEN 20 ELSE unique_recipients_24h END +
     CASE WHEN amount_24h > 100000 THEN 30 ELSE amount_24h / 3333.33 END +
     CASE WHEN device_shared_accounts > 5 THEN 25 ELSE device_shared_accounts * 5 END
     as raw_risk_score

RETURN a.account_id,
       CASE WHEN raw_risk_score > 100 THEN 100 ELSE toInteger(raw_risk_score) END as risk_score,
       recent_transactions, unique_recipients_24h, amount_24h,
       total_network_degree, device_shared_accounts,
       CASE
         WHEN raw_risk_score >= 80 THEN 'CRITICAL'
         WHEN raw_risk_score >= 60 THEN 'HIGH'
         WHEN raw_risk_score >= 40 THEN 'MEDIUM'
         WHEN raw_risk_score >= 20 THEN 'LOW'
         ELSE 'MINIMAL'
       END as risk_level;