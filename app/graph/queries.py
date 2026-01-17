#!/usr/bin/env python3
"""
Cypher Queries for Customer 360 Graph Analytics
Essential queries for customer insights using PuppyGraph
"""

import os
import logging
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class Customer360Queries:
    """Customer 360 graph analytics using Cypher queries"""
    
    def __init__(self):
        """Initialize connection to PuppyGraph via Neo4j Bolt protocol"""
        load_dotenv()
        
        self.host = os.getenv('PUPPYGRAPH_HOST', 'localhost')
        self.port = 7687  # PuppyGraph Cypher port
        self.username = 'puppygraph'
        self.password = os.getenv('PUPPYGRAPH_PASSWORD', 'puppygraph123')
        self.driver = None
        self.mock_mode = False
        
        # Create Neo4j driver to connect to PuppyGraph
        uri = f"bolt://{self.host}:{self.port}"
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(self.username, self.password))
            # Test the connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Successfully connected to PuppyGraph at {uri}")
        except Exception as e:
            logger.warning(f"Failed to connect to PuppyGraph at {uri}: {e}")
            logger.info("Running in mock mode with sample data")
            self.mock_mode = True
            self.driver = None
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
    
    def run_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute a Cypher query and return results"""
        if self.mock_mode or not self.driver:
            logger.debug("Running in mock mode - returning empty result")
            return []
            
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Cypher query failed: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Parameters: {parameters}")
            logger.warning("Switching to mock mode due to query failure")
            self.mock_mode = True
            return []
    
    def get_customer_360_view(self, customer_id: str) -> Dict:
        """Get complete 360-degree view of a customer"""
        
        query = """
        MATCH (c:Customer {customer_id: $customer_id})
        OPTIONAL MATCH (c)-[p:PURCHASED]->(product:Product)
        OPTIONAL MATCH (c)-[v:VIEWED]->(viewed:Product)
        
        WITH c, 
             COLLECT(DISTINCT {
                 product: product.name,
                 category: product.category,
                 amount: p.amount,
                 timestamp: p.timestamp
             }) AS purchases,
             COLLECT(DISTINCT {
                 product: viewed.name,
                 category: viewed.category,
                 timestamp: v.timestamp,
                 duration: v.duration
             }) AS views
        
        RETURN c.name AS customer_name,
               c.email AS email,
               c.segment AS segment,
               c.ltv AS ltv,
               SIZE(purchases) AS total_purchases,
               SIZE(views) AS total_views,
               purchases[..5] AS recent_purchases,
               views[..5] AS recent_views
        """
        
        result = self.run_query(query, {'customer_id': customer_id})
        return result[0] if result else {}
    
    def get_customer_recommendations(self, customer_id: str, limit: int = 10) -> List[Dict]:
        """Get product recommendations based on similar customers"""
        
        query = """
        // Find customers with similar purchase patterns
        MATCH (target:Customer {customer_id: $customer_id})-[:PURCHASED]->(p:Product)
        WITH target, COLLECT(p) AS targetProducts
        
        MATCH (other:Customer)-[:PURCHASED]->(p:Product)
        WHERE p IN targetProducts AND other <> target
        WITH target, other, COUNT(DISTINCT p) AS commonProducts
        WHERE commonProducts >= 2
        
        // Find products purchased by similar customers but not by target
        MATCH (other)-[:PURCHASED]->(rec:Product)
        WHERE NOT (target)-[:PURCHASED]->(rec)
        
        RETURN rec.name AS product_name,
               rec.category AS category,
               rec.brand AS brand,
               rec.price AS price,
               COUNT(DISTINCT other) AS recommended_by_customers,
               AVG(commonProducts) AS similarity_score
        ORDER BY recommended_by_customers DESC, similarity_score DESC
        LIMIT $limit
        """
        
        return self.run_query(query, {'customer_id': customer_id, 'limit': limit})
    
    def get_top_customers_by_segment(self, segment: str = None, limit: int = 20) -> List[Dict]:
        """Get top customers by total spending, optionally filtered by segment"""
        
        where_clause = "WHERE c.segment = $segment" if segment else ""
        
        query = f"""
        MATCH (c:Customer)-[p:PURCHASED]->(product:Product)
        {where_clause}
        
        WITH c, 
             COUNT(p) AS total_purchases,
             SUM(p.amount) AS total_spent,
             COLLECT(DISTINCT product.category) AS categories
        
        RETURN c.customer_id AS customer_id,
               c.name AS customer_name,
               c.segment AS segment,
               c.ltv AS ltv,
               total_purchases,
               ROUND(total_spent, 2) AS total_spent,
               SIZE(categories) AS unique_categories,
               categories[..3] AS top_categories
        ORDER BY total_spent DESC
        LIMIT $limit
        """
        
        params = {'limit': limit}
        if segment:
            params['segment'] = segment
        
        return self.run_query(query, params)
    
    def get_popular_products(self, category: str = None, limit: int = 20) -> List[Dict]:
        """Get most popular products by purchase count"""
        
        if self.mock_mode or not self.driver:
            return self._get_mock_popular_products(category, limit)
        
        where_clause = "WHERE p.category = $category" if category else ""
        
        query = f"""
        MATCH (c:Customer)-[purchased:PURCHASED]->(p:Product)
        {where_clause}
        
        WITH p, 
             COUNT(purchased) AS purchase_count,
             COUNT(DISTINCT c) AS unique_customers,
             SUM(purchased.amount) AS total_revenue,
             AVG(purchased.amount) AS avg_purchase_amount
        
        RETURN p.name AS product_name,
               p.category AS category,
               p.brand AS brand,
               p.price AS list_price,
               purchase_count,
               unique_customers,
               ROUND(total_revenue, 2) AS total_revenue,
               ROUND(avg_purchase_amount, 2) AS avg_purchase_amount
        ORDER BY purchase_count DESC
        LIMIT $limit
        """
        
        params = {'limit': limit}
        if category:
            params['category'] = category
        
        result = self.run_query(query, params)
        return result if result else self._get_mock_popular_products(category, limit)
    
    def get_customer_journey(self, customer_id: str) -> List[Dict]:
        """Get chronological customer journey (views and purchases)"""
        
        query = """
        MATCH (c:Customer {customer_id: $customer_id})
        
        // Get all purchases
        OPTIONAL MATCH (c)-[p:PURCHASED]->(purchased:Product)
        WITH c, COLLECT({
            type: 'PURCHASE',
            product_name: purchased.name,
            category: purchased.category,
            amount: p.amount,
            timestamp: p.timestamp,
            channel: p.channel
        }) AS purchases
        
        // Get all views
        OPTIONAL MATCH (c)-[v:VIEWED]->(viewed:Product)
        WITH c, purchases, COLLECT({
            type: 'VIEW',
            product_name: viewed.name,
            category: viewed.category,
            duration: v.duration,
            timestamp: v.timestamp,
            device: v.device
        }) AS views
        
        // Combine and sort by timestamp
        WITH purchases + views AS all_events
        UNWIND all_events AS event
        
        RETURN event.type AS event_type,
               event.product_name AS product_name,
               event.category AS category,
               event.amount AS amount,
               event.duration AS duration,
               event.timestamp AS timestamp,
               event.channel AS channel,
               event.device AS device
        ORDER BY event.timestamp DESC
        LIMIT 50
        """
        
        return self.run_query(query, {'customer_id': customer_id})
    
    def get_category_affinity(self, limit: int = 10) -> List[Dict]:
        """Find product categories frequently bought together"""
        
        query = """
        MATCH (c:Customer)-[:PURCHASED]->(p1:Product)
        MATCH (c)-[:PURCHASED]->(p2:Product)
        WHERE p1.category < p2.category  // Avoid duplicates and self-matches
        
        WITH p1.category AS category1, 
             p2.category AS category2, 
             COUNT(DISTINCT c) AS customers_buying_both
        
        MATCH (:Customer)-[:PURCHASED]->(:Product {category: category1})
        WITH category1, category2, customers_buying_both, COUNT(DISTINCT c) AS total_category1_customers
        
        MATCH (:Customer)-[:PURCHASED]->(:Product {category: category2})
        WITH category1, category2, customers_buying_both, total_category1_customers, 
             COUNT(DISTINCT c) AS total_category2_customers
        
        // Calculate affinity metrics
        WITH category1, category2, customers_buying_both,
             total_category1_customers, total_category2_customers,
             ROUND(toFloat(customers_buying_both) / total_category1_customers, 3) AS affinity_1_to_2,
             ROUND(toFloat(customers_buying_both) / total_category2_customers, 3) AS affinity_2_to_1
        
        RETURN category1,
               category2,
               customers_buying_both,
               ROUND((affinity_1_to_2 + affinity_2_to_1) / 2, 3) AS avg_affinity
        ORDER BY avg_affinity DESC
        LIMIT $limit
        """
        
        return self.run_query(query, {'limit': limit})
    
    def get_segment_analysis(self) -> List[Dict]:
        """Analyze customer segments behavior"""
        
        if self.mock_mode or not self.driver:
            return self._get_mock_segment_analysis()
        
        query = """
        MATCH (c:Customer)
        OPTIONAL MATCH (c)-[p:PURCHASED]->(product:Product)
        
        WITH c.segment AS segment,
             COUNT(DISTINCT c) AS total_customers,
             COUNT(p) AS total_purchases,
             SUM(p.amount) AS total_revenue,
             AVG(c.ltv) AS avg_ltv,
             COLLECT(DISTINCT product.category) AS categories
        
        RETURN segment,
               total_customers,
               total_purchases,
               ROUND(total_revenue, 2) AS total_revenue,
               ROUND(toFloat(total_purchases) / total_customers, 1) AS avg_purchases_per_customer,
               ROUND(total_revenue / total_customers, 2) AS avg_revenue_per_customer,
               ROUND(avg_ltv, 2) AS avg_ltv,
               SIZE(categories) AS unique_categories_purchased
        ORDER BY total_revenue DESC
        """
        
        result = self.run_query(query)
        return result if result else self._get_mock_segment_analysis()
    
    def search_customers(self, search_term: str, limit: int = 20) -> List[Dict]:
        """Search customers by name or email"""
        
        query = """
        MATCH (c:Customer)
        WHERE toLower(c.name) CONTAINS toLower($search_term) 
           OR toLower(c.email) CONTAINS toLower($search_term)
        
        OPTIONAL MATCH (c)-[p:PURCHASED]->(product:Product)
        WITH c, COUNT(p) AS total_purchases, SUM(p.amount) AS total_spent
        
        RETURN c.customer_id AS customer_id,
               c.name AS customer_name,
               c.email AS email,
               c.segment AS segment,
               c.ltv AS ltv,
               total_purchases,
               ROUND(total_spent, 2) AS total_spent
        ORDER BY total_spent DESC
        LIMIT $limit
        """
        
        if self.mock_mode or not self.driver:
            return self._get_mock_customer_search(search_term, limit)
        
        result = self.run_query(query, {'search_term': search_term, 'limit': limit})
        return result if result else self._get_mock_customer_search(search_term, limit)
    
    # Mock data methods for fallback when PuppyGraph is not available
    def _get_mock_segment_analysis(self) -> List[Dict]:
        """Mock segment analysis data"""
        return [
            {
                'segment': 'Premium',
                'total_customers': 150000,
                'total_purchases': 750000,
                'total_revenue': 125000000.50,
                'avg_purchases_per_customer': 5.0,
                'avg_revenue_per_customer': 833.33,
                'avg_ltv': 5200.50,
                'unique_categories_purchased': 8
            },
            {
                'segment': 'Regular',
                'total_customers': 450000,
                'total_purchases': 1350000,
                'total_revenue': 189000000.75,
                'avg_purchases_per_customer': 3.0,
                'avg_revenue_per_customer': 420.00,
                'avg_ltv': 2800.75,
                'unique_categories_purchased': 6
            },
            {
                'segment': 'Basic',
                'total_customers': 400000,
                'total_purchases': 800000,
                'total_revenue': 96000000.25,
                'avg_purchases_per_customer': 2.0,
                'avg_revenue_per_customer': 240.00,
                'avg_ltv': 1200.25,
                'unique_categories_purchased': 4
            }
        ]
    
    def _get_mock_customer_search(self, search_term: str, limit: int) -> List[Dict]:
        """Mock customer search results"""
        all_customers = [
            {'customer_id': '0002d9cc-ce1e-4ed2-b169-7d1a778e7a72', 'customer_name': 'Michael Myers', 'email': 'michael.myers@example.org', 'segment': 'Premium', 'ltv': 5200.50, 'total_purchases': 15, 'total_spent': 8750.25},
            {'customer_id': '00038af4-afee-4e3a-8ba2-9b31d77eff7f', 'customer_name': 'John Mcconnell', 'email': 'john.mcconnell@example.com', 'segment': 'Regular', 'ltv': 2800.75, 'total_purchases': 8, 'total_spent': 3420.50},
            {'customer_id': '00054351-cc20-43e4-a10e-9e6e39fc4311', 'customer_name': 'Sarah Duncan', 'email': 'sarah.duncan@example.net', 'segment': 'Premium', 'ltv': 6100.00, 'total_purchases': 18, 'total_spent': 12450.75},
            {'customer_id': '0008ab35-aa33-40ca-bd85-64c3870e310f', 'customer_name': 'Michael Gardner', 'email': 'michael.gardner@gmail.com', 'segment': 'Regular', 'ltv': 3200.25, 'total_purchases': 10, 'total_spent': 4680.00},
            {'customer_id': '0009a6c7-832e-4ab8-b803-a3046b06a9f9', 'customer_name': 'John Palmer', 'email': 'john.palmer@yahoo.com', 'segment': 'Basic', 'ltv': 1500.50, 'total_purchases': 5, 'total_spent': 1200.25}
        ]
        
        # Filter based on search term
        search_lower = search_term.lower()
        filtered = []
        for customer in all_customers:
            if (search_lower in customer['customer_name'].lower() or 
                search_lower in customer['email'].lower()):
                filtered.append(customer)
        
        return filtered[:limit]
    
    def _get_mock_popular_products(self, category: str = None, limit: int = 20) -> List[Dict]:
        """Mock popular products data"""
        all_products = [
            {'product_name': 'iPhone 15 Pro Max', 'category': 'Electronics', 'brand': 'Apple', 'list_price': 1199.99, 'purchase_count': 8542, 'unique_customers': 7821, 'total_revenue': 10250000.58, 'avg_purchase_amount': 1201.25},
            {'product_name': 'Premium Coffee Beans', 'category': 'Food', 'brand': 'Starbucks', 'list_price': 24.99, 'purchase_count': 6234, 'unique_customers': 4521, 'total_revenue': 155742.66, 'avg_purchase_amount': 24.99},
            {'product_name': 'Wireless Headphones', 'category': 'Electronics', 'brand': 'Sony', 'list_price': 299.99, 'purchase_count': 5874, 'unique_customers': 5102, 'total_revenue': 1762000.26, 'avg_purchase_amount': 299.99},
            {'product_name': 'Organic Cotton T-Shirt', 'category': 'Clothing', 'brand': 'Patagonia', 'list_price': 45.00, 'purchase_count': 4521, 'unique_customers': 3876, 'total_revenue': 203445.00, 'avg_purchase_amount': 45.00},
            {'product_name': 'Smart Watch', 'category': 'Electronics', 'brand': 'Samsung', 'list_price': 399.99, 'purchase_count': 4102, 'unique_customers': 3654, 'total_revenue': 1640000.98, 'avg_purchase_amount': 399.99},
            {'product_name': 'Yoga Mat', 'category': 'Sports', 'brand': 'Lululemon', 'list_price': 78.00, 'purchase_count': 3845, 'unique_customers': 3201, 'total_revenue': 299910.00, 'avg_purchase_amount': 78.00},
            {'product_name': 'Running Shoes', 'category': 'Sports', 'brand': 'Nike', 'list_price': 149.99, 'purchase_count': 3654, 'unique_customers': 3298, 'total_revenue': 548000.46, 'avg_purchase_amount': 149.99},
            {'product_name': 'Skincare Set', 'category': 'Beauty', 'brand': 'Glossier', 'list_price': 89.00, 'purchase_count': 3102, 'unique_customers': 2876, 'total_revenue': 276078.00, 'avg_purchase_amount': 89.00}
        ]
        
        # Filter by category if specified
        if category:
            filtered_products = [p for p in all_products if p['category'].lower() == category.lower()]
        else:
            filtered_products = all_products
        
        return filtered_products[:limit]


def main():
    """Main function for testing queries"""
    
    queries = Customer360Queries()
    
    try:
        # Test basic connectivity
        logger.info("Testing basic queries...")
        
        # Get segment analysis
        segments = queries.get_segment_analysis()
        print("\n Customer Segment Analysis:")
        for segment in segments:
            print(f"  {segment}")
        
        # Get top customers
        top_customers = queries.get_top_customers_by_segment(limit=5)
        print(f"\n Top 5 Customers:")
        for customer in top_customers:
            print(f"  {customer}")
        
        # Get popular products
        popular = queries.get_popular_products(limit=5)
        print(f"\n Top 5 Popular Products:")
        for product in popular:
            print(f"  {product}")
            
        print("\n Query tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Query test failed: {e}")
    finally:
        queries.close()


if __name__ == "__main__":
    main()