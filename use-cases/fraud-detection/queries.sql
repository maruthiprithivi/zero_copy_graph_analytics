-- Fraud Detection SQL Queries for ClickHouse
-- These queries demonstrate analytical approaches to fraud detection
-- Note: Graph traversal queries are in queries.cypher (PuppyGraph excels at relationships)

-- ============================================================================
-- BASIC FRAUD ANALYTICS
-- ============================================================================

-- 1. Fraud Customer Overview
SELECT
    is_fraudulent,
    COUNT(*) as customer_count,
    AVG(risk_score) as avg_risk_score
FROM fraud_customers
GROUP BY is_fraudulent
ORDER BY is_fraudulent DESC;

-- 2. High-Risk Customers
SELECT
    customer_id,
    name,
    email,
    risk_score,
    status,
    is_fraudulent
FROM fraud_customers
WHERE risk_score > 50
ORDER BY risk_score DESC
LIMIT 20;

-- 3. Fraudulent Accounts by Type
SELECT
    account_type,
    is_fraudulent,
    COUNT(*) as account_count,
    AVG(balance) as avg_balance
FROM fraud_accounts
GROUP BY account_type, is_fraudulent
ORDER BY account_type, is_fraudulent DESC;

-- ============================================================================
-- DEVICE ANALYSIS
-- ============================================================================

-- 4. Suspicious Devices Overview
SELECT
    is_suspicious,
    device_type,
    COUNT(*) as device_count
FROM fraud_devices
GROUP BY is_suspicious, device_type
ORDER BY is_suspicious DESC, device_count DESC;

-- 5. Devices by Location
SELECT
    location,
    COUNT(*) as device_count,
    SUM(is_suspicious) as suspicious_count
FROM fraud_devices
GROUP BY location
ORDER BY suspicious_count DESC
LIMIT 20;

-- ============================================================================
-- MERCHANT ANALYSIS
-- ============================================================================

-- 6. Merchant Risk Overview
SELECT
    category,
    COUNT(*) as merchant_count,
    AVG(risk_score) as avg_risk_score,
    SUM(is_fraudulent) as fraudulent_count
FROM fraud_merchants
GROUP BY category
ORDER BY avg_risk_score DESC;

-- 7. High-Risk Merchants
SELECT
    merchant_id,
    merchant_name,
    category,
    risk_score,
    is_fraudulent
FROM fraud_merchants
WHERE risk_score > 50 OR is_fraudulent = 1
ORDER BY risk_score DESC
LIMIT 20;

-- ============================================================================
-- TRANSACTION ANALYTICS
-- ============================================================================

-- 8. Transaction Volume by Type
SELECT
    transaction_type,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount,
    SUM(is_fraudulent) as fraudulent_count
FROM fraud_transactions
GROUP BY transaction_type
ORDER BY total_amount DESC;

-- 9. Flagged vs Fraudulent Transactions
SELECT
    is_flagged,
    is_fraudulent,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    AVG(risk_score) as avg_risk_score
FROM fraud_transactions
GROUP BY is_flagged, is_fraudulent
ORDER BY is_fraudulent DESC, is_flagged DESC;

-- 10. High-Risk Transactions
SELECT
    transaction_id,
    from_account_id,
    to_account_id,
    amount,
    transaction_type,
    risk_score,
    is_fraudulent
FROM fraud_transactions
WHERE risk_score > 50 OR is_fraudulent = 1
ORDER BY risk_score DESC
LIMIT 50;

-- ============================================================================
-- HEAVY ANALYTICAL QUERIES (ClickHouse Strengths - Not Graph-Friendly)
-- ============================================================================

-- 11. Transaction Velocity Analysis (Transactions per hour per account)
SELECT
    from_account_id,
    toStartOfHour(timestamp) as hour,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount,
    MAX(amount) - MIN(amount) as amount_range,
    COUNT(*) - lagInFrame(COUNT(*)) OVER (PARTITION BY from_account_id ORDER BY toStartOfHour(timestamp)) as velocity_change
FROM fraud_transactions
GROUP BY from_account_id, hour
HAVING transaction_count >= 2
ORDER BY transaction_count DESC
LIMIT 50;

