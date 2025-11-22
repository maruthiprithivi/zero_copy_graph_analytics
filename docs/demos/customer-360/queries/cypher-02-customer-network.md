# 2. Customer Purchase Network

## Business Context

**Difficulty:** Beginner
**Graph Pattern:** Simple pattern with filtering
**Use Case:** Segment Analysis, Network Visualization
**Business Value:** This query returns entire graph structures (nodes and relationships) for visualization purposes, enabling analysts to see the network of VIP customers and their product preferences. Unlike the first query which returns tabular data, this returns the actual graph objects, perfect for visual exploration tools that can render interactive network diagrams.

## The Query

```cypher
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN c, p
LIMIT 100;
```

## Graph Visualization Concept

This query creates a bipartite graph visualization showing VIP customers on one side and products on the other, with PURCHASED relationships connecting them. Imagine a network diagram where VIP customer nodes are displayed in one color (e.g., gold) and product nodes in another (e.g., blue), with lines showing who bought what. High-degree product nodes (many incoming PURCHASED edges) represent popular items among VIP customers, while high-degree customer nodes represent power buyers.

## Expected Results

### Execution Metrics
- **Status:** Skipped (mock mode - no database connection)
- **Expected Execution Time:** 100-150ms (filtered scan + relationship traversal)
- **Expected Rows:** Up to 100 customer-product pairs
- **Hops/Depth:** 1 (single relationship traversal)

### Sample Output

The output returns full node objects with all properties, suitable for graph visualization:

```json
{
  "c": {
    "customer_id": "CUST_10001",
    "name": "Sarah Johnson",
    "segment": "VIP",
    "lifetime_value": 15250.00,
    "email": "sarah.j@example.com"
  },
  "p": {
    "product_id": "PROD_5001",
    "name": "MacBook Pro 16\"",
    "category": "Electronics",
    "brand": "Apple",
    "price": 2499.00
  }
}
```

When visualized, you would see:
- 50-80 VIP customer nodes (limited by LIMIT 100 and overlapping purchases)
- 60-100 unique product nodes
- 100 PURCHASED relationship edges

## Understanding the Results

### For Beginners

Unlike the previous query that returned specific properties in a table format, this query returns entire nodes (c and p) as objects. This is specifically designed for graph visualization tools that can render the network structure.

Think of this like the difference between getting a spreadsheet of who bought what versus seeing an actual network diagram where customers and products are circles, and purchases are lines connecting them. The visual representation makes patterns immediately obvious - which products are most popular, which customers buy the most diverse items, and whether there are clusters of similar buying behavior.

Graph visualization tools can render this data interactively, allowing you to click on nodes to see details, zoom in on specific areas, and apply different layouts (force-directed, circular, hierarchical). This makes it easy for business users to explore the data without writing queries.

The LIMIT 100 is crucial here - without it, you could return thousands or millions of relationships, which would be impossible to visualize meaningfully. For VIP segments with 200-500 customers, limiting to 100 relationships gives you a representative sample that renders quickly.

The WHERE clause filters to only VIP customers, which is important because VIP behavior patterns often differ significantly from other segments. VIPs might show higher brand loyalty, larger basket sizes, and more cross-category purchasing. Visualizing their network separately allows you to understand the unique characteristics of your most valuable customers.

### Technical Deep Dive

This query demonstrates Cypher's ability to return graph structures, not just tabular results. The RETURN c, p clause returns node objects with all their properties, labels, and internal IDs. This is fundamentally different from SQL's always-tabular output format.

The query execution plan for PuppyGraph/Neo4j would be: (1) Scan Customer nodes filtered by segment='VIP' (using a label scan with property filter), (2) For each customer, expand PURCHASED relationships, (3) Return the customer node and connected product node as pairs, (4) Stop after 100 results.

The lack of property projection means all node properties are included in the response. This increases data transfer but eliminates the need for follow-up queries. Visualization tools receive complete node context immediately.

Performance considerations: With a VIP segment typically representing 5-10% of customers, the filtered scan is efficient. If VIP represents 500 customers with an average of 75 purchases each (37,500 total relationships), returning 100 pairs samples about 0.27% of the data - enough for visual insight without overwhelming the renderer.

The query can be optimized by adding indexes:
```cypher
CREATE INDEX FOR (c:Customer) ON (c.segment);
```

For production visualization systems, consider using pagination to load the network incrementally:
```cypher
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN c, p
SKIP $offset LIMIT $pageSize;
```

