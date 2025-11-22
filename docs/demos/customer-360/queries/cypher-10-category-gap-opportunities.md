# 10. Find Customers Without Purchases in High-Value Categories

## Business Context

**Difficulty:** Intermediate
**Graph Pattern:** Negation pattern with EXISTS clause
**Use Case:** Cross-Sell Opportunities, Targeted Marketing
**Business Value:** Identify high-value customers (VIP/Premium) who haven't purchased from profitable categories like Electronics. These represent immediate cross-sell opportunities with high conversion potential because the customers already trust your brand and have purchasing power.

## The Query

```cypher
MATCH (c:Customer)
WHERE c.segment IN ['VIP', 'Premium']
  AND NOT EXISTS {
    MATCH (c)-[:PURCHASED]->(p:Product)
    WHERE p.category = 'Electronics'
  }
RETURN c.customer_id,
       c.name,
       c.segment,
       c.lifetime_value
ORDER BY c.lifetime_value DESC
LIMIT 100;
```

## Graph Visualization Concept

Customer nodes without any PURCHASED edges to Electronics products. In a full graph visualization, you'd see VIP customers connected to Home, Apparel, and Grocery products, but with a conspicuous absence of connections to the Electronics category cloud - representing untapped potential.

## Expected Results

### Execution Metrics
- **Status:** Skipped (mock mode)
- **Expected Execution Time:** 100-200ms
- **Expected Rows:** Up to 100 customers
- **Hops/Depth:** 1 (with negation check)

### Sample Output

| customer_id | name | segment | lifetime_value |
|-------------|------|---------|----------------|
| CUST_45821 | Maria Garcia | VIP | 18,750.00 |
| CUST_23910 | Thomas Anderson | VIP | 16,200.00 |
| CUST_67234 | Patricia Wilson | Premium | 14,850.00 |
| CUST_39105 | Christopher Lee | VIP | 13,420.00 |
| CUST_51672 | Elizabeth Brown | Premium | 11,990.00 |

## Understanding the Results

### For Beginners

The NOT EXISTS clause checks for the absence of a pattern. This query finds VIP and Premium customers who have never bought from the Electronics category - a missed opportunity since these customers have high lifetime value and purchasing power.

Think of NOT EXISTS as asking "show me customers where this pattern doesn't exist". It's the opposite of a normal MATCH, which finds where patterns do exist. These customers are already engaged (high lifetime value) but haven't explored Electronics, making them prime targets for Electronics campaigns with high conversion probability.

The EXISTS clause is like checking "does this customer have any Electronics purchases?" If the answer is no, they're included in results. If yes, they're filtered out.

### Technical Deep Dive

The NOT EXISTS pattern in Cypher is equivalent to SQL's NOT EXISTS subquery but more concise. The inner MATCH describes the pattern you're checking for absence of - in this case, a PURCHASED relationship to an Electronics product.

Execution plan: (1) Scan customers where segment IN ['VIP', 'Premium'], (2) For each customer, check if EXISTS pattern matches (quick check using relationship indexes), (3) Keep only customers where pattern doesn't exist, (4) Sort by lifetime_value and limit.

The EXISTS check is optimized - it doesn't need to find all Electronics purchases, just whether at least one exists. It short-circuits on first match, making it efficient even for customers with hundreds of purchases.

Performance optimization with indexes:
```cypher
CREATE INDEX FOR (c:Customer) ON (c.segment);
CREATE INDEX FOR (p:Product) ON (p.category);
```

Alternative formulation using OPTIONAL MATCH:
```cypher
MATCH (c:Customer)
WHERE c.segment IN ['VIP', 'Premium']
OPTIONAL MATCH (c)-[:PURCHASED]->(p:Product)
WHERE p.category = 'Electronics'
WITH c, COUNT(p) as electronics_purchases
WHERE electronics_purchases = 0
RETURN c.customer_id, c.name, c.segment, c.lifetime_value
ORDER BY c.lifetime_value DESC
LIMIT 100;
```

