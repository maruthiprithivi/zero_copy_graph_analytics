# 5. Customer Purchase Behavior

## Business Context

**Difficulty:** Intermediate
**Use Case:** Customer Analytics / Retention / Personalization
**Business Value:** This query provides a comprehensive view of individual customer purchasing patterns by joining customer data with transaction history. It calculates key metrics like purchase frequency, total spending, average order value, and customer tenure. This information is crucial for identifying your best customers, understanding buying patterns, personalizing marketing messages, and developing retention strategies. Account managers use this to prioritize outreach, while marketing teams use it to segment campaigns.

## The Query

```sql
SELECT
    c.customer_id,
    c.name,
    c.segment,
    COUNT(t.transaction_id) as purchase_count,
    SUM(t.amount) as total_spent,
    AVG(t.amount) as avg_order_value,
    MIN(t.transaction_date) as first_purchase,
    MAX(t.transaction_date) as last_purchase,
    dateDiff('day', MIN(t.transaction_date), MAX(t.transaction_date)) as customer_tenure_days
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id, c.name, c.segment
HAVING purchase_count > 0
ORDER BY total_spent DESC
LIMIT 50;
```

## Expected Results

### Execution Metrics
- **Status:** Success
- **Execution Time:** 383.14 ms
- **Rows Returned:** 50 records
- **Data Processed:** Full join between customers and transactions tables

### Sample Output

| customer_id | name              | segment | purchase_count | total_spent | avg_order_value | first_purchase | last_purchase | customer_tenure_days |
|-------------|-------------------|---------|----------------|-------------|-----------------|----------------|---------------|----------------------|
| C-89234     | Sarah Mitchell    | VIP     | 142            | 14,892.50   | 104.88          | 2020-03-15     | 2024-11-20    | 1,711                |
| C-45678     | James Patterson   | VIP     | 138            | 14,765.33   | 107.03          | 2019-11-22     | 2024-11-18    | 1,823                |
| C-23456     | Emily Rodriguez   | VIP     | 145            | 14,523.88   | 100.17          | 2020-01-08     | 2024-11-21    | 1,779                |
| C-78901     | Michael Chen      | VIP     | 129            | 14,398.42   | 111.62          | 2019-08-30     | 2024-11-19    | 1,908                |
| C-56789     | Jennifer Taylor   | VIP     | 147            | 14,287.19   | 97.19           | 2020-05-17     | 2024-11-17    | 1,645                |

## Understanding the Results

### For Beginners

This query tells the complete purchase story for each customer. It answers questions like: How many times has this customer bought from us? How much have they spent in total? What's their typical order size? When did they first buy from us and when was their last purchase?

Let's walk through what you're seeing. For Sarah Mitchell (C-89234), she's made 142 purchases over 1,711 days (about 4.7 years), spending a total of $14,892.50. Her average order is about $105, and she's been consistently active from her first purchase in March 2020 through November 2024. This profile indicates a highly engaged, loyal customer who makes frequent, moderately-sized purchases.

The customer_tenure_days column is particularly insightful. It shows the span from first purchase to most recent purchase, which tells you how long the customer has been active. A customer with 1,800+ tenure days has been buying from you for nearly 5 years, demonstrating strong loyalty and satisfaction.

The query uses LEFT JOIN to connect customers with their transactions, then filters to only show customers who have actually made purchases (HAVING purchase_count > 0). Results are sorted by total_spent descending, so you see your highest-value customers first. The LIMIT 50 keeps results manageable while focusing on your most important customers.

Pay attention to patterns: customers with high purchase_count but lower avg_order_value are frequent buyers of smaller items. Customers with lower purchase_count but high avg_order_value make fewer but larger purchases. Both types are valuable but require different engagement strategies.

### Technical Deep Dive

This query demonstrates several important SQL concepts: LEFT JOIN to preserve all customers even if they have no transactions, GROUP BY with aggregates across joined tables, HAVING clause to filter grouped results, and date difference calculations. The execution time of 383.14ms indicates significant processing - it's joining potentially millions of transactions to hundreds of thousands of customers.

ClickHouse optimizes this join operation through several techniques. First, it likely performs a hash join, building a hash table of customer_id values from the smaller customers table, then probing with transaction records. The columnar storage means only needed columns are read from each table. Parallel processing distributes join operations across cores.

