# 14. Brand Performance Across Segments

## Business Context

**Difficulty:** Beginner | **Graph Pattern:** Multi-dimensional aggregation | **Use Case:** Brand Partnerships, Pricing Strategy | **Business Value:** Analyze brand popularity across customer segments to inform partnership negotiations, pricing strategies, and segment-specific brand positioning.

## The Query

```cypher
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
RETURN p.brand,
       c.segment,
       COUNT(DISTINCT c) as unique_customers,
       COUNT(p) as total_purchases
ORDER BY p.brand, unique_customers DESC;
```

## Expected Results

Brand purchase patterns segmented by customer type. Shows which brands resonate with VIP vs Regular customers.

**Expected Rows:** 100-200 brand-segment combinations | **Execution Time:** 250-450ms | **Hops:** 1

### Sample Output

| brand | segment | unique_customers | total_purchases |
|-------|---------|------------------|-----------------|
| Apple | VIP | 687 | 2,341 |
| Apple | Premium | 1,234 | 3,872 |
| Apple | Regular | 2,145 | 4,231 |
| Samsung | Premium | 892 | 2,109 |
| Samsung | Regular | 1,876 | 3,654 |

## Business Insights

Apple dominates VIP segment with high purchase frequency per customer. Samsung shows broader appeal across segments. Use this data for targeted brand campaigns and partnership negotiations based on segment penetration.

## Try It Yourself

```bash
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
RETURN p.brand, c.segment,
       COUNT(DISTINCT c) as unique_customers,
       COUNT(p) as total_purchases
ORDER BY p.brand, unique_customers DESC;

# Focus on top brands in VIP segment:
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN p.brand, COUNT(DISTINCT c) as vip_customers,
       COUNT(p) as purchases,
       toFloat(COUNT(p)) / COUNT(DISTINCT c) as purchases_per_vip
ORDER BY vip_customers DESC
LIMIT 15;
```

## Related Queries
- Query 8: Brand Loyalty Analysis
- Query 12: Most Popular Products by Segment
- Query 13: Category Preferences by Segment
