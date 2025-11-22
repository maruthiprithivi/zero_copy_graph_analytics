# 6. Category Expansion Recommendations

## Business Context

**Difficulty:** Intermediate
**Graph Pattern:** Multi-hop with category filtering
**Use Case:** Cross-Category Marketing, Customer Expansion
**Business Value:** Discover which product categories customers purchase after buying from a specific category. This enables targeted cross-category marketing campaigns to expand customer shopping behavior beyond single categories. Graph databases make this analysis trivial through relationship traversal, while SQL requires complex self-joins and grouping.

## The Query

```cypher
MATCH (c:Customer)-[:PURCHASED]->(p1:Product)
WHERE p1.category = 'Electronics'
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p2.category <> 'Electronics'
RETURN p2.category as other_category,
       COUNT(DISTINCT c) as customer_count,
       COUNT(DISTINCT p2) as product_count
ORDER BY customer_count DESC;
```

## Graph Visualization Concept

Electronics products on the left, customers in the middle, and all other category products on the right. The thickness of connections between customers and non-Electronics categories shows expansion patterns. Strong connections to Home, Apparel, or Grocery indicate common cross-category journeys.

## Expected Results

### Execution Metrics
- **Status:** Skipped (mock mode)
- **Expected Execution Time:** 200-400ms (full traversal with aggregation)
- **Expected Rows:** 8-12 categories
- **Hops/Depth:** 2

### Sample Output

| other_category | customer_count | product_count |
|---------------|----------------|---------------|
| Home | 1,247 | 3,821 |
| Apparel | 982 | 2,654 |
| Grocery | 876 | 1,432 |
| Sports | 654 | 1,987 |
| Beauty | 543 | 1,123 |
| Books | 432 | 2,341 |
| Toys | 321 | 876 |

## Understanding the Results

### For Beginners

This query tells you "customers who buy Electronics also buy from these other categories, in order of popularity". It helps you understand where customers go after they buy from a specific category.

If 1,247 customers who bought Electronics also bought Home products, that's a strong signal to market smart home devices, furniture, or kitchen appliances to your Electronics shoppers. The product_count tells you how diverse their purchases are within each category.

### Technical Deep Dive

The two MATCH clauses are connected through the customer variable (c), creating an implicit inner join. The first MATCH finds all customers who bought Electronics, the second finds their other purchases in different categories.

The WHERE clauses filter: first to anchor on Electronics, then to exclude Electronics from results. The GROUP BY is implicit - Cypher groups by all non-aggregated RETURN values automatically.

For better performance with large datasets, add a customer segment filter or limit to recent purchases:
```cypher
MATCH (c:Customer)-[r:PURCHASED]->(p1:Product)
WHERE p1.category = 'Electronics' AND r.purchase_date > date() - duration('P180D')
MATCH (c)-[r2:PURCHASED]->(p2:Product)
WHERE p2.category <> 'Electronics' AND r2.purchase_date > date() - duration('P180D')
RETURN p2.category, COUNT(DISTINCT c) as customer_count, COUNT(DISTINCT p2) as product_count
ORDER BY customer_count DESC;
```

## Business Insights

### Graph-Specific Advantages

Cross-category analysis in graph databases reveals natural customer journey patterns that are buried in SQL joins. The ability to traverse from one product category through customers to other categories makes expansion opportunities immediately visible.

### Actionable Recommendations

1. **Targeted Campaigns**: Create "Electronics → Home" marketing campaigns for the 1,247 customers who show this pattern
2. **Bundle Creation**: Pair Electronics with top expansion categories (Electronics + Home bundles)
3. **Email Segmentation**: Customers who only buy Electronics get targeted cross-category offers
4. **Store Layout**: In physical retail, position complementary categories near each other

## Related Queries

1. **Query 11: Category Gap Analysis** - Identifies customers who haven't expanded to expected categories
2. **Query 20: Cross-Category Purchase Diversity** - Measures customer engagement across categories

## Try It Yourself

```bash
MATCH (c:Customer)-[:PURCHASED]->(p1:Product)
WHERE p1.category = 'Electronics'
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p2.category <> 'Electronics'
RETURN p2.category as other_category,
       COUNT(DISTINCT c) as customer_count,
       COUNT(DISTINCT p2) as product_count
ORDER BY customer_count DESC;
```
