// Customer 360 Cypher Queries for PuppyGraph
// These queries demonstrate graph traversal and relationship analysis

// ============================================================================
// BASIC GRAPH QUERIES
// ============================================================================

// 1. Get Customer and Their Purchases
MATCH (c:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
RETURN c.name as customer, c.segment, p.name as product, p.category, p.brand
LIMIT 20;

// 2. Customer Purchase Network
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN c, p
LIMIT 100;

// 3. Product Relationships
MATCH (p:Product)
WHERE p.category = 'Electronics'
RETURN p.name, p.brand, p.price, p.stock_quantity
LIMIT 50;

// ============================================================================
// PRODUCT RECOMMENDATION QUERIES
// ============================================================================

// 4. Collaborative Filtering - Products Purchased by Similar Customers
// Find products that similar customers bought but target customer hasn't
MATCH (target:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p1:Product)
MATCH (other:Customer)-[:PURCHASED]->(p1)
MATCH (other)-[:PURCHASED]->(p2:Product)
WHERE target.segment = other.segment
  AND NOT (target)-[:PURCHASED]->(p2)
  AND target <> other
WITH p2, COLLECT(DISTINCT other) as similar_customers
RETURN DISTINCT p2.name as recommended_product,
       p2.category,
       p2.brand,
       p2.price,
       SIZE(similar_customers) as purchased_by_similar_customers
ORDER BY purchased_by_similar_customers DESC, p2.name
LIMIT 10;

// 5. Product Affinity - Frequently Bought Together
MATCH (c:Customer)-[:PURCHASED]->(p1:Product {product_id: 'PROD_123'})
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p1 <> p2
RETURN p2.name as related_product,
       p2.category,
       p2.brand,
       COUNT(DISTINCT c) as times_bought_together
ORDER BY times_bought_together DESC
LIMIT 15;

// 6. Category Expansion Recommendations
// Customers who bought in one category, what else did they buy?
MATCH (c:Customer)-[:PURCHASED]->(p1:Product)
WHERE p1.category = 'Electronics'
MATCH (c)-[:PURCHASED]->(p2:Product)
WHERE p2.category <> 'Electronics'
RETURN p2.category as other_category,
       COUNT(DISTINCT c) as customer_count,
       COUNT(DISTINCT p2) as product_count
ORDER BY customer_count DESC;

// ============================================================================
// CUSTOMER SEGMENTATION & BEHAVIOR
// ============================================================================

// 7. High-Value Customer Purchase Patterns
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

// 8. Brand Loyalty Analysis
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE p.brand = 'Apple'
WITH c, COUNT(DISTINCT p) as apple_products
WHERE apple_products >= 3
MATCH (c)-[:PURCHASED]->(all_products:Product)
RETURN c.customer_id,
       c.name,
       c.segment,
       apple_products,
       COUNT(DISTINCT all_products) as total_products,
       toFloat(apple_products) / COUNT(DISTINCT all_products) as brand_loyalty_ratio
ORDER BY brand_loyalty_ratio DESC
LIMIT 50;

// 9. Customer Journey - Purchase Sequence
MATCH path = (c:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
RETURN c.name as customer,
       p.name as product,
       p.category,
       p.brand
ORDER BY p.name
LIMIT 20;

// ============================================================================
// CROSS-SELL OPPORTUNITIES
// ============================================================================

// 10. Find Customers Without Purchases in High-Value Categories
MATCH (c:Customer)
WHERE c.segment IN ['VIP', 'Premium']
OPTIONAL MATCH (c)-[:PURCHASED]->(p:Product {category: 'Electronics'})
WITH c, p
WHERE p IS NULL
RETURN c.customer_id,
       c.name,
       c.segment,
       c.lifetime_value
ORDER BY c.lifetime_value DESC
LIMIT 100;

// 11. Category Gap Analysis
// Customers who bought in category A but not category B
MATCH (c:Customer)-[:PURCHASED]->(p1:Product)
WHERE p1.category = 'Electronics'
OPTIONAL MATCH (c)-[:PURCHASED]->(p2:Product {category: 'Home'})
WITH c, p1, p2
WHERE p2 IS NULL
RETURN c.customer_id,
       c.name,
       c.segment,
       COUNT(DISTINCT p1) as electronics_purchases
ORDER BY electronics_purchases DESC
LIMIT 50;

// ============================================================================
// PRODUCT POPULARITY & TRENDS
// ============================================================================

// 12. Most Popular Products by Segment
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WHERE c.segment = 'VIP'
RETURN p.product_id,
       p.name,
       p.category,
       p.brand,
       COUNT(DISTINCT c) as vip_customers,
       p.price
ORDER BY vip_customers DESC
LIMIT 20;

// 13. Category Preferences by Segment
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
RETURN c.segment,
       p.category,
       COUNT(DISTINCT c) as customers,
       COUNT(p) as total_purchases
ORDER BY c.segment, total_purchases DESC;

// 14. Brand Performance Across Segments
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
RETURN p.brand,
       c.segment,
       COUNT(DISTINCT c) as unique_customers,
       COUNT(p) as total_purchases
ORDER BY p.brand, unique_customers DESC;

// ============================================================================
// ADVANCED RECOMMENDATION PATHS
// ============================================================================

// 15. 2-Hop Recommendation Path
// Find products through 2 degrees of customer similarity
MATCH (target:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p1:Product)
MATCH (c1:Customer)-[:PURCHASED]->(p1)
MATCH (c1)-[:PURCHASED]->(p2:Product)
MATCH (c2:Customer)-[:PURCHASED]->(p2)
MATCH (c2)-[:PURCHASED]->(p3:Product)
WHERE target <> c1
  AND target <> c2
  AND c1 <> c2
  AND NOT (target)-[:PURCHASED]->(p2)
  AND NOT (target)-[:PURCHASED]->(p3)
  AND p1 <> p2
  AND p2 <> p3
WITH p3, COLLECT(DISTINCT c2) as recommenders
RETURN DISTINCT p3.name as recommended_product,
       p3.category,
       p3.brand,
       p3.price,
       SIZE(recommenders) as recommendation_strength
ORDER BY recommendation_strength DESC, p3.price DESC
LIMIT 10;

// 16. Complementary Product Discovery
// Products often purchased in sequence by similar customers
MATCH (c1:Customer)-[:PURCHASED]->(p1:Product)
WHERE p1.product_id = 'PROD_123'
MATCH (c2:Customer)-[:PURCHASED]->(p1)
MATCH (c2)-[:PURCHASED]->(p2:Product)
WHERE c1.segment = c2.segment
  AND p1 <> p2
  AND NOT (c1)-[:PURCHASED]->(p2)
RETURN p2.name as complementary_product,
       p2.category,
       p2.brand,
       p2.price,
       COUNT(DISTINCT c2) as times_purchased_after
ORDER BY times_purchased_after DESC
LIMIT 10;

// ============================================================================
// CUSTOMER SIMILARITY & CLUSTERING
// ============================================================================

// 17. Find Similar Customers Based on Purchase Overlap
MATCH (c1:Customer {customer_id: 'CUST_12345'})-[:PURCHASED]->(p:Product)
MATCH (c2:Customer)-[:PURCHASED]->(p)
WHERE c1 <> c2
WITH c1, c2, COUNT(DISTINCT p) as shared_products
MATCH (c1)-[:PURCHASED]->(all_p1:Product)
MATCH (c2)-[:PURCHASED]->(all_p2:Product)
WITH c1, c2,
     shared_products,
     COUNT(DISTINCT all_p1) as c1_total,
     COUNT(DISTINCT all_p2) as c2_total
RETURN c2.customer_id,
       c2.name,
       c2.segment,
       shared_products,
       c1_total as my_products,
       c2_total as their_products,
       toFloat(shared_products) / c1_total as similarity_score
ORDER BY similarity_score DESC, shared_products DESC
LIMIT 20;

// 18. Customer Segment Network Density
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
RETURN c.segment,
       COUNT(DISTINCT c) as customers,
       COUNT(DISTINCT p) as products,
       COUNT(*) as total_purchases,
       toFloat(COUNT(*)) / (COUNT(DISTINCT c) * COUNT(DISTINCT p)) as network_density
ORDER BY network_density DESC;

// ============================================================================
// CHURN RISK & ENGAGEMENT
// ============================================================================

// 19. Low Engagement Customers in High-Value Segments
MATCH (c:Customer)
WHERE c.segment IN ['VIP', 'Premium']
OPTIONAL MATCH (c)-[:PURCHASED]->(p:Product)
WITH c, COUNT(p) as purchase_count
WHERE purchase_count < 3
RETURN c.customer_id,
       c.name,
       c.segment,
       c.lifetime_value,
       purchase_count
ORDER BY c.lifetime_value DESC
LIMIT 50;

// 20. Cross-Category Purchase Diversity
MATCH (c:Customer)-[:PURCHASED]->(p:Product)
WITH c, COLLECT(DISTINCT p.category) as categories
RETURN c.customer_id,
       c.name,
       c.segment,
       c.lifetime_value,
       SIZE(categories) as category_diversity,
       categories
ORDER BY category_diversity DESC, c.lifetime_value DESC
LIMIT 50;
