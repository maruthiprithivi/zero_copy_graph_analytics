# 19. Low Engagement Customers in High-Value Segments

## Business Context

**Difficulty:** Intermediate | **Graph Pattern:** OPTIONAL MATCH with filtering | **Use Case:** Churn Prevention, Retention Campaigns | **Business Value:** Identify VIP and Premium customers with low purchase counts - they have high lifetime value but low engagement, indicating churn risk or recent segment upgrades. These customers need immediate retention intervention.

## The Query

```cypher
MATCH (c:Customer)
WHERE c.segment IN ['VIP', 'Premium']
OPTIONAL MATCH (c)-[:PURCHASED]->(p:Product)
WITH c, COUNT(p) as purchase_count
WHERE purchase_count < 3
RETURN c.customer_id,
       c.name,
       c.segment,
       c.lifetime_value,
       purchase_count
ORDER BY c.lifetime_value DESC
LIMIT 50;
```

## Expected Results

High-value customers with fewer than 3 purchases - either at-risk veterans or newly upgraded customers needing engagement.

**Expected Rows:** Up to 50 customers | **Execution Time:** 150-250ms | **Hops:** 1 (optional)

### Sample Output

| customer_id | name | segment | lifetime_value | purchase_count |
|-------------|------|---------|----------------|----------------|
| CUST_78234 | Jennifer Wang | VIP | 15,200.00 | 2 |
| CUST_45019 | Michael Torres | VIP | 12,850.00 | 1 |
| CUST_92103 | Sarah Anderson | Premium | 8,430.00 | 2 |
| CUST_61847 | David Kim | Premium | 7,920.00 | 0 |

## Understanding the Results

### For Beginners

OPTIONAL MATCH is like a LEFT JOIN in SQL - it returns customers even if they have no purchases. This is important because some customers might have lifetime_value from activities other than tracked purchases, or they're newly added to the system.

The WITH clause counts purchases (including 0 for customers with no matches), then filters to customers with fewer than 3. These are your at-risk VIPs - high value but low engagement.

A VIP with $15,200 lifetime value but only 2 purchases is unusual. They might be:
1. Recently upgraded to VIP (previous purchases not tracked)
2. Churning (stopped purchasing)
3. Bulk buyers (few purchases, high value per transaction)
4. Data quality issues (missing purchase records)

All scenarios require attention - either welcome campaigns for new VIPs or retention efforts for churning ones.

### Technical Deep Dive

OPTIONAL MATCH allows patterns that might not exist. Without OPTIONAL, customers with zero purchases wouldn't appear in results. With OPTIONAL, they appear with p=NULL, which COUNT(p) treats as 0.

The WHERE filter after WITH operates on aggregated results (purchase_count), not on individual rows. This is equivalent to SQL's HAVING clause.

For production, add temporal context:
```cypher
MATCH (c:Customer)
WHERE c.segment IN ['VIP', 'Premium']
OPTIONAL MATCH (c)-[r:PURCHASED]->(p:Product)
WHERE r.purchase_date > date() - duration('P180D')
WITH c, COUNT(p) as recent_purchases
WHERE recent_purchases < 3
RETURN c.customer_id, c.name, c.segment, c.lifetime_value,
       recent_purchases
ORDER BY c.lifetime_value DESC, recent_purchases ASC
LIMIT 50;
```

This focuses on recent engagement (last 6 months), which is a better churn indicator than all-time purchase count.

## Business Insights

### Graph-Specific Advantages

OPTIONAL MATCH enables complex null-handling scenarios that are awkward in SQL. Finding customers with low relationship counts (or no relationships) is natural in graph queries but requires LEFT JOINs with COALESCE in SQL.

### Actionable Recommendations

1. **Immediate Outreach**: VIPs with 0-2 purchases and high LTV need personal account manager contact within 48 hours
2. **Win-Back Campaigns**: Automated email series with exclusive offers and re-engagement incentives
3. **Survey Deployment**: Understand why engagement is low - product selection issues, pricing concerns, or competitive switching
4. **Upgrade Validation**: Check if these customers were recently upgraded; if so, implement new VIP onboarding sequence

## Comparison to SQL

**SQL Equivalent:**
```sql
SELECT c.customer_id, c.name, c.segment, c.lifetime_value,
       COUNT(pur.purchase_id) as purchase_count
FROM customers c
LEFT JOIN purchases pur ON c.customer_id = pur.customer_id
WHERE c.segment IN ('VIP', 'Premium')
GROUP BY c.customer_id, c.name, c.segment, c.lifetime_value
HAVING COUNT(pur.purchase_id) < 3
ORDER BY c.lifetime_value DESC
LIMIT 50;
```

The Cypher version is more concise and the OPTIONAL MATCH intent is clearer than LEFT JOIN.

## Related Queries

1. **Query 7: High-Value Customer Purchase Patterns** - Context on typical VIP behavior
2. **Query 10: Category Gap Opportunities** - Specific cross-sell targets for these customers
3. **Query 20: Cross-Category Purchase Diversity** - Engagement breadth analysis

## Try It Yourself

```bash
MATCH (c:Customer)
WHERE c.segment IN ['VIP', 'Premium']
OPTIONAL MATCH (c)-[:PURCHASED]->(p:Product)
WITH c, COUNT(p) as purchase_count
WHERE purchase_count < 3
RETURN c.customer_id, c.name, c.segment,
       c.lifetime_value, purchase_count
ORDER BY c.lifetime_value DESC
LIMIT 50;

# Recent engagement version:
MATCH (c:Customer)
WHERE c.segment IN ['VIP', 'Premium']
OPTIONAL MATCH (c)-[r:PURCHASED]->(p:Product)
WHERE r.purchase_date > date() - duration('P180D')
WITH c, COUNT(p) as recent_purchases
WHERE recent_purchases < 3
RETURN c.customer_id, c.name, c.segment,
       c.lifetime_value, recent_purchases,
       CASE
         WHEN recent_purchases = 0 THEN 'CRITICAL'
         WHEN recent_purchases = 1 THEN 'HIGH'
         ELSE 'MEDIUM'
       END as churn_risk
ORDER BY churn_risk, c.lifetime_value DESC
LIMIT 50;
```
