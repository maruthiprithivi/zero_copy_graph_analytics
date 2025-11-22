# 1. Get Customer and Their Purchases

## Business Context

**Difficulty:** Beginner
**Graph Pattern:** Simple 1-hop traversal
**Use Case:** Customer Profile View
**Business Value:** This query showcases the fundamental advantage of graph databases - the ability to instantly traverse relationships between customers and their purchases without complex joins. In a traditional SQL database, you would need to join customer and purchase tables, but in a graph, the relationship is a first-class citizen that can be traversed in constant time regardless of data volume.

## The Query

```cypher
MATCH (c:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
RETURN c.name as customer, c.segment, p.name as product, p.category, p.brand
LIMIT 20;
```

## Graph Visualization Concept

This query starts at a specific Customer node (identified by customer_id 'CUST_12345') and follows all outgoing PURCHASED edges to connected Product nodes. The graph pattern looks like a star, with the customer at the center and products radiating outward. Each PURCHASED relationship represents a single purchase transaction, creating a direct connection between the customer and what they bought.

## Expected Results

### Execution Metrics
- **Status:** Skipped (mock mode - no database connection)
- **Expected Execution Time:** 50-100ms (index lookup on customer_id + relationship traversal)
- **Expected Rows:** Up to 20 products
- **Hops/Depth:** 1 (single relationship traversal)

### Sample Output

| customer | segment | product | category | brand |
|----------|---------|---------|----------|-------|
| John Smith | VIP | iPhone 15 Pro | Electronics | Apple |
| John Smith | VIP | AirPods Pro | Electronics | Apple |
| John Smith | VIP | Organic Coffee Beans | Grocery | Starbucks |
| John Smith | VIP | Nike Running Shoes | Apparel | Nike |
| John Smith | VIP | Samsung 4K TV | Electronics | Samsung |
| John Smith | VIP | Bose Headphones | Electronics | Bose |
| John Smith | VIP | Yoga Mat | Sports | Lululemon |
| John Smith | VIP | Kitchen Mixer | Home | KitchenAid |

## Understanding the Results

### For Beginners

Graph databases store data as nodes (entities) and relationships (connections). In this query, we're asking the database to find a specific customer node and then "walk" along the PURCHASED relationships to see what products they bought.

Think of it like following a map: you start at a person's house (the Customer node), and follow roads (PURCHASED relationships) to see all the stores they've visited (Product nodes). The beauty of this approach is that the relationships are stored physically adjacent to the nodes, making traversal incredibly fast.

In a traditional relational database, you would have a customers table and a products table, with a purchases table acting as a junction. Every time you query, the database has to scan the purchases table to match customer IDs with product IDs. As your data grows to millions of purchases, these table scans become slower. In a graph database, the relationships are pre-computed and stored as pointers, so traversal time stays constant regardless of total data volume.

This query is foundational because it demonstrates pattern matching - the core concept of Cypher. The MATCH clause describes the pattern you're looking for (a customer connected to products), and the WHERE clause filters to a specific customer. The database engine then finds all instances of this pattern in your graph.

The LIMIT 20 clause is a practical consideration - most customers have dozens or hundreds of purchases, so we limit the results to make them manageable. Without the limit, you would see every product this customer has ever purchased.

### Technical Deep Dive

The Cypher query uses several key graph concepts. The MATCH clause employs ASCII art notation to describe graph patterns: `(c:Customer)` represents a node variable 'c' with label 'Customer', and `-[:PURCHASED]->` represents a directed relationship of type PURCHASED. The arrow direction matters - it flows from customer to product.

The property filter `{customer_id: 'CUST_12345'}` leverages an index on the Customer.customer_id property. PuppyGraph/Neo4j will use this index to directly locate the starting node in O(log n) time, then traverse relationships in O(1) time per relationship. This is fundamentally different from SQL's WHERE clause, which requires scanning rows.

Pattern matching in Cypher is declarative - you describe what you want, not how to get it. The query planner determines the optimal execution strategy. For this simple pattern, the strategy is: (1) Index lookup on customer_id, (2) Expand along PURCHASED relationships, (3) Return properties from both customer and product nodes.

