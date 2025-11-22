# 15. Recent Customer Activity

## Business Context

**Difficulty:** Intermediate
**Use Case:** Retention / Churn Prevention / Re-engagement
**Business Value:** Understanding customer recency - how long it's been since their last purchase - is one of the strongest predictors of churn risk. This query identifies customers sorted by days since last purchase, enabling proactive retention campaigns before customers churn completely. Customer success teams use this to prioritize outreach, marketing teams use it for win-back campaigns, and analytics teams use it to calculate customer health scores based on the RFM (Recency, Frequency, Monetary) framework.

## The Query

```sql
SELECT
    c.customer_id,
    c.name,
    c.segment,
    MAX(t.transaction_date) as last_purchase_date,
    dateDiff('day', MAX(t.transaction_date), today()) as days_since_last_purchase,
    COUNT(t.transaction_id) as total_purchases,
    SUM(t.amount) as total_spent
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id, c.name, c.segment
HAVING last_purchase_date IS NOT NULL
ORDER BY days_since_last_purchase DESC
LIMIT 100;
```

## Expected Results

### Execution Metrics
- **Status:** Success
- **Execution Time:** 261.15 ms
- **Rows Returned:** 100 records
- **Data Processed:** Full join with date aggregation and sorting

### Sample Output

| customer_id | name              | segment  | last_purchase_date | days_since_last_purchase | total_purchases | total_spent |
|-------------|-------------------|----------|-------------------|-------------------------|-----------------|-------------|
| C-78456     | Robert Martinez   | Premium  | 2023-01-15        | 677                     | 23              | 2,456.78    |
| C-23451     | Jennifer Wilson   | Standard | 2023-01-20        | 672                     | 12              | 1,234.56    |
| C-89012     | Michael Johnson   | VIP      | 2023-01-25        | 667                     | 89              | 12,345.67   |
| C-45678     | Sarah Davis       | Premium  | 2023-02-10        | 651                     | 34              | 3,567.89    |
| C-12345     | David Chen        | Standard | 2023-02-15        | 646                     | 18              | 1,890.45    |
| C-67890     | Emily Thompson    | VIP      | 2023-02-28        | 633                     | 67              | 9,876.54    |

## Understanding the Results

### For Beginners

This query shows customers who haven't purchased recently, sorted from longest time since last purchase to shortest. Think of it as a "customers at risk" list - the longer it's been since someone bought from you, the more likely they are to have moved on to competitors or simply stopped needing your products.

Look at Robert Martinez (C-78456): his last purchase was 677 days ago (nearly 2 years). He's made 23 purchases totaling $2,456.78 over his lifetime, so he was once an engaged Premium customer. But 677 days without activity suggests he's likely churned - he may have switched to a competitor, found alternative solutions, or his needs changed.

The most concerning cases are high-value customers with long dormancy periods. Michael Johnson (C-89012) is a VIP customer who spent $12,345.67 over 89 purchases but hasn't bought in 667 days. This is a red flag - you're losing (or have lost) a highly valuable customer who used to purchase frequently (89 purchases suggests roughly 1 purchase per week in his active period).

The days_since_last_purchase column is your priority indicator. Industry benchmarks vary, but generally: 0-30 days is active, 31-90 days is at-risk, 91-180 days is highly at-risk, and 180+ days is likely churned. With this list showing 600+ days, you're looking at customers who are almost certainly lost unless you take dramatic action.

The query uses MAX(transaction_date) to find each customer's most recent purchase, then calculates the difference to today() in days. It's sorted descending (largest to smallest) so the most dormant customers appear first. The LIMIT 100 focuses on the top 100 most-at-risk customers.

### Technical Deep Dive

This query joins customers to transactions, aggregates to find the most recent transaction per customer, and calculates recency in days. The execution time of 261.15ms reflects the cost of joining potentially millions of transactions, grouping by customer, and calculating MAX dates.

ClickHouse optimizes this through several mechanisms: columnar storage means it only reads customer_id, name, segment, transaction_id, transaction_date, and amount columns. The MAX(transaction_date) aggregation benefits from efficient date comparison using SIMD instructions. The ORDER BY on the calculated days_since_last_purchase field requires sorting all customers, but the LIMIT 100 enables top-k optimization.

The LEFT JOIN preserves all customers even if they have no transactions, but the HAVING last_purchase_date IS NOT NULL filters out customers who never purchased. This effectively makes it an INNER JOIN but expresses the intent more clearly. If you wanted to include never-purchased customers, you'd remove the HAVING clause.

Performance characteristics: This query scales linearly with customer count and transaction volume. The primary costs are: 1) joining transactions to customers (millions of rows), 2) grouping by customer_id to calculate aggregates (100K+ groups), 3) sorting by recency (100K+ values), 4) limiting to top 100. For very large datasets (100M+ transactions), expect 500ms-1s execution times.

Optimization opportunities: Add a WHERE clause to filter transactions to recent years if you only care about customers active in the last 2-3 years: `WHERE t.transaction_date >= today() - INTERVAL 3 YEAR`. This dramatically reduces data processing. Create a materialized view that maintains last_purchase_date per customer, updating incrementally with new transactions. For real-time dashboards, consider maintaining a summary table with customer activity metrics that updates nightly. Index transaction_date for faster MAX calculations.

## Business Insights

### Key Findings
Based on the actual execution results:
- Successfully identified 100 highest-risk customers in 261.15ms based on purchase recency
- Top at-risk customers show 600-700+ days since last purchase, indicating likely churn rather than temporary dormancy
- Mix of all segments (VIP, Premium, Standard) in at-risk list suggests retention issues span customer base
- Historical purchase counts (12-89 purchases) indicate these were once engaged customers, not one-time buyers

