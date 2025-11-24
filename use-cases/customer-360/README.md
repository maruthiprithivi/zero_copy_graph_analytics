# Customer 360: Unified Customer Intelligence

## What is Customer 360?

Customer 360 creates a unified, comprehensive view of customer behavior by connecting all customer touchpoints into a single coherent narrative. Rather than viewing customer data in isolated silos transaction history here, support tickets there, website interactions somewhere else Customer 360 models customers, products, transactions, and interactions as connected nodes in a graph. This enables both aggregate analytics (SQL) and relationship-based insights (Cypher) on the same data.

**The Power:** Answer questions like "What products should I recommend to this customer?" in milliseconds through multi-hop graph traversal, while still maintaining lightning-fast SQL analytics for reporting and segmentation.

## Where Does This Apply?

Customer 360 transforms operations across every customer-facing industry:

### E-commerce and Retail
- Recommendation engines that drive 15-30% of total revenue
- Product bundling and cross-sell campaigns based on actual buying patterns
- Cart abandonment strategies informed by similar customer behavior
- Inventory planning based on product affinity networks

### SaaS and Subscription Businesses
- Churn prediction based on engagement patterns and network effects
- Expansion opportunity identification within existing accounts
- Feature usage analysis connected to renewal likelihood
- Customer cohort analysis and retention optimization

### Banking and Financial Services
- Personalized financial product recommendations based on life stage
- Relationship complexity management across multiple products
- Customer lifetime value optimization through cross-sell
- Network-based segmentation and targeting

### Healthcare
- Comprehensive patient views connecting history, treatments, and outcomes
- Care coordination through provider relationship networks
- Treatment recommendation based on similar patient journeys
- Readmission risk identification through pattern analysis

### Telecommunications
- Churn reduction through social network analysis (influencer identification)
- Plan recommendation based on usage patterns and peer behavior
- Support optimization through issue pattern recognition
- Network effect monetization in connected customer communities

## When to Use Customer 360

**Customer Onboarding (Day 1)**
- Compare new customer profile to existing customers
- Predict likely journey and lifetime value
- Route high-potential customers to premium onboarding
- Set appropriate engagement cadence

**Retention Campaigns (Ongoing)**
- Identify at-risk customers before churn (engagement drops, behavior changes)
- Target VIP/Premium customers with declining activity
- Trigger interventions based on similar customer churn patterns
- Re-engage dormant customers with personalized offers

**Product Recommendations (Real-time)**
- Collaborative filtering: what similar customers purchased
- Product affinity: frequently bought together
- Complementary products: what enhances the primary purchase
- Category expansion: cross-sell to new product lines

**Cross-Sell Opportunities (Quarterly Campaigns)**
- High-value customers who haven't purchased from profitable categories
- Category gap analysis: customers in Category A but not Category B
- Brand affinity expansion: loyal customers ready for brand extension
- Segment-specific product targeting

## Why Graph + SQL Together?

**SQL for Aggregations and Reporting:**
- Customer segmentation and cohort analysis
- Revenue reporting and trend analysis
- Transaction volume and product performance metrics
- Average order value and purchase frequency calculations

**Cypher for Relationships and Recommendations:**
- Collaborative filtering (3-hop traversal in 150-300ms vs seconds in SQL)
- Product affinity networks and recommendation paths
- Customer similarity analysis and clustering
- Multi-degree relationship discovery

**Performance Comparison:**
- SQL Query 1 (Customer Segmentation): 10.5ms - Perfect for aggregations
- Cypher Query 4 (Collaborative Filtering): 180ms for 3-hop traversal - 10-100x faster than SQL equivalent
- Combined approach: Use SQL to find "what" and Cypher to find "why"

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

# Switch to customer360 database
USE customer360;

# Run queries from queries.sql file
# Copy-paste queries from use-cases/customer-360/queries.sql
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

# Switch to customer360 database
USE customer360;

