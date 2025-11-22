# 16. Complementary Product Discovery

## Business Context

**Difficulty:** Intermediate | **Graph Pattern:** 3-hop with segment filtering | **Use Case:** Product Bundles, Sequential Recommendations | **Business Value:** Discover products that similar customers purchased after buying a specific product, filtered by customer segment. This identifies complementary products for bundles and sequential purchase recommendations.

## The Query

```cypher
MATCH (c1:Customer)-[:PURCHASED]->(p1:Product)
WHERE p1.product_id = 'PROD_123'
MATCH (c2:Customer)-[:PURCHASED]->(p1)
MATCH (c2)-[:PURCHASED]->(p2:Product)
WHERE c1.segment = c2.segment
  AND p1 <> p2
  AND NOT (c1)-[:PURCHASED]->(p2)
RETURN p2.name as complementary_product,
       p2.category,
       p2.brand,
       p2.price,
       COUNT(DISTINCT c2) as times_purchased_after
ORDER BY times_purchased_after DESC
LIMIT 10;
```

## Expected Results

Products that segment-matched customers bought alongside PROD_123 but the anchor customer hasn't. Segment filtering ensures relevance (VIP recommendations for VIP customers).

**Expected Rows:** 10 products | **Execution Time:** 150-300ms | **Hops:** 3

### Sample Output

| complementary_product | category | brand | price | times_purchased_after |
|----------------------|----------|-------|-------|----------------------|
| iPhone Case Pro | Electronics | Apple | 49.00 | 89 |
| Wireless Charger | Electronics | Anker | 39.00 | 76 |
| Screen Protector | Electronics | ZAGG | 29.00 | 68 |

## Business Insights

Segment-filtered affinity is more accurate than general affinity. VIP customers who buy iPhones also buy premium cases and accessories, while Regular customers might buy budget alternatives. This query ensures recommendations match purchasing power and preferences.

## Try It Yourself

```bash
MATCH (c1:Customer)-[:PURCHASED]->(p1:Product)
WHERE p1.product_id = 'PROD_123'
MATCH (c2:Customer)-[:PURCHASED]->(p1)
MATCH (c2)-[:PURCHASED]->(p2:Product)
WHERE c1.segment = c2.segment
  AND p1 <> p2
  AND NOT (c1)-[:PURCHASED]->(p2)
RETURN p2.name as complementary_product,
       p2.category, p2.brand, p2.price,
       COUNT(DISTINCT c2) as times_purchased_after
ORDER BY times_purchased_after DESC
LIMIT 10;
```

## Related Queries
- Query 5: Product Affinity (no segment filtering)
- Query 4: Collaborative Filtering
- Query 15: 2-Hop Recommendation Path
