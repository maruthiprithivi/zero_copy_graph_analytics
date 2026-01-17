// Customer 360 Cypher Queries for PuppyGraph
// These queries demonstrate graph traversal and relationship analysis
// Schema: Customer -> PURCHASED -> Product
// Note: Revenue/aggregation queries are in queries.sql (ClickHouse excels at aggregations)

// ============================================================================
// BASIC GRAPH QUERIES
// ============================================================================

// 1. Get Customer and Their Purchases - VIP Segment
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN c.name as customer, c.segment, p.name as product, p.category, p.brand
LIMIT 20;

// 2. Customer Purchase Network
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN c, p
LIMIT 100;

// 3. Product Relationships - Electronics
MATCH (p:Product)
WHERE p.category = 'Electronics'
RETURN p.name, p.brand, p.category
LIMIT 50;

// 4. Premium Customer Purchases
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'Premium'
RETURN c.name as customer, c.email, p.name as product, p.category
LIMIT 20;

// ============================================================================
// PRODUCT RECOMMENDATION QUERIES
// ============================================================================

// 5. Product Affinity - Frequently Bought Together (Electronics)
MATCH (c1:Customer)-[:PURCHASED]->(p1:Product)
MATCH (c1)-[:PURCHASED]->(p2:Product)
WHERE p1.category = 'Electronics'
  AND p2.category = 'Electronics'
  AND p1 <> p2
RETURN p1.name as product_1, p2.name as product_2, COUNT(DISTINCT c1) as co_purchases
ORDER BY co_purchases DESC
LIMIT 10;

// 6. Cross-Category Affinity - Electronics buyers also buy
MATCH (c:Customer)-[:PURCHASED]->(p1:Product)
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p1.category = 'Electronics'
  AND p2.category <> 'Electronics'
RETURN p2.category as other_category, COUNT(DISTINCT c) as customer_count
ORDER BY customer_count DESC
LIMIT 10;

// 7. Brand Affinity - Apple Customers
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE p.brand = 'Apple'
RETURN c.name, c.segment, p.name, p.category
LIMIT 20;

// ============================================================================
// CUSTOMER SEGMENTATION & BEHAVIOR
// ============================================================================

// 8. High-Value Segment Purchase Counts
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment IN ['VIP', 'Premium']
RETURN c.name, c.segment, COUNT(DISTINCT p) as unique_products
ORDER BY unique_products DESC
LIMIT 20;

// 9. Brand Loyalty Analysis - Apple
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE p.brand = 'Apple'
WITH c, COUNT(DISTINCT p) as apple_products
WHERE apple_products >= 2
RETURN c.name, c.segment, apple_products
ORDER BY apple_products DESC
LIMIT 20;

// 10. Customer Journey - Premium Segment
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'Premium'
WITH c, p
LIMIT 30
RETURN c.name as customer, c.segment, p.name as product, p.category, p.brand
ORDER BY c.name, p.category;

// ============================================================================
// CROSS-SELL OPPORTUNITIES
// ============================================================================

// 11. VIP Customers - Category Distribution
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN p.category, COUNT(DISTINCT c) as vip_customers, COUNT(p) as total_purchases
ORDER BY total_purchases DESC
LIMIT 10;

// 12. Premium Customers - Category Distribution
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'Premium'
RETURN p.category, COUNT(DISTINCT c) as premium_customers, COUNT(p) as total_purchases
ORDER BY total_purchases DESC
LIMIT 10;

// ============================================================================
// PRODUCT POPULARITY & TRENDS
// ============================================================================

// 13. Most Popular Products by VIP Customers
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN p.name, p.category, p.brand, COUNT(DISTINCT c) as vip_customers
ORDER BY vip_customers DESC
LIMIT 20;

// 14. Most Popular Products by Premium Customers
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'Premium'
RETURN p.name, p.category, p.brand, COUNT(DISTINCT c) as premium_customers
ORDER BY premium_customers DESC
LIMIT 20;

// 15. Brand Popularity - All Segments
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment IN ['VIP', 'Premium', 'Regular']
RETURN p.brand, c.segment, COUNT(DISTINCT c) as unique_customers
ORDER BY unique_customers DESC
LIMIT 20;

// ============================================================================
// ADVANCED RECOMMENDATION PATHS
// ============================================================================

// 16. 2-Hop Product Relationships (Simplified)
MATCH (c1:Customer)-[:PURCHASED]->(p1:Product)
WHERE c1.segment = 'VIP'
WITH c1, p1
LIMIT 5
MATCH (c1)-[:PURCHASED]->(p2:Product)
WHERE p1 <> p2
RETURN p1.name as product_1, p2.name as product_2, p1.category, p2.category
LIMIT 20;

// 17. Co-Purchase by Brand
MATCH (c:Customer)-[:PURCHASED]->(p1:Product)
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p1.brand = 'Samsung' AND p2.brand <> 'Samsung'
RETURN p1.name, p2.brand, p2.category, COUNT(DISTINCT c) as customers
ORDER BY customers DESC
LIMIT 15;

// ============================================================================
// COUNT QUERIES
// ============================================================================

// 18. Total Customers Count
MATCH (c:Customer)
RETURN count(c) as total_customers;

// 19. Total Products Count
MATCH (p:Product)
RETURN count(p) as total_products;