This OPTIONAL MATCH version is less efficient because it must count all Electronics purchases (or confirm zero), while NOT EXISTS can exit early.

## Business Insights

### Graph-Specific Advantages

1. **Negative Pattern Matching**: Graph databases excel at finding absence of relationships - something that's expensive in SQL with LEFT JOIN + NULL checks
2. **Segmentation + Behavior**: Combining customer properties (segment, lifetime_value) with relationship absence enables sophisticated targeting
3. **Real-Time Gap Analysis**: As customers make purchases, they automatically exit this result set - always up-to-date

### Actionable Recommendations

1. **Targeted Email Campaigns**: Send "Discover Our Electronics" campaigns to these 100 customers with personalized product recommendations
2. **Exclusive Offers**: Provide first-time Electronics buyer discounts (10-15% off) to convert these high-value prospects
3. **Sales Outreach**: For VIPs with $15,000+ lifetime value, personal outreach from account managers
4. **Category Launch Campaigns**: When launching new Electronics products, prioritize these customers for early access

## Comparison to SQL

**SQL Equivalent:**
```sql
SELECT c.customer_id, c.name, c.segment, c.lifetime_value
FROM customers c
WHERE c.segment IN ('VIP', 'Premium')
  AND NOT EXISTS (
    SELECT 1
    FROM purchases pur
    INNER JOIN products p ON pur.product_id = p.product_id
    WHERE pur.customer_id = c.customer_id
      AND p.category = 'Electronics'
  )
ORDER BY c.lifetime_value DESC
LIMIT 100;
```

**Why Cypher is Better:**
- More concise negation syntax
- No JOIN required in the subquery
- Clearer intent: "customers without this relationship pattern"
- Better performance through early-exit optimization

## Related Queries

1. **Query 11: Category Gap Analysis** - Identifies customers with category A but not category B purchases
2. **Query 19: Low Engagement Customers** - Finds high-value customers with low overall purchase counts
3. **Query 6: Category Expansion Recommendations** - Shows which categories customers do expand into

## Try It Yourself

```bash
MATCH (c:Customer)
WHERE c.segment IN ['VIP', 'Premium']
  AND NOT EXISTS {
    MATCH (c)-[:PURCHASED]->(p:Product)
    WHERE p.category = 'Electronics'
  }
RETURN c.customer_id,
       c.name,
       c.segment,
       c.lifetime_value
ORDER BY c.lifetime_value DESC
LIMIT 100;

# Variations:

# 1. Multiple category gaps:
MATCH (c:Customer)
WHERE c.segment = 'VIP'
  AND NOT EXISTS {
    MATCH (c)-[:PURCHASED]->(p:Product)
    WHERE p.category IN ['Electronics', 'Home']
  }
RETURN c.customer_id, c.name, c.lifetime_value
ORDER BY c.lifetime_value DESC;

# 2. Recent customer gaps (engaged but not in Electronics):
MATCH (c:Customer)-[r:PURCHASED]->(:Product)
WHERE c.segment IN ['VIP', 'Premium']
  AND r.purchase_date > date() - duration('P90D')
  AND NOT EXISTS {
    MATCH (c)-[:PURCHASED]->(p:Product {category: 'Electronics'})
  }
RETURN DISTINCT c.customer_id, c.name, c.lifetime_value
ORDER BY c.lifetime_value DESC
LIMIT 50;

# 3. Category gap with purchase count context:
MATCH (c:Customer)
WHERE c.segment IN ['VIP', 'Premium']
  AND NOT EXISTS {
    MATCH (c)-[:PURCHASED]->(p:Product {category: 'Electronics'})
  }
OPTIONAL MATCH (c)-[:PURCHASED]->(all_products:Product)
WITH c, COUNT(DISTINCT all_products) as total_purchases
WHERE total_purchases >= 10
RETURN c.customer_id, c.name, c.lifetime_value, total_purchases
ORDER BY c.lifetime_value DESC
LIMIT 100;
```