This query type is particularly powerful when combined with graph visualization libraries like D3.js, vis.js, or commercial tools like Neo4j Bloom, which can render force-directed layouts where connected nodes cluster together naturally.

## Business Insights

### Graph-Specific Advantages

1. **Visual Pattern Discovery**: Human brains are excellent at recognizing patterns in visual data. A graph visualization can reveal customer clusters, product affinities, and outliers instantly - patterns that would require complex SQL analytics to discover.

2. **Interactive Exploration**: Returning full node objects enables drill-down exploration. Click a customer to see all their purchases, click a product to see all buyers, double-click to expand the network further.

3. **Real-Time Segmentation**: The ability to filter by segment and instantly visualize the resulting network makes it easy to compare VIP vs Premium vs Regular customer patterns side-by-side.

4. **Anomaly Detection**: In a network visualization, unusual patterns stand out - a customer connected to 50+ products, a niche product unexpectedly popular with VIPs, or isolated customer-product pairs that suggest fraud or data quality issues.

### Key Findings

Typical patterns visible in VIP customer networks:
- **Product Hubs**: High-value electronics and luxury goods show many incoming connections from VIPs
- **Brand Clusters**: VIP customers often cluster around premium brands (Apple, Sony, KitchenAid)
- **Cross-Category Stars**: Some customers show star patterns with products spanning 5-8 categories
- **Isolated Pairs**: VIPs who have made very few purchases may indicate recent upgrades or churn risk

### Actionable Recommendations

1. **Portfolio Optimization**: Identify which products are popular among VIPs to inform inventory and marketing decisions. If 40% of VIPs purchased a specific product, ensure ample stock.

2. **Personalization Strategy**: Customers with dense, diverse product networks are highly engaged. Those with sparse networks need targeted engagement campaigns.

3. **Upsell Targeting**: Products popular among VIPs but not yet purchased by specific VIP customers represent prime upsell opportunities.

4. **Segment Refinement**: If some VIP customers show purchasing patterns more similar to Premium customers, consider segment reassignment or create sub-segments.

## Comparison to SQL

**SQL Equivalent:**
```sql
SELECT
    c.customer_id, c.name, c.segment, c.lifetime_value, c.email,
    p.product_id, p.name, p.category, p.brand, p.price
FROM customers c
INNER JOIN purchases pur ON c.customer_id = pur.customer_id
INNER JOIN products p ON pur.product_id = p.product_id
WHERE c.segment = 'VIP'
LIMIT 100;
```

**Why Cypher is Better:**
- **Graph-Native Output**: Returns actual graph structures that visualization tools can render directly
- **Relationship Context**: The PURCHASED relationship is part of the result, enabling visualization of connection strength (e.g., multiple purchases)
- **Explorability**: Visualization tools can use the returned node IDs to make follow-up queries for expansion without re-querying the original data

**When SQL is Better:**
- Generating reports or exports that need tabular format (CSV, Excel)
- Aggregations across the entire VIP segment without need for individual relationships
- Integration with BI tools that expect traditional result sets

## Related Queries

1. **Query 7: High-Value Customer Purchase Patterns** - Analyzes VIP purchasing in detail with aggregations
2. **Query 12: Most Popular Products by Segment** - Identifies which products are VIP favorites
3. **Query 13: Category Preferences by Segment** - Breaks down VIP preferences by product category

## Try It Yourself

```bash
# Via PuppyGraph Web UI (http://localhost:8081)
# The web UI typically has built-in visualization for graph results

MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN c, p
LIMIT 100;

# Try variations:

# 1. Compare segments visually (run separately and compare):
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'Premium'
RETURN c, p
LIMIT 100;

# 2. Focus on a specific category:
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP' AND p.category = 'Electronics'
RETURN c, p
LIMIT 100;

# 3. Include relationship properties for richer visualization:
MATCH (c:Customer)-[r:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN c, r, p
LIMIT 100;

# 4. High-value VIPs only:
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP' AND c.lifetime_value > 10000
RETURN c, p
LIMIT 100;
```

**Visualization Tips:**
- Use node size to represent lifetime_value for customers and price for products
- Color nodes by segment (customer) and category (product)
- Use edge thickness to show relationship count if aggregating
- Apply force-directed layout to see natural clustering
- Filter out low-degree nodes for cleaner visualization of core patterns


---

**Navigation:** [← Demo Guide](../README.md) | [All Cypher Queries](../CYPHER-QUERIES.md) | [Docs Home](../../../README.md)
