// Fraud Detection Cypher Queries for PuppyGraph
// These queries demonstrate graph-based fraud pattern detection
// Note: Complex aggregations are in queries.sql (ClickHouse excels at aggregations)

// ============================================================================
// DEVICE SHARING DETECTION (Account Takeover Patterns)
// ============================================================================

// 1. Find Accounts Sharing Devices
// Detects potential account takeover by finding accounts using the same device
MATCH (a1:FraudAccount)-[:USED_DEVICE]->(d:FraudDevice)<-[:USED_DEVICE]-(a2:FraudAccount)
WHERE a1 <> a2
RETURN a1.account_id as account_1, a2.account_id as account_2,
       d.device_id, d.device_fingerprint, d.is_suspicious
LIMIT 50;

// 2. Suspicious Device Clusters
// Find devices flagged as suspicious and the accounts using them
MATCH (d:FraudDevice)<-[:USED_DEVICE]-(a:FraudAccount)
WHERE d.is_suspicious = 1
RETURN d.device_id, d.device_type, d.location, d.ip_address,
       a.account_id, a.is_fraudulent
LIMIT 50;

// ============================================================================
// CUSTOMER-ACCOUNT NETWORKS
// ============================================================================

// 3. Customer Account Ownership Network
// Find customers and their associated accounts
MATCH (c:FraudCustomer)-[:OWNS_ACCOUNT]->(a:FraudAccount)
RETURN c.customer_id, c.name, c.is_fraudulent, c.risk_score,
       a.account_id, a.account_type, a.is_fraudulent as account_fraudulent
LIMIT 100;

// 4. Fraudulent Customer Networks
// Find customers marked as fraudulent and their account relationships
MATCH (c:FraudCustomer)-[:OWNS_ACCOUNT]->(a:FraudAccount)
WHERE c.is_fraudulent = 1
RETURN c.customer_id, c.name, c.risk_score, c.status,
       a.account_id, a.balance, a.is_fraudulent as account_fraud
LIMIT 50;

// ============================================================================
// TRANSACTION PATH ANALYSIS
// ============================================================================

// 5. Direct Account-to-Account Transactions
// Find all direct transactions between accounts
MATCH (from:FraudAccount)-[t:FRAUD_TRANSACTION]->(to:FraudAccount)
RETURN from.account_id as from_account, to.account_id as to_account,
       t.transaction_type, t.is_fraudulent, t.is_flagged
LIMIT 100;

// 6. Flagged Fraudulent Transactions
// Find transactions marked as fraudulent
MATCH (from:FraudAccount)-[t:FRAUD_TRANSACTION]->(to:FraudAccount)
WHERE t.is_fraudulent = 1
RETURN from.account_id, to.account_id, t.transaction_id,
       t.transaction_type, t.risk_score, t.is_flagged
LIMIT 50;

// 7. Connected Fraudulent Accounts
// Find accounts linked through transactions where at least one is fraudulent
MATCH (a1:FraudAccount)-[:FRAUD_TRANSACTION]->(a2:FraudAccount)
WHERE a1.is_fraudulent = 1 OR a2.is_fraudulent = 1
RETURN a1.account_id, a1.is_fraudulent as a1_fraud,
       a2.account_id, a2.is_fraudulent as a2_fraud
LIMIT 50;

// ============================================================================
// MERCHANT PAYMENT ANALYSIS
// ============================================================================

// 8. Merchant Payment Network
// Find accounts paying specific merchants
MATCH (a:FraudAccount)-[t:PAID_MERCHANT]->(m:FraudMerchant)
RETURN a.account_id, m.merchant_id, m.merchant_name, m.category,
       m.is_fraudulent as merchant_fraud, m.risk_score
LIMIT 100;

// 9. High-Risk Merchant Transactions
// Find transactions to merchants with high risk scores
MATCH (a:FraudAccount)-[t:PAID_MERCHANT]->(m:FraudMerchant)
WHERE m.risk_score > 50 OR m.is_fraudulent = 1
RETURN a.account_id, a.is_fraudulent as account_fraud,
       m.merchant_id, m.merchant_name, m.risk_score, m.is_fraudulent
LIMIT 50;

// ============================================================================
// COUNT / VERIFICATION QUERIES
// ============================================================================

// 10. Total Fraud Customers Count
MATCH (c:FraudCustomer)
RETURN count(c) as total_fraud_customers;

// 11. Total Fraud Accounts Count
MATCH (a:FraudAccount)
RETURN count(a) as total_fraud_accounts;

// 12. Total Fraud Transactions Count
MATCH ()-[t:FRAUD_TRANSACTION]->()
RETURN count(t) as total_fraud_transactions;

// 13. Total Device Usage Edges Count
MATCH ()-[u:USED_DEVICE]->()
RETURN count(u) as total_device_usage;

// 14. Fraudulent vs Legitimate Accounts Distribution
MATCH (a:FraudAccount)
RETURN a.is_fraudulent as is_fraudulent, count(a) as count
ORDER BY is_fraudulent DESC;

// 15. Suspicious Devices Count
MATCH (d:FraudDevice)
WHERE d.is_suspicious = 1
RETURN count(d) as suspicious_devices;

// ============================================================================
// ADVANCED GRAPH PATTERNS - Demonstrating Graph Power for Fraud Detection
// ============================================================================

