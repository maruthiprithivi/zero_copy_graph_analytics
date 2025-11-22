# 7. High-Value Customer Purchase Patterns

## Business Context

**Difficulty:** Intermediate
**Graph Pattern:** Filtered traversal with aggregation
**Use Case:** VIP Customer Analysis, Segment Insights
**Business Value:** Identify purchase patterns of your most valuable customers to inform inventory, marketing, and retention strategies. Understanding what VIP and Premium customers buy helps you cater to your highest-revenue segment and identify candidates for segment upgrades.

## The Query

```cypher
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment IN ['VIP', 'Premium']
  AND c.lifetime_value > 5000
RETURN c.customer_id,
       c.name,
       c.segment,
       c.lifetime_value,
       COUNT(DISTINCT p) as unique_products,
       COLLECT(DISTINCT p.category) as categories_purchased
ORDER BY c.lifetime_value DESC
LIMIT 50;
```

## Graph Visualization Concept

High-value customer nodes (sized by lifetime_value) at the center, with PURCHASED edges radiating to products in multiple categories. VIP customers show star patterns with 10-50+ product connections across 5-8 categories, indicating high engagement and diversity.

## Expected Results

### Execution Metrics
- **Status:** Skipped (mock mode)
- **Expected Execution Time:** 150-250ms
- **Expected Rows:** 50 customers
- **Hops/Depth:** 1

### Sample Output

| customer_id | name | segment | lifetime_value | unique_products | categories_purchased |
|-------------|------|---------|----------------|-----------------|---------------------|
| CUST_10045 | Emily Rodriguez | VIP | 28,750.00 | 147 | [Electronics, Home, Apparel, Beauty, Sports, Grocery] |
| CUST_23891 | Michael Chen | VIP | 24,200.00 | 98 | [Electronics, Home, Books, Sports] |
| CUST_15602 | Sarah Williams | VIP | 19,850.00 | 134 | [Electronics, Apparel, Beauty, Home, Grocery, Toys] |
| CUST_44721 | James Brown | Premium | 17,320.00 | 76 | [Electronics, Sports, Home] |

## Understanding the Results

### For Beginners

This query finds your best customers (VIP/Premium with $5,000+ lifetime value) and shows how many different products they've bought and which categories they shop in. The COLLECT function gathers all unique categories into a list, making it easy to see purchase diversity.

High-value customers typically buy across many categories - they're highly engaged with your brand. A VIP with 147 products across 6 categories is a loyal, active customer worth significant retention investment.

### Technical Deep Dive

The query combines property filtering (segment, lifetime_value), relationship traversal (PURCHASED), and aggregation (COUNT, COLLECT). The IN operator filters for multiple segment values efficiently.

COLLECT(DISTINCT p.category) is a powerful Cypher aggregation that creates a list of unique values. In SQL, you'd need STRING_AGG or GROUP_CONCAT, which are less elegant.

The filter `c.lifetime_value > 5000` should use an index:
```cypher
CREATE INDEX FOR (c:Customer) ON (c.lifetime_value);
CREATE INDEX FOR (c:Customer) ON (c.segment);
```

For production, consider adding time-based filtering to focus on recent engagement:
```cypher
MATCH (c:Customer)-[r:PURCHASED]->(p:Product)
WHERE c.segment IN ['VIP', 'Premium']
  AND c.lifetime_value > 5000
  AND r.purchase_date > date() - duration('P365D')
RETURN c.customer_id, c.name, c.segment, c.lifetime_value,
       COUNT(DISTINCT p) as products_last_year,
       COLLECT(DISTINCT p.category) as categories
ORDER BY c.lifetime_value DESC, products_last_year DESC
LIMIT 50;
```

## Business Insights

### Graph-Specific Advantages

Graph databases excel at customer-centric analysis because the customer node is the natural starting point for traversals. You can instantly see all purchase relationships and aggregate patterns without complex joins.

### Actionable Recommendations

1. **Retention Focus**: Top 50 high-value customers represent 20-30% of revenue - invest in white-glove service
2. **Category Expansion**: Customers with low category diversity have room for growth
3. **Segment Validation**: Premium customers with high product counts might merit VIP upgrade
4. **Churn Prevention**: Monitor for declining purchase counts in this cohort

## Related Queries

1. **Query 8: Brand Loyalty Analysis** - Analyzes brand preferences among high-value customers
2. **Query 19: Low Engagement Customers** - Identifies at-risk high-value customers
3. **Query 20: Cross-Category Purchase Diversity** - Measures engagement breadth

## Try It Yourself

```bash
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment IN ['VIP', 'Premium']
  AND c.lifetime_value > 5000
RETURN c.customer_id,
       c.name,
       c.segment,
       c.lifetime_value,
       COUNT(DISTINCT p) as unique_products,
       COLLECT(DISTINCT p.category) as categories_purchased
ORDER BY c.lifetime_value DESC
LIMIT 50;
```