// 20. Total Purchases Count
MATCH ()-[r:PURCHASED]->()
RETURN count(r) as total_purchases;

// ============================================================================
// INTERACTION-BASED QUERIES (VIEWED, CLICKED, ADDED_TO_CART edges)
// ============================================================================

// 21. Products Most Viewed by VIP Customers
MATCH (c:Customer)-[:VIEWED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN p.name, p.category, p.brand, COUNT(*) as view_count
ORDER BY view_count DESC
LIMIT 20;

// 22. Customer Engagement - Views and Clicks
MATCH (c:Customer)-[:VIEWED]->(p:Product)
OPTIONAL MATCH (c)-[:CLICKED]->(p)
RETURN c.segment, COUNT(*) as total_interactions
ORDER BY total_interactions DESC;

// 23. Full Customer Journey - View, Click, Purchase
MATCH (c:Customer)-[:VIEWED]->(p:Product)
WHERE c.segment = 'VIP'
OPTIONAL MATCH (c)-[:CLICKED]->(p)
OPTIONAL MATCH (c)-[r:PURCHASED]->(p)
RETURN c.name, p.name, p.category,
       CASE WHEN r IS NOT NULL THEN 'Purchased' ELSE 'Not Purchased' END as outcome
LIMIT 50;

// ============================================================================
// ADVANCED GRAPH PATTERNS - Demonstrating Graph Power
// ============================================================================

// 24. Multi-Hop Recommendation Chain (3 degrees of separation)
// Find products through: P1 -> bought by C1 -> also bought P2 -> bought by C2 -> also bought P3
MATCH (p1:Product)<-[:PURCHASED]-(c1:Customer)-[:PURCHASED]->(p2:Product)<-[:PURCHASED]-(c2:Customer)-[:PURCHASED]->(p3:Product)
WHERE p1 <> p2 AND p2 <> p3 AND p1 <> p3 AND c1 <> c2
  AND p1.category = 'Electronics'
RETURN p1.name as seed_product, p2.name as bridge_product, p3.name as recommended_product,
       COUNT(DISTINCT c2) as recommendation_strength
ORDER BY recommendation_strength DESC
LIMIT 15;

// 25. Customer Purchase Triangle (VIP Customers sharing multiple products)
MATCH (c1:Customer)-[:PURCHASED]->(p1:Product)<-[:PURCHASED]-(c2:Customer)
WHERE c1 <> c2 AND c1.segment = 'VIP' AND c2.segment = 'VIP'
WITH c1, c2, COUNT(DISTINCT p1) as shared_products
WHERE shared_products >= 3
RETURN c1.name as customer_1, c2.name as customer_2, shared_products
ORDER BY shared_products DESC
LIMIT 20;

// 26. Category Bridge Analysis (Products connecting Electronics and Home)
MATCH (c:Customer)-[:PURCHASED]->(p1:Product)
WHERE p1.category = 'Electronics'
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p2.category = 'Home'
RETURN p1.name as electronics_product, p2.name as home_product,
       COUNT(DISTINCT c) as customers_buying_both
ORDER BY customers_buying_both DESC
LIMIT 15;

// 27. Brand Ecosystem Network (Customers in Apple + Samsung ecosystems)
MATCH (c:Customer)-[:PURCHASED]->(apple:Product)
WHERE apple.brand = 'Apple'
WITH c, COUNT(DISTINCT apple) as apple_products
MATCH (c)-[:PURCHASED]->(samsung:Product)
WHERE samsung.brand = 'Samsung'
WITH c, apple_products, COUNT(DISTINCT samsung) as samsung_products
RETURN c.name, c.segment, apple_products, samsung_products
ORDER BY apple_products + samsung_products DESC
LIMIT 20;

// 28. View-to-Purchase Conversion Path (Complete funnel)
// Shows customers who have engaged in view, click, AND purchase activities
MATCH (c:Customer)-[:VIEWED]->(v:Product)
MATCH (c)-[:CLICKED]->(cl:Product)
MATCH (c)-[:PURCHASED]->(p:Product)
WHERE c.segment IN ['VIP', 'Premium']
RETURN c.name, c.segment,
       v.name as viewed_product,
       cl.name as clicked_product,
       p.name as purchased_product
LIMIT 30;

// 29. Influential Products (Products whose buyers also buy many other products)
MATCH (c:Customer)-[:PURCHASED]->(p1:Product)
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p1 <> p2
WITH p1, COUNT(DISTINCT p2) as leads_to_products, COUNT(DISTINCT c) as buyer_count
WHERE buyer_count >= 5
RETURN p1.name as influential_product, p1.category, buyer_count, leads_to_products
ORDER BY leads_to_products DESC
LIMIT 20;

// 30. Segment Crossover Products (Products popular with both VIP and Regular customers)
MATCH (c1:Customer)-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(c2:Customer)
WHERE c1.segment = 'VIP' AND c2.segment = 'Regular' AND c1 <> c2
WITH p, COUNT(DISTINCT c1) as vip_buyers, COUNT(DISTINCT c2) as regular_buyers
RETURN p.name, p.category, p.brand, vip_buyers, regular_buyers
ORDER BY vip_buyers + regular_buyers DESC
LIMIT 20;
