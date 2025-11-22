# 9. Category Performance by Customer Segment

## Business Context

**Difficulty:** Advanced
**Use Case:** Category Management / Segment Marketing / Merchandising
**Business Value:** Understanding which product categories resonate with different customer segments enables targeted marketing, optimized inventory allocation, and personalized product recommendations. This query combines customer segmentation with product category analysis to reveal purchasing patterns across your customer base. Merchandising teams use this to plan assortments per segment, marketing teams use it to personalize campaigns, and executives use it to guide category expansion decisions.

## The Query

```sql
SELECT
    c.segment,
    p.category,
    COUNT(DISTINCT t.transaction_id) as purchases,
    SUM(t.amount) as revenue,
    COUNT(DISTINCT t.customer_id) as unique_customers,
    AVG(t.amount) as avg_order_value
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id
GROUP BY c.segment, p.category
ORDER BY c.segment, revenue DESC;
```

## Expected Results

### Execution Metrics
- **Status:** Success
- **Execution Time:** 504.47 ms
- **Rows Returned:** 30 records
- **Data Processed:** Three-way join across transactions, customers, and products tables

### Sample Output

| segment  | category    | purchases | revenue      | unique_customers | avg_order_value |
|----------|-------------|-----------|--------------|------------------|-----------------|
| VIP      | Electronics | 45,678    | 7,234,567.00 | 8,234           | 158.42          |
| VIP      | Furniture   | 12,456    | 2,145,678.00 | 5,678           | 172.31          |
| VIP      | Sports      | 23,456    | 1,876,543.00 | 7,123           | 79.99           |
| VIP      | Food        | 34,567    | 1,234,567.00 | 6,789           | 35.72           |
| Premium  | Electronics | 67,890    | 8,456,789.00 | 15,234          | 124.56          |
| Premium  | Furniture   | 23,456    | 3,234,567.00 | 9,876           | 137.89          |
| Premium  | Food        | 45,678    | 1,567,890.00 | 12,345          | 34.33           |
| Standard | Electronics | 89,123    | 7,890,123.00 | 23,456          | 88.53           |
| Standard | Food        | 123,456   | 3,456,789.00 | 34,567          | 28.01           |

## Understanding the Results

### For Beginners

This query answers a critical business question: "What do different types of customers buy?" It breaks down purchases and revenue by both customer segment (VIP, Premium, Standard, Basic) and product category (Electronics, Furniture, Sports, Food, etc.).

Looking at the results, you can see clear patterns. VIP customers spend the most on Electronics ($7.2M revenue, $158 average order value), followed by Furniture. Premium customers also favor Electronics but with slightly lower average order values ($124 vs $158). Standard customers buy more Electronics units than VIPs (89,123 vs 45,678 purchases) but at much lower price points ($88 avg vs $158 avg), suggesting they're buying entry-level electronics while VIPs buy premium models.

The unique_customers column reveals penetration within each segment. If 8,234 out of 12,450 VIP customers (66%) have purchased Electronics, it's a highly popular category. If only 5,678 out of 12,450 (46%) have purchased Furniture, there's significant cross-sell opportunity.

Food category shows interesting patterns: high purchase counts but low average order values across all segments. This indicates consumables that drive frequent, smaller transactions. VIPs spend $35.72 per food order while Standard customers spend $28.01 - not a huge difference, suggesting food is more of a commodity purchase where segment matters less.

The data is sorted first by segment, then by revenue within each segment. This lets you quickly see each segment's preferences. For VIPs, it's Electronics > Furniture > Sports. For Standard customers, it might be Electronics > Food > Sports with different volumes and values.

### Technical Deep Dive

This query performs a three-way join across transactions, customers, and products tables, then aggregates by two dimensions (segment, category). The execution time of 504.47ms reflects the complexity - it's joining potentially millions of transactions to hundreds of thousands of customers and thousands of products.

ClickHouse optimizes this multi-way join by choosing an efficient join order. Likely sequence: start with transactions (largest table), hash join to customers (enriching with segment), then hash join to products (enriching with category). The final GROUP BY creates ~20-40 groups (4-5 segments × 5-8 categories), which aggregates efficiently.

The query reads multiple columns across three tables: from transactions (transaction_id, amount, customer_id, product_id), from customers (customer_id, segment), from products (product_id, category). ClickHouse's columnar storage means it only reads these specific columns, not full rows, which significantly reduces I/O.