The performance advantage over SQL is significant. A SQL equivalent would be:
```sql
SELECT c.name, c.segment, p.name, p.category, p.brand
FROM customers c
JOIN purchases pur ON c.customer_id = pur.customer_id
JOIN products p ON pur.product_id = p.product_id
WHERE c.customer_id = 'CUST_12345'
LIMIT 20;
```

This requires two joins, which means the database must build hash tables or perform index nested loops. With millions of purchases, even indexed joins have overhead. Graph traversal avoids this entirely by using direct memory pointers.

For optimization, ensure customer_id has an index (CREATE INDEX FOR (c:Customer) ON (c.customer_id)), and consider using relationship properties if you need to filter by purchase date or amount.

## Business Insights

### Graph-Specific Advantages

1. **Relationship-First Design**: The PURCHASED relationship is a first-class entity in the graph, not a foreign key. This makes queries more intuitive and closer to how business users think about data.

2. **Join-Free Queries**: No expensive joins mean consistent performance regardless of the number of purchases in your system. A customer with 10 purchases and one with 10,000 purchases will have similar query times.

3. **Extensibility**: Adding new relationship types (REVIEWED, RETURNED, WISHLISTED) doesn't require schema changes or additional junction tables - just create the relationships.

4. **Pattern Recognition**: This simple pattern becomes the building block for complex recommendations. Other queries will extend this pattern to find similar customers or related products.

### Key Findings

Based on typical Customer 360 data patterns:
- VIP segment customers typically have 50-200 purchases across multiple categories
- High-value customers show cross-category purchasing (Electronics, Home, Apparel)
- Brand loyalty patterns emerge through repeated purchases from the same manufacturer
- Purchase diversity indicates customer engagement level

### Actionable Recommendations

1. **Customer Service Context**: When a VIP customer calls, instantly pull their purchase history to provide personalized service and identify upsell opportunities.

2. **Segmentation Validation**: Verify segment classifications by examining purchase patterns - VIP customers should show consistent high-value, diverse purchases.

3. **Next-Best-Action**: Use this foundation to build real-time recommendation engines that suggest products based on purchase history and similar customer patterns.

4. **Churn Prevention**: Customers with declining purchase frequency can be identified and targeted with retention campaigns.

## Comparison to SQL

**SQL Equivalent:**
```sql
SELECT
    c.name as customer,
    c.segment,
    p.name as product,
    p.category,
    p.brand
FROM customers c
INNER JOIN purchases pur ON c.customer_id = pur.customer_id
INNER JOIN products p ON pur.product_id = p.product_id
WHERE c.customer_id = 'CUST_12345'
LIMIT 20;
```

**Why Cypher is Better:**
- **Readability**: The graph pattern `(Customer)-[:PURCHASED]->(Product)` is immediately understandable to non-technical stakeholders
- **Performance**: No join overhead - relationships are pre-materialized pointers
- **Scalability**: Query time doesn't degrade as the purchases table grows from thousands to millions of rows
- **Flexibility**: Easy to extend with additional patterns (e.g., add customer's friends, similar products) without query rewrites

**When SQL is Better:**
- Simple aggregations on a single table
- Batch processing where you need to scan all purchases anyway
- Reporting queries that don't require relationship traversal

## Related Queries

1. **Query 4: Collaborative Filtering** - Extends this pattern to find products that similar customers purchased
2. **Query 9: Customer Journey** - Analyzes the sequence and timing of purchases to understand customer behavior
3. **Query 17: Find Similar Customers** - Uses purchase overlap to identify customers with similar preferences

## Try It Yourself

```bash
# Via PuppyGraph Web UI (http://localhost:8081)
# Replace CUST_12345 with actual customer IDs from your data

MATCH (c:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
RETURN c.name as customer, c.segment, p.name as product, p.category, p.brand
LIMIT 20;

# Try variations:
# 1. Filter by category:
MATCH (c:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
WHERE p.category = 'Electronics'
RETURN p.name, p.brand, p.price
LIMIT 10;

# 2. Count purchases by category:
MATCH (c:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
RETURN p.category, COUNT(p) as purchase_count
ORDER BY purchase_count DESC;

# 3. Find expensive purchases:
MATCH (c:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
WHERE p.price > 500
RETURN p.name, p.price, p.category
ORDER BY p.price DESC;
```


---

**Navigation:** [← Demo Guide](../README.md) | [All Cypher Queries](../CYPHER-QUERIES.md) | [Docs Home](../../../README.md)
