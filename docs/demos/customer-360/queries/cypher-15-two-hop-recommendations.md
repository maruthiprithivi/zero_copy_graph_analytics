# 15. 2-Hop Recommendation Path

## Business Context

**Difficulty:** Advanced | **Graph Pattern:** 5-hop multi-degree traversal | **Use Case:** Deep Discovery, Serendipitous Recommendations | **Business Value:** Find products through two degrees of customer similarity - customers who bought what similar customers bought. This discovers less obvious recommendations that might be missed by simpler collaborative filtering, enabling serendipitous product discovery.

## The Query

```cypher
MATCH (target:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p1:Product)
MATCH (c1:Customer)-[:PURCHASED]->(p1)
MATCH (c1)-[:PURCHASED]->(p2:Product)
MATCH (c2:Customer)-[:PURCHASED]->(p2)
MATCH (c2)-[:PURCHASED]->(p3:Product)
WHERE target <> c1
  AND target <> c2
  AND c1 <> c2
  AND NOT (target)-[:PURCHASED]->(p2)
  AND NOT (target)-[:PURCHASED]->(p3)
  AND p1 <> p2
  AND p2 <> p3
RETURN DISTINCT p3.name as recommended_product,
       p3.category,
       p3.brand,
       p3.price,
       COUNT(DISTINCT c2) as recommendation_strength
ORDER BY recommendation_strength DESC, p3.price DESC
LIMIT 10;
```

## Expected Results

Deep recommendations from 2 degrees of separation. Products you haven't discovered yet but are popular among customers similar to your similar customers.

**Expected Rows:** 10 products | **Execution Time:** 500-1000ms (complex multi-hop) | **Hops:** 5

## Graph Visualization Concept

Target → [Your Products] → [Similar Customers] → [Intermediate Products] → [2nd-Degree Similar Customers] → [Deep Recommendations]. Five hops that uncover hidden gems.

## Understanding the Results

### For Beginners

This query goes two levels deep in similarity. First, it finds customers similar to you (they bought what you bought). Then, it finds customers similar to those customers. Finally, it recommends products from this second-degree similarity group that you haven't purchased yet.

Think of it as "friends of friends" recommendations. Your friends have good taste. Their friends probably have good taste too. This discovers products outside your immediate circle that you might love.

### Technical Deep Dive

Five MATCH clauses create a complex traversal pattern:
1. Target customer → their products (p1)
2. p1 → other customers who bought p1 (c1 - 1st degree similar)
3. c1 → their other products (p2)
4. p2 → customers who bought p2 (c2 - 2nd degree similar)
5. c2 → their products (p3 - deep recommendations)

Multiple WHERE filters prevent cycles, duplicates, and already-purchased products. This query showcases graph database strength - expressing complex multi-hop patterns declaratively.

For large graphs, this query can be expensive. Optimize by:
- Adding segment filters: `WHERE target.segment = c1.segment AND c1.segment = c2.segment`
- Limiting to recent purchases: `WHERE r.purchase_date > date() - duration('P180D')`
- Using TOP K per hop to limit fan-out

## Business Insights

### Graph-Specific Advantages

Multi-hop traversals are where graph databases shine brightest vs SQL. Expressing this pattern in SQL would require 5 self-joins with complex conditions - nearly impossible to write and extremely slow to execute. In Cypher, it's readable and runs in under 1 second.

### Actionable Recommendations

1. **Discovery Engine**: Use for "You Might Also Like" features that go beyond obvious recommendations
2. **New Product Launch**: Test new products with customers who match 2-hop patterns from early adopters
3. **Trend Prediction**: Products gaining strength at 2-hop level may be emerging trends
4. **Personalization Depth**: Combine 1-hop (Query 4) and 2-hop recommendations for varied discovery

## Comparison to SQL

The SQL equivalent would require 5 CTEs with self-joins on the purchases table, multiple subqueries to filter already-purchased products, and complex conditions to prevent cycles. It would likely take 10-100x longer to execute and be nearly impossible to maintain.

## Related Queries

1. **Query 4: Collaborative Filtering** - Simpler 1-hop version
2. **Query 16: Complementary Product Discovery** - Similar multi-hop with segment filtering
3. **Query 17: Find Similar Customers** - Analyzes customer similarity

## Try It Yourself

```bash
MATCH (target:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p1:Product)
MATCH (c1:Customer)-[:PURCHASED]->(p1)
MATCH (c1)-[:PURCHASED]->(p2:Product)
MATCH (c2:Customer)-[:PURCHASED]->(p2)
MATCH (c2)-[:PURCHASED]->(p3:Product)
WHERE target <> c1 AND target <> c2 AND c1 <> c2
  AND NOT (target)-[:PURCHASED]->(p2)
  AND NOT (target)-[:PURCHASED]->(p3)
  AND p1 <> p2 AND p2 <> p3
RETURN DISTINCT p3.name as recommended_product,
       p3.category, p3.brand, p3.price,
       COUNT(DISTINCT c2) as recommendation_strength
ORDER BY recommendation_strength DESC, p3.price DESC
LIMIT 10;

# With segment filtering for better relevance:
MATCH (target:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p1:Product)
MATCH (c1:Customer)-[:PURCHASED]->(p1)
WHERE target.segment = c1.segment
MATCH (c1)-[:PURCHASED]->(p2:Product)
MATCH (c2:Customer)-[:PURCHASED]->(p2)
WHERE c1.segment = c2.segment
MATCH (c2)-[:PURCHASED]->(p3:Product)
WHERE target <> c1 AND target <> c2 AND c1 <> c2
  AND NOT (target)-[:PURCHASED]->(p2)
  AND NOT (target)-[:PURCHASED]->(p3)
  AND p1 <> p2 AND p2 <> p3
RETURN DISTINCT p3.name, p3.category, p3.price,
       COUNT(DISTINCT c2) as strength
ORDER BY strength DESC
LIMIT 10;
```
