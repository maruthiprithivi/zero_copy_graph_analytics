# 8. Brand Loyalty Analysis

## Business Context

**Difficulty:** Advanced
**Graph Pattern:** Multi-stage traversal with filtering and calculations
**Use Case:** Brand Partnership, Marketing Campaigns, Customer Segmentation
**Business Value:** Identify customers who show strong loyalty to specific brands by calculating the ratio of brand-specific purchases to total purchases. This enables targeted partnership campaigns, brand ambassador programs, and helps predict customer response to brand-specific offers.

## The Query

```cypher
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE p.brand = 'Apple'
WITH c, COUNT(DISTINCT p) as apple_products
WHERE apple_products >= 3
MATCH (c)-[:PURCHASED]->(all_products:Product)
RETURN c.customer_id,
       c.name,
       c.segment,
       apple_products,
       COUNT(DISTINCT all_products) as total_products,
       toFloat(apple_products) / COUNT(DISTINCT all_products) as brand_loyalty_ratio
ORDER BY brand_loyalty_ratio DESC
LIMIT 50;
```

## Graph Visualization Concept

Customer nodes at the center with two types of connections: Apple product purchases (highlighted in one color) vs all other purchases (different color). Highly loyal customers show dense Apple connections relative to other brands - like a pie chart where Apple slice is 70%+ of purchases.

## Expected Results

### Execution Metrics
- **Status:** Skipped (mock mode)
- **Expected Execution Time:** 250-400ms (two-stage traversal with calculations)
- **Expected Rows:** Up to 50 customers
- **Hops/Depth:** 2 stages (brand-specific, then all purchases)

### Sample Output

| customer_id | name | segment | apple_products | total_products | brand_loyalty_ratio |
|-------------|------|---------|----------------|----------------|---------------------|
| CUST_28451 | Jennifer Lee | VIP | 12 | 15 | 0.80 |
| CUST_19203 | David Park | Premium | 8 | 11 | 0.73 |
| CUST_50782 | Lisa Anderson | VIP | 15 | 22 | 0.68 |
| CUST_33914 | Robert Kim | VIP | 9 | 14 | 0.64 |
| CUST_47291 | Amanda White | Premium | 6 | 10 | 0.60 |

## Understanding the Results

### For Beginners

This query measures brand loyalty by comparing how many products a customer bought from a specific brand (Apple) versus their total purchases. A loyalty ratio of 0.80 means 80% of their purchases are Apple products - extremely high loyalty.

The query works in two stages using the WITH clause. First, it finds customers who bought at least 3 Apple products. Then, for those customers, it counts all their purchases to calculate the loyalty ratio. The WITH clause is like a checkpoint - it filters customers before the second stage, improving performance.

Think of brand loyalty ratio like a report card score. 0.80-1.0 is an A+ (brand fanatic), 0.60-0.79 is an A (strong loyalty), 0.40-0.59 is a B (moderate loyalty). These highly loyal customers are prime candidates for Apple partnership marketing, early access programs, or brand ambassador initiatives.

### Technical Deep Dive

This query demonstrates Cypher's WITH clause for multi-stage query composition. The first MATCH finds Apple products, WITH aggregates and filters, then the second MATCH re-expands from the filtered customers to all their purchases.

The WITH clause creates a pipeline: data flows through MATCH → WHERE → WITH → WHERE → MATCH → RETURN. This is more readable than SQL's nested subqueries or CTEs.

Key optimization: The `WHERE apple_products >= 3` filter in the WITH clause reduces the number of customers for the second MATCH. If 1,000 customers bought any Apple products but only 200 bought 3+, the second traversal only processes 200 customers instead of 1,000.

The toFloat() conversion is necessary for division in Cypher - integer division would truncate results. This is equivalent to SQL's CAST(apple_products AS FLOAT).

For production with millions of customers, add indexes:
```cypher
CREATE INDEX FOR (p:Product) ON (p.brand);
```

An alternative formulation using single-pass aggregation:
```cypher
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WITH c,
     COUNT(DISTINCT CASE WHEN p.brand = 'Apple' THEN p END) as apple_count,
     COUNT(DISTINCT p) as total_count
WHERE apple_count >= 3
RETURN c.customer_id, c.name, c.segment,
       apple_count, total_count,
       toFloat(apple_count) / total_count as loyalty_ratio
ORDER BY loyalty_ratio DESC
LIMIT 50;
```

