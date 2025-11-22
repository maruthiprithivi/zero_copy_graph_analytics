#!/usr/bin/env python3
"""
Enhanced Customer 360 Data Generator - 5 Persona Connected Stories at Scale
Generates 10M customers with 5 main personas, 1B transactions, and interconnected relationships
"""

import os
import sys
import uuid
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from faker import Faker
from tqdm import tqdm
import logging
from pathlib import Path

# Add app directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from personas import MAIN_PERSONAS, PURCHASE_PATTERNS, RELATIONSHIP_TYPES, generate_persona_network

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PersonaDataGenerator:
    """Generate massive scale data centered around 5 personas"""

    def __init__(self, scale_config: Dict = None):
        # Default massive scale configuration
        self.config = scale_config or {
            'customers': 10_000_000,        # 10M customers
            'products': 100_000,            # 100K products
            'transactions': 1_000_000_000,  # 1B transactions
            'interactions': 2_500_000_000,  # 2.5B interactions
            'relationships': 50_000_000,    # 50M customer connections
            'support_tickets': 10_000_000,  # 10M support cases
            'master_seed': 42,              # Master seed for reproducibility
            'batch_size': 100_000,          # Batch processing size
            'output_dir': 'data'
        }

        # Initialize seeds for different data types
        self.seeds = {
            'customers': self.config['master_seed'],
            'products': self.config['master_seed'] + 100,
            'transactions': self.config['master_seed'] + 200,
            'interactions': self.config['master_seed'] + 300,
            'relationships': self.config['master_seed'] + 400,
            'support': self.config['master_seed'] + 500
        }

        # Setup Faker instances with different seeds
        self.fakers = {}
        for category, seed in self.seeds.items():
            faker = Faker()
            Faker.seed(seed)
            self.fakers[category] = faker

        # Create output directory
        Path(self.config['output_dir']).mkdir(exist_ok=True)

        logger.info(f"PersonaDataGenerator initialized for scale: {self.config['customers']:,} customers")

    def generate_products(self) -> pd.DataFrame:
        """Generate product catalog optimized for persona preferences"""
        logger.info(f"Generating {self.config['products']:,} products...")

        # Set seed for products
        random.seed(self.seeds['products'])
        np.random.seed(self.seeds['products'])
        faker = self.fakers['products']

        # Extended categories matching persona preferences
        categories = {
            'electronics': {'weight': 0.20, 'price_range': (50, 2000), 'personas': ['sarah_001']},
            'smart_home': {'weight': 0.15, 'price_range': (100, 1500), 'personas': ['sarah_001']},
            'books': {'weight': 0.10, 'price_range': (10, 100), 'personas': ['marcus_002', 'dorothy_005']},
            'clothing': {'weight': 0.15, 'price_range': (20, 300), 'personas': ['marcus_002']},
            'home_goods': {'weight': 0.12, 'price_range': (25, 500), 'personas': ['elena_003', 'dorothy_005']},
            'kids': {'weight': 0.08, 'price_range': (15, 200), 'personas': ['elena_003']},
            'food_service': {'weight': 0.05, 'price_range': (200, 2000), 'personas': ['robert_004']},
            'health': {'weight': 0.10, 'price_range': (20, 400), 'personas': ['elena_003', 'dorothy_005']},
            'fitness': {'weight': 0.05, 'price_range': (30, 800), 'personas': ['sarah_001']}
        }

        products = []
        for i in tqdm(range(self.config['products']), desc="Products"):
            # Select category based on weights
            category = np.random.choice(
                list(categories.keys()),
                p=[cat['weight'] for cat in categories.values()]
            )

            cat_info = categories[category]
            price = round(random.uniform(*cat_info['price_range']), 2)

            # Create realistic product names
            product_name = faker.catch_phrase()
            brand = faker.company()

            product = {
                'product_id': str(uuid.uuid4()),
                'name': f"{brand} {product_name}",
                'category': category,
                'brand': brand,
                'price': price,
                'target_personas': ','.join(cat_info.get('personas', [])),
                'launch_date': faker.date_between(start_date='-3y', end_date='today'),
                'in_stock': random.choice([True] * 9 + [False]),  # 90% in stock
                'rating': round(random.uniform(3.0, 5.0), 1),
                'created_at': datetime.utcnow()
            }
            products.append(product)

        df = pd.DataFrame(products)
        logger.info(f"Generated {len(df):,} products across {len(categories)} categories")
        return df

    def generate_main_personas(self) -> pd.DataFrame:
        """Generate the 5 main personas with their networks"""
        logger.info("Generating main personas with networks...")

        random.seed(self.seeds['customers'])
        faker = self.fakers['customers']

        all_customers = []

        # Generate main personas first
        for persona_id, persona in MAIN_PERSONAS.items():
            customer = {
                'customer_id': persona_id,
                'email': persona.email,
                'name': persona.name,
                'age': persona.age,
                'persona_type': persona.persona_type,
                'segment': persona.segment,
                'location': persona.location,
                'price_sensitivity': persona.price_sensitivity,
                'convenience_priority': persona.convenience_priority,
                'social_influence': persona.social_influence,
                'quality_focus': persona.quality_focus,
                'tech_savvy': persona.tech_savvy,
                'ltv_tier': persona.ltv_tier,
                'preferred_channels': ','.join(persona.preferred_channels),
                'purchase_frequency': persona.purchase_frequency,
                'is_main_persona': True,
                'registration_date': faker.date_between(start_date='-2y', end_date='-6m'),
                'last_login': faker.date_between(start_date='-7d', end_date='today'),
                'created_at': datetime.utcnow()
            }
            all_customers.append(customer)

            # Generate network for each main persona
            network_ids = generate_persona_network(persona_id)
            for network_id in network_ids:
                # Create similar customers with variations
                network_customer = self._create_similar_customer(persona, network_id, faker)
                all_customers.append(network_customer)

        # Generate remaining customers to reach target scale
        remaining = self.config['customers'] - len(all_customers)
        logger.info(f"Generating {remaining:,} additional customers...")

        segments = ['premium', 'standard', 'value', 'new']
        segment_weights = [0.15, 0.35, 0.35, 0.15]

        for i in tqdm(range(remaining), desc="Additional customers"):
            segment = np.random.choice(segments, p=segment_weights)

            customer = {
                'customer_id': str(uuid.uuid4()),
                'email': faker.email(),
                'name': faker.name(),
                'age': random.randint(18, 75),
                'persona_type': 'general',
                'segment': segment,
                'location': f"{faker.city()}, {faker.state_abbr()}",
                'price_sensitivity': random.randint(30, 90),
                'convenience_priority': random.randint(20, 80),
                'social_influence': random.randint(10, 60),
                'quality_focus': random.randint(40, 90),
                'tech_savvy': random.randint(30, 80),
                'ltv_tier': segment,
                'preferred_channels': ','.join(random.choices(['website', 'mobile_app', 'email', 'phone'], k=2)),
                'purchase_frequency': random.choice(['weekly', 'monthly', 'quarterly']),
                'is_main_persona': False,
                'registration_date': faker.date_between(start_date='-2y', end_date='today'),
                'last_login': faker.date_between(start_date='-30d', end_date='today'),
                'created_at': datetime.utcnow()
            }
            all_customers.append(customer)

        df = pd.DataFrame(all_customers)
        logger.info(f"Generated {len(df):,} total customers")
        return df

    def _create_similar_customer(self, base_persona, customer_id: str, faker) -> Dict:
        """Create a customer similar to base persona with variations"""
        # Add some variation to base attributes
        variation = 15  # +/- 15% variation

        return {
            'customer_id': customer_id,
            'email': faker.email(),
            'name': faker.name(),
            'age': max(18, min(75, base_persona.age + random.randint(-5, 5))),
            'persona_type': f"{base_persona.persona_type}_network",
            'segment': base_persona.segment,
            'location': f"{faker.city()}, {faker.state_abbr()}",
            'price_sensitivity': max(0, min(100, base_persona.price_sensitivity + random.randint(-variation, variation))),
            'convenience_priority': max(0, min(100, base_persona.convenience_priority + random.randint(-variation, variation))),
            'social_influence': max(0, min(100, base_persona.social_influence + random.randint(-variation, variation))),
            'quality_focus': max(0, min(100, base_persona.quality_focus + random.randint(-variation, variation))),
            'tech_savvy': max(0, min(100, base_persona.tech_savvy + random.randint(-variation, variation))),
            'ltv_tier': base_persona.ltv_tier,
            'preferred_channels': ','.join(base_persona.preferred_channels),
            'purchase_frequency': base_persona.purchase_frequency,
            'is_main_persona': False,
            'registration_date': faker.date_between(start_date='-2y', end_date='today'),
            'last_login': faker.date_between(start_date='-30d', end_date='today'),
            'created_at': datetime.utcnow()
        }

    def generate_relationships(self, customers: pd.DataFrame) -> pd.DataFrame:
        """Generate customer relationships focusing on persona connections"""
        logger.info(f"Generating {self.config['relationships']:,} customer relationships...")

        random.seed(self.seeds['relationships'])

        relationships = []

        # First, create main persona relationships
        for (persona1, persona2), rel_type in RELATIONSHIP_TYPES.items():
            relationship = {
                'relationship_id': str(uuid.uuid4()),
                'customer_id_1': persona1,
                'customer_id_2': persona2,
                'relationship_type': rel_type,
                'strength': random.uniform(0.7, 1.0),  # Strong relationships for main personas
                'created_date': datetime.utcnow() - timedelta(days=random.randint(30, 365)),
                'is_main_connection': True
            }
            relationships.append(relationship)

        # Generate network relationships
        customer_ids = customers['customer_id'].tolist()
        main_persona_ids = list(MAIN_PERSONAS.keys())

        remaining = self.config['relationships'] - len(relationships)

        for _ in tqdm(range(remaining), desc="Relationships"):
            customer_1 = random.choice(customer_ids)
            customer_2 = random.choice(customer_ids)

            if customer_1 != customer_2:
                # Determine relationship type based on personas
                rel_types = ['SIMILAR_TO', 'FRIEND_OF', 'INFLUENCED_BY', 'REFERRED_BY']
                if customer_1 in main_persona_ids or customer_2 in main_persona_ids:
                    rel_types = ['INFLUENCED_BY', 'REFERRED_BY'] + rel_types

                relationship = {
                    'relationship_id': str(uuid.uuid4()),
                    'customer_id_1': customer_1,
                    'customer_id_2': customer_2,
                    'relationship_type': random.choice(rel_types),
                    'strength': random.uniform(0.1, 0.9),
                    'created_date': datetime.utcnow() - timedelta(days=random.randint(1, 730)),
                    'is_main_connection': False
                }
                relationships.append(relationship)

        df = pd.DataFrame(relationships)
        logger.info(f"Generated {len(df):,} relationships")
        return df

    def generate_transactions_at_scale(self, customers: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
        """Generate 1B transactions with persona-specific patterns"""
        logger.info(f"Generating {self.config['transactions']:,} transactions...")

        random.seed(self.seeds['transactions'])
        faker = self.fakers['transactions']

        # Pre-compute customer data for efficiency
        customer_data = customers.set_index('customer_id')[
            ['persona_type', 'segment', 'purchase_frequency', 'is_main_persona']
        ].to_dict('index')

        product_data = products[['product_id', 'price', 'category', 'target_personas']].to_dict('records')

        # Transaction distribution by persona type
        transaction_weights = {
            'tech_influencer': 50,      # Sarah generates many transactions
            'budget_student': 20,       # Marcus fewer but regular
            'busy_parent': 80,         # Elena frequent convenience purchases
            'business_owner': 200,     # Robert high-value bulk orders
            'digital_senior': 30,      # Dorothy careful, quality purchases
            'general': 10              # Regular customers
        }

        transactions = []
        batch_size = self.config['batch_size']

        # Calculate transactions per customer type
        total_weight = sum(
            transaction_weights.get(data['persona_type'].split('_')[0],
                                   transaction_weights.get(data['persona_type'],
                                                          transaction_weights['general']))
            for data in customer_data.values()
        )

        transactions_generated = 0
        target = self.config['transactions']

        for customer_id, data in tqdm(customer_data.items(), desc="Customer transactions"):
            persona_base = data['persona_type'].split('_')[0]
            weight = transaction_weights.get(persona_base, transaction_weights['general'])

            # Scale transactions for main personas
            if data['is_main_persona']:
                weight *= 3

            # Calculate number of transactions for this customer
            customer_transactions = int((weight / total_weight) * target)

            for _ in range(customer_transactions):
                if transactions_generated >= target:
                    break

                # Select product based on persona preferences
                product = self._select_product_for_persona(persona_base, product_data)

                # Generate realistic transaction
                transaction = self._create_transaction(
                    customer_id, product, data, faker
                )
                transactions.append(transaction)
                transactions_generated += 1

                # Batch processing for memory efficiency
                if len(transactions) >= batch_size:
                    yield pd.DataFrame(transactions)
                    transactions = []

            if transactions_generated >= target:
                break

        # Yield remaining transactions
        if transactions:
            yield pd.DataFrame(transactions)

        logger.info(f"Generated {transactions_generated:,} transactions")

    def _select_product_for_persona(self, persona_type: str, products: List[Dict]) -> Dict:
        """Select product based on persona preferences"""
        if persona_type in PURCHASE_PATTERNS:
            preferred_categories = PURCHASE_PATTERNS[persona_type]['categories']
            # Filter products by preferred categories
            matching_products = [
                p for p in products
                if p['category'] in preferred_categories
            ]
            if matching_products:
                return random.choice(matching_products)

        return random.choice(products)

    def _create_transaction(self, customer_id: str, product: Dict,
                           customer_data: Dict, faker) -> Dict:
        """Create a realistic transaction"""
        base_price = product['price']

        # Apply persona-specific pricing patterns
        persona_type = customer_data['persona_type'].split('_')[0]

        if persona_type == 'budget_student':
            # Students look for discounts
            amount = base_price * random.uniform(0.7, 0.95)
        elif persona_type == 'business_owner':
            # B2B gets volume pricing but orders more
            quantity = random.randint(5, 50)
            amount = base_price * quantity * random.uniform(0.85, 0.95)
        else:
            quantity = random.randint(1, 3)
            amount = base_price * quantity * random.uniform(0.9, 1.1)

        return {
            'transaction_id': str(uuid.uuid4()),
            'customer_id': customer_id,
            'product_id': product['product_id'],
            'amount': round(amount, 2),
            'quantity': quantity if 'quantity' in locals() else 1,
            'category': product['category'],
            'timestamp': faker.date_time_between(start_date='-1y', end_date='now'),
            'channel': random.choice(['website', 'mobile_app', 'store', 'phone']),
            'created_at': datetime.utcnow()
        }

    def generate_all_data(self):
        """Generate all data components"""
        logger.info("Starting comprehensive data generation...")

        # Generate base data
        products = self.generate_products()
        customers = self.generate_main_personas()
        relationships = self.generate_relationships(customers)

        # Save base data
        products.to_parquet(f"{self.config['output_dir']}/products.parquet", compression='snappy')
        customers.to_parquet(f"{self.config['output_dir']}/customers.parquet", compression='snappy')
        relationships.to_parquet(f"{self.config['output_dir']}/relationships.parquet", compression='snappy')

        # Generate transactions in batches
        logger.info("Generating transactions in batches...")
        batch_count = 0
        for transaction_batch in self.generate_transactions_at_scale(customers, products):
            batch_file = f"{self.config['output_dir']}/transactions_batch_{batch_count:04d}.parquet"
            transaction_batch.to_parquet(batch_file, compression='snappy')
            batch_count += 1

        logger.info(f"Data generation complete! Generated {batch_count} transaction batches")
        return {
            'customers': len(customers),
            'products': len(products),
            'relationships': len(relationships),
            'transaction_batches': batch_count
        }

if __name__ == "__main__":
    # Generate data at massive scale
    config = {
        'customers': 10_000_000,
        'products': 100_000,
        'transactions': 1_000_000_000,
        'relationships': 50_000_000,
        'master_seed': 42,
        'batch_size': 100_000,
        'output_dir': 'data'
    }

    generator = PersonaDataGenerator(config)
    results = generator.generate_all_data()

    logger.info("Generation Summary:")
    for key, value in results.items():
        logger.info(f"  {key}: {value:,}" if isinstance(value, int) else f"  {key}: {value}")