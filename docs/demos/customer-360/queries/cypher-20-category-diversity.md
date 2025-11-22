# 20. Cross-Category Purchase Diversity

## Business Context

**Difficulty:** Intermediate | **Graph Pattern:** Collection aggregation with SIZE function | **Use Case:** Engagement Measurement, Customer Health Scoring | **Business Value:** Measure customer engagement breadth by counting how many distinct product categories each customer has purchased from. Higher diversity indicates deeper engagement and brand loyalty, while low diversity suggests opportunity for category expansion.

## The Query

```cypher
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WITH c, COLLECT(DISTINCT p.category) as categories
RETURN c.customer_id,
       c.name,
       c.segment,
       c.lifetime_value,
       SIZE(categories) as category_diversity,
       categories
ORDER BY category_diversity DESC, c.lifetime_value DESC
LIMIT 50;
```

## Expected Results

Customers ranked by category diversity - how many different product categories they've purchased from. High diversity = high engagement.

**Expected Rows:** 50 customers | **Execution Time:** 200-400ms | **Hops:** 1 with aggregation

### Sample Output

| customer_id | name | segment | lifetime_value | category_diversity | categories |
|-------------|------|---------|----------------|--------------------|------------|
| CUST_29481 | Emily Rodriguez | VIP | 28,750.00 | 8 | [Electronics, Home, Apparel, Beauty, Sports, Grocery, Books, Toys] |
| CUST_48103 | Michael Chen | VIP | 24,200.00 | 7 | [Electronics, Home, Sports, Apparel, Books, Auto, Grocery] |
| CUST_71829 | Sarah Williams | Premium | 19,850.00 | 7 | [Electronics, Beauty, Apparel, Home, Grocery, Toys, Books] |
| CUST_36592 | James Brown | VIP | 17,320.00 | 6 | [Electronics, Sports, Home, Apparel, Auto, Books] |

## Understanding the Results

### For Beginners

The COLLECT function gathers all category values into a list, and DISTINCT ensures each category appears only once. SIZE counts how many categories are in the list. A customer with category_diversity of 8 has purchased from 8 different categories - very high engagement.

Think of category diversity as a breadth score. A customer who only buys Electronics (diversity = 1) is single-category focused. A customer who buys from 6+ categories is exploring your full catalog and trusting your brand across multiple product types - much stronger loyalty.

The categories list shows exactly which categories they've explored, enabling gap analysis. If a high-diversity customer has 7 categories but not Home, that's a specific cross-sell opportunity.

### Technical Deep Dive

COLLECT is Cypher's list aggregation function. `COLLECT(DISTINCT p.category)` creates a list of unique category values for each customer. SIZE(list) returns the length of the list.

This pattern demonstrates Cypher's support for complex data types in aggregations. In SQL, you'd need STRING_AGG or GROUP_CONCAT with string parsing to achieve similar results, or multiple rows per customer.