// 16. Multi-Hop Money Flow (3-hop transaction chain for money laundering detection)
MATCH (a1:FraudAccount)-[:FRAUD_TRANSACTION]->(a2:FraudAccount)
      -[:FRAUD_TRANSACTION]->(a3:FraudAccount)
      -[:FRAUD_TRANSACTION]->(a4:FraudAccount)
WHERE a1 <> a2 AND a2 <> a3 AND a3 <> a4
RETURN a1.account_id as hop1, a2.account_id as hop2,
       a3.account_id as hop3, a4.account_id as hop4
LIMIT 20;

// 17. Fraud Ring Detection (Accounts connected through shared devices)
MATCH (a1:FraudAccount)-[:USED_DEVICE]->(d1:FraudDevice)<-[:USED_DEVICE]-(a2:FraudAccount)
      -[:USED_DEVICE]->(d2:FraudDevice)<-[:USED_DEVICE]-(a3:FraudAccount)
WHERE a1 <> a2 AND a2 <> a3 AND a1 <> a3 AND d1 <> d2
RETURN a1.account_id as account_1, a2.account_id as account_2, a3.account_id as account_3,
       d1.device_id as device_1, d2.device_id as device_2
LIMIT 20;

// 18. Customer-Account-Device Triangle (Risk propagation)
MATCH (c:FraudCustomer)-[:OWNS_ACCOUNT]->(a:FraudAccount)-[:USED_DEVICE]->(d:FraudDevice)
WHERE c.risk_score > 50 OR a.is_fraudulent = 1 OR d.is_suspicious = 1
RETURN c.customer_id, c.name, c.risk_score,
       a.account_id, a.is_fraudulent,
       d.device_id, d.is_suspicious
LIMIT 50;

// 19. High-Risk Transaction Network (Flagged transactions with device context)
MATCH (from:FraudAccount)-[t:FRAUD_TRANSACTION]->(to:FraudAccount)
WHERE t.is_flagged = 1
OPTIONAL MATCH (from)-[:USED_DEVICE]->(d:FraudDevice)
RETURN from.account_id as from_account, to.account_id as to_account,
       t.transaction_id, t.risk_score,
       d.device_id, d.is_suspicious as suspicious_device
LIMIT 50;

// 20. Merchant Fraud Network (Accounts paying multiple high-risk merchants)
MATCH (a:FraudAccount)-[:PAID_MERCHANT]->(m1:FraudMerchant)
WHERE m1.risk_score > 50
MATCH (a)-[:PAID_MERCHANT]->(m2:FraudMerchant)
WHERE m2.risk_score > 50 AND m1 <> m2
RETURN a.account_id, a.is_fraudulent,
       m1.merchant_name as merchant_1, m1.risk_score as risk_1,
       m2.merchant_name as merchant_2, m2.risk_score as risk_2
LIMIT 30;

// 21. Transaction Chain with Device Context (2-hop with device tracking)
MATCH (a1:FraudAccount)-[:FRAUD_TRANSACTION]->(a2:FraudAccount)-[:FRAUD_TRANSACTION]->(a3:FraudAccount)
OPTIONAL MATCH (a1)-[:USED_DEVICE]->(d1:FraudDevice)
OPTIONAL MATCH (a2)-[:USED_DEVICE]->(d2:FraudDevice)
WHERE a1 <> a2 AND a2 <> a3
RETURN a1.account_id as account_1, a2.account_id as account_2, a3.account_id as account_3,
       d1.device_id as device_1, d2.device_id as device_2
LIMIT 30;

// 22. Customer Network Analysis (Customers connected through transaction chains)
MATCH (c1:FraudCustomer)-[:OWNS_ACCOUNT]->(a:FraudAccount)<-[:FRAUD_TRANSACTION]-(a2:FraudAccount)<-[:OWNS_ACCOUNT]-(c2:FraudCustomer)
WHERE c1 <> c2
RETURN c1.name as customer_1, c1.risk_score as risk_1,
       c2.name as customer_2, c2.risk_score as risk_2,
       a.account_id as connecting_account
LIMIT 30;

// 23. Multi-Device Account Activity (Accounts using multiple devices)
MATCH (a:FraudAccount)-[:USED_DEVICE]->(d:FraudDevice)
WITH a, COUNT(DISTINCT d) as device_count
WHERE device_count >= 2
RETURN a.account_id, a.is_fraudulent, device_count
ORDER BY device_count DESC
LIMIT 30;

// 24. Suspicious Activity Cluster (Fraudulent customers with their network)
MATCH (c:FraudCustomer)-[:OWNS_ACCOUNT]->(a:FraudAccount)
WHERE c.is_fraudulent = 1 OR a.is_fraudulent = 1
OPTIONAL MATCH (a)-[:USED_DEVICE]->(d:FraudDevice)
OPTIONAL MATCH (a)-[:PAID_MERCHANT]->(m:FraudMerchant)
RETURN c.customer_id, c.name, c.risk_score,
       a.account_id, a.is_fraudulent,
       COUNT(DISTINCT d) as devices_used, COUNT(DISTINCT m) as merchants_paid
LIMIT 50;

// 25. Bidirectional Transaction Pattern (Circular money flow detection)
MATCH (a1:FraudAccount)-[:FRAUD_TRANSACTION]->(a2:FraudAccount)-[:FRAUD_TRANSACTION]->(a1)
RETURN a1.account_id as account_1, a2.account_id as account_2,
       a1.is_fraudulent as fraud_1, a2.is_fraudulent as fraud_2
LIMIT 20;
