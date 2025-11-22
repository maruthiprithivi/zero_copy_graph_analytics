-- Customer 360 SQL Queries for ClickHouse
-- These queries demonstrate analytical workloads on customer data

-- ============================================================================
-- BASIC CUSTOMER ANALYTICS
-- ============================================================================

-- 1. Customer Segmentation Overview
SELECT
    segment,
    COUNT(*) as customer_count,
    AVG(lifetime_value) as avg_ltv,
    SUM(lifetime_value) as total_ltv,
    MIN(lifetime_value) as min_ltv,
    MAX(lifetime_value) as max_ltv
FROM customers
GROUP BY segment
ORDER BY total_ltv DESC;

-- 2. Top Customers by Lifetime Value
SELECT
    customer_id,
    name,
    email,
    segment,
    lifetime_value,
    registration_date
FROM customers
ORDER BY lifetime_value DESC
LIMIT 20;

-- 3. Customer Registration Trends
SELECT
    toYYYYMM(registration_date) as year_month,
    segment,
    COUNT(*) as new_customers,
    AVG(lifetime_value) as avg_ltv
FROM customers
GROUP BY year_month, segment
ORDER BY year_month DESC, segment;

-- ============================================================================
-- TRANSACTION ANALYTICS
-- ============================================================================

-- 4. Transaction Volume and Revenue by Month
SELECT
    toYYYYMM(transaction_date) as year_month,
    COUNT(*) as transaction_count,
    SUM(amount) as total_revenue,
    AVG(amount) as avg_transaction_value,
    COUNT(DISTINCT customer_id) as unique_customers
FROM transactions
GROUP BY year_month
ORDER BY year_month DESC;

-- 5. Customer Purchase Behavior
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

-- 6. Product Performance
SELECT
    p.product_id,
    p.name as product_name,
    p.category,
    p.brand,
    COUNT(t.transaction_id) as times_purchased,
    SUM(t.amount) as total_revenue,
    COUNT(DISTINCT t.customer_id) as unique_buyers,
    AVG(t.amount) as avg_sale_price
FROM products p
LEFT JOIN transactions t ON p.product_id = t.product_id
GROUP BY p.product_id, p.name, p.category, p.brand
HAVING times_purchased > 0
ORDER BY total_revenue DESC
LIMIT 50;

-- ============================================================================
-- CUSTOMER INTERACTION ANALYTICS
-- ============================================================================

-- 7. Interaction Patterns by Type
SELECT
    interaction_type,
    COUNT(*) as interaction_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    AVG(duration_minutes) as avg_duration
FROM interactions
GROUP BY interaction_type
ORDER BY interaction_count DESC;

-- 8. Customer Engagement Score
SELECT
    c.customer_id,
    c.name,
    c.segment,
    COUNT(DISTINCT i.interaction_id) as total_interactions,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'purchase' THEN i.interaction_id END) as purchases,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'view' THEN i.interaction_id END) as views,
    COUNT(DISTINCT CASE WHEN i.interaction_type = 'support' THEN i.interaction_id END) as support_tickets,
    AVG(i.duration_minutes) as avg_interaction_duration
FROM customers c
LEFT JOIN interactions i ON c.customer_id = i.customer_id
GROUP BY c.customer_id, c.name, c.segment
HAVING total_interactions > 0
ORDER BY total_interactions DESC
LIMIT 100;

-- ============================================================================
-- PRODUCT CATEGORY ANALYTICS
-- ============================================================================

-- 9. Category Performance by Customer Segment
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

-- 10. Brand Affinity by Segment
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

-- ============================================================================
-- COHORT ANALYSIS
-- ============================================================================

-- 11. Monthly Cohort Retention
WITH cohorts AS (
    SELECT
        customer_id,
        toYYYYMM(MIN(transaction_date)) as cohort_month
    FROM transactions
    GROUP BY customer_id
)
SELECT
    cohorts.cohort_month,
    toYYYYMM(t.transaction_date) as transaction_month,
    COUNT(DISTINCT t.customer_id) as active_customers,
    SUM(t.amount) as revenue
FROM cohorts
JOIN transactions t ON cohorts.customer_id = t.customer_id
GROUP BY cohorts.cohort_month, transaction_month
ORDER BY cohorts.cohort_month, transaction_month;

-- 12. Customer Lifetime Value Analysis
SELECT
    segment,
    quartile,
    COUNT(*) as customer_count,
    AVG(lifetime_value) as avg_ltv,
    MIN(lifetime_value) as min_ltv,
    MAX(lifetime_value) as max_ltv
FROM (
    SELECT
        customer_id,
        segment,
        lifetime_value,
        ntile(4) OVER (PARTITION BY segment ORDER BY lifetime_value) as quartile
    FROM customers
)
GROUP BY segment, quartile
ORDER BY segment, quartile;

-- ============================================================================
-- CROSS-SELL / UPSELL OPPORTUNITIES
-- ============================================================================

-- 13. Customers Who Haven't Purchased in Category
-- Find VIP/Premium customers who haven't purchased in high-value categories
SELECT DISTINCT
    c.customer_id,
    c.name,
    c.segment,
    c.lifetime_value,
    'Electronics' as recommended_category
FROM customers c
WHERE c.segment IN ('VIP', 'Premium')
AND NOT EXISTS (
    SELECT 1 FROM transactions t
    JOIN products p ON t.product_id = p.product_id
    WHERE t.customer_id = c.customer_id
    AND p.category = 'Electronics'
)
LIMIT 100;

-- 14. Product Basket Analysis
-- Products frequently bought together
SELECT
    p1.name as product_1,
    p2.name as product_2,
    COUNT(*) as times_bought_together
FROM transactions t1
JOIN transactions t2 ON t1.customer_id = t2.customer_id
    AND t1.transaction_id != t2.transaction_id
    AND ABS(dateDiff('day', t1.transaction_date, t2.transaction_date)) <= 7
JOIN products p1 ON t1.product_id = p1.product_id
JOIN products p2 ON t2.product_id = p2.product_id
WHERE p1.product_id < p2.product_id
GROUP BY p1.name, p2.name
HAVING times_bought_together >= 5
ORDER BY times_bought_together DESC
LIMIT 50;

-- 15. Recent Customer Activity
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