The WITH clause groups by customer (implicit in Cypher's aggregation semantics - all non-aggregated variables in the RETURN become grouping keys). This is cleaner than SQL's explicit GROUP BY.

For large datasets, consider:
```cypher
MATCH (c:Customer)-[r:PURCHASED]->(p:Product)
WHERE r.purchase_date > date() - duration('P365D')
WITH c, COLLECT(DISTINCT p.category) as categories
WHERE SIZE(categories) >= 3
RETURN c.customer_id, c.name, c.segment, c.lifetime_value,
       SIZE(categories) as category_diversity, categories
ORDER BY category_diversity DESC, c.lifetime_value DESC
LIMIT 50;
```

This focuses on recent purchases (more indicative of current engagement) and filters to customers with minimum diversity.

## Business Insights

### Graph-Specific Advantages

Collecting and analyzing sets of related attributes (categories) through relationship traversal is natural in graph databases. The COLLECT function operates directly on traversed data, avoiding complex string aggregations or array_agg functions required in SQL.

### Actionable Recommendations

1. **Engagement Scoring**: Use category diversity as a component of customer health scores (7+ categories = A+, 5-6 = A, 3-4 = B)
2. **Expansion Campaigns**: Target 3-4 category customers with "Expand Your Discovery" campaigns showcasing unexplored categories
3. **VIP Validation**: High-value customers with low diversity might not merit VIP status - investigate or reclassify
4. **Retention Indicator**: Declining diversity over time signals disengagement; increasing diversity indicates growing loyalty
5. **Category Gaps**: For each customer, identify which categories they haven't explored and target with specific campaigns

## Comparison to SQL

**SQL Equivalent:**
```sql
SELECT c.customer_id, c.name, c.segment, c.lifetime_value,
       COUNT(DISTINCT p.category) as category_diversity,
       STRING_AGG(DISTINCT p.category, ', ') as categories
FROM customers c
INNER JOIN purchases pur ON c.customer_id = pur.customer_id
INNER JOIN products p ON pur.product_id = p.product_id
GROUP BY c.customer_id, c.name, c.segment, c.lifetime_value
ORDER BY category_diversity DESC, c.lifetime_value DESC
LIMIT 50;
```

Cypher's COLLECT returns a proper list structure, while SQL's STRING_AGG returns a delimited string requiring parsing. Graph version is also more readable.

## Related Queries

1. **Query 6: Category Expansion Recommendations** - Analyzes cross-category patterns at scale
2. **Query 7: High-Value Customer Purchase Patterns** - Related engagement analysis
3. **Query 11: Category Gap Analysis** - Identifies specific category gaps
4. **Query 18: Customer Segment Network Density** - Segment-level diversity patterns

## Try It Yourself

```bash
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WITH c, COLLECT(DISTINCT p.category) as categories
RETURN c.customer_id, c.name, c.segment, c.lifetime_value,
       SIZE(categories) as category_diversity, categories
ORDER BY category_diversity DESC, c.lifetime_value DESC
LIMIT 50;

# Variations:

# 1. Find low-diversity VIPs (expansion opportunities):
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
WITH c, COLLECT(DISTINCT p.category) as categories
WHERE SIZE(categories) <= 3
RETURN c.customer_id, c.name, c.lifetime_value,
       SIZE(categories) as diversity, categories
ORDER BY c.lifetime_value DESC;

# 2. Category gap identification:
MATCH (c:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
WITH COLLECT(DISTINCT p.category) as my_categories
MATCH (all:Product)
WITH my_categories, COLLECT(DISTINCT all.category) as all_categories
RETURN [cat IN all_categories WHERE NOT cat IN my_categories] as unexplored_categories;

# 3. Diversity trends by segment:
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WITH c, COLLECT(DISTINCT p.category) as categories
RETURN c.segment,
       AVG(SIZE(categories)) as avg_diversity,
       MIN(SIZE(categories)) as min_diversity,
       MAX(SIZE(categories)) as max_diversity
ORDER BY avg_diversity DESC;

# 4. Recent diversity (engagement health):
MATCH (c:Customer)-[r:PURCHASED]->(p:Product)
WHERE r.purchase_date > date() - duration('P180D')
WITH c, COLLECT(DISTINCT p.category) as recent_categories
WHERE SIZE(recent_categories) >= 3
RETURN c.customer_id, c.name, c.segment,
       SIZE(recent_categories) as recent_diversity,
       recent_categories
ORDER BY recent_diversity DESC
LIMIT 30;
```

## Advanced Analysis

### Diversity Score Calculation

Combine category diversity with other metrics for comprehensive engagement scoring:

```cypher
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WITH c, COLLECT(DISTINCT p.category) as categories, COUNT(p) as total_purchases
WITH c, SIZE(categories) as diversity, total_purchases,
     toFloat(SIZE(categories)) / 10.0 * 40 as diversity_points,  // 40% weight, max 10 categories
     CASE
       WHEN total_purchases >= 50 THEN 30
       WHEN total_purchases >= 20 THEN 20
       WHEN total_purchases >= 10 THEN 10
       ELSE toFloat(total_purchases) / 10 * 10
     END as volume_points,  // 30% weight
     CASE
       WHEN c.lifetime_value >= 10000 THEN 30
       WHEN c.lifetime_value >= 5000 THEN 20
       WHEN c.lifetime_value >= 2000 THEN 10
       ELSE toFloat(c.lifetime_value) / 2000 * 10
     END as value_points  // 30% weight
WITH c, diversity, total_purchases,
     diversity_points + volume_points + value_points as engagement_score
RETURN c.customer_id, c.name, c.segment,
       diversity, total_purchases, c.lifetime_value,
       ROUND(engagement_score) as engagement_score,
       CASE
         WHEN engagement_score >= 80 THEN 'Champion'
         WHEN engagement_score >= 60 THEN 'Loyal'
         WHEN engagement_score >= 40 THEN 'Potential'
         WHEN engagement_score >= 20 THEN 'At Risk'
         ELSE 'Churning'
       END as engagement_tier
ORDER BY engagement_score DESC
LIMIT 100;
```

This creates a comprehensive engagement score weighted across diversity, purchase volume, and lifetime value.
