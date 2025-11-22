# 13. Category Preferences by Segment

## Business Context

**Difficulty:** Beginner | **Graph Pattern:** Aggregation across dimensions | **Use Case:** Segment Profiling, Marketing Strategy | **Business Value:** Understand which product categories resonate with each customer segment to tailor marketing messages, inventory allocation, and promotional strategies per segment.

## The Query

```cypher
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
RETURN c.segment,
       p.category,
       COUNT(DISTINCT c) as customers,
       COUNT(p) as total_purchases
ORDER BY c.segment, total_purchases DESC;
```

## Expected Results

Category breakdown for each segment showing purchase volume and unique customer counts. Reveals segment-specific preferences.

**Expected Rows:** 30-50 segment-category combinations | **Execution Time:** 200-400ms | **Hops:** 1

### Sample Output

| segment | category | customers | total_purchases |
|---------|----------|-----------|-----------------|
| VIP | Electronics | 842 | 3,421 |
| VIP | Home | 731 | 2,187 |
| VIP | Apparel | 654 | 1,892 |
| Premium | Electronics | 1,234 | 4,567 |
| Premium | Grocery | 1,098 | 8,234 |
| Regular | Grocery | 4,521 | 18,745 |

## Business Insights

VIP customers show strong preference for Electronics and Home categories with higher per-customer purchase counts. Regular customers focus on Grocery and everyday items. This data informs segment-specific catalog design and promotional campaigns.

## Try It Yourself

```bash
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
RETURN c.segment, p.category,
       COUNT(DISTINCT c) as customers,
       COUNT(p) as total_purchases
ORDER BY c.segment, total_purchases DESC;

# Calculate average purchases per customer:
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WITH c.segment as segment, p.category as category,
     COUNT(DISTINCT c) as customers, COUNT(p) as purchases
RETURN segment, category, customers, purchases,
       toFloat(purchases) / customers as avg_per_customer
ORDER BY segment, avg_per_customer DESC;
```

## Related Queries
- Query 12: Most Popular Products by Segment
- Query 14: Brand Performance Across Segments
- Query 18: Customer Segment Network Density
