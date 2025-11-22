# 5. Product Affinity - Frequently Bought Together

## Business Context

**Difficulty:** Intermediate
**Graph Pattern:** 2-hop traversal (product->customers->other products)
**Use Case:** Cross-sell, Bundle Recommendations, Basket Analysis
**Business Value:** This "frequently bought together" query powers cross-sell recommendations like Amazon's product bundles. By finding products that customers frequently purchase alongside a target product, you can create effective product bundles, optimize store layouts, and generate dynamic cross-sell offers at checkout. Graph databases excel at this because the purchase relationships make co-occurrence patterns immediately accessible.

## The Query

```cypher
MATCH (c:Customer)-[:PURCHASED]->(p1:Product {product_id: 'PROD_123'})
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p1 <> p2
RETURN p2.name as related_product,
       p2.category,
       p2.brand,
       COUNT(DISTINCT c) as times_bought_together
ORDER BY times_bought_together DESC
LIMIT 15;
```

## Graph Visualization Concept

Start with a specific Product node (PROD_123), expand to all Customers who purchased it, then expand from those customers to all other products they bought. The visualization shows a bipartite pattern: the anchor product in the center, customers in one ring around it, and related products in an outer ring. Products with the most connections represent the strongest affinities.

## Expected Results

### Execution Metrics
- **Status:** Skipped (mock mode)
- **Expected Execution Time:** 100-200ms
- **Expected Rows:** Up to 15 products
- **Hops/Depth:** 2 (product->customers->related products)

### Sample Output

| related_product | category | brand | times_bought_together |
|----------------|----------|-------|----------------------|
| iPhone Case | Electronics | Apple | 127 |
| Screen Protector | Electronics | ZAGG | 98 |
| AirPods Pro | Electronics | Apple | 84 |
| Wireless Charger | Electronics | Anker | 76 |
| USB-C Cable | Electronics | Belkin | 68 |
| Car Phone Mount | Auto | iOttie | 45 |
| Power Bank | Electronics | Anker | 42 |
| Phone Grip | Electronics | PopSocket | 38 |

## Understanding the Results

### For Beginners

This query answers "what do customers typically buy when they purchase this product?" It's the foundation of cross-sell recommendations. If you're buying an iPhone, the system can suggest a case, screen protector, and AirPods because 100+ other customers bought these items together.

The two MATCH clauses create a path: start at product PROD_123, follow PURCHASED relationships backward to find customers who bought it, then follow PURCHASED relationships forward to find what else those customers bought. The COUNT tells you how many customers bought each combination.

The results are sorted by co-occurrence frequency - items bought together most often appear first. This gives you a prioritized list for cross-sell recommendations.

### Technical Deep Dive

The query uses an implicit join through the customer variable (c). Both MATCH clauses share the same (c) node, which means they find customers who appear in both patterns. This is equivalent to a SQL self-join on the purchases table but expressed more intuitively.

The anchor filter `{product_id: 'PROD_123'}` uses an inline property match, which triggers an index lookup. For optimal performance, ensure this index exists:
```cypher
CREATE INDEX FOR (p:Product) ON (p.product_id);
```

The WHERE clause `p1 <> p2` prevents returning the anchor product itself as a recommendation. This is a simple node comparison by identity.

Execution plan: (1) Index lookup for PROD_123, (2) Expand to customers via incoming PURCHASED edges, (3) For each customer, expand to all products via outgoing PURCHASED edges, (4) Filter out the anchor product, (5) Group by product and count distinct customers, (6) Sort and limit.

For large e-commerce sites with millions of purchases, consider adding recency filters:
```cypher
MATCH (c:Customer)-[r1:PURCHASED]->(p1:Product {product_id: 'PROD_123'})
WHERE r1.purchase_date > date() - duration('P90D')
MATCH (c)-[r2:PURCHASED]->(p2:Product)
WHERE r2.purchase_date > date() - duration('P90D')
  AND p1 <> p2
  AND abs(duration.between(r1.purchase_date, r2.purchase_date).days) <= 30
```

This focuses on recent purchases and requires the products to be bought within 30 days of each other - a stronger signal of affinity.

## Business Insights

### Graph-Specific Advantages

1. **Real-Time Basket Analysis**: As customers add items to cart, you can instantly query for complementary products without pre-computed market basket tables
2. **Dynamic Bundling**: Create product bundles based on actual purchase behavior, updated automatically as patterns evolve
3. **Category Discovery**: Notice when products from unexpected categories are frequently bought together (e.g., iPhones + car mounts)

### Actionable Recommendations

1. **Automated Bundling**: Create "Frequently Bought Together" bundles for the top 10-15 products at a 5-10% discount
2. **Checkout Optimization**: Display top 3 affinity products during checkout to increase average order value
3. **Inventory Planning**: Ensure related products are stocked proportionally (if you have 100 iPhones, stock 80+ cases)
4. **Store Layout**: Place high-affinity products near each other in physical stores

## Comparison to SQL

**SQL Equivalent:**
```sql
WITH product_customers AS (
    SELECT customer_id
    FROM purchases
    WHERE product_id = 'PROD_123'
)
SELECT p.name, p.category, p.brand,
       COUNT(DISTINCT pur.customer_id) as times_bought_together
FROM purchases pur
INNER JOIN product_customers pc ON pur.customer_id = pc.customer_id
INNER JOIN products p ON pur.product_id = p.product_id
WHERE pur.product_id <> 'PROD_123'
GROUP BY p.product_id, p.name, p.category, p.brand
ORDER BY times_bought_together DESC
LIMIT 15;
```

Cypher is cleaner and more performant due to direct relationship traversal vs JOIN operations.

## Related Queries

1. **Query 4: Collaborative Filtering** - Uses similar multi-hop patterns for personalized recommendations
2. **Query 16: Complementary Product Discovery** - Extends this with segment filtering for more targeted affinities
3. **Query 6: Category Expansion** - Analyzes cross-category purchase patterns at scale

## Try It Yourself

```bash
# Via PuppyGraph Web UI (http://localhost:8081)

MATCH (c:Customer)-[:PURCHASED]->(p1:Product {product_id: 'PROD_123'})
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p1 <> p2
RETURN p2.name as related_product,
       p2.category,
       p2.brand,
       COUNT(DISTINCT c) as times_bought_together
ORDER BY times_bought_together DESC
LIMIT 15;

# Variations:

# 1. Category-specific affinity:
MATCH (c:Customer)-[:PURCHASED]->(p1:Product {product_id: 'PROD_123'})
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p1 <> p2 AND p2.category = 'Electronics'
RETURN p2.name, p2.brand, COUNT(DISTINCT c) as co_purchases
ORDER BY co_purchases DESC
LIMIT 10;

# 2. High-value affinity (for upsells):
MATCH (c:Customer)-[:PURCHASED]->(p1:Product {product_id: 'PROD_123'})
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p1 <> p2 AND p2.price > p1.price
RETURN p2.name, p2.price, COUNT(DISTINCT c) as upsell_count
ORDER BY upsell_count DESC
LIMIT 10;

# 3. Affinity by customer segment:
MATCH (c:Customer)-[:PURCHASED]->(p1:Product {product_id: 'PROD_123'})
WHERE c.segment = 'VIP'
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p1 <> p2
RETURN p2.name, COUNT(DISTINCT c) as vip_purchases
ORDER BY vip_purchases DESC
LIMIT 10;
```
