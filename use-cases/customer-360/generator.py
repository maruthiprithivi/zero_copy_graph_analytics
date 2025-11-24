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
    
    def generate_customers(self) -> pd.DataFrame:
        """Generate customer data"""
        logger.info(f"Generating {self.scale:,} customers...")
        
        customers = []
        segments = ['VIP', 'Premium', 'Regular', 'Basic', 'New']
        segment_weights = [0.05, 0.15, 0.30, 0.30, 0.20]
        
        # LTV ranges by segment
        ltv_ranges = {
            'VIP': (5000, 25000),
            'Premium': (2000, 8000),
            'Regular': (500, 2500),
            'Basic': (100, 800),
            'New': (50, 300)
        }
        
        for i in tqdm(range(self.scale), desc="Customers"):
            segment = random.choices(segments, weights=segment_weights)[0]
            min_ltv, max_ltv = ltv_ranges[segment]
            
            customer = {
                'customer_id': str(uuid.uuid4()),
                'email': self.fake.email(),
                'name': self.fake.name(),
                'segment': segment,
                'ltv': round(random.uniform(min_ltv, max_ltv), 2),
                'registration_date': self.fake.date_between(start_date='-2y', end_date='today'),
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
        logger.info(f"Generated {len(df):,} products")
        return df
    
    def generate_transactions(self, customers: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
        """Generate transaction data"""
        total_transactions = self.scale * self.avg_transactions_per_customer
        logger.info(f"Generating ~{total_transactions:,} transactions...")
        
        transactions = []
        customer_ids = customers['customer_id'].tolist()
        product_data = products[['product_id', 'price', 'category']].to_dict('records')
        
        # Transaction patterns by segment
        segment_patterns = {
            'VIP': {'freq': 20, 'amount_multiplier': 2.5},
            'Premium': {'freq': 12, 'amount_multiplier': 1.8},
            'Regular': {'freq': 8, 'amount_multiplier': 1.2},
            'Basic': {'freq': 5, 'amount_multiplier': 0.8},
            'New': {'freq': 3, 'amount_multiplier': 0.6}
        }
        
        for _, customer in tqdm(customers.iterrows(), total=len(customers), desc="Transactions"):
            segment = customer['segment']
            pattern = segment_patterns[segment]
            
            # Number of transactions for this customer
            num_transactions = np.random.poisson(pattern['freq'])
            
            for _ in range(num_transactions):
                product = random.choice(product_data)
                base_price = product['price']
                
                # Apply segment multiplier and some randomness
                multiplier = pattern['amount_multiplier'] * random.uniform(0.7, 1.3)
                amount = round(base_price * multiplier, 2)
                
                transaction = {
                    'transaction_id': str(uuid.uuid4()),
                    'customer_id': customer['customer_id'],
                    'product_id': product['product_id'],
                    'amount': amount,
                    'quantity': random.randint(1, 3),
                    'timestamp': self.fake.date_time_between(start_date='-1y', end_date='now'),
                    'channel': random.choice(['web', 'mobile_app', 'store']),
                    'status': random.choices(['completed', 'cancelled'], weights=[0.9, 0.1])[0]
                }
                transactions.append(transaction)
        
        df = pd.DataFrame(transactions)
        logger.info(f"Generated {len(df):,} transactions")
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
    
    def generate_all(self, output_dir: str = "data") -> Dict[str, pd.DataFrame]:
        """Generate all data and save to files"""
        logger.info("Starting Customer 360 data generation...")
        start_time = datetime.utcnow()
        
        # Generate core entities
        customers = self.generate_customers()
        products = self.generate_products()
        transactions = self.generate_transactions(customers, products)
        interactions = self.generate_interactions(customers, products)
        
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
    
    args = parser.parse_args()
    
    # Generate data
    generator = Customer360Generator(scale=args.scale, seed=args.seed)
    data = generator.generate_all(output_dir=args.output)
    
    print(f"\n Data generation completed!")
    print(f" Files saved in: {args.output}/")
    print(f" Generated:")
    for table, df in data.items():
        print(f"   • {table}: {len(df):,} records")
    
    print(f"\n Next steps:")
    print(f"   1. Load data: python clickhouse.py --load")
    print(f"   2. Start dashboard: streamlit run app.py")


if __name__ == "__main__":
    main()