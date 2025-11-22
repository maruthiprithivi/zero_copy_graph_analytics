# 17. Find Similar Customers Based on Purchase Overlap

## Business Context

**Difficulty:** Advanced | **Graph Pattern:** Multi-stage with Jaccard similarity | **Use Case:** Customer Clustering, Lookalike Audiences | **Business Value:** Identify customers with similar purchase patterns using product overlap to calculate similarity scores. This enables lookalike audience targeting, peer recommendations, and customer segmentation refinement.

## The Query

```cypher
MATCH (c1:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
MATCH (c2:Customer)-[:PURCHASED]->(p)
WHERE c1 <> c2
WITH c1, c2, COUNT(DISTINCT p) as shared_products
MATCH (c1)-[:PURCHASED]->(all_p1:Product)
MATCH (c2)-[:PURCHASED]->(all_p2:Product)
WITH c1, c2,
     shared_products,
     COUNT(DISTINCT all_p1) as c1_total,
     COUNT(DISTINCT all_p2) as c2_total
RETURN c2.customer_id,
       c2.name,
       c2.segment,
       shared_products,
       c1_total as my_products,
       c2_total as their_products,
       toFloat(shared_products) / c1_total as similarity_score
ORDER BY similarity_score DESC, shared_products DESC
LIMIT 20;
```

## Expected Results

Customers ranked by similarity score (0.0-1.0) based on purchase overlap. High scores indicate similar tastes and preferences.

**Expected Rows:** 20 customers | **Execution Time:** 300-600ms | **Hops:** 3 with aggregations

### Sample Output

| customer_id | name | segment | shared_products | my_products | their_products | similarity_score |
|-------------|------|---------|-----------------|-------------|----------------|------------------|
| CUST_45821 | David Kim | VIP | 23 | 45 | 67 | 0.511 |
| CUST_29103 | Sarah Lee | VIP | 19 | 45 | 52 | 0.422 |
| CUST_67234 | Mike Chen | Premium | 18 | 45 | 48 | 0.400 |

## Understanding the Results

### For Beginners

This query calculates how similar other customers are to you based on shared purchases. The similarity score is the percentage of your purchases that overlap with theirs. A score of 0.51 means 51% of your purchases match theirs - very high similarity.

The WITH clauses create a pipeline: first, count shared products between you and each other customer. Then, count total products for both customers. Finally, calculate the similarity ratio.

### Technical Deep Dive

This implements a simplified Jaccard similarity coefficient: `|intersection| / |set1|`. A full Jaccard would be `|intersection| / |union|`, but this one-sided version answers "what percentage of my purchases do they also have?"

The multi-stage WITH clauses demonstrate Cypher's pipeline processing:
1. Find shared products → aggregate count
2. Find all products for both customers → aggregate counts
3. Calculate similarity ratio → return ranked results

For true Jaccard similarity:
```cypher
RETURN toFloat(shared_products) / (c1_total + c2_total - shared_products) as jaccard_score
```

This query is expensive for customers with many purchases. Optimize by limiting to recent purchases or high-value items.

## Business Insights

### Graph-Specific Advantages

Calculating customer similarity in graph databases is natural - follow PURCHASED edges, find overlaps, aggregate. In SQL, this requires self-joins, INTERSECT operations, and complex GROUP BYs. Graph traversal makes similarity analysis 10-50x faster.

### Actionable Recommendations

1. **Lookalike Audiences**: Use high-similarity customers for Facebook/Google Ads lookalike targeting
2. **Peer Recommendations**: Show "Customers similar to you also liked..." features
3. **Segment Refinement**: Customers with high similarity might belong in the same micro-segment
4. **Social Features**: Enable "Find similar shoppers" features for community building

## Comparison to SQL

SQL equivalent requires multiple CTEs with self-joins on purchases table, INTERSECT for shared products, and complex division operations. Graph version is more intuitive and performant.

## Related Queries

1. **Query 4: Collaborative Filtering** - Uses similarity for recommendations
2. **Query 15: 2-Hop Recommendation Path** - Extends similarity to 2nd degree
3. **Query 18: Customer Segment Network Density** - Analyzes segment-wide similarity

## Try It Yourself

```bash
MATCH (c1:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
MATCH (c2:Customer)-[:PURCHASED]->(p)
WHERE c1 <> c2
WITH c1, c2, COUNT(DISTINCT p) as shared_products
MATCH (c1)-[:PURCHASED]->(all_p1:Product)
MATCH (c2)-[:PURCHASED]->(all_p2:Product)
WITH c1, c2, shared_products,
     COUNT(DISTINCT all_p1) as c1_total,
     COUNT(DISTINCT all_p2) as c2_total
RETURN c2.customer_id, c2.name, c2.segment,
       shared_products, c1_total as my_products,
       c2_total as their_products,
       toFloat(shared_products) / c1_total as similarity_score
ORDER BY similarity_score DESC, shared_products DESC
LIMIT 20;

# True Jaccard similarity:
MATCH (c1:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
MATCH (c2:Customer)-[:PURCHASED]->(p)
WHERE c1 <> c2
WITH c1, c2, COUNT(DISTINCT p) as shared
MATCH (c1)-[:PURCHASED]->(all_p1:Product)
MATCH (c2)-[:PURCHASED]->(all_p2:Product)
WITH c2, shared,
     COUNT(DISTINCT all_p1) as t1,
     COUNT(DISTINCT all_p2) as t2
RETURN c2.name,
       toFloat(shared) / (t1 + t2 - shared) as jaccard
ORDER BY jaccard DESC
LIMIT 20;
```
