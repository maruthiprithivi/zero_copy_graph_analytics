-- Fraud Detection SQL Queries for ClickHouse
-- These queries demonstrate traditional SQL approaches to fraud detection

-- 1. Find accounts with shared devices (potential account takeover)
SELECT
    device_id,
    COUNT(DISTINCT account_id) as account_count,
    GROUP_CONCAT(DISTINCT account_id) as accounts,
    MAX(login_count) as max_logins,
    SUM(failed_attempts) as total_failed_attempts
FROM device_account_usage
GROUP BY device_id
HAVING account_count > 5  -- Same device accessing many accounts
ORDER BY account_count DESC, total_failed_attempts DESC
LIMIT 20;

-- 2. Detect high-velocity transactions (potential fraud)
SELECT
    from_account_id,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount,
    MAX(amount) as max_amount,
    COUNT(DISTINCT to_account_id) as unique_recipients,
    COUNT(DISTINCT merchant_id) as unique_merchants
FROM transactions
WHERE timestamp >= NOW() - INTERVAL 1 HOUR
GROUP BY from_account_id
HAVING transaction_count > 10 OR total_amount > 50000
ORDER BY transaction_count DESC, total_amount DESC;

-- 3. Find accounts with suspicious round-number transactions
SELECT
    from_account_id,
    to_account_id,
    COUNT(*) as round_transactions,
    SUM(amount) as total_amount,
    GROUP_CONCAT(DISTINCT amount) as amounts
FROM transactions
WHERE amount IN (1000, 5000, 10000, 25000, 50000, 100000)  -- Round numbers
    AND timestamp >= NOW() - INTERVAL 7 DAY
GROUP BY from_account_id, to_account_id
HAVING round_transactions > 3
ORDER BY total_amount DESC;

-- 4. Identify accounts with impossible geographic transactions
WITH account_locations AS (
    SELECT
        t.from_account_id,
        t.timestamp,
        d.location,
        LAG(d.location) OVER (PARTITION BY t.from_account_id ORDER BY t.timestamp) as prev_location,
        LAG(t.timestamp) OVER (PARTITION BY t.from_account_id ORDER BY t.timestamp) as prev_timestamp
    FROM transactions t
    JOIN devices d ON t.device_id = d.device_id
    WHERE t.timestamp >= NOW() - INTERVAL 1 DAY
    AND d.location IS NOT NULL
)
SELECT
    from_account_id,
    location,
    prev_location,
    timestamp,
    prev_timestamp,
    DATEDIFF('minute', prev_timestamp, timestamp) as time_diff_minutes
FROM account_locations
WHERE location != prev_location
    AND DATEDIFF('minute', prev_timestamp, timestamp) < 60  -- Less than 1 hour between different locations
    AND location NOT LIKE '%' || prev_location || '%'  -- Different cities/states
ORDER BY time_diff_minutes;