-- 12. Risk Score Distribution with Percentiles
SELECT
    CASE
        WHEN risk_score < 20 THEN 'Low (0-20)'
        WHEN risk_score < 40 THEN 'Medium-Low (20-40)'
        WHEN risk_score < 60 THEN 'Medium (40-60)'
        WHEN risk_score < 80 THEN 'Medium-High (60-80)'
        ELSE 'High (80-100)'
    END as risk_band,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    SUM(is_fraudulent) as actual_fraud_count,
    SUM(is_fraudulent) / COUNT(*) * 100 as fraud_rate_pct,
    AVG(amount) as avg_transaction_amount
FROM fraud_transactions
GROUP BY risk_band
ORDER BY fraud_rate_pct DESC;

-- 13. Account Risk Scoring with Running Fraud Rate
WITH account_stats AS (
    SELECT
        from_account_id,
        COUNT(*) as total_transactions,
        SUM(is_fraudulent) as fraud_count,
        SUM(amount) as total_amount,
        AVG(risk_score) as avg_risk_score
    FROM fraud_transactions
    GROUP BY from_account_id
)
SELECT
    from_account_id,
    total_transactions,
    fraud_count,
    total_amount,
    avg_risk_score,
    fraud_count / total_transactions * 100 as fraud_rate,
    RANK() OVER (ORDER BY fraud_count / total_transactions DESC) as risk_rank,
    SUM(fraud_count) OVER (ORDER BY fraud_count / total_transactions DESC) as cumulative_frauds
FROM account_stats
WHERE total_transactions >= 2
ORDER BY fraud_rate DESC
LIMIT 50;

-- 14. Time-Series Fraud Pattern Detection (Daily trends)
SELECT
    toDate(timestamp) as day,
    COUNT(*) as total_transactions,
    SUM(is_fraudulent) as fraud_count,
    SUM(is_flagged) as flagged_count,
    SUM(amount) as total_amount,
    SUM(CASE WHEN is_fraudulent = 1 THEN amount ELSE 0 END) as fraud_amount,
    AVG(SUM(is_fraudulent)) OVER (ORDER BY toDate(timestamp) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as rolling_7day_fraud_avg,
    stddevPop(risk_score) as risk_score_volatility
FROM fraud_transactions
GROUP BY day
ORDER BY day DESC
LIMIT 30;

-- 15. Merchant Category Fraud Analysis with Statistical Measures
SELECT
    m.category,
    COUNT(DISTINCT m.merchant_id) as merchant_count,
    COUNT(t.transaction_id) as transaction_count,
    SUM(t.amount) as total_amount,
    SUM(t.is_fraudulent) as fraud_count,
    SUM(t.is_fraudulent) / COUNT(t.transaction_id) * 100 as fraud_rate_pct,
    AVG(t.risk_score) as avg_risk_score,
    stddevPop(t.amount) as amount_std_dev,
    quantile(0.5)(t.amount) as median_amount,
    quantile(0.95)(t.amount) as p95_amount
FROM fraud_transactions t
JOIN fraud_merchants m ON t.merchant_id = m.merchant_id
GROUP BY m.category
ORDER BY fraud_rate_pct DESC;

-- 16. Device-Based Fraud Correlation
SELECT
    d.device_type,
    d.is_suspicious,
    COUNT(DISTINCT d.device_id) as device_count,
    COUNT(t.transaction_id) as transaction_count,
    SUM(t.is_fraudulent) as fraud_count,
    SUM(t.is_fraudulent) / COUNT(t.transaction_id) * 100 as fraud_rate_pct,
    AVG(t.amount) as avg_amount,
    SUM(t.amount) as total_amount
FROM fraud_devices d
JOIN fraud_transactions t ON d.device_id = t.device_id
GROUP BY d.device_type, d.is_suspicious
ORDER BY fraud_rate_pct DESC;

-- 17. Account Balance vs Fraud Risk Correlation
SELECT
    CASE
        WHEN a.balance < 1000 THEN 'Low (<1K)'
        WHEN a.balance < 5000 THEN 'Medium (1K-5K)'
        WHEN a.balance < 20000 THEN 'High (5K-20K)'
        ELSE 'Very High (>20K)'
    END as balance_band,
    COUNT(DISTINCT a.account_id) as account_count,
    SUM(a.is_fraudulent) as fraudulent_accounts,
    SUM(a.is_fraudulent) / COUNT(DISTINCT a.account_id) * 100 as fraud_rate_pct,
    COUNT(t.transaction_id) as transaction_count,
    SUM(t.amount) as total_transaction_volume
FROM fraud_accounts a
LEFT JOIN fraud_transactions t ON a.account_id = t.from_account_id
GROUP BY balance_band
ORDER BY fraud_rate_pct DESC;