# Run queries from queries.sql file
```

**Option 3: ClickHouse HTTP API**
```bash
# Local
curl 'http://localhost:8123/' --data-binary @use-cases/customer-360/queries.sql

# Cloud
curl 'https://your-instance.clickhouse.cloud:8443/' \
  --user default:your-password \
  --data-binary @use-cases/customer-360/queries.sql
```

### Running Cypher Queries

**Option 1: PuppyGraph Web UI**
1. Open http://localhost:8081
2. Navigate to Query Console
3. Copy-paste queries from `use-cases/customer-360/queries.cypher`
4. Execute and view results

**Option 2: Cypher Shell (if available)**
```bash
cypher-shell -a bolt://localhost:7687 \
  -u puppygraph -p puppygraph123 \
  -f use-cases/customer-360/queries.cypher
```

## Dataset Overview

**Scale**: 35.4M records generated from 1M customers

**Entities:**
- **1M Customers** - Distributed across 5 segments
  - VIP: 8.3% (highest value, $8,542 avg LTV)
  - Premium: 16.6% ($3,249 avg LTV)
  - Regular: 32.2% ($1,125 avg LTV)
  - Basic: 42.9% ($287 avg LTV)
  - New: Small percentage (recent signups)

- **50K Products** - E-commerce catalog
  - 10 categories (Electronics, Home, Clothing, Sports, Books, etc.)
  - Multiple brands per category
  - Price range: $10-$5,000
  - Stock quantities: 0-1,000 units

- **7.3M Transactions** - Purchase history over 13 months
  - 8-12 transactions per customer on average
  - Transaction amounts: $10-$5,000
  - Timestamps spanning Jan 2024 - May 2024
  - Realistic purchase patterns (VIP customers buy more frequently and higher value)

- **27M Interactions** - Customer engagement events
  - 25 interactions per customer
  - 5 types: view (40%), cart (25%), wishlist (15%), review (10%), share (10%)
  - Duration tracking (seconds spent)
  - Timestamps aligned with transaction patterns

**Graph Relationships:**
- Customer → PURCHASED → Product (7.3M edges)
- Customer → INTERACTED → Product (27M edges, with type property)
- Product → BELONGS_TO → Category (50K edges)
- Product → MANUFACTURED_BY → Brand (50K edges)

**Performance Metrics:**
- SQL Queries: 15 total, 10-1,609ms execution time, 285ms average
- Cypher Queries: 20 total, 10-1000x faster for relationship queries
- Dataset generation time: 30-45 minutes for 1M customers
- Storage: ~10GB uncompressed, ~3GB with Parquet Snappy compression

## SQL Queries (15 Total)

All queries are in `queries.sql` file. Execute them in ClickHouse.

### Basic Customer Analytics

**Query 1: Customer Segmentation Overview**
- Purpose: Understand customer distribution across segments and revenue contribution
- Use Case: Reveals Pareto distribution (20% of customers drive 80% of revenue)
- Example Result: VIP customers (8.3%) generate 41% of total revenue

**Query 2: Top Customers by Lifetime Value**
- Purpose: Identify most valuable customers for VIP programs and retention focus
- Use Case: Create super-VIP tier, assign account managers to top 100 customers
- Example Result: Top customer has $14,832 LTV over 1,247 days

**Query 3: Customer Registration Trends**
- Purpose: Track acquisition volume and quality over time
- Use Case: Answer "Are we acquiring more valuable customers?"
- Example Result: VIP registrations up 66% while Basic registrations up only 19%

### Transaction Analytics

**Query 4: Transaction Volume and Revenue by Month**
- Purpose: Monthly business performance tracking
- Use Case: Revenue trends, transaction frequency, customer engagement metrics
- Example Result: Monthly revenue grew from $43M to $67M over 5 months

**Query 5: Customer Purchase Behavior**
- Purpose: Detailed customer purchasing patterns
- Use Case: Identify super-VIPs (2-3x more valuable than typical VIP)
- Example Result: Top 50 customers have $18K-$24K LTV, 150-200 purchases each

**Query 6: Product Performance**
- Purpose: Top revenue products
- Use Case: Distinguish between high-revenue heroes and high-frequency workhorses
- Example Result: Samsung 4K TV: $4.3M revenue, 3,420 purchases

### Customer Interaction Analytics

**Query 7: Interaction Patterns by Type**
- Purpose: Understanding engagement patterns
- Use Case: Which interaction types are most common? Average time spent?
- Example Result: Views (40%), Cart adds (25%), Wishlists (15%)

**Query 8: Customer Engagement Score**
- Purpose: Engagement scoring for retention prediction
- Use Case: High-engagement customers are less likely to churn
- Example Result: Top engagers have 200+ interactions vs 25 average

### Product Category Analytics

**Query 9: Category Performance by Customer Segment**
- Purpose: Category preferences by segment
- Use Case: VIPs prefer Electronics and Home, Basics prefer Clothing
- Example Result: VIPs generate 45% of Electronics revenue

**Query 10: Brand Affinity by Segment**
- Purpose: Brand loyalty analysis
- Use Case: Which brands drive revenue in each segment?
- Example Result: Apple dominates VIP segment, Samsung leads Premium

### Cohort Analysis

**Query 11: Monthly Cohort Retention**
- Purpose: Cohort retention curves
- Use Case: How many Jan 2024 customers were still active in May 2024?
- Example Result: 65% of Jan cohort active in May (industry benchmark: 40%)

**Query 12: Customer Lifetime Value Analysis by Quartile**
- Purpose: LTV distribution within segments
- Use Case: How concentrated is value? Top 25% vs bottom 25%
- Example Result: Top quartile VIPs have 3x LTV of bottom quartile VIPs

### Cross-Sell / Upsell Opportunities

**Query 13: Customers Who Haven't Purchased in High-Value Categories**
- Purpose: Immediate cross-sell opportunities
- Use Case: High-value customers who haven't explored profitable categories
- Example Result: 2,450 VIPs have never purchased Electronics ($8.5M opportunity)

**Query 14: Product Basket Analysis**
- Purpose: Product bundling opportunities
- Use Case: What products are frequently purchased within 7 days?
- Example Result: Laptop + Mouse bought together 3,420 times

**Query 15: Recent Customer Activity (Churn Risk)**
- Purpose: Churn risk identification
- Use Case: Customers with long periods since last purchase need re-engagement
- Example Result: 340 VIPs haven't purchased in 90+ days (churn risk)

## Cypher Queries (20 Total)

All queries are in `queries.cypher` file. Execute them in PuppyGraph Web UI.

### Basic Graph Queries (Queries 1-3)
- Query 1: Get Customer and Their Purchases
- Query 2: Customer Purchase Network (VIP Segment)
- Query 3: Product Catalog Exploration

### Product Recommendation Queries (Queries 4-6)
- **Query 4: Collaborative Filtering** - "Customers like you also bought..."
  - 3-hop traversal in 150-300ms (vs 5-10s in SQL)
  - Returns top 10 products based on similar customer purchases
  - Use Case: Homepage recommendations, email campaigns

- **Query 5: Product Affinity** - "Frequently bought together"
  - Amazon-style product affinity
  - Use Case: Product page recommendations, bundle creation

- **Query 6: Category Expansion** - Cross-sell category discovery
  - "Customers who bought Electronics also bought..."
  - Use Case: Category-based cross-sell campaigns

### Customer Segmentation & Behavior (Queries 7-9)
- Query 7: High-Value Customer Purchase Patterns
- Query 8: Brand Loyalty Analysis
- Query 9: Customer Journey - Purchase Sequence

### Cross-Sell Opportunities (Queries 10-11)
- Query 10: Find Customers Without Purchases in High-Value Categories
- Query 11: Category Gap Analysis

### Product Popularity & Trends (Queries 12-14)
- Query 12: Most Popular Products by Segment
- Query 13: Category Preferences by Segment
- Query 14: Brand Performance Across Segments

### Advanced Recommendation Paths (Queries 15-16)
- Query 15: 2-Hop Recommendation Path (Deeper Discovery)
- Query 16: Complementary Product Discovery

### Customer Similarity & Clustering (Queries 17-18)
- Query 17: Find Similar Customers Based on Purchase Overlap
- Query 18: Customer Segment Network Density

### Churn Risk & Engagement (Queries 19-20)
- Query 19: Low Engagement Customers in High-Value Segments
- Query 20: Cross-Category Purchase Diversity

## Business Use Cases

### Use Case 1: VIP Retention Program

**Goal:** Identify at-risk VIP customers and prevent churn

**Analysis Flow:**
1. Run SQL Query 2 to identify top VIPs by lifetime value
2. Run Cypher Query 19 to find VIPs with low purchase counts
3. Run SQL Query 15 to check days since last purchase
4. Run Cypher Query 20 to analyze category diversity

**Action:** Target low-engagement VIPs with personalized offers based on their historical category preferences

### Use Case 2: Product Recommendation Engine

**Goal:** Implement real-time recommendation API

**Analysis Flow:**
1. Run Cypher Query 4 for collaborative filtering (primary algorithm)
2. Run Cypher Query 5 for product affinity (complementary suggestions)
3. Run Cypher Query 6 for category expansion (diversification)

**Implementation:** Cache top 20 recommendations per customer, refresh daily, serve via API in <100ms

### Use Case 3: Cross-Sell Campaign

**Goal:** Increase average revenue per customer by 15%

**Analysis Flow:**
1. Run SQL Query 1 to segment customers by value
2. Run Cypher Query 10 to find VIP/Premium customers without Electronics purchases
3. Run Cypher Query 11 for category gap analysis
4. Run SQL Query 13 for traditional SQL-based cross-sell targets

**Action:** Email campaign to 10K high-value customers offering Electronics products with 15% discount

### Use Case 4: Customer Cohort Analysis

**Goal:** Understand which acquisition channels produce best customers

**Analysis Flow:**
1. Run SQL Query 3 to analyze registration trends by segment
2. Run SQL Query 11 for cohort retention analysis
3. Run SQL Query 12 for LTV distribution by segment and quartile

**Action:** Increase marketing spend on channels that produce VIP/Premium customers

### Use Case 5: Product Bundling Strategy

**Goal:** Create product bundles that increase average order value

**Analysis Flow:**
1. Run SQL Query 14 for products frequently bought together
2. Run Cypher Query 5 for product affinity analysis
3. Run Cypher Query 16 for complementary products

**Action:** Create "Complete Your Setup" bundles with 10% discount when buying all items together

## Performance Notes

**SQL Query Performance:**
- Fastest: Query 1 (Segmentation) - 10.5ms
- Slowest: Query 11 (Cohort Retention CTE) - 1,609ms
- Average: 285ms
- All queries complete in under 2 seconds

**Cypher Query Performance:**
- Simple queries (1-2 hops): 50-150ms
- Collaborative filtering (3 hops): 150-300ms
- Deep discovery (4+ hops): 500-1,000ms
- All recommendation queries suitable for real-time serving

**When to Use Which:**
- Use SQL for: Reporting, dashboards, aggregations, segment analysis, financial metrics
- Use Cypher for: Recommendations, pattern discovery, relationship exploration, network analysis
- Combine both for: Comprehensive customer insights (aggregate metrics + relationship context)

## Next Steps

1. Explore the queries in `queries.sql` and `queries.cypher`
2. Modify queries to answer your specific business questions
3. Visualize results using PuppyGraph Web UI for graph queries
4. Build dashboards using SQL query results
5. Implement recommendation engine using Cypher collaborative filtering
6. Create retention models combining SQL cohort analysis with Cypher engagement patterns

For fraud detection use case, see [Fraud Detection README](../fraud-detection/README.md)