-- 5. Find merchants with unusually high approval rates
SELECT
    m.merchant_id,
    m.merchant_name,
    m.category,
    COUNT(t.transaction_id) as total_transactions,
    SUM(CASE WHEN t.is_flagged = 0 THEN 1 ELSE 0 END) as approved_transactions,
    (SUM(CASE WHEN t.is_flagged = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as approval_rate,
    AVG(t.amount) as avg_transaction_amount,
    SUM(t.amount) as total_volume
FROM merchants m
JOIN transactions t ON m.merchant_id = t.merchant_id
WHERE t.timestamp >= NOW() - INTERVAL 30 DAY
GROUP BY m.merchant_id, m.merchant_name, m.category
HAVING total_transactions > 100
    AND approval_rate > 95  -- Unusually high approval rate
ORDER BY approval_rate DESC, total_volume DESC;

-- 6. Detect accounts with similar customer information (synthetic identity)
SELECT
    c1.customer_id as customer1,
    c2.customer_id as customer2,
    c1.name as name1,
    c2.name as name2,
    c1.ssn_hash,
    c1.phone,
    c1.address,
    CASE
        WHEN c1.ssn_hash = c2.ssn_hash THEN 'SSN'
        WHEN c1.phone = c2.phone THEN 'PHONE'
        WHEN c1.address = c2.address THEN 'ADDRESS'
        ELSE 'OTHER'
    END as match_type
FROM customers c1
JOIN customers c2 ON (
    (c1.ssn_hash = c2.ssn_hash OR c1.phone = c2.phone OR c1.address = c2.address)
    AND c1.customer_id < c2.customer_id  -- Avoid duplicates
)
WHERE c1.created_at >= NOW() - INTERVAL 90 DAY  -- Recent accounts
    OR c2.created_at >= NOW() - INTERVAL 90 DAY
ORDER BY match_type, c1.created_at DESC;

-- 7. Find transaction chains (potential money laundering)
WITH RECURSIVE transaction_chains AS (
    -- Start with high-value transactions
    SELECT
        transaction_id,
        from_account_id,
        to_account_id,
        amount,
        timestamp,
        1 as chain_length,
        ARRAY[from_account_id] as path,
        transaction_id as root_transaction
    FROM transactions
    WHERE amount > 10000
        AND timestamp >= NOW() - INTERVAL 7 DAY

    UNION ALL

    -- Follow the chain
    SELECT
        t.transaction_id,
        t.from_account_id,
        t.to_account_id,
        t.amount,
        t.timestamp,
        tc.chain_length + 1,
        arrayPushBack(tc.path, t.from_account_id),
        tc.root_transaction
    FROM transactions t
    JOIN transaction_chains tc ON t.from_account_id = tc.to_account_id
    WHERE tc.chain_length < 5  -- Limit chain length
        AND t.timestamp > tc.timestamp  -- Forward in time
        AND t.timestamp <= tc.timestamp + INTERVAL 24 HOUR  -- Within 24 hours
        AND NOT has(tc.path, t.to_account_id)  -- Avoid cycles
)
SELECT
    root_transaction,
    chain_length,
    path,
    SUM(amount) as total_amount,
    COUNT(*) as transaction_count
FROM transaction_chains
WHERE chain_length >= 3  -- Chains of 3+ transactions
GROUP BY root_transaction, chain_length, path
ORDER BY total_amount DESC, chain_length DESC;

-- 8. Calculate account risk scores based on transaction patterns
SELECT
    a.account_id,
    a.customer_id,
    c.name,
    -- Velocity risk
    COUNT(t.transaction_id) as transaction_count,
    SUM(t.amount) as total_amount,
    AVG(t.amount) as avg_amount,
    STDDEV(t.amount) as amount_stddev,

    -- Time-based risk
    COUNT(DISTINCT DATE(t.timestamp)) as active_days,
    MAX(t.timestamp) as last_transaction,

    -- Network risk
    COUNT(DISTINCT t.to_account_id) as unique_recipients,
    COUNT(DISTINCT t.merchant_id) as unique_merchants,
    COUNT(DISTINCT t.device_id) as unique_devices,

    -- Calculated risk score (0-100)
    LEAST(100,
        -- High transaction volume (0-30 points)
        (transaction_count / 100.0) * 30 +
        -- High unique recipients (0-20 points)
        (unique_recipients / 50.0) * 20 +
        -- Multiple devices (0-25 points)
        (unique_devices / 10.0) * 25 +
        -- High amount variance (0-25 points)
        (amount_stddev / avg_amount) * 25
    ) as risk_score

FROM accounts a
JOIN customers c ON a.customer_id = c.customer_id
LEFT JOIN transactions t ON a.account_id = t.from_account_id
WHERE t.timestamp >= NOW() - INTERVAL 30 DAY
GROUP BY a.account_id, a.customer_id, c.name
HAVING transaction_count > 5  -- Minimum activity
ORDER BY risk_score DESC, transaction_count DESC
LIMIT 100;

-- 9. Detect burst activity patterns
WITH hourly_activity AS (
    SELECT
        from_account_id,
        toHour(timestamp) as hour,
        DATE(timestamp) as date,
        COUNT(*) as transactions_per_hour,
        SUM(amount) as amount_per_hour
    FROM transactions
    WHERE timestamp >= NOW() - INTERVAL 7 DAY
    GROUP BY from_account_id, hour, date
),
account_hourly_stats AS (
    SELECT
        from_account_id,
        AVG(transactions_per_hour) as avg_hourly_transactions,
        STDDEV(transactions_per_hour) as stddev_hourly_transactions,
        MAX(transactions_per_hour) as max_hourly_transactions
    FROM hourly_activity
    GROUP BY from_account_id
    HAVING COUNT(*) >= 10  -- At least 10 hours of activity
)
SELECT
    ha.from_account_id,
    ha.date,
    ha.hour,
    ha.transactions_per_hour,
    ahs.avg_hourly_transactions,
    (ha.transactions_per_hour - ahs.avg_hourly_transactions) / ahs.stddev_hourly_transactions as z_score
FROM hourly_activity ha
JOIN account_hourly_stats ahs ON ha.from_account_id = ahs.from_account_id
WHERE ha.transactions_per_hour > ahs.avg_hourly_transactions + 3 * ahs.stddev_hourly_transactions
    AND ahs.stddev_hourly_transactions > 0
ORDER BY z_score DESC, ha.transactions_per_hour DESC;

-- 10. Find dormant accounts suddenly becoming active (potential takeover)
WITH account_activity AS (
    SELECT
        from_account_id,
        MIN(timestamp) as first_transaction,
        MAX(timestamp) as last_transaction,
        COUNT(*) as total_transactions,
        DATEDIFF('day', MIN(timestamp), MAX(timestamp)) as account_lifespan_days
    FROM transactions
    GROUP BY from_account_id
),
recent_activity AS (
    SELECT
        from_account_id,
        COUNT(*) as recent_transactions,
        MIN(timestamp) as recent_activity_start
    FROM transactions
    WHERE timestamp >= NOW() - INTERVAL 7 DAY
    GROUP BY from_account_id
)
SELECT
    aa.from_account_id,
    aa.first_transaction,
    aa.last_transaction,
    aa.total_transactions,
    aa.account_lifespan_days,
    ra.recent_transactions,
    ra.recent_activity_start,
    DATEDIFF('day', aa.last_transaction, ra.recent_activity_start) as dormancy_period_days,
    (ra.recent_transactions * 100.0 / aa.total_transactions) as recent_activity_percentage
FROM account_activity aa
JOIN recent_activity ra ON aa.from_account_id = ra.from_account_id
WHERE DATEDIFF('day', aa.last_transaction, ra.recent_activity_start) > 90  -- Dormant for 90+ days
    AND ra.recent_transactions > 10  -- Suddenly very active
    AND ra.recent_activity_start >= NOW() - INTERVAL 7 DAY
ORDER BY dormancy_period_days DESC, ra.recent_transactions DESC;