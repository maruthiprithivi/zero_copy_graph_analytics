# Fraud Detection: Graph-Powered Financial Crime Prevention

## What is Graph-Based Fraud Detection?

Fraud is fundamentally a network problem. Criminals don't operate in isolation they work in rings, share stolen identities, launder money through chains of accounts, and coordinate attacks using common infrastructure. Traditional rule-based fraud systems examine transactions individually, asking questions like "Is this amount over $10,000?" While useful, this approach misses the bigger picture: the network of relationships that exposes organized fraud operations.

Graph databases revolutionize fraud detection by treating relationships as first-class data. Instead of asking "What did this account do?" they ask "Who is this account connected to?" and "How does money flow through this network?" This shift enables detection of fraud patterns that are invisible to traditional systems.

**The Power:** Detect account takeover rings (1 device accessing 500 accounts), trace money laundering cycles through 6 intermediaries both significantly faster with graph queries than traditional SQL approaches.

## Where Does This Apply?

Graph-based fraud detection transforms financial crime prevention across industries:

**Banking & Payments:** Transaction authorization, account takeover prevention, wire fraud, money laundering compliance, check kiting detection

**Insurance:** Claims fraud networks, provider collusion, identity fraud, first-party fraud detection

**E-commerce:** Account takeover prevention, payment fraud, promotion abuse, return fraud rings, fake review networks

**Cryptocurrency:** Mixer/tumbler detection, ICO scam networks, exchange fraud, ransomware tracing, sanctions evasion

**Healthcare:** Billing fraud networks, provider kickbacks, prescription drug diversion, identity theft, phantom billing

## When to Deploy Graph Fraud Detection

**Real-Time Authorization:** Calculate multi-factor fraud risk using network context (device sharing, velocity, network degree) for payment decisions

**Batch Investigation:** Run graph algorithms overnight (community detection, PageRank, cycle detection) to discover fraud rings

**Regulatory Compliance:** Automate SAR/CTR reporting by tracing transaction chains and mapping money mule networks

**Forensic Investigation:** Visualize full networks and trace money flows for case investigations and law enforcement cooperation

**Network Mapping:** Build comprehensive fraud intelligence by mapping the criminal landscape for proactive prevention

## Why Graph Excels at Fraud Detection

The fraud network problem exposes a fundamental limitation of relational databases.

**SQL Complexity: O(n^3) - Cubic Growth**
- Multi-hop relationship queries require multiple self-joins
- Comparing every transaction to every other transaction becomes infeasible at scale
- Recursive CTEs hit limits with complex patterns

**Graph Complexity: O(n) - Linear Growth**
- Graph traversal follows edges directly using index-free adjacency
- Efficient exploration of multi-hop relationships
- Significant performance improvements for relationship-based queries

**Three fraud detection patterns difficult or impossible in SQL:**
1. Fraud ring community detection (requires Louvain algorithm - no SQL equivalent)
2. Network centrality analysis (PageRank, betweenness - requires iterative graph algorithms)
3. Deep cycle detection (recursive CTEs hit limits, miss complex laundering schemes)

## How to Run

### Prerequisites
Ensure you have completed the setup from the [root README](../../README.md):
```bash
# Local deployment
make local
make generate-local

# OR Hybrid deployment
make hybrid
make generate-hybrid
```

### Running SQL Queries

**Option 1: ClickHouse Client (Local)**
```bash
# Connect to ClickHouse
docker exec -it clickhouse-local clickhouse-client --password=clickhouse123

# Switch to fraud_detection database
USE fraud_detection;

# Run queries from queries.sql file
# Copy-paste queries from use-cases/fraud-detection/queries.sql
```

**Option 2: ClickHouse Client (Hybrid)**
```bash
# Connect to ClickHouse Cloud
clickhouse-client \
  --host=your-instance.clickhouse.cloud \
  --port=9440 \
  --user=default \
  --password=your-password \
  --secure

# Switch to fraud_detection database
USE fraud_detection;

# Run queries from queries.sql file
```

### Running Cypher Queries

**PuppyGraph Web UI**
1. Open http://localhost:8081
2. Navigate to Query Console
3. Copy-paste queries from `use-cases/fraud-detection/queries.cypher`
4. Execute and view results

## Dataset Overview

**Scale**: 1.29M records simulating a realistic financial institution

**Entities:**
- **100K Customers** (3% fraudulent, 97% legitimate)
  - 3,000 fraudulent customer accounts
  - 97,000 legitimate customers
  - Each customer has fraud_score, kyc_verified, pep_flagged attributes

- **170K Accounts** (5% involved in fraud)
  - 1 account per customer on average
  - 8,500 accounts involved in fraud schemes
  - Account types: checking, savings, credit, investment

- **50K Devices** (10% suspicious)
  - Device fingerprints (browser, OS, screen resolution)
  - Geographic locations (city, state, country)
  - 5,000 devices flagged as suspicious

- **10K Merchants** (8% fraudulent)
  - Merchant categories (retail, restaurant, online, gas, etc.)
  - 800 merchants flagged as high-risk or fraudulent
  - Risk ratings from 0 (safe) to 100 (confirmed fraud)

- **1M Transactions** over 90 days
  - 100K fraudulent transactions (10%)
  - 900K legitimate transactions (90%)
  - Transaction amounts: $1-$100,000
  - Timestamps spanning 90-day period
  - is_flagged boolean for fraud identification

**Embedded Fraud Scenarios (5 Types):**

1. **Account Takeover Ring (390 accounts)**
   - Pattern: Star topology - 1 device accessing many compromised accounts
   - Detection: 25 devices each accessing 15-20 accounts
   - Indicators: High failed login attempts (147 per device), rapid account switching

2. **Money Laundering Network (390 accounts)**
   - Pattern: Circular transfer patterns through intermediary accounts
   - Detection: 3-8 hop cycles moving $12.8M total
   - Indicators: Round-number transactions, rapid sequential transfers, layering

3. **Credit Card Fraud Cluster (390 accounts)**
   - Pattern: Bipartite network - stolen cards used at specific merchants
   - Detection: Same card used in different geographic locations simultaneously
   - Indicators: High-velocity transactions, geographic impossibility, merchant testing patterns

4. **Synthetic Identity Fraud (390 accounts)**
   - Pattern: Clique - accounts sharing stolen PII (SSN, phone, address)
   - Detection: Accounts with shared SSN hashes, phones, or addresses
   - Indicators: Similar account opening dates, shared drop addresses, coordinated activity

5. **Merchant Collusion Network (390 accounts)**
   - Pattern: Dense subgraph - colluding merchants and account holders
   - Detection: Merchants with unusually high approval rates (>95%)
   - Indicators: Coordinated transaction timing, card testing, rapid sequential payments

**Dataset Characteristics:**
- SQL Queries: 10 analytical queries for pattern detection
- Cypher Queries: 10 graph queries for network analysis and fraud ring detection
- Storage: ~3GB uncompressed, ~1GB with Parquet Snappy compression

## SQL Queries (10 Total)

All queries are in `queries.sql` file. Execute them in ClickHouse.

### Query 1: Find Accounts with Shared Devices
- **Purpose:** Account takeover detection - identify devices accessing multiple accounts
- **Use Case:** Credential stuffing attacks, compromised device detection
- **Example Result:** device_ato_001 accessed 47 accounts with 147 failed login attempts

### Query 2: Detect High-Velocity Transactions
- **Purpose:** Velocity fraud detection - rapid transaction patterns
- **Use Case:** Stolen card fraud, automated attacks
- **Example Result:** 15 accounts with 10+ transactions in 1 hour, $50K+ total

### Query 3: Find Suspicious Round-Number Transactions
- **Purpose:** Structuring detection - avoiding reporting thresholds
- **Use Case:** Money laundering, smurfing schemes
- **Example Result:** 340 account pairs with 3+ round-number transactions ($10K, $25K, $50K)

### Query 4: Identify Impossible Geographic Transactions
- **Purpose:** Geographic impossibility detection
- **Use Case:** Cloned card detection, account takeover
- **Example Result:** 23 accounts with transactions in different cities within short time spans

### Query 5: Find Merchants with Unusually High Approval Rates
- **Purpose:** Merchant fraud detection
- **Use Case:** Colluding merchants, card testing operations
- **Example Result:** 12 merchants with >95% approval rate and 100+ transactions

### Query 6: Detect Similar Customer Information (Synthetic Identity)
- **Purpose:** Synthetic identity detection via shared PII
- **Use Case:** Fake identity rings, stolen SSN usage
- **Example Result:** 56 customer pairs sharing SSN, phone, or address

### Query 7: Find Transaction Chains (Money Laundering)
- **Purpose:** Money laundering detection through transaction chains
- **Use Case:** Layering schemes, money mule networks
- **Example Result:** 8 chains of 3+ transactions totaling $150K+

