#!/usr/bin/env python3
"""
Customer 360 Data Generator - Enhanced with Batch Processing
Generates realistic customer, product, and transaction data with configurable batch sizes
"""

import os
import uuid
import random
import numpy as np
import math
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
import pandas as pd
from faker import Faker
from tqdm import tqdm
import logging
from dotenv import load_dotenv

# Setup logging
def setup_logging():
    load_dotenv()
    level = logging.DEBUG if os.getenv('VERBOSE_LOGGING', 'true').lower() == 'true' else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data_generation.log')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class Customer360Generator:
    """Simple data generator for Customer 360 demo"""
    
    def __init__(self, scale: int = None, seed: int = None):
        """
        Initialize generator with environment-based configuration
        
        Args:
            scale: Number of customers to generate (overrides env var)
            seed: Random seed for reproducible data (overrides env var)
        """
        load_dotenv()
        
        # Get configuration from environment or use defaults
        self.scale = scale or int(os.getenv('CUSTOMER_SCALE', 1_000_000))
        seed = seed or int(os.getenv('RANDOM_SEED', 42))
        self.batch_file_size = int(os.getenv('BATCH_FILE_SIZE', 100_000))
        self.output_dir = os.getenv('DATA_OUTPUT_DIR', 'data')
        self.compression = os.getenv('PARQUET_COMPRESSION', 'snappy')
        self.overwrite_existing = os.getenv('OVERWRITE_EXISTING_DATA', 'false').lower() == 'true'
        
        # Setup Faker with seed for reproducible data
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)
        
        # Configuration based on scale
        if self.scale <= 1_000_000:
            self.product_count = 10_000
            self.avg_transactions_per_customer = 8
        elif self.scale <= 10_000_000:
            self.product_count = 25_000
            self.avg_transactions_per_customer = 10
        else:  # 100M+
            self.product_count = 50_000
            self.avg_transactions_per_customer = 12
        
        logger.info(f"Generator initialized:")
        logger.info(f"  - Scale: {self.scale:,} customers")
        logger.info(f"  - Products: {self.product_count:,}")
        logger.info(f"  - Batch size: {self.batch_file_size:,}")
        logger.info(f"  - Output dir: {self.output_dir}")
        logger.info(f"  - Compression: {self.compression}")

        # Initialize tracking dictionaries for patterns
        self.customer_brand_affinity = {}
        self.customer_category_exclusions = {}
        self.customer_purchase_count = {}
        self.seed_purchases = {}
        self.products_by_category = {}
        self.products_by_brand = {}

        # Seed data tracking (UUIDs stored for reference)
        self.seed_customers = {}  # {segment: [customer_dicts]}
        self.seed_products = {}   # {category: {brand: [product_dicts]}}
        self.seed_customer_ids = []  # All seed customer IDs
        self.seed_product_ids = []   # All seed product IDs

    def _assign_brand_affinity(self, customer_segment: str) -> str:
        """Assign brand affinity to customer - 30% develop brand loyalty"""
        if random.random() < 0.30:
            if customer_segment in ['VIP', 'Premium']:
                primary_brands = ['Apple', 'Sony', 'Nike', 'Samsung']
            else:
                primary_brands = ['HP', 'Dell', 'Gap', 'Adidas']
            return random.choice(primary_brands)
        return None

    def _should_exclude_category(self, customer_segment: str) -> List[str]:
        """20% of VIP/Premium customers have NOT purchased Electronics"""
        if customer_segment in ['VIP', 'Premium'] and random.random() < 0.20:
            return ['Electronics']
        return []

    def _generate_monthly_cohort_date(self, customer_index: int) -> datetime:
        """Distribute customers across 12 monthly cohorts"""
        cohort_month = customer_index % 12
        join_date = datetime.now() - timedelta(days=365 - (cohort_month * 30))
        return join_date

    def _generate_transaction_timestamp(self) -> datetime:
        """Create temporal patterns with recency bias"""
        days_ago = random.choices(
            [random.randint(0, 90), random.randint(90, 180), random.randint(180, 365)],
            weights=[0.60, 0.30, 0.10]
        )[0]
        return datetime.now() - timedelta(days=days_ago)

    def _get_category_affinity_categories(self, category: str) -> List[str]:
        """Get affinity categories for cross-category purchases"""
        category_affinity = {
            'Electronics': ['Home', 'Clothing'],
            'Clothing': ['Beauty'],
            'Home': ['Electronics'],
            'Sports': ['Clothing'],
            'Beauty': ['Clothing'],
            'Books': []
        }
        return category_affinity.get(category, [])

    def _get_product_basket(self, product_name: str) -> List[str]:
        """Get basket items commonly bought with a product"""
        if 'Laptop' in product_name or 'Dell' in product_name or 'HP' in product_name:
            return ['Mouse', 'Laptop Bag']
        elif 'Phone' in product_name or 'Apple' in product_name or 'Samsung' in product_name:
            return ['Charger']
        elif 'Camera' in product_name or 'Sony' in product_name:
            return ['Memory Card']
        return []

    def generate_seed_customers(self) -> List[Dict]:
        """
        Generate 50 seed customers with guaranteed segment distribution.
        These customers will have predictable patterns for query testing.
        """
        logger.info("Generating seed customers for guaranteed query results...")

        seeds = []
        segments = ['VIP', 'Premium', 'Regular', 'Basic', 'New']

        # LTV ranges by segment (same as regular customers)
        ltv_ranges = {
            'VIP': (8000, 30000),
            'Premium': (5000, 12000),
            'Regular': (800, 3000),
            'Basic': (200, 1000),
            'New': (50, 400)
        }

        for segment in segments:
            self.seed_customers[segment] = []
            min_ltv, max_ltv = ltv_ranges[segment]

            for i in range(10):  # 10 customers per segment
                customer_id = str(uuid.uuid4())
                self.seed_customer_ids.append(customer_id)

                customer = {
                    'customer_id': customer_id,
                    'email': f"seed_{segment.lower()}_{i}@example.com",
                    'name': f"Seed {segment} Customer {i}",
                    'segment': segment,
                    'ltv': round(random.uniform(min_ltv, max_ltv), 2),
                    'registration_date': datetime.now() - timedelta(days=random.randint(30, 365)),
                    'created_at': datetime.utcnow()
                }
                seeds.append(customer)
                self.seed_customers[segment].append(customer)

                # Set brand affinity for VIP/Premium seed customers
                if segment in ['VIP', 'Premium']:
                    self.customer_brand_affinity[customer_id] = 'Apple' if i < 5 else 'Samsung'
                else:
                    self.customer_brand_affinity[customer_id] = None

                # Some VIP/Premium customers exclude Electronics (for cross-sell queries)
                if segment in ['VIP', 'Premium'] and i >= 8:  # Last 2 per segment
                    self.customer_category_exclusions[customer_id] = ['Electronics']
                else:
                    self.customer_category_exclusions[customer_id] = []

        logger.info(f"Generated {len(seeds)} seed customers")
        return seeds

    def generate_seed_products(self) -> List[Dict]:
        """
        Generate seed products with specific categories and brands.
        Ensures we have products for all query patterns.
        """
        logger.info("Generating seed products for guaranteed query results...")

        seeds = []

        # Product configuration: (category, brand, count, price_range)
        product_configs = [
            ('Electronics', 'Apple', 5, (500, 2000)),
            ('Electronics', 'Samsung', 5, (400, 1500)),
            ('Electronics', 'Sony', 5, (300, 1200)),
            ('Clothing', 'Nike', 5, (50, 300)),
            ('Clothing', 'Adidas', 5, (40, 250)),
            ('Home', 'IKEA', 5, (50, 500)),
            ('Home', 'Wayfair', 5, (60, 600)),
            ('Books', 'Penguin', 3, (15, 50)),
            ('Sports', 'Nike', 4, (30, 200)),
            ('Beauty', 'Loreal', 3, (20, 100)),
        ]

        for category, brand, count, (min_price, max_price) in product_configs:
            if category not in self.seed_products:
                self.seed_products[category] = {}
            if brand not in self.seed_products[category]:
                self.seed_products[category][brand] = []

            for i in range(count):
                product_id = str(uuid.uuid4())
                self.seed_product_ids.append(product_id)

                product = {
                    'product_id': product_id,
                    'name': f"{brand} {category} Seed {i+1}",
                    'category': category,
                    'brand': brand,
                    'price': round(random.uniform(min_price, max_price), 2),
                    'launch_date': self.fake.date_between(start_date='-2y', end_date='today'),
                    'created_at': datetime.utcnow()
                }
                seeds.append(product)
                self.seed_products[category][brand].append(product)

        logger.info(f"Generated {len(seeds)} seed products")
        return seeds

    def generate_seed_transactions(self) -> List[Dict]:
        """
        Generate seed transactions that guarantee all query patterns return results.
        This is the "backwards" approach - creating data that matches query requirements.
        """
        logger.info("Generating seed transactions for guaranteed query results...")

        txns = []

        # Helper to create transaction
        def create_txn(customer, product, days_ago=None):
            timestamp = datetime.now() - timedelta(days=days_ago or random.randint(1, 90))
            return {
                'transaction_id': str(uuid.uuid4()),
                'customer_id': customer['customer_id'],
                'product_id': product['product_id'],
                'amount': round(product['price'] * random.uniform(0.9, 1.3), 2),
                'quantity': random.randint(1, 2),
                'timestamp': timestamp,
                'channel': random.choice(['web', 'mobile_app', 'store']),
                'status': 'completed'
            }

        # =================================================================
        # PATTERN 1: Brand Loyalty (Cypher Q8)
        # 5 VIP customers each buy 3+ Apple products
        # =================================================================
        logger.debug("Creating brand loyalty pattern...")
        apple_products = self.seed_products.get('Electronics', {}).get('Apple', [])
        vip_customers = self.seed_customers.get('VIP', [])

        for i, customer in enumerate(vip_customers[:5]):
            for product in apple_products[:3]:  # 3 Apple products each
                txns.append(create_txn(customer, product, days_ago=random.randint(10, 60)))

        # =================================================================
        # PATTERN 2: Collaborative Filtering (Cypher Q4)
        # VIP customers sharing products - C1 buys P1, C2 buys P1 and P2
        # =================================================================
        logger.debug("Creating collaborative filtering pattern...")
        samsung_products = self.seed_products.get('Electronics', {}).get('Samsung', [])

        if len(vip_customers) >= 4 and len(samsung_products) >= 3:
            # Customer 0 and 1 both buy Samsung product 0
            txns.append(create_txn(vip_customers[0], samsung_products[0]))
            txns.append(create_txn(vip_customers[1], samsung_products[0]))
            # Customer 1 also buys Samsung product 1 (recommendation for Customer 0)
            txns.append(create_txn(vip_customers[1], samsung_products[1]))

            # Customer 2 and 3 share another pattern
            txns.append(create_txn(vip_customers[2], samsung_products[1]))
            txns.append(create_txn(vip_customers[3], samsung_products[1]))
            txns.append(create_txn(vip_customers[3], samsung_products[2]))

        # =================================================================
        # PATTERN 3: Product Affinity - Frequently Bought Together (Cypher Q5)
        # Same customers buying multiple Electronics products
        # =================================================================
        logger.debug("Creating product affinity pattern...")
        sony_products = self.seed_products.get('Electronics', {}).get('Sony', [])
        premium_customers = self.seed_customers.get('Premium', [])

        for customer in premium_customers[:5]:
            # Each Premium customer buys 2-3 Sony products
            for product in sony_products[:random.randint(2, 3)]:
                txns.append(create_txn(customer, product))

        # =================================================================
        # PATTERN 4: Category Expansion (Cypher Q6)
        # Customers who bought Electronics also bought other categories
        # =================================================================
        logger.debug("Creating category expansion pattern...")
        clothing_products = self.seed_products.get('Clothing', {}).get('Nike', [])
        home_products = self.seed_products.get('Home', {}).get('IKEA', [])

        for customer in vip_customers[:3]:
            # VIP customers who bought Electronics also buy Clothing and Home
            if clothing_products:
                txns.append(create_txn(customer, clothing_products[0]))
            if home_products:
                txns.append(create_txn(customer, home_products[0]))

        # =================================================================
        # PATTERN 5: Cross-Category Gap Analysis (Cypher Q10, Q11, SQL Q13)
        # VIP/Premium customers WITHOUT Electronics purchases
        # =================================================================
        logger.debug("Creating category gap pattern...")
        # VIP customers 8-9 and Premium customers 8-9 only buy non-Electronics
        for segment in ['VIP', 'Premium']:
            segment_customers = self.seed_customers.get(segment, [])
            for customer in segment_customers[8:10]:  # Last 2 customers
                if clothing_products:
                    txns.append(create_txn(customer, random.choice(clothing_products)))
                if home_products:
                    txns.append(create_txn(customer, random.choice(home_products)))

        # =================================================================
        # PATTERN 6: Basket Purchases - Within 7 Days (SQL Q14)
        # Products bought by same customer within 7-day window
        # =================================================================
        logger.debug("Creating basket purchase pattern...")
        regular_customers = self.seed_customers.get('Regular', [])
        adidas_products = self.seed_products.get('Clothing', {}).get('Adidas', [])

        for customer in regular_customers[:5]:
            base_timestamp = datetime.now() - timedelta(days=random.randint(30, 60))

            # Buy 2-3 products within 7 days
            products_to_buy = random.sample(adidas_products, min(3, len(adidas_products)))
            for i, product in enumerate(products_to_buy):
                txn = create_txn(customer, product)
                txn['timestamp'] = base_timestamp + timedelta(days=i * 2)  # 0, 2, 4 days apart
                txns.append(txn)

        # =================================================================
        # PATTERN 7: 2-Hop Recommendation Chains (Cypher Q15)
        # C1->P1, C2->P1, C2->P2, C3->P2, C3->P3, C4->P3
        # =================================================================
        logger.debug("Creating 2-hop recommendation chains...")
        all_segments = ['VIP', 'Premium', 'Regular']

        for _ in range(5):  # Create 5 chains
            # Pick 4 customers from different segments
            chain_customers = []
            for seg in random.sample(all_segments, 3):
                seg_custs = self.seed_customers.get(seg, [])
                if seg_custs:
                    chain_customers.append(random.choice(seg_custs))
            if len(chain_customers) < 3:
                continue

            # Add one more customer
            extra_seg = random.choice(all_segments)
            extra_custs = self.seed_customers.get(extra_seg, [])
            if extra_custs:
                chain_customers.append(random.choice(extra_custs))

            if len(chain_customers) < 4:
                continue

            # Pick 3 products
            all_products = []
            for cat_products in self.seed_products.values():
                for brand_products in cat_products.values():
                    all_products.extend(brand_products)

            if len(all_products) < 3:
                continue

            chain_products = random.sample(all_products, 3)

            # Create chain pattern
            chain_pattern = [
                (0, 0), (1, 0),  # C0 and C1 both buy P0
                (1, 1), (2, 1),  # C1 and C2 both buy P1
                (2, 2), (3, 2),  # C2 and C3 both buy P2
            ]

            for cust_idx, prod_idx in chain_pattern:
                if cust_idx < len(chain_customers) and prod_idx < len(chain_products):
                    txns.append(create_txn(chain_customers[cust_idx], chain_products[prod_idx]))

        # =================================================================
        # PATTERN 8: Low Engagement High-Value (Cypher Q19)
        # VIP/Premium customers with < 3 purchases (churn risk)
        # =================================================================
        logger.debug("Creating low engagement pattern...")
        # VIP customers 5-7 get only 1-2 purchases
        for customer in vip_customers[5:8]:
            # Just 1-2 random purchases
            random_products = random.sample(apple_products + samsung_products, min(2, len(apple_products)))
            for product in random_products[:random.randint(1, 2)]:
                txns.append(create_txn(customer, product))

        # =================================================================
        # PATTERN 9: Cross-Category Diversity (Cypher Q20)
        # Customers buying from multiple categories
        # =================================================================
        logger.debug("Creating cross-category diversity pattern...")
        books_products = self.seed_products.get('Books', {}).get('Penguin', [])
        sports_products = self.seed_products.get('Sports', {}).get('Nike', [])
        beauty_products = self.seed_products.get('Beauty', {}).get('Loreal', [])

        for customer in premium_customers[5:8]:
            # Buy from 4+ different categories
            if apple_products:
                txns.append(create_txn(customer, random.choice(apple_products)))
            if clothing_products:
                txns.append(create_txn(customer, random.choice(clothing_products)))
            if books_products:
                txns.append(create_txn(customer, random.choice(books_products)))
            if sports_products:
                txns.append(create_txn(customer, random.choice(sports_products)))
            if beauty_products:
                txns.append(create_txn(customer, random.choice(beauty_products)))

        # =================================================================
        # PATTERN 10: Segment Purchase Distribution (Cypher Q1, Q7, Q12-14)
        # Ensure all segments have purchases for segment-based queries
        # =================================================================
        logger.debug("Creating segment distribution pattern...")
        for segment in ['Basic', 'New']:
            segment_customers = self.seed_customers.get(segment, [])
            wayfair_products = self.seed_products.get('Home', {}).get('Wayfair', [])

            for customer in segment_customers[:5]:
                # Basic/New customers buy affordable products
                if wayfair_products:
                    txns.append(create_txn(customer, random.choice(wayfair_products)))
                if adidas_products:
                    txns.append(create_txn(customer, random.choice(adidas_products)))

        logger.info(f"Generated {len(txns)} seed transactions")
        return txns

    def generate_seed_interactions(self) -> List[Dict]:
        """Generate seed interactions for all seed customers."""
        logger.info("Generating seed interactions...")

        interactions = []
        interaction_types = ['view', 'click', 'search', 'cart_add']
        devices = ['desktop', 'mobile', 'tablet']

        # Ensure each seed customer has interactions
        for segment_customers in self.seed_customers.values():
            for customer in segment_customers:
                # 5-10 interactions per seed customer
                num_interactions = random.randint(5, 10)
                for _ in range(num_interactions):
                    product_id = random.choice(self.seed_product_ids) if self.seed_product_ids else str(uuid.uuid4())

                    interaction = {
                        'interaction_id': str(uuid.uuid4()),
                        'customer_id': customer['customer_id'],
                        'product_id': product_id,
                        'type': random.choice(interaction_types),
                        'timestamp': self.fake.date_time_between(start_date='-6m', end_date='now'),
                        'duration': random.randint(10, 300),
                        'device': random.choice(devices),
                        'session_id': str(uuid.uuid4())
                    }
                    interactions.append(interaction)

        logger.info(f"Generated {len(interactions)} seed interactions")
        return interactions

    def generate_customers(self) -> pd.DataFrame:
        """Generate customer data"""
        logger.info(f"Generating {self.scale:,} customers...")
        
        customers = []
        segments = ['VIP', 'Premium', 'Regular', 'Basic', 'New']
        segment_weights = [0.10, 0.20, 0.30, 0.25, 0.15]

        # LTV ranges by segment
        ltv_ranges = {
            'VIP': (8000, 30000),
            'Premium': (5000, 12000),
            'Regular': (800, 3000),
            'Basic': (200, 1000),
            'New': (50, 400)
        }
        
        for i in tqdm(range(self.scale), desc="Customers"):
            segment = random.choices(segments, weights=segment_weights)[0]
            min_ltv, max_ltv = ltv_ranges[segment]

            customer_id = str(uuid.uuid4())

            # Assign brand affinity and category exclusions
            brand_affinity = self._assign_brand_affinity(segment)
            category_exclusions = self._should_exclude_category(segment)

            self.customer_brand_affinity[customer_id] = brand_affinity
            self.customer_category_exclusions[customer_id] = category_exclusions

            # Use monthly cohort for registration
            registration_date = self._generate_monthly_cohort_date(i)

            customer = {
                'customer_id': customer_id,
                'email': self.fake.email(),
                'name': self.fake.name(),
                'segment': segment,
                'ltv': round(random.uniform(min_ltv, max_ltv), 2),
                'registration_date': registration_date,
                'created_at': datetime.utcnow()
            }
            customers.append(customer)
        
        df = pd.DataFrame(customers)
        logger.info(f"Generated {len(df):,} customers")
        return df
    
    def generate_products(self) -> pd.DataFrame:
        """Generate product catalog"""
        logger.info(f"Generating {self.product_count:,} products...")
        
        categories = {
            'Electronics': (50, 2000),
            'Clothing': (20, 500),
            'Home': (25, 800),
            'Books': (10, 100),
            'Sports': (30, 600),
            'Beauty': (15, 200)
        }
        
        brands = {
            'Electronics': ['Apple', 'Samsung', 'Sony', 'Dell', 'HP'],
            'Clothing': ['Nike', 'Adidas', 'Zara', 'Gap', 'Levi'],
            'Home': ['IKEA', 'Wayfair', 'Target', 'HomeDepot'],
            'Books': ['Penguin', 'Harper', 'Simon', 'Random'],
            'Sports': ['Nike', 'Adidas', 'Wilson', 'Spalding'],
            'Beauty': ['Loreal', 'Maybelline', 'MAC', 'Sephora']
        }
        
        products = []
        
        for i in tqdm(range(self.product_count), desc="Products"):
            category = random.choice(list(categories.keys()))
            brand = random.choice(brands[category])
            min_price, max_price = categories[category]
            
            product = {
                'product_id': str(uuid.uuid4()),
                'name': f"{brand} {category} Product {i+1}",
                'category': category,
                'brand': brand,
                'price': round(random.uniform(min_price, max_price), 2),
                'launch_date': self.fake.date_between(start_date='-3y', end_date='today'),
                'created_at': datetime.utcnow()
            }
            products.append(product)
        
        df = pd.DataFrame(products)

        # Build product indexes for efficient lookup
        for product in products:
            category = product['category']
            brand = product['brand']

            if category not in self.products_by_category:
                self.products_by_category[category] = []
            self.products_by_category[category].append(product)

            if brand not in self.products_by_brand:
                self.products_by_brand[brand] = []
            self.products_by_brand[brand].append(product)

        logger.info(f"Generated {len(df):,} products")
        logger.info(f"  - Categories: {len(self.products_by_category)}")
        logger.info(f"  - Brands: {len(self.products_by_brand)}")
        return df
    
    def generate_transactions(self, customers: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
        """Generate transaction data with intentional patterns"""
        total_transactions = self.scale * self.avg_transactions_per_customer
        logger.info(f"Generating ~{total_transactions:,} transactions with pattern-based logic...")

        transactions = []
        product_data = products[['product_id', 'price', 'category', 'brand', 'name']].to_dict('records')

        # Enhanced segment patterns
        segment_patterns = {
            'VIP': {'freq': 25, 'amount_multiplier': 3.0},
            'Premium': {'freq': 15, 'amount_multiplier': 2.2},
            'Regular': {'freq': 8, 'amount_multiplier': 1.2},
            'Basic': {'freq': 4, 'amount_multiplier': 0.8},
            'New': {'freq': 2, 'amount_multiplier': 0.6}
        }

        # Track pending basket items
        basket_transactions = []

        for _, customer in tqdm(customers.iterrows(), total=len(customers), desc="Transactions"):
            customer_id = customer['customer_id']
            segment = customer['segment']
            pattern = segment_patterns[segment]

            # Phase 1: Low-engagement pattern (10% of VIP/Premium with <3 purchases)
            if segment in ['VIP', 'Premium'] and random.random() < 0.10:
                num_transactions = random.randint(1, 2)
            else:
                num_transactions = np.random.poisson(pattern['freq'])

            # Track purchases for this customer
            self.customer_purchase_count[customer_id] = num_transactions

            # Get customer patterns
            brand_affinity = self.customer_brand_affinity.get(customer_id)
            category_exclusions = self.customer_category_exclusions.get(customer_id, [])

            customer_transactions = []

            for txn_index in range(num_transactions):
                # Phase 2 & 3: Select product based on brand affinity and category exclusions
                product = None

                # 60% chance to buy from preferred brand if they have one
                if brand_affinity and random.random() < 0.60:
                    if brand_affinity in self.products_by_brand:
                        available_products = [p for p in self.products_by_brand[brand_affinity]
                                            if p['category'] not in category_exclusions]
                        if available_products:
                            product = random.choice(available_products)

                # If no product selected yet, choose random (respecting exclusions)
                if not product:
                    available_products = [p for p in product_data
                                        if p['category'] not in category_exclusions]
                    if available_products:
                        product = random.choice(available_products)
                    else:
                        # If all categories excluded (shouldn't happen), pick any
                        product = random.choice(product_data)

                # Phase 4: Use temporal clustering for timestamp
                timestamp = self._generate_transaction_timestamp()

                # Calculate amount
                base_price = product['price']
                multiplier = pattern['amount_multiplier'] * random.uniform(0.7, 1.3)
                amount = round(base_price * multiplier, 2)

                transaction = {
                    'transaction_id': str(uuid.uuid4()),
                    'customer_id': customer_id,
                    'product_id': product['product_id'],
                    'amount': amount,
                    'quantity': random.randint(1, 3),
                    'timestamp': timestamp,
                    'channel': random.choice(['web', 'mobile_app', 'store']),
                    'status': random.choices(['completed', 'cancelled'], weights=[0.9, 0.1])[0]
                }
                customer_transactions.append(transaction)
                transactions.append(transaction)

                # Phase 5: Generate basket purchases (30% chance)
                basket_items = self._get_product_basket(product['name'])
                if basket_items and random.random() < 0.30:
                    for basket_item_keyword in basket_items:
                        # Find product matching basket item
                        matching_products = [p for p in product_data if basket_item_keyword in p['name']]
                        if matching_products:
                            basket_product = random.choice(matching_products)
                            basket_timestamp = timestamp + timedelta(days=random.randint(0, 7))

                            basket_txn = {
                                'transaction_id': str(uuid.uuid4()),
                                'customer_id': customer_id,
                                'product_id': basket_product['product_id'],
                                'amount': round(basket_product['price'] * pattern['amount_multiplier'], 2),
                                'quantity': 1,
                                'timestamp': basket_timestamp,
                                'channel': random.choice(['web', 'mobile_app', 'store']),
                                'status': 'completed'
                            }
                            basket_transactions.append(basket_txn)

            # Phase 3: Cross-category purchases (40% chance per transaction)
            for txn in customer_transactions:
                if random.random() < 0.40:
                    # Get the category of the current product
                    current_product = next((p for p in product_data if p['product_id'] == txn['product_id']), None)
                    if current_product:
                        affinity_categories = self._get_category_affinity_categories(current_product['category'])
                        if affinity_categories:
                            affinity_category = random.choice(affinity_categories)
                            if affinity_category not in category_exclusions and affinity_category in self.products_by_category:
                                cross_product = random.choice(self.products_by_category[affinity_category])

                                cross_txn = {
                                    'transaction_id': str(uuid.uuid4()),
                                    'customer_id': customer_id,
                                    'product_id': cross_product['product_id'],
                                    'amount': round(cross_product['price'] * pattern['amount_multiplier'], 2),
                                    'quantity': 1,
                                    'timestamp': txn['timestamp'] + timedelta(minutes=random.randint(5, 120)),
                                    'channel': txn['channel'],
                                    'status': 'completed'
                                }
                                transactions.append(cross_txn)

        # Add basket transactions
        transactions.extend(basket_transactions)

        df = pd.DataFrame(transactions)
        logger.info(f"Generated {len(df):,} transactions")
        logger.info(f"  - Primary transactions: {len(df) - len(basket_transactions):,}")
        logger.info(f"  - Basket transactions: {len(basket_transactions):,}")
        return df
    
    def generate_interactions(self, customers: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
        """Generate customer interaction data"""
        total_interactions = self.scale * 25  # Average 25 interactions per customer
        logger.info(f"Generating ~{total_interactions:,} interactions...")
        
        interactions = []
        customer_ids = customers['customer_id'].tolist()
        product_ids = products['product_id'].tolist()
        
        interaction_types = ['view', 'click', 'search', 'cart_add']
        devices = ['desktop', 'mobile', 'tablet']
        
        for customer_id in tqdm(random.choices(customer_ids, k=total_interactions), desc="Interactions"):
            interaction = {
                'interaction_id': str(uuid.uuid4()),
                'customer_id': customer_id,
                'product_id': random.choice(product_ids),
                'type': random.choice(interaction_types),
                'timestamp': self.fake.date_time_between(start_date='-6m', end_date='now'),
                'duration': random.randint(10, 300),  # seconds
                'device': random.choice(devices),
                'session_id': str(uuid.uuid4())
            }
            interactions.append(interaction)
        
        df = pd.DataFrame(interactions)
        logger.info(f"Generated {len(df):,} interactions")
        return df

    def create_recommendation_chains(self, customers: pd.DataFrame, products: pd.DataFrame,
                                    transactions: pd.DataFrame, num_chains: int = 20) -> pd.DataFrame:
        """Phase 6: Create multi-hop recommendation paths for collaborative filtering"""
        logger.info(f"Creating {num_chains} recommendation chains for multi-hop paths...")

        new_transactions = []
        product_data = products[['product_id', 'price', 'category', 'brand', 'name']].to_dict('records')

        # Group customers by segment for clustering
        customers_by_segment = {}
        for _, customer in customers.iterrows():
            segment = customer['segment']
            if segment not in customers_by_segment:
                customers_by_segment[segment] = []
            customers_by_segment[segment].append(customer)

        # Create chains for VIP, Premium, Regular segments
        for segment in ['VIP', 'Premium', 'Regular']:
            segment_customers = customers_by_segment.get(segment, [])
            if len(segment_customers) < 4:
                continue

            segment_chains = min(num_chains // 3, len(segment_customers) // 4)

            for _ in range(segment_chains):
                # Select 4 customers for the chain
                chain_customers = random.sample(segment_customers, k=4)

                # Select 3 products from same category (preferably Electronics)
                if 'Electronics' in self.products_by_category and len(self.products_by_category['Electronics']) >= 3:
                    chain_products = random.sample(self.products_by_category['Electronics'], k=3)
                else:
                    # Fallback to any category with enough products
                    available_category = next((cat for cat, prods in self.products_by_category.items()
                                             if len(prods) >= 3), None)
                    if not available_category:
                        continue
                    chain_products = random.sample(self.products_by_category[available_category], k=3)

                # Create chain: C1->P1, C2->P1, C2->P2, C3->P2, C3->P3, C4->P3
                chain_pattern = [
                    (0, 0),  # Customer 0 buys Product 0
                    (1, 0),  # Customer 1 buys Product 0
                    (1, 1),  # Customer 1 buys Product 1
                    (2, 1),  # Customer 2 buys Product 1
                    (2, 2),  # Customer 2 buys Product 2
                    (3, 2),  # Customer 3 buys Product 2
                ]

                timestamp_base = self._generate_transaction_timestamp()

                for cust_idx, prod_idx in chain_pattern:
                    customer = chain_customers[cust_idx]
                    product = chain_products[prod_idx]

                    # Check if this purchase already exists
                    existing = transactions[
                        (transactions['customer_id'] == customer['customer_id']) &
                        (transactions['product_id'] == product['product_id'])
                    ]

                    if len(existing) == 0:
                        # Create new transaction
                        txn = {
                            'transaction_id': str(uuid.uuid4()),
                            'customer_id': customer['customer_id'],
                            'product_id': product['product_id'],
                            'amount': round(product['price'] * 1.5, 2),
                            'quantity': 1,
                            'timestamp': timestamp_base + timedelta(days=random.randint(0, 30)),
                            'channel': random.choice(['web', 'mobile_app', 'store']),
                            'status': 'completed'
                        }
                        new_transactions.append(txn)

        if new_transactions:
            new_df = pd.DataFrame(new_transactions)
            logger.info(f"Created {len(new_df):,} recommendation chain transactions")
            return pd.concat([transactions, new_df], ignore_index=True)
        else:
            logger.info("No new recommendation chain transactions created")
            return transactions

    def save_data_in_batches(self, data: Dict[str, pd.DataFrame], output_dir: str = None):
        """Save data in batch files for efficient loading"""
        output_dir = output_dir or self.output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        for table_name, df in data.items():
            logger.info(f"Saving {table_name} data in batches...")
            
            # Create table-specific directory
            table_dir = os.path.join(output_dir, table_name)
            os.makedirs(table_dir, exist_ok=True)
            
            # Check if data already exists and handle accordingly
            existing_files = len([f for f in os.listdir(table_dir) if f.endswith('.parquet')])
            if existing_files > 0:
                if self.overwrite_existing:
                    logger.warning(f"Overwriting existing {existing_files} batch files for {table_name}")
                    import shutil
                    shutil.rmtree(table_dir)
                    os.makedirs(table_dir, exist_ok=True)
                else:
                    logger.warning(f"Skipping {table_name} - {existing_files} batch files already exist")
                    continue
            
            # Calculate number of batches
            total_rows = len(df)
            num_batches = math.ceil(total_rows / self.batch_file_size)
            
            logger.info(f"Splitting {total_rows:,} records into {num_batches} batches of ~{self.batch_file_size:,} each")
            
            # Save in batches with progress bar
            show_progress = os.getenv('SHOW_PROGRESS_BARS', 'true').lower() == 'true'
            batch_range = tqdm(range(num_batches), desc=f"Saving {table_name}") if show_progress else range(num_batches)
            
            for batch_num in batch_range:
                start_idx = batch_num * self.batch_file_size
                end_idx = min((batch_num + 1) * self.batch_file_size, total_rows)
                batch_df = df.iloc[start_idx:end_idx]
                
                # Generate batch filename
                batch_filename = f"{table_name}_batch_{batch_num:04d}.parquet"
                batch_path = os.path.join(table_dir, batch_filename)
                
                # Save batch with compression
                batch_df.to_parquet(
                    batch_path, 
                    index=False, 
                    compression=self.compression
                )
                
                logger.debug(f"Saved {batch_filename}: {len(batch_df):,} records")
            
            logger.info(f" {table_name}: {total_rows:,} records saved in {num_batches} batch files")
    
    def save_data(self, data: Dict[str, pd.DataFrame], output_dir: str = None):
        """Save generated data - choose between single files or batches based on size"""
        output_dir = output_dir or self.output_dir
        
        # For large datasets, use batch files; for small ones, use single files
        total_records = sum(len(df) for df in data.values())
        
        if total_records > self.batch_file_size * 2:  # Use batching for larger datasets
            logger.info(f"Large dataset detected ({total_records:,} total records), using batch files")
            self.save_data_in_batches(data, output_dir)
        else:
            logger.info(f"Small dataset ({total_records:,} total records), using single files")
            os.makedirs(output_dir, exist_ok=True)
            
            for table_name, df in data.items():
                file_path = os.path.join(output_dir, f"{table_name}.parquet")
                
                # Check if file exists
                if os.path.exists(file_path) and not self.overwrite_existing:
                    logger.warning(f"Skipping {table_name} - file already exists: {file_path}")
                    continue
                
                df.to_parquet(file_path, index=False, compression=self.compression)
                logger.info(f"Saved {table_name}: {len(df):,} records → {file_path}")
    
    def generate_all(self, output_dir: str = "data", include_seeds: bool = True) -> Dict[str, pd.DataFrame]:
        """Generate all data and save to files

        Args:
            output_dir: Directory to save generated data
            include_seeds: If True, generate seed data first for guaranteed query results
        """
        logger.info("Starting Customer 360 data generation with pattern-based logic...")
        start_time = datetime.utcnow()

        # Generate seed data first if requested
        seed_customers = []
        seed_products = []
        seed_transactions = []
        seed_interactions = []

        if include_seeds:
            logger.info("=== Generating Seed Data for Guaranteed Query Results ===")
            seed_customers = self.generate_seed_customers()
            seed_products = self.generate_seed_products()
            seed_transactions = self.generate_seed_transactions()
            seed_interactions = self.generate_seed_interactions()

        # Generate core entities
        customers = self.generate_customers()
        products = self.generate_products()
        transactions = self.generate_transactions(customers, products)

        # Phase 6: Create recommendation chains for multi-hop paths
        transactions = self.create_recommendation_chains(customers, products, transactions)

        # Generate interactions
        interactions = self.generate_interactions(customers, products)

        # Merge seed data with generated data
        if include_seeds:
            logger.info("=== Merging Seed Data with Generated Data ===")

            # Merge customers
            seed_customers_df = pd.DataFrame(seed_customers)
            customers = pd.concat([seed_customers_df, customers], ignore_index=True)

            # Merge products
            seed_products_df = pd.DataFrame(seed_products)
            products = pd.concat([seed_products_df, products], ignore_index=True)

            # Merge transactions
            seed_transactions_df = pd.DataFrame(seed_transactions)
            transactions = pd.concat([seed_transactions_df, transactions], ignore_index=True)

            # Merge interactions
            seed_interactions_df = pd.DataFrame(seed_interactions)
            interactions = pd.concat([seed_interactions_df, interactions], ignore_index=True)

            logger.info(f"Merged seed data:")
            logger.info(f"  - Seed customers: {len(seed_customers_df)}")
            logger.info(f"  - Seed products: {len(seed_products_df)}")
            logger.info(f"  - Seed transactions: {len(seed_transactions_df)}")
            logger.info(f"  - Seed interactions: {len(seed_interactions_df)}")

        # Package data
        data = {
            'customers': customers,
            'products': products,
            'transactions': transactions,
            'interactions': interactions
        }

        # Save data
        self.save_data(data, output_dir)

        # Summary
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        total_records = sum(len(df) for df in data.values())
        logger.info(f"Generation completed in {duration:.1f}s")
        logger.info(f"Total records: {total_records:,}")
        logger.info(f"Output directory: {output_dir}/")
        logger.info(f"")
        logger.info(f"Pattern Summary:")
        logger.info(f"  - Customers with brand affinity: {sum(1 for v in self.customer_brand_affinity.values() if v):,}")
        logger.info(f"  - Customers with category exclusions: {sum(1 for v in self.customer_category_exclusions.values() if v):,}")
        logger.info(f"  - Low-engagement customers: {sum(1 for v in self.customer_purchase_count.values() if v < 3):,}")

        return data


def main():
    """Main function - can be run as script"""
    import argparse
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate Customer 360 demo data')
    parser.add_argument('--scale', type=int,
                       choices=[1_000_000, 10_000_000, 100_000_000],
                       default=int(os.getenv('CUSTOMER_SCALE', 1_000_000)),
                       help='Number of customers to generate')
    parser.add_argument('--output', type=str, default='data',
                       help='Output directory for generated files')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducible data')
    parser.add_argument('--include-seeds', action='store_true', default=True,
                       help='Include seed data for guaranteed query results (default: True)')
    parser.add_argument('--no-seeds', action='store_true',
                       help='Disable seed data generation')

    args = parser.parse_args()

    # Determine whether to include seeds
    include_seeds = args.include_seeds and not args.no_seeds

    # Generate data
    generator = Customer360Generator(scale=args.scale, seed=args.seed)
    data = generator.generate_all(output_dir=args.output, include_seeds=include_seeds)

    print(f"\nData generation completed!")
    print(f"Files saved in: {args.output}/")
    print(f"Generated:")
    for table, df in data.items():
        print(f"   - {table}: {len(df):,} records")

    if include_seeds:
        print(f"\nSeed data included for guaranteed query results")

    print(f"\nNext steps:")
    print(f"   1. Load data: python clickhouse.py --load")
    print(f"   2. Start dashboard: streamlit run app.py")


if __name__ == "__main__":
    main()