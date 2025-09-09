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
        
        # Create Neo4j driver to connect to PuppyGraph
        uri = f"bolt://{self.host}:{self.port}"
        self.driver = GraphDatabase.driver(uri, auth=(self.username, self.password))
        
        logger.info(f"Connected to PuppyGraph at {uri}")
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
    
    def run_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute a Cypher query and return results"""
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
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
        
        return self.run_query(query, params)
    
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
        
        return self.run_query(query)
    
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
        
        return self.run_query(query, {'search_term': search_term, 'limit': limit})


def main():
    """Main function for testing queries"""
    
    queries = Customer360Queries()
    
    try:
        # Test basic connectivity
        logger.info("Testing basic queries...")
        
        # Get segment analysis
        segments = queries.get_segment_analysis()
        print("\n📊 Customer Segment Analysis:")
        for segment in segments:
            print(f"  {segment}")
        
        # Get top customers
        top_customers = queries.get_top_customers_by_segment(limit=5)
        print(f"\n👑 Top 5 Customers:")
        for customer in top_customers:
            print(f"  {customer}")
        
        # Get popular products
        popular = queries.get_popular_products(limit=5)
        print(f"\n🎯 Top 5 Popular Products:")
        for product in popular:
            print(f"  {product}")
            
        print("\n✅ Query tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Query test failed: {e}")
    finally:
        queries.close()


if __name__ == "__main__":
    main()