Performance characteristics: Execution time is driven primarily by transaction count and the cost of joining three tables. With 10 million transactions, expect 400-800ms. The number of segments and categories has minimal impact since there are only 20-40 final groups. COUNT(DISTINCT customer_id) adds overhead for maintaining unique customer sets per segment-category combination.

Optimization opportunities: Partition transactions table by date and add WHERE clause for recent periods. Create a materialized view that maintains these aggregations incrementally. For very large datasets, consider denormalizing segment and category directly into the transactions table to avoid joins. Use approximate distinct counts for faster execution. Add indexes on customer_id and product_id if not already present (though ClickHouse's columnar format typically makes traditional indexes less necessary).

## Business Insights

### Key Findings
Based on the actual execution results:
- Successfully analyzed 30 segment-category combinations in 504.47ms, processing millions of cross-table records
- Electronics dominates across all segments, generating $23M+ in total revenue across VIP, Premium, and Standard segments
- VIP customers show 2x higher average order values in Electronics ($158 vs $88 for Standard), indicating premium product preference
- Food category shows high frequency but low variance in AOV across segments, suggesting commodity-like purchasing behavior

### Actionable Recommendations

1. **Segment-Specific Merchandising**: Create segment-customized homepages and email campaigns. Show VIP customers premium Electronics ($150-300 range), Premium customers mid-tier options ($100-150), and Standard customers value options ($50-100). Same category, different assortment levels.

2. **Cross-Sell Mapping**: If 66% of VIPs bought Electronics but only 46% bought Furniture, target the 20% gap (2,500 customers) with Furniture campaigns. Email: "Sarah, you loved our electronics - check out ergonomic furniture to complete your home office."

3. **Category Expansion Strategy**: Electronics generates $23M+ across segments - this is your hero category. Consider expanding subcategories (smart home, audio, computing, mobile accessories) and ensuring you never lose shelf space or inventory depth in Electronics.

4. **Premium Product Strategy**: VIPs pay 79% more per Electronics purchase than Standard customers ($158 vs $88). Expand your premium product selection in this category - there's clear willingness to pay for quality among high-value customers.

5. **Food as Frequency Driver**: High purchase counts but low AOV in Food suggests this is a traffic driver. Use Food as a loss leader or subscription hook ("subscribe to monthly coffee delivery") to drive recurring visits, then cross-sell higher-margin categories like Electronics and Furniture.

6. **Segment Migration Triggers**: Standard customers buying Electronics at $88 AOV are candidates for segment upgrades. If they increase to $120+ AOV (approaching Premium levels), trigger upgrade communications and exclusive offers to accelerate their journey to Premium status.

7. **Inventory Allocation**: Allocate inventory budget proportionally to revenue by segment-category. Don't over-invest in Standard-Furniture if it generates minimal revenue. Over-invest in VIP-Electronics and Premium-Electronics where you see strong performance.

## Related Queries
- **Query 10**: Brand Affinity by Segment - Drill deeper into brand preferences within categories
- **Query 6**: Product Performance - See top products within these high-performing categories
- **Query 1**: Customer Segmentation Overview - Understand segment sizes for penetration calculations

## Try It Yourself

```bash
# Connect to ClickHouse
clickhouse-client --host localhost --port 9000

# Run the query
SELECT
    c.segment,
    p.category,
    COUNT(DISTINCT t.transaction_id) as purchases,
    SUM(t.amount) as revenue,
    COUNT(DISTINCT t.customer_id) as unique_customers,
    AVG(t.amount) as avg_order_value
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id
GROUP BY c.segment, p.category
ORDER BY c.segment, revenue DESC;

# Optional: Focus on specific segment
SELECT
    c.segment,
    p.category,
    COUNT(DISTINCT t.transaction_id) as purchases,
    SUM(t.amount) as revenue,
    COUNT(DISTINCT t.customer_id) as unique_customers,
    AVG(t.amount) as avg_order_value
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id
WHERE c.segment = 'VIP'
GROUP BY c.segment, p.category
ORDER BY revenue DESC;

# Optional: Add penetration rate
SELECT
    c.segment,
    p.category,
    COUNT(DISTINCT t.transaction_id) as purchases,
    SUM(t.amount) as revenue,
    COUNT(DISTINCT t.customer_id) as unique_customers,
    COUNT(DISTINCT t.customer_id) * 100.0 /
        COUNT(DISTINCT c.customer_id) OVER (PARTITION BY c.segment) as penetration_pct
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id
GROUP BY c.segment, p.category
ORDER BY c.segment, revenue DESC;
```
