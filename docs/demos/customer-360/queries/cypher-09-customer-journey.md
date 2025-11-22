# 9. Customer Journey - Purchase Sequence

## Business Context

**Difficulty:** Beginner
**Graph Pattern:** Path pattern with named path variable
**Use Case:** Customer Timeline, Journey Analysis
**Business Value:** Visualize a customer's complete purchase history as a connected path, enabling journey analysis and understanding of customer behavior over time. The path pattern captures the full context of relationships, which can be extended to analyze purchase sequences, frequency, and patterns.

## The Query

```cypher
MATCH path = (c:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
RETURN c.name as customer,
       p.name as product,
       p.category,
       p.brand
ORDER BY p.name
LIMIT 20;
```

## Graph Visualization Concept

A customer node at the center with PURCHASED edges fanning out to product nodes like spokes on a wheel. The path variable captures each customer-to-product connection as a complete path, which can be visualized as a star pattern or timeline when purchase dates are included.

## Expected Results

### Execution Metrics
- **Status:** Skipped (mock mode)
- **Expected Execution Time:** 50-100ms
- **Expected Rows:** Up to 20 purchases
- **Hops/Depth:** 1 (customer to products)

### Sample Output

| customer | product | category | brand |
|----------|---------|----------|-------|
| John Smith | AirPods Pro | Electronics | Apple |
| John Smith | Coffee Maker | Home | Cuisinart |
| John Smith | Desk Chair | Home | Herman Miller |
| John Smith | Fitness Tracker | Electronics | Fitbit |
| John Smith | iPhone 15 Pro | Electronics | Apple |
| John Smith | Running Shoes | Apparel | Nike |
| John Smith | Yoga Mat | Sports | Lululemon |

## Understanding the Results

### For Beginners

The path variable captures each complete customer-product connection. While this query returns tabular data similar to Query 1, the path pattern is designed for relationship analysis. You can extend it to analyze purchase sequences, time between purchases, or build complete customer journey timelines.

Think of path as capturing the entire story of each connection - not just the nodes but the relationship itself. This becomes powerful when relationships have properties like purchase_date, amount, or quantity, enabling temporal analysis.

### Technical Deep Dive

The `path =` syntax creates a path variable that captures the entire matched pattern. Though not used in the RETURN clause here, path variables enable advanced analysis:

```cypher
MATCH path = (c:Customer {customer_id: 'CUST_12345'})-[r:PURCHASED]->(p:Product)
RETURN c.name as customer,
       p.name as product,
       r.purchase_date as when_purchased,
       r.amount as spent,
       length(path) as path_length
ORDER BY r.purchase_date DESC
LIMIT 20;
```

Path variables become essential for multi-hop traversals:
```cypher
MATCH path = (c:Customer)-[:PURCHASED]->(:Product)-[:IN_CATEGORY]->(cat:Category)
WHERE c.customer_id = 'CUST_12345'
RETURN nodes(path) as journey, length(path) as hops;
```

Functions like nodes(path), relationships(path), and length(path) extract path components for analysis.

## Business Insights

### Graph-Specific Advantages

Path patterns are foundational for journey analytics in graph databases. By capturing complete relationship context, you can analyze sequences, frequencies, and behavioral patterns that are difficult to express in SQL.

### Actionable Recommendations

1. **Purchase Frequency**: Analyze time gaps between purchases to identify engagement patterns
2. **Category Progression**: Track which categories customers explore over time
3. **Lifetime Value Tracking**: Monitor cumulative spending through journey analysis
4. **Churn Prediction**: Customers with increasing gaps between purchases may be at risk

## Related Queries

1. **Query 1: Get Customer and Their Purchases** - Basic version without path pattern
2. **Query 15: 2-Hop Recommendation Path** - Uses multi-hop paths for recommendations
3. **Query 17: Find Similar Customers** - Compares purchase paths between customers

## Try It Yourself

```bash
MATCH path = (c:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
RETURN c.name as customer,
       p.name as product,
       p.category,
       p.brand
ORDER BY p.name
LIMIT 20;

# With relationship properties:
MATCH path = (c:Customer {customer_id: 'CUST_12345'})-[r:PURCHASED]->(p:Product)
RETURN c.name, p.name, r.purchase_date, r.amount
ORDER BY r.purchase_date DESC
LIMIT 20;
```