This version is more efficient for very large datasets because it only traverses the graph once.

## Business Insights

### Graph-Specific Advantages

1. **Multi-Dimensional Loyalty**: Extend this pattern to analyze loyalty across multiple dimensions (brand + category, brand + price range) without query rewrites
2. **Loyalty Evolution**: Add temporal filtering to track how loyalty changes over time
3. **Competitive Analysis**: Compare loyalty ratios across competing brands (Apple vs Samsung) in single query

### Actionable Recommendations

1. **VIP Programs**: Customers with 0.70+ loyalty ratios are ideal for Apple partnership rewards programs
2. **Trade-In Campaigns**: High Apple loyalty customers are prime targets for iPhone upgrade campaigns
3. **Ecosystem Expansion**: Customers with high loyalty but few products (8-10) have room to expand within Apple ecosystem
4. **Brand Ambassador Recruitment**: Top 0.80+ loyalty customers could be recruited as brand advocates

## Comparison to SQL

**SQL Equivalent:**
```sql
WITH apple_buyers AS (
    SELECT c.customer_id, c.name, c.segment,
           COUNT(DISTINCT p.product_id) as apple_products
    FROM customers c
    INNER JOIN purchases pur ON c.customer_id = pur.customer_id
    INNER JOIN products p ON pur.product_id = p.product_id
    WHERE p.brand = 'Apple'
    GROUP BY c.customer_id, c.name, c.segment
    HAVING COUNT(DISTINCT p.product_id) >= 3
),
all_purchases AS (
    SELECT c.customer_id,
           COUNT(DISTINCT p.product_id) as total_products
    FROM customers c
    INNER JOIN purchases pur ON c.customer_id = pur.customer_id
    INNER JOIN products p ON pur.product_id = p.product_id
    WHERE c.customer_id IN (SELECT customer_id FROM apple_buyers)
    GROUP BY c.customer_id
)
SELECT ab.customer_id, ab.name, ab.segment,
       ab.apple_products, ap.total_products,
       CAST(ab.apple_products AS FLOAT) / ap.total_products as brand_loyalty_ratio
FROM apple_buyers ab
INNER JOIN all_purchases ap ON ab.customer_id = ap.customer_id
ORDER BY brand_loyalty_ratio DESC
LIMIT 50;
```

The Cypher version is more readable and performant with fewer JOINs and CTEs.

## Related Queries

1. **Query 7: High-Value Customer Patterns** - Context on VIP purchasing behavior
2. **Query 12: Most Popular Products by Segment** - Brand popularity across segments
3. **Query 14: Brand Performance Across Segments** - Broader brand analysis

## Try It Yourself

```bash
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE p.brand = 'Apple'
WITH c, COUNT(DISTINCT p) as apple_products
WHERE apple_products >= 3
MATCH (c)-[:PURCHASED]->(all_products:Product)
RETURN c.customer_id,
       c.name,
       c.segment,
       apple_products,
       COUNT(DISTINCT all_products) as total_products,
       toFloat(apple_products) / COUNT(DISTINCT all_products) as brand_loyalty_ratio
ORDER BY brand_loyalty_ratio DESC
LIMIT 50;

# Variations:

# 1. Multi-brand loyalty comparison:
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WITH c, p.brand as brand, COUNT(DISTINCT p) as brand_products
WHERE brand_products >= 3
MATCH (c)-[:PURCHASED]->(all:Product)
WITH c, brand, brand_products,
     COUNT(DISTINCT all) as total,
     toFloat(brand_products) / COUNT(DISTINCT all) as loyalty
WHERE loyalty > 0.5
RETURN brand, COUNT(c) as loyal_customers, AVG(loyalty) as avg_loyalty
ORDER BY loyal_customers DESC;

# 2. Category-specific brand loyalty:
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE p.brand = 'Apple' AND p.category = 'Electronics'
WITH c, COUNT(DISTINCT p) as apple_electronics
WHERE apple_electronics >= 2
MATCH (c)-[:PURCHASED]->(all:Product {category: 'Electronics'})
RETURN c.name, apple_electronics,
       COUNT(DISTINCT all) as total_electronics,
       toFloat(apple_electronics) / COUNT(DISTINCT all) as category_loyalty
ORDER BY category_loyalty DESC
LIMIT 30;
```