### Query 8: Calculate Account Risk Scores
- **Purpose:** Holistic risk scoring using multiple factors
- **Use Case:** Real-time fraud scoring, account monitoring
- **Example Result:** Top 100 accounts with risk scores 80-100 (critical/high risk)

### Query 9: Detect Burst Activity Patterns
- **Purpose:** Abnormal activity spike detection
- **Use Case:** Account takeover, automated fraud
- **Example Result:** 19 accounts with burst activity (3+ standard deviations above normal)

### Query 10: Find Dormant Accounts Suddenly Active
- **Purpose:** Account takeover detection via dormancy patterns
- **Use Case:** Compromised accounts, social engineering
- **Example Result:** 12 accounts dormant 90+ days now highly active

## Cypher Queries (10 Total)

All queries are in `queries.cypher` file. Execute them in PuppyGraph Web UI.

### Query 1: Find Account Takeover Rings (Connected Components)
- **Purpose:** Discover full account takeover networks
- **Graph Algorithm:** Connected component analysis
- **Use Case:** Map entire credential stuffing operation in single query
- **Example Result:** 5 takeover rings, largest has 47 accounts via 1 device

### Query 2: Detect Money Laundering Cycles
- **Purpose:** Find circular money flows (3-6 hops)
- **Graph Algorithm:** Cycle detection with temporal constraints
- **Use Case:** SAR filing, money mule network mapping
- **Example Result:** 12 cycles totaling $50K+, 3-6 accounts per cycle

### Query 3: Fraud Ring Community Detection
- **Purpose:** Discover organized fraud communities
- **Graph Algorithm:** Louvain community detection
- **Use Case:** Strategic fraud intelligence, ring mapping
- **Example Result:** 8 suspicious communities, 5-50 accounts each

### Query 4: PageRank for Key Account Identification
- **Purpose:** Identify central accounts in fraud networks (money flow hubs)
- **Graph Algorithm:** PageRank with transaction weights
- **Use Case:** Ringleader identification, network disruption
- **Example Result:** Top 20 accounts by PageRank (network hubs)

### Query 5: Betweenness Centrality (Money Flow Hubs)
- **Purpose:** Find accounts that serve as transaction intermediaries
- **Graph Algorithm:** Betweenness centrality approximation
- **Use Case:** Money mule detection, intermediary identification
- **Example Result:** 15 accounts appearing in 100+ transaction paths

### Query 6: Find Synthetic Identity Clusters
- **Purpose:** Detect fake identity rings via shared PII
- **Graph Algorithm:** Similarity clustering (Levenshtein distance)
- **Use Case:** Synthetic identity fraud detection
- **Example Result:** 25 clusters with shared SSN/phone/address

### Query 7: Detect Coordinated Attack Patterns
- **Purpose:** Identify burst attacks on target accounts
- **Graph Algorithm:** Temporal network analysis
- **Use Case:** DDoS-style fraud attacks, coordinated schemes
- **Example Result:** 4 target accounts with 10+ attackers in 1 hour

### Query 8: Find Merchant Collusion Networks
- **Purpose:** Detect merchant fraud rings
- **Graph Algorithm:** Bipartite network analysis
- **Use Case:** Merchant collusion, card testing operations
- **Example Result:** 6 merchant pairs with 5+ shared customers in 1 hour

### Query 9: Trace Money Flow Paths (Temporal Constraints)
- **Purpose:** Follow money from source to destination
- **Graph Algorithm:** Variable-length path matching with temporal ordering
- **Use Case:** Forensic investigation, fund tracing
- **Example Result:** $125K traced through 5 intermediaries in 3 days

### Query 10: Real-Time Fraud Scoring Using Graph Features
- **Purpose:** Calculate fraud risk score using network context
- **Graph Algorithm:** Multi-factor graph feature extraction
- **Use Case:** Real-time transaction authorization
- **Example Result:** Risk scores 0-100 with breakdown (velocity, network, devices)

## Fraud Scenarios Embedded in Dataset

### Scenario 1: Account Takeover Ring (390 accounts)
**Pattern:** Star topology - devices accessing multiple compromised accounts
**Detection:** SQL Query 1 (device patterns), Cypher Query 1 (full network mapping)
**Key Indicators:** 25 devices accessing 15-20 accounts each, high failed logins, rapid account switching

### Scenario 2: Money Laundering Network (390 accounts)
**Pattern:** Circular transaction flows through intermediary accounts
**Detection:** SQL Query 7 (transaction chains), Cypher Query 2 (cycle detection)
**Key Indicators:** Round-number transactions, rapid transfers, 3-8 hop cycles, $12.8M total

