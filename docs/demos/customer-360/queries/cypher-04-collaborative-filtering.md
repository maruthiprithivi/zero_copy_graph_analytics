# 4. Collaborative Filtering - Products Purchased by Similar Customers

## Business Context

**Difficulty:** Intermediate
**Graph Pattern:** Multi-hop traversal with filtering
**Use Case:** Product Recommendations, Personalization
**Business Value:** This query demonstrates the true power of graph databases for recommendation engines. By traversing relationships 2-3 hops deep (target customer -> products -> similar customers -> recommended products), we can find items that similar customers bought but the target customer hasn't yet purchased. This collaborative filtering approach is 10-100x faster in a graph database than SQL because relationships are pre-computed pointers, not expensive joins.

## The Query

```cypher
MATCH (target:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p1:Product)
MATCH (other:Customer)-[:PURCHASED]->(p1)
MATCH (other)-[:PURCHASED]->(p2:Product)
WHERE target.segment = other.segment
  AND NOT (target)-[:PURCHASED]->(p2)
  AND target <> other
RETURN DISTINCT p2.name as recommended_product,
       p2.category,
       p2.brand,
       p2.price,
       COUNT(DISTINCT other) as purchased_by_similar_customers
ORDER BY purchased_by_similar_customers DESC, p2.name
LIMIT 10;
```

## Graph Visualization Concept

This query creates a 3-hop recommendation path:
1. Start at the target customer (CUST_12345)
2. Fan out to all products they've purchased (1st hop)
3. For each product, find other customers who bought the same item (2nd hop - these are "similar" customers)
4. Follow those similar customers to find products they bought that the target hasn't (3rd hop - these are recommendations)

Visualized, it looks like: Target Customer -> [Shared Products] -> [Similar Customers] -> [Recommended Products]. Products with many similar customer connections rise to the top as strongest recommendations.

## Expected Results

### Execution Metrics
- **Status:** Skipped (mock mode - no database connection)
- **Expected Execution Time:** 150-300ms (multi-hop traversal with filtering)
- **Expected Rows:** Up to 10 recommended products
- **Hops/Depth:** 3 (target->product->similar customers->recommendations)

### Sample Output

| recommended_product | category | brand | price | purchased_by_similar_customers |
|---------------------|----------|-------|-------|-------------------------------|
| Sony WH-1000XM5 Headphones | Electronics | Sony | 399.00 | 47 |
| AirPods Pro | Electronics | Apple | 249.00 | 42 |
| Samsung 4K TV 55" | Electronics | Samsung | 1299.00 | 38 |
| Bose QuietComfort Earbuds | Electronics | Bose | 279.00 | 35 |
| Magic Keyboard | Electronics | Apple | 349.00 | 31 |
| Logitech MX Master 3 | Electronics | Logitech | 99.00 | 28 |
| Ring Video Doorbell | Home | Ring | 179.00 | 24 |
| Dyson V15 Vacuum | Home | Dyson | 649.00 | 22 |
| Nespresso Machine | Home | Nespresso | 199.00 | 19 |
| Fitbit Charge 6 | Electronics | Fitbit | 149.00 | 17 |

## Understanding the Results

### For Beginners

Collaborative filtering is based on the principle "people who bought what you bought also liked these other things". This is how Amazon's "Customers who bought this item also bought" feature works.

The query starts by finding all products you've purchased, then finds other customers who bought the same products. These are your "similar" customers because they have overlapping taste with you. Finally, it looks at what these similar customers bought that you haven't yet purchased - those are your recommendations.

The beauty of graph databases for this pattern is that these connections already exist as relationships. The database doesn't need to compute similarity scores or build temporary tables - it just follows the edges. Each MATCH clause is a single hop across relationships that are stored as direct memory pointers.

The WHERE clause adds important filters: (1) Only recommend from customers in the same segment (VIP customers get VIP-appropriate recommendations), (2) Don't recommend products you already bought, (3) Don't compare yourself to yourself.

The COUNT tells us how many similar customers bought each recommended product. A product recommended by 47 similar customers is much stronger than one recommended by just 5. This is your confidence score - higher numbers mean the recommendation is more likely to resonate with you.

Think of it like asking your friends for restaurant recommendations. If 10 friends who share your taste all rave about a restaurant you haven't tried, that's a strong signal you'll like it too. If only 1 friend mentioned it, it's a weaker signal.

### Technical Deep Dive

This query showcases Cypher's pattern matching for multi-hop traversals. Each MATCH clause expands from the results of the previous one:

1. **First MATCH**: Anchor on target customer, expand to their purchased products. If the customer has 50 purchases, we get 50 rows at this stage.

2. **Second MATCH**: For each product, expand to all customers who bought it. If each product was bought by 20 customers on average, we now have 50 * 20 = 1,000 rows.

3. **Third MATCH**: For each similar customer, expand to all their purchases. If each customer bought 40 products, we have 1,000 * 40 = 40,000 candidate recommendations.

4. **WHERE Filtering**: Eliminates already-purchased products, different segments, and self-comparisons, reducing to ~5,000-10,000 rows.

5. **Aggregation**: COUNT(DISTINCT other) groups by product, collapsing to ~100-500 unique recommendations.

6. **Sorting and Limiting**: Top 10 strongest recommendations.

The NOT clause `NOT (target)-[:PURCHASED]->(p2)` is a negated pattern - it checks that a specific relationship doesn't exist. This is expensive in SQL (requires LEFT JOIN with NULL check or NOT EXISTS subquery) but efficient in graph databases.

