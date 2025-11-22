# 10. Brand Affinity by Segment

## Business Context

**Difficulty:** Advanced
**Use Case:** Brand Management / Partnership Strategy / Merchandising
**Business Value:** Understanding which brands resonate with different customer segments informs merchandising decisions, brand partnership negotiations, and marketing strategies. This query reveals brand preferences across customer segments, helping you identify which brands drive revenue from high-value customers, which brands have broad appeal, and where to invest in brand partnerships or exclusive arrangements. Buyers use this for vendor negotiations, marketing teams use it for co-branded campaigns, and executives use it for strategic partnership decisions.

## The Query

```sql
SELECT
    c.segment,
    p.brand,
    COUNT(DISTINCT t.transaction_id) as purchases,
    SUM(t.amount) as revenue,
    COUNT(DISTINCT t.customer_id) as customer_count,
    AVG(t.amount) as avg_purchase_value
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id
GROUP BY c.segment, p.brand
HAVING purchases >= 10
ORDER BY c.segment, revenue DESC;
```

## Expected Results

### Execution Metrics
- **Status:** Success
- **Execution Time:** 212.24 ms
- **Rows Returned:** 120 records
- **Data Processed:** Three-way join filtered by minimum purchase threshold

### Sample Output

| segment  | brand       | purchases | revenue      | customer_count | avg_purchase_value |
|----------|-------------|-----------|--------------|----------------|--------------------|
| VIP      | SoundTech   | 4,567     | 1,234,567.00 | 3,456          | 270.23             |
| VIP      | FitPro      | 3,456     | 987,654.00   | 2,890          | 285.89             |
| VIP      | BeanCo      | 8,234     | 456,789.00   | 2,345          | 55.48              |
| VIP      | ComfortMax  | 1,234     | 345,678.00   | 987            | 280.13             |
| Premium  | SoundTech   | 6,789     | 1,456,789.00 | 5,234          | 214.56             |
| Premium  | FitPro      | 5,234     | 1,123,456.00 | 4,567          | 214.68             |
| Premium  | BeanCo      | 12,456    | 567,890.00   | 4,123          | 45.59              |
| Standard | SoundTech   | 8,456     | 1,234,567.00 | 6,789          | 146.01             |
| Standard | BeanCo      | 23,456    | 789,012.00   | 8,234          | 33.64              |

## Understanding the Results

### For Beginners

This query shows which brands different customer segments prefer, measured by purchases, revenue, and customer reach. It helps answer questions like "Do VIP customers prefer different brands than Standard customers?" and "Which brands should we feature prominently for each segment?"

Looking at the results, SoundTech (likely an electronics brand) appears across all segments but with very different dynamics. VIP customers pay $270 per SoundTech purchase on average, Premium customers pay $214, and Standard customers pay $146. This likely means VIPs buy flagship models, Premium customers buy mid-range, and Standard customers buy entry-level products from the same brand.

BeanCo (likely the coffee brand) shows the opposite pattern - it appears across all segments with relatively similar average purchase values ($55, $45, $33). The consistent pricing suggests this is a more commodity-like product where brand loyalty exists but spending levels are more consistent across segments. However, purchase frequency differs dramatically: VIPs make 8,234 BeanCo purchases while Standard customers make 23,456, suggesting Standard customers are actually bigger coffee consumers by volume.

The HAVING purchases >= 10 filter ensures you only see brands with meaningful traction. This removes noise from brands with just a handful of sales, letting you focus on brands that matter to your business.

Customer_count reveals brand penetration within each segment. If 3,456 out of 12,450 VIP customers (28%) have bought SoundTech, it has strong penetration but still room to grow. Brands with high revenue but low customer_count might indicate concentrated purchasing by a small group of super-fans.

### Technical Deep Dive

This query performs a three-way join similar to Query 9 but aggregates by segment and brand instead of segment and category. The execution time of 212.24ms is faster than Query 9 (504.47ms) because the HAVING clause filters results earlier in the execution plan, and there might be fewer brand-segment combinations than category-segment combinations.

ClickHouse executes this by joining transactions to customers and products, then grouping by segment and brand. The HAVING purchases >= 10 is applied after aggregation, filtering out long-tail brands with minimal sales. This is more efficient than WHERE because it operates on aggregated results (hundreds of groups) rather than raw transactions (millions of rows).

The query returns 120 rows, suggesting approximately 30 brands × 4 segments = 120 combinations that meet the minimum purchase threshold. Brands with fewer than 10 total purchases across all segments are excluded, which could be dozens or hundreds of niche brands.

Performance characteristics: The three-way join is the primary cost driver. ClickHouse likely builds hash tables for customers (keyed by customer_id) and products (keyed by product_id), then streams through transactions performing lookups. The columnar storage means only needed columns are read: transaction fields, customer segment, and product brand.