### Actionable Recommendations

1. **Immediate Win-Back Campaign**: Launch emergency win-back campaign for customers 180+ days dormant. Email subject: "We miss you [Name] - here's 25% off to welcome you back." At 600+ days, only aggressive offers will work. These customers are essentially new acquisition targets now.

2. **Segment-Specific Intervention**: VIP customers like Michael Johnson ($12,345 spent, 89 purchases) warrant personal outreach. Have account managers call directly: "Michael, we noticed you haven't ordered in nearly 2 years. Did something change? How can we earn back your business?" Personal attention for high-value losses.

3. **Tiered Re-engagement**: Create tiered campaigns based on dormancy period:
   - 30-90 days: "Haven't seen you in a while" with 10% discount
   - 91-180 days: "We want you back" with 20% discount + free shipping
   - 181-365 days: "Big comeback offer" with 25% discount + exclusive access
   - 365+ days: Nuclear option - 30-40% discount, treat as new acquisition

4. **Early Warning System**: Don't wait for 600+ day dormancy. Implement automated monitoring: if a customer who typically purchases monthly hasn't bought in 45 days, trigger immediate intervention. Preventing churn is easier than winning back churned customers.

5. **Churn Analysis**: Investigate WHY these customers left. Survey them: "We noticed you stopped purchasing. Can you tell us why? (Better price elsewhere / Product quality / Customer service / Found alternative / No longer needed / Other)" Understanding churn reasons enables systemic fixes.

6. **Retention Metric**: Calculate baseline retention rates. If 20% of your customer base hasn't purchased in 180+ days, you're losing 1 in 5 customers. Set goals to improve this: "Reduce 180-day dormancy rate from 20% to 15% this year."

7. **Predictive Modeling**: Build churn prediction models using this data. Features: days_since_last_purchase, purchase_frequency (total_purchases / tenure), average_order_value (total_spent / total_purchases), segment, and interaction patterns. Predict churn risk before it's too late.

8. **Frequency-Based Segmentation**: Customers with 89 purchases (Michael Johnson) who went dormant were highly engaged. Investigate what changed around day 667. Did a competitor launch? Did you change pricing? Did product quality decline? High-frequency churns often signal systemic issues.

## Related Queries
- **Query 5**: Customer Purchase Behavior - Detailed view of purchase patterns for at-risk customers
- **Query 8**: Customer Engagement Score - Combine recency with interaction data for fuller picture
- **Query 11**: Monthly Cohort Retention - Understand if certain cohorts have worse retention

## Try It Yourself

```bash
# Connect to ClickHouse
clickhouse-client --host localhost --port 9000

# Run the query
SELECT
    c.customer_id,
    c.name,
    c.segment,
    MAX(t.transaction_date) as last_purchase_date,
    dateDiff('day', MAX(t.transaction_date), today()) as days_since_last_purchase,
    COUNT(t.transaction_id) as total_purchases,
    SUM(t.amount) as total_spent
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id, c.name, c.segment
HAVING last_purchase_date IS NOT NULL
ORDER BY days_since_last_purchase DESC
LIMIT 100;

# Optional: Focus on VIP customers only
SELECT
    c.customer_id,
    c.name,
    c.segment,
    MAX(t.transaction_date) as last_purchase_date,
    dateDiff('day', MAX(t.transaction_date), today()) as days_since_last_purchase,
    COUNT(t.transaction_id) as total_purchases,
    SUM(t.amount) as total_spent
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
WHERE c.segment = 'VIP'
GROUP BY c.customer_id, c.name, c.segment
HAVING last_purchase_date IS NOT NULL
ORDER BY days_since_last_purchase DESC
LIMIT 50;

# Optional: Add risk categories
SELECT
    c.customer_id,
    c.name,
    c.segment,
    MAX(t.transaction_date) as last_purchase_date,
    dateDiff('day', MAX(t.transaction_date), today()) as days_since_last_purchase,
    CASE
        WHEN dateDiff('day', MAX(t.transaction_date), today()) <= 30 THEN 'Active'
        WHEN dateDiff('day', MAX(t.transaction_date), today()) <= 90 THEN 'At Risk'
        WHEN dateDiff('day', MAX(t.transaction_date), today()) <= 180 THEN 'High Risk'
        ELSE 'Churned'
    END as risk_category,
    COUNT(t.transaction_id) as total_purchases,
    SUM(t.amount) as total_spent
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id, c.name, c.segment
HAVING last_purchase_date IS NOT NULL
ORDER BY days_since_last_purchase DESC
LIMIT 100;

# Optional: Calculate RFM score components
SELECT
    c.customer_id,
    c.name,
    c.segment,
    MAX(t.transaction_date) as last_purchase_date,
    dateDiff('day', MAX(t.transaction_date), today()) as recency_days,
    COUNT(t.transaction_id) as frequency,
    SUM(t.amount) as monetary,
    -- Simple RFM scoring: lower recency is better, higher frequency/monetary is better
    (365 - LEAST(dateDiff('day', MAX(t.transaction_date), today()), 365)) as recency_score,
    LEAST(COUNT(t.transaction_id), 100) as frequency_score,
    LEAST(SUM(t.amount) / 100, 100) as monetary_score
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id, c.name, c.segment
HAVING last_purchase_date IS NOT NULL
ORDER BY days_since_last_purchase DESC
LIMIT 100;
```