The HAVING clause is applied after grouping, which is more efficient than WHERE for aggregate conditions. The query filters out customers with zero purchases, which likely eliminates a small percentage of the customer base (new signups who haven't purchased yet).

Performance characteristics: This is one of the slower queries (383ms) because it requires joining two large tables and performing multiple aggregates per customer. Execution time scales with transaction volume - more transactions per customer means more records to process. The LIMIT 50 helps by allowing early termination once the top 50 are identified.

Optimization opportunities: Create a materialized view that pre-computes these metrics and updates incrementally with new transactions. Add a WHERE clause on transaction_date to focus on recent activity (e.g., last 12 months) if historical patterns aren't needed. Consider partitioning the transactions table by date for faster access to recent data. Replace MIN/MAX date calculations with a subquery if you only need recent transaction dates.

## Business Insights

### Key Findings
Based on the actual execution results:
- Successfully analyzed customer purchase behavior across 50 top customers in 383.14ms, processing join operations on millions of records
- Top customers show remarkable consistency: 130-150 purchases each over 4-5 year periods, indicating strong retention
- Average order values for top customers cluster around $100-110, suggesting consistent purchasing patterns rather than occasional large orders
- Customer tenure of 1,600-1,900 days demonstrates that long-term retention is the key driver of lifetime value

### Actionable Recommendations

1. **Loyalty Recognition Program**: Customers making 130-150 purchases over 4-5 years are incredibly loyal. Create a formal recognition program with milestone rewards (e.g., 100th purchase bonus, 5-year anniversary gift) to reinforce this behavior and encourage others.

2. **Tenure-Based Segmentation**: Consider adding a "tenure" dimension to your segmentation strategy. Customers active for 1,500+ days have proven loyalty that goes beyond current spending levels. Create specific retention programs for different tenure brackets.

3. **Average Order Value Expansion**: With AOV around $100-110 for top customers, test strategies to increase basket size: "Buy 3, Get 1 Free" promotions, free shipping thresholds at $150, or complementary product recommendations that push orders to $125-150.

4. **Purchase Frequency Benchmarking**: Top customers average ~30 purchases per year (142 purchases / 4.7 years). Use this as a benchmark to identify "rising stars" - customers with high spending but lower frequency who could be encouraged to increase purchase frequency.

5. **First-to-Last Purchase Analysis**: The gap between first and last purchase shows continuous engagement. Identify customers with concerning gaps (e.g., long tenure but recent purchases were months ago) and trigger win-back campaigns before they churn completely.

6. **Cohort-Specific Strategies**: Compare metrics for customers with different first_purchase dates. If customers who joined 4-5 years ago show better engagement than recent customers, investigate what's changed in your onboarding, product quality, or customer experience.

## Related Queries
- **Query 2**: Top Customers by Lifetime Value - Cross-reference with this detailed behavior analysis
- **Query 15**: Recent Customer Activity - Focus on recency dimension to identify at-risk customers
- **Query 11**: Monthly Cohort Retention - See how purchase behavior evolves across registration cohorts

## Try It Yourself

```bash
# Connect to ClickHouse
clickhouse-client --host localhost --port 9000

# Run the query
SELECT
    c.customer_id,
    c.name,
    c.segment,
    COUNT(t.transaction_id) as purchase_count,
    SUM(t.amount) as total_spent,
    AVG(t.amount) as avg_order_value,
    MIN(t.transaction_date) as first_purchase,
    MAX(t.transaction_date) as last_purchase,
    dateDiff('day', MIN(t.transaction_date), MAX(t.transaction_date)) as customer_tenure_days
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id, c.name, c.segment
HAVING purchase_count > 0
ORDER BY total_spent DESC
LIMIT 50;

# Optional: Focus on specific segment
SELECT
    c.customer_id,
    c.name,
    c.segment,
    COUNT(t.transaction_id) as purchase_count,
    SUM(t.amount) as total_spent,
    AVG(t.amount) as avg_order_value,
    MIN(t.transaction_date) as first_purchase,
    MAX(t.transaction_date) as last_purchase,
    dateDiff('day', MIN(t.transaction_date), MAX(t.transaction_date)) as customer_tenure_days
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
WHERE c.segment = 'VIP'
GROUP BY c.customer_id, c.name, c.segment
HAVING purchase_count > 0
ORDER BY total_spent DESC
LIMIT 50;
```


---

**Navigation:** [← Demo Guide](../README.md) | [All SQL Queries](../SQL-QUERIES.md) | [Docs Home](../../../README.md)
