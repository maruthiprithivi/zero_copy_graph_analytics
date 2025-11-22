# 11. Category Gap Analysis

## Business Context

**Difficulty:** Intermediate | **Graph Pattern:** Multi-condition negation | **Use Case:** Cross-Sell Targeting | **Business Value:** Find customers who purchased from category A but not category B, revealing specific cross-sell opportunities. Graph databases make multi-condition pattern matching intuitive through nested negation patterns.

## The Query

```cypher
MATCH (c:Customer)-[:PURCHASED]->(p1:Product)
WHERE p1.category = 'Electronics'
  AND NOT EXISTS {
    MATCH (c)-[:PURCHASED]->(p2:Product)
    WHERE p2.category = 'Home'
  }
RETURN c.customer_id,
       c.name,
       c.segment,
       COUNT(DISTINCT p1) as electronics_purchases
ORDER BY electronics_purchases DESC
LIMIT 50;
```

## Expected Results

Customers who bought Electronics (10-100+ items) but never explored Home category. These are engaged Electronics buyers who might need smart home devices, furniture, or appliances.

**Expected Rows:** 50 customers | **Execution Time:** 150-250ms | **Hops:** 1 with negation

## Business Insights

Electronics buyers often need complementary Home products (smart home devices, office furniture). A customer with 47 Electronics purchases but zero Home purchases represents a significant cross-sell gap. Target with "Complete Your Smart Home" campaigns.

## Try It Yourself

```bash
MATCH (c:Customer)-[:PURCHASED]->(p1:Product)
WHERE p1.category = 'Electronics'
  AND NOT EXISTS {
    MATCH (c)-[:PURCHASED]->(p2:Product)
    WHERE p2.category = 'Home'
  }
RETURN c.customer_id, c.name, c.segment,
       COUNT(DISTINCT p1) as electronics_purchases
ORDER BY electronics_purchases DESC
LIMIT 50;
```

## Related Queries
- Query 10: Category Gap Opportunities
- Query 6: Category Expansion Recommendations
- Query 20: Cross-Category Purchase Diversity