### Scenario 3: Credit Card Fraud Cluster (390 accounts)
**Pattern:** Cloned cards used in different geographic locations simultaneously
**Detection:** SQL Query 4 (geographic impossibility), Cypher Query 8 (merchant networks)
**Key Indicators:** Same card in different cities, high-velocity testing, merchant targeting

### Scenario 4: Synthetic Identity Fraud (390 accounts)
**Pattern:** Fake identities sharing stolen PII (SSN, phone, address)
**Detection:** SQL Query 6 (shared PII), Cypher Query 6 (identity clusters)
**Key Indicators:** Shared SSN hashes, common addresses, coordinated account opening

### Scenario 5: Merchant Collusion Network (390 accounts)
**Pattern:** Colluding merchants coordinating with fraudsters
**Detection:** SQL Query 5 (approval rates), Cypher Query 8 (collusion networks)
**Key Indicators:** >95% approval rates, shared customers, coordinated timing

## Business Use Cases

### Use Case 1: Real-Time Transaction Authorization

**Goal:** Approve/decline transactions using fraud risk score

**Implementation:**
- Cypher Query 10: Calculate real-time fraud score using graph features
- Velocity (recent transaction count)
- Network degree (account connectivity)
- Device sharing (suspicious device patterns)
- Historical behavior (deviation from norm)

**Decision Logic:**
- Risk 0-20: Auto-approve
- Risk 21-60: Step-up authentication
- Risk 61-80: Manual review
- Risk 81-100: Auto-decline

**Impact:** Significant reduction in fraud losses and false positives

### Use Case 2: Daily Fraud Ring Investigation

**Goal:** Discover organized fraud networks for proactive investigation

**Analysis Flow:**
1. Run Cypher Query 3 (Community Detection) overnight
2. Identify suspicious communities (5-50 accounts, high transaction density)
3. Run Cypher Query 4 (PageRank) to find ringleaders
4. Run Cypher Query 9 (Money Flow Tracing) for each ring

**Output:** Daily report with fraud rings prioritized by impact

**Impact:** Proactive fraud ring discovery and losses prevention

### Use Case 3: SAR Filing Automation

**Goal:** Automate Suspicious Activity Report (SAR) generation for BSA/AML compliance

**Analysis Flow:**
1. Run SQL Query 7 (Transaction Chains) weekly
2. Run Cypher Query 2 (Money Laundering Cycles)
3. For flagged accounts, run Cypher Query 9 (Money Flow Tracing)
4. Generate evidence package with network visualization

**Compliance:** Automate 30-day SAR filing requirement

**Impact:** Significant reduction in SAR preparation time, maintain filing compliance

### Use Case 4: Account Takeover Prevention

**Goal:** Detect compromised accounts in real-time

**Monitoring:**
- Run SQL Query 1 periodically (shared devices)
- Alert on devices accessing 3+ accounts
- Run Cypher Query 1 for full network mapping when triggered
- Freeze accounts pending verification

**Impact:** Rapid detection and response to account takeovers

### Use Case 5: Synthetic Identity Detection

**Goal:** Identify fake identity rings during account opening

**Verification Flow:**
1. During account opening, check customer PII against existing accounts
2. Run SQL Query 6 (Synthetic Identity) for SSN/phone/address matches
3. If matches found, run Cypher Query 6 (Identity Clusters) for full network
4. Flag application for manual review if in known synthetic identity cluster

**Impact:** Significant reduction in synthetic identity fraud

## When to Use Which

**Use SQL for:**
- Periodic batch analysis and reporting
- Simple pattern detection
- Historical analysis and aggregations

**Use Cypher for:**
- Real-time fraud decisions
- Network mapping and fraud ring discovery
- Complex pattern matching across relationships
- Multi-hop traversals and cycle detection

**Combine Both for:**
- Comprehensive fraud intelligence (SQL for patterns, Cypher for networks)

## Next Steps

1. Explore the queries in `queries.sql` and `queries.cypher`
2. Modify queries to match your fraud patterns
3. Visualize fraud networks using PuppyGraph Web UI
4. Build real-time fraud scoring API using Cypher Query 10
5. Implement daily fraud ring discovery using Cypher Queries 3-4
6. Create SAR automation using SQL Query 7 + Cypher Query 2
7. Set up account takeover monitoring using SQL Query 1 + Cypher Query 1

For customer analytics use case, see [Customer 360 README](../customer-360/README.md)