Performance optimizations:
- Index on Customer.customer_id for the anchor lookup
- Consider filtering products by recency (`p1.purchase_date > date() - duration('P90D')`) to focus on recent behavior
- Add price filters to avoid recommending $5,000 products to budget customers
- Use LIMIT earlier in the query to reduce intermediate result sizes

The segment filter (`target.segment = other.segment`) is crucial for relevance. VIP customers have different purchasing patterns than Regular customers - mixing segments dilutes recommendation quality.

For production systems, this query should include relationship properties:
```cypher
MATCH (target:Customer {customer_id: 'CUST_12345'})-[r1:PURCHASED]->(p1:Product)
WHERE r1.purchase_date > date() - duration('P180D')
```

This focuses on recent purchases, which are more predictive of current preferences.

## Business Insights

### Graph-Specific Advantages

1. **Real-Time Recommendations**: This query runs in milliseconds, enabling real-time personalization as customers browse. SQL equivalents with multiple self-joins often take seconds or require pre-computed recommendation tables.

2. **Explainable Recommendations**: The graph path shows exactly why a product is recommended: "47 customers in your segment who bought products you own also bought this." This transparency builds trust.

3. **Dynamic Adaptation**: As purchase patterns change, recommendations automatically update. No need to retrain models or rebuild recommendation caches.

4. **Multi-Dimensional Similarity**: The query filters by segment, but you could easily extend it to include location, age range, or purchase frequency without query rewrites.

## Comparison to SQL

**SQL Equivalent:**
```sql
WITH target_products AS (
    SELECT product_id
    FROM purchases
    WHERE customer_id = 'CUST_12345'
),
similar_customers AS (
    SELECT DISTINCT p2.customer_id
    FROM purchases p2
    INNER JOIN target_products tp ON p2.product_id = tp.product_id
    INNER JOIN customers c1 ON p2.customer_id = c1.customer_id
    INNER JOIN customers c2 ON c1.segment = c2.segment
    WHERE c2.customer_id = 'CUST_12345'
      AND p2.customer_id <> 'CUST_12345'
),
recommendations AS (
    SELECT p3.product_id,
           COUNT(DISTINCT p3.customer_id) as similar_customer_count
    FROM purchases p3
    INNER JOIN similar_customers sc ON p3.customer_id = sc.customer_id
    WHERE p3.product_id NOT IN (SELECT product_id FROM target_products)
    GROUP BY p3.product_id
)
SELECT pr.name, pr.category, pr.brand, pr.price,
       r.similar_customer_count as purchased_by_similar_customers
FROM recommendations r
INNER JOIN products pr ON r.product_id = pr.product_id
ORDER BY similar_customer_count DESC, pr.name
LIMIT 10;
```

**Why Cypher is 10x Better:**
- **Readability**: The graph pattern is immediately understandable
- **Performance**: 3 relationship traversals vs 7 JOINs (each JOIN requires hash table construction or nested loops)
- **Maintainability**: Adding new filters (e.g., price range, category) requires 1 line in Cypher vs rewriting CTEs in SQL
- **Scalability**: As purchases grow to millions, SQL JOIN performance degrades significantly; graph traversal time stays constant

## Related Queries

1. **Query 5: Product Affinity** - Finds products frequently bought together with a specific item
2. **Query 15: 2-Hop Recommendation Path** - Extends this to 4-5 hops for even deeper discovery
3. **Query 17: Find Similar Customers** - Identifies customers with similar purchase patterns

## Try It Yourself

```bash
# Via PuppyGraph Web UI (http://localhost:8081)

MATCH (target:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p1:Product)
MATCH (other:Customer)-[:PURCHASED]->(p1)
MATCH (other)-[:PURCHASED]->(p2:Product)
WHERE target.segment = other.segment
  AND NOT (target)-[:PURCHASED]->(p2)
  AND target <> other
RETURN DISTINCT p2.name as recommended_product,
       p2.category,
       p2.brand,
       p2.price,
       COUNT(DISTINCT other) as purchased_by_similar_customers
ORDER BY purchased_by_similar_customers DESC, p2.name
LIMIT 10;

# Variations:

# 1. Category-specific recommendations:
MATCH (target:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p1:Product)
WHERE p1.category = 'Electronics'
MATCH (other:Customer)-[:PURCHASED]->(p1)
MATCH (other)-[:PURCHASED]->(p2:Product)
WHERE target.segment = other.segment
  AND p2.category = 'Electronics'
  AND NOT (target)-[:PURCHASED]->(p2)
  AND target <> other
RETURN DISTINCT p2.name, p2.brand, p2.price,
       COUNT(DISTINCT other) as strength
ORDER BY strength DESC
LIMIT 10;

# 2. Budget-conscious recommendations:
MATCH (target:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p1:Product)
MATCH (other:Customer)-[:PURCHASED]->(p1)
MATCH (other)-[:PURCHASED]->(p2:Product)
WHERE target.segment = other.segment
  AND NOT (target)-[:PURCHASED]->(p2)
  AND target <> other
  AND p2.price < 500
RETURN DISTINCT p2.name, p2.price,
       COUNT(DISTINCT other) as similar_buyers
ORDER BY similar_buyers DESC
LIMIT 10;

# 3. Cross-category discovery:
MATCH (target:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p1:Product)
MATCH (other:Customer)-[:PURCHASED]->(p1)
MATCH (other)-[:PURCHASED]->(p2:Product)
WHERE target.segment = other.segment
  AND NOT (target)-[:PURCHASED]->(p2)
  AND target <> other
  AND p2.category <> p1.category
RETURN DISTINCT p2.category, COUNT(DISTINCT p2) as products,
       COUNT(DISTINCT other) as recommenders
ORDER BY recommenders DESC;
```
