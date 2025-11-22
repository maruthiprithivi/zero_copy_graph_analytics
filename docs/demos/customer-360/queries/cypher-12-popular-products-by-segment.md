# 12. Most Popular Products by Segment

## Business Context

**Difficulty:** Beginner | **Graph Pattern:** Filtered traversal with aggregation | **Use Case:** Inventory Planning, Segment Marketing | **Business Value:** Identify which products are most popular among specific customer segments to optimize inventory, pricing, and marketing strategies for each segment.

## The Query

```cypher
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN p.product_id,
       p.name,
       p.category,
       p.brand,
       COUNT(DISTINCT c) as vip_customers,
       p.price
ORDER BY vip_customers DESC
LIMIT 20;
```

## Expected Results

Top 20 products purchased by VIP customers, sorted by popularity. Expect high-end electronics, premium brands, and luxury items.

**Expected Rows:** 20 products | **Execution Time:** 100-150ms | **Hops:** 1

### Sample Output

| product_id | name | category | brand | vip_customers | price |
|------------|------|----------|-------|---------------|-------|
| PROD_5001 | MacBook Pro 16" | Electronics | Apple | 234 | 2499.00 |
| PROD_2819 | iPhone 15 Pro Max | Electronics | Apple | 198 | 1199.00 |
| PROD_7234 | AirPods Pro | Electronics | Apple | 176 | 249.00 |

## Business Insights

VIP customers gravitate toward premium brands and high-ticket items. Products popular among VIPs should be prominently featured in VIP communications and stocked appropriately. Consider VIP-exclusive bundles of top products.

## Try It Yourself

```bash
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN p.product_id, p.name, p.category, p.brand,
       COUNT(DISTINCT c) as vip_customers, p.price
ORDER BY vip_customers DESC
LIMIT 20;

# Compare segments:
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
RETURN p.name, c.segment, COUNT(DISTINCT c) as customers
ORDER BY c.segment, customers DESC;
```

## Related Queries
- Query 7: High-Value Customer Purchase Patterns
- Query 13: Category Preferences by Segment
- Query 14: Brand Performance Across Segments