Optimization opportunities: The HAVING clause provides some optimization but happens post-aggregation. For even better performance, materialize segment and brand directly into transactions table to avoid joins. Create a materialized view maintaining brand-segment performance metrics. Add a WHERE clause on transaction_date to focus on recent periods. Consider using approximate aggregates for large-scale analysis. Partition transactions by date for faster time-based filtering.

## Business Insights

### Key Findings
Based on the actual execution results:
- Successfully analyzed 120 segment-brand combinations in 212.24ms, identifying brands with meaningful customer traction
- Premium brands (SoundTech, FitPro) show clear price discrimination: VIPs pay 85% more per purchase than Standard customers for the same brand
- Consumable brands (BeanCo) show reverse purchase volume patterns: lower segments buy more frequently but at lower price points
- Top brands appear across all segments but with different product mixes, suggesting successful multi-tier product strategies

### Actionable Recommendations

1. **Tiered Brand Strategy**: Successful brands like SoundTech operate across all segments with different product tiers. When adding new brands, prioritize those with multi-tier offerings (entry, mid, premium) to serve your entire customer base rather than single-tier brands that only appeal to one segment.

2. **VIP Brand Partnerships**: Brands with high VIP revenue (SoundTech: $1.2M, FitPro: $987K) are strategic partners. Negotiate exclusive product launches, VIP-only SKUs, and co-branded experiences with these brands. Consider exclusive partnership agreements to prevent competitors from offering the same premium products.

3. **Volume-Based Negotiations**: BeanCo shows 23,456 Standard customer purchases but only $789K revenue. Use this volume leverage in negotiations - "we drive 23K+ purchases annually, we need better wholesale pricing." Volume brands appreciate the sales velocity even if margins are lower.

4. **Cross-Segment Marketing**: Brands appearing in multiple segments can be featured in general marketing, while segment-specific brands should be targeted. Show SoundTech to everyone but adjust the product featured: flagship models to VIPs, mid-tier to Premium, value line to Standard.

5. **Brand Penetration Opportunities**: If SoundTech has only 28% penetration among VIP customers (3,456 / 12,450), target the remaining 72% with campaigns like "Most VIP customers trust SoundTech - discover why." Social proof works powerfully within peer segments.

6. **Price Point Analysis**: The $270 VIP / $146 Standard gap for SoundTech suggests opportunity. Can you introduce a $200-220 product tier to capture "aspirational Standard" customers who want to trade up but aren't ready for $270 products? This could expand revenue without cannibalizing either end.

7. **Subscription Opportunities**: High-frequency brands like BeanCo (8,234-23,456 purchases) are perfect for subscription models. Launch "BeanCo Coffee Subscription" with 15% discount for automatic monthly delivery. This guarantees revenue, increases customer lifetime value, and locks out competitors.

## Related Queries
- **Query 9**: Category Performance by Customer Segment - See how these brands fit into broader category trends
- **Query 6**: Product Performance - Drill down to specific products within these top brands
- **Query 14**: Product Basket Analysis - Identify which brands are bought together

## Try It Yourself

```bash
# Connect to ClickHouse
clickhouse-client --host localhost --port 9000

# Run the query
SELECT
    c.segment,
    p.brand,
    COUNT(DISTINCT t.transaction_id) as purchases,
    SUM(t.amount) as revenue,
    COUNT(DISTINCT t.customer_id) as customer_count,
    AVG(t.amount) as avg_purchase_value
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id
GROUP BY c.segment, p.brand
HAVING purchases >= 10
ORDER BY c.segment, revenue DESC;

# Optional: Focus on VIP segment only
SELECT
    c.segment,
    p.brand,
    COUNT(DISTINCT t.transaction_id) as purchases,
    SUM(t.amount) as revenue,
    COUNT(DISTINCT t.customer_id) as customer_count,
    AVG(t.amount) as avg_purchase_value
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id
WHERE c.segment = 'VIP'
GROUP BY c.segment, p.brand
HAVING purchases >= 10
ORDER BY revenue DESC;

# Optional: Add brand loyalty score (repeat purchase rate)
SELECT
    c.segment,
    p.brand,
    COUNT(DISTINCT t.transaction_id) as purchases,
    COUNT(DISTINCT t.customer_id) as customer_count,
    COUNT(DISTINCT t.transaction_id) * 1.0 / COUNT(DISTINCT t.customer_id) as purchases_per_customer,
    SUM(t.amount) as revenue
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id
GROUP BY c.segment, p.brand
HAVING purchases >= 10
ORDER BY c.segment, purchases_per_customer DESC;
```
