# 18. Customer Segment Network Density

## Business Context

**Difficulty:** Intermediate | **Graph Pattern:** Aggregation with density calculation | **Use Case:** Segment Analysis, Market Efficiency | **Business Value:** Calculate network density for each customer segment - the ratio of actual purchases to possible purchases. High density indicates concentrated buying patterns (segment buys specific products), while low density indicates diverse exploration.

## The Query

```cypher
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
RETURN c.segment,
       COUNT(DISTINCT c) as customers,
       COUNT(DISTINCT p) as products,
       COUNT(*) as total_purchases,
       toFloat(COUNT(*)) / (COUNT(DISTINCT c) * COUNT(DISTINCT p)) as network_density
ORDER BY network_density DESC;
```

## Expected Results

Density metrics for each segment showing how concentrated purchase patterns are.

**Expected Rows:** 3-5 segments | **Execution Time:** 300-500ms | **Hops:** 1 with aggregations

### Sample Output

| segment | customers | products | total_purchases | network_density |
|---------|-----------|----------|-----------------|-----------------|
| VIP | 842 | 1,247 | 63,421 | 0.0604 |
| Premium | 2,341 | 2,109 | 147,892 | 0.0299 |
| Regular | 8,765 | 3,891 | 312,445 | 0.0092 |

## Understanding the Results

### For Beginners

Network density measures how "connected" a segment is - what percentage of possible customer-product connections actually exist. If 842 VIP customers and 1,247 products existed, there could be 842 × 1,247 = 1,049,874 possible purchases. Actual purchases (63,421) divided by possible purchases gives density of 6.04%.

VIP customers show higher density (6%) than Regular customers (0.9%), meaning VIPs buy a concentrated set of products (premium/luxury items), while Regular customers spread across many products (exploratory behavior).

### Technical Deep Dive

Density formula: `actual_edges / possible_edges = total_purchases / (customers * products)`

This is a graph metrics calculation borrowed from social network analysis. In a complete bipartite graph (every customer bought every product), density = 1.0. In reality, densities are low (0.001-0.10) because customers only buy a tiny fraction of available products.

The COUNT(*) counts relationship instances (purchases), which can include duplicates if customers bought the same product multiple times. For unique purchase density, use:
```cypher
WITH c.segment as segment,
     COUNT(DISTINCT c) as customers,
     COUNT(DISTINCT p) as products,
     COUNT(DISTINCT c.customer_id + '-' + p.product_id) as unique_pairs
RETURN segment, customers, products, unique_pairs,
       toFloat(unique_pairs) / (customers * products) as unique_density
ORDER BY unique_density DESC;
```

## Business Insights

### Graph-Specific Advantages

Network density is a pure graph metric that has no natural SQL equivalent. It reveals structural properties of customer-product relationships that are invisible in tabular data. High-density segments are easier to serve (focused inventory), while low-density segments require broader catalogs.

### Actionable Recommendations

1. **Inventory Strategy**: High-density segments (VIP) need smaller, curated catalogs; low-density segments need broad selection
2. **Marketing Efficiency**: High-density segments have clear preferences - targeted campaigns work well
3. **Personalization Depth**: Low-density segments need stronger recommendation engines to navigate choices
4. **Segment Maturity**: Declining density over time indicates segment maturation and diversification

## Related Queries

1. **Query 13: Category Preferences by Segment** - Deeper dive into segment preferences
2. **Query 17: Find Similar Customers** - Individual customer similarity
3. **Query 7: High-Value Customer Purchase Patterns** - VIP segment analysis

## Try It Yourself

```bash
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
RETURN c.segment,
       COUNT(DISTINCT c) as customers,
       COUNT(DISTINCT p) as products,
       COUNT(*) as total_purchases,
       toFloat(COUNT(*)) / (COUNT(DISTINCT c) * COUNT(DISTINCT p)) as network_density
ORDER BY network_density DESC;

# Unique purchase density (no repeat purchases):
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WITH c.segment as segment, c, p
WITH segment,
     COUNT(DISTINCT c) as customers,
     COUNT(DISTINCT p) as products,
     COUNT(DISTINCT c.customer_id + '-' + p.product_id) as unique_purchases
RETURN segment, customers, products, unique_purchases,
       toFloat(unique_purchases) / (customers * products) as density
ORDER BY density DESC;
```
