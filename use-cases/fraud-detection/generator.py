#!/usr/bin/env python3
"""
Fraud Detection Data Generator
Generates realistic fraud scenarios with rich interconnected data
"""

import os
import random
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple
import numpy as np
import pandas as pd
from faker import Faker
from tqdm import tqdm
import networkx as nx
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class FraudScenario:
    """Configuration for a fraud scenario"""
    name: str
    account_count: int
    transaction_multiplier: float
    pattern: str
    description: str

class FraudDetectionDataGenerator:
    """Generates comprehensive fraud detection data"""

    def __init__(self, scale: str = "medium", seed: int = None):
        """
        Initialize fraud detection data generator

        Args:
            scale: Data scale (small, medium, large)
            seed: Random seed for reproducible data (overrides RANDOM_SEED env var)
        """
        load_dotenv()

        self.scale = scale

        # Set seed for reproducible data generation
        seed = seed or int(os.getenv('RANDOM_SEED', 42))
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)
        np.random.seed(seed)

        print(f"Fraud Detection Generator initialized with seed: {seed}")

        self.setup_scale_parameters()

        # Fraud scenarios to generate
        self.fraud_scenarios = {
            "account_takeover": FraudScenario(
                name="Account Takeover Ring",
                account_count=500,
                transaction_multiplier=3.0,
                pattern="star",
                description="Single device accessing multiple accounts"
            ),
            "money_laundering": FraudScenario(
                name="Money Laundering Network",
                account_count=100,
                transaction_multiplier=5.0,
                pattern="circular",
                description="Circular money flows through shell companies"
            ),
            "credit_card_fraud": FraudScenario(
                name="Credit Card Fraud Cluster",
                account_count=1000,
                transaction_multiplier=2.0,
                pattern="bipartite",
                description="Multiple cards used at same merchants"
            ),
            "synthetic_identity": FraudScenario(
                name="Synthetic Identity Fraud",
                account_count=200,
                transaction_multiplier=1.5,
                pattern="clique",
                description="Fake identities with similar attributes"
            ),
            "merchant_collusion": FraudScenario(
                name="Merchant Collusion Network",
                account_count=150,
                transaction_multiplier=4.0,
                pattern="dense",
                description="Cross-referral between merchants"
            )
        }

    def setup_scale_parameters(self):
        """Setup data generation parameters based on scale"""
        scale_configs = {
            "small": {
                "customers": 10000,
                "accounts": 15000,
                "transactions": 100000,
                "devices": 5000,
                "merchants": 2000
            },
            "medium": {
                "customers": 100000,
                "accounts": 150000,
                "transactions": 1000000,
                "devices": 25000,
                "merchants": 10000
            },
            "large": {
                "customers": 1000000,
                "accounts": 1500000,
                "transactions": 10000000,
                "devices": 100000,
                "merchants": 50000
            }
        }

        self.config = scale_configs.get(self.scale, scale_configs["medium"])

        # Fraud ratios (what percentage of data should be fraudulent)
        self.fraud_ratios = {
            "accounts": 0.05,  # 5% of accounts involved in fraud
            "transactions": 0.02,  # 2% of transactions are fraudulent
            "customers": 0.03,  # 3% of customers are fraudulent
            "devices": 0.10,  # 10% of devices are suspicious
            "merchants": 0.08   # 8% of merchants are fraudulent
        }

    def generate_customers(self) -> pd.DataFrame:
        """Generate customer data with fraud markers"""
        customers = []
        fraud_customer_count = int(self.config["customers"] * self.fraud_ratios["customers"])

        print(f"Generating {self.config['customers']} customers ({fraud_customer_count} fraudulent)...")

        for i in tqdm(range(self.config["customers"]), desc="Customers"):
            is_fraudulent = i < fraud_customer_count

            # Generate base customer data
            customer_id = f"cust_{i+1:010d}"
            name = self.fake.name()
            email = self.fake.email()
            phone = self.fake.phone_number()

            # Create SSN hash (for synthetic identity detection)
            ssn = self.fake.ssn()
            if is_fraudulent and random.random() < 0.3:  # 30% of fraud customers share SSN patterns
                # Create similar SSN for synthetic identity fraud
                base_ssn = f"{random.choice(['123', '456', '789'])}-{random.choice(['45', '67', '89'])}-{random.randint(1000, 9999)}"
                ssn = base_ssn

            ssn_hash = hashlib.sha256(ssn.encode()).hexdigest()[:16]

            # Address (for synthetic identity detection)
            address = self.fake.street_address()
            city = self.fake.city()
            state = self.fake.state_abbr()
            zip_code = self.fake.zipcode()

            if is_fraudulent and random.random() < 0.4:  # 40% of fraud customers share addresses
                # Use common fraudulent addresses
                fraud_addresses = [
                    "123 Fake Street", "456 Scam Avenue", "789 Fraud Lane",
                    "111 Suspicious Way", "222 Identity Drive"
                ]
                address = random.choice(fraud_addresses)

            date_of_birth = self.fake.date_of_birth(minimum_age=18, maximum_age=80)

            # Risk score (higher for fraudulent customers)
            if is_fraudulent:
                risk_score = random.uniform(70, 95)
            else:
                risk_score = random.uniform(10, 40)

            # Creation date (recent accounts are more suspicious)
            if is_fraudulent and random.random() < 0.6:  # 60% of fraud accounts are recent
                created_at = self.fake.date_time_between(start_date='-90d', end_date='now')
            else:
                created_at = self.fake.date_time_between(start_date='-5y', end_date='now')

            status = random.choices(
                ['active', 'suspended', 'closed'],
                weights=[85, 10, 5] if not is_fraudulent else [50, 40, 10]
            )[0]

            customers.append({
                'customer_id': customer_id,
                'name': name,
                'email': email,
                'phone': phone,
                'ssn_hash': ssn_hash,
                'address': address,
                'city': city,
                'state': state,
                'zip_code': zip_code,
                'date_of_birth': date_of_birth,
                'risk_score': risk_score,
                'created_at': created_at,
                'status': status,
                'is_fraudulent': is_fraudulent
            })

        return pd.DataFrame(customers)

    def generate_accounts(self, customers: pd.DataFrame) -> pd.DataFrame:
        """Generate accounts linked to customers"""
        accounts = []
        account_id = 1

        print(f"Generating {self.config['accounts']} accounts...")

        for _, customer in tqdm(customers.iterrows(), total=len(customers), desc="Accounts"):
            # Number of accounts per customer (fraudulent customers have more accounts)
            if customer['is_fraudulent']:
                num_accounts = random.choices([1, 2, 3, 4, 5], weights=[20, 30, 25, 15, 10])[0]
            else:
                num_accounts = random.choices([1, 2, 3], weights=[60, 30, 10])[0]

            for _ in range(num_accounts):
                if account_id > self.config['accounts']:
                    break

                account_type = random.choices(
                    ['checking', 'savings', 'credit', 'loan'],
                    weights=[40, 30, 20, 10]
                )[0]

                # Balance (fraudulent accounts have suspicious patterns)
                if customer['is_fraudulent']:
                    if random.random() < 0.3:  # 30% have very high balances
                        balance = random.uniform(100000, 1000000)
                    else:
                        balance = random.uniform(0, 10000)
                else:
                    balance = np.random.lognormal(8, 1.5)  # More realistic distribution

                credit_limit = balance * random.uniform(2, 5) if account_type == 'credit' else None

                opened_at = customer['created_at'] + timedelta(days=random.randint(0, 30))

                status = random.choices(
                    ['active', 'frozen', 'closed'],
                    weights=[80, 15, 5] if not customer['is_fraudulent'] else [60, 30, 10]
                )[0]

                accounts.append({
                    'account_id': f"acc_{account_id:010d}",
                    'customer_id': customer['customer_id'],
                    'account_type': account_type,
                    'balance': round(balance, 2),
                    'credit_limit': round(credit_limit, 2) if credit_limit else None,
                    'opened_at': opened_at,
                    'status': status,
                    'is_fraudulent': customer['is_fraudulent']
                })

                account_id += 1

        return pd.DataFrame(accounts)

    def generate_devices(self) -> pd.DataFrame:
        """Generate devices with suspicious patterns"""
        devices = []
        suspicious_device_count = int(self.config["devices"] * self.fraud_ratios["devices"])

        print(f"Generating {self.config['devices']} devices ({suspicious_device_count} suspicious)...")

        for i in tqdm(range(self.config["devices"]), desc="Devices"):
            is_suspicious = i < suspicious_device_count

            device_id = f"dev_{i+1:010d}"

            # Device fingerprint (suspicious devices have common patterns)
            if is_suspicious and random.random() < 0.4:  # 40% share fingerprints
                device_fingerprint = random.choice([
                    "fp_malware_001", "fp_bot_network", "fp_fraud_tool",
                    "fp_takeover_001", "fp_automated_002"
                ])
            else:
                device_fingerprint = self.fake.sha256()[:20]

            device_type = random.choices(
                ['mobile', 'desktop', 'tablet'],
                weights=[60, 30, 10]
            )[0]

            os = random.choices(
                ['iOS', 'Android', 'Windows', 'macOS', 'Linux'],
                weights=[25, 35, 25, 10, 5]
            )[0]

            browser = random.choices(
                ['Chrome', 'Safari', 'Firefox', 'Edge', 'Other'],
                weights=[50, 20, 15, 10, 5]
            )[0]

            # IP address (suspicious devices cluster in certain ranges)
            if is_suspicious and random.random() < 0.5:  # 50% cluster in suspicious ranges
                ip_ranges = ["192.168.1", "10.0.0", "172.16.1", "203.0.113", "198.51.100"]
                ip_base = random.choice(ip_ranges)
                ip_address = f"{ip_base}.{random.randint(1, 254)}"
            else:
                ip_address = self.fake.ipv4()

            # Location
            location = self.fake.city() + ", " + self.fake.state_abbr()

            first_seen = self.fake.date_time_between(start_date='-2y', end_date='-1d')
            last_seen = self.fake.date_time_between(start_date=first_seen, end_date='now')

            devices.append({
                'device_id': device_id,
                'device_fingerprint': device_fingerprint,
                'device_type': device_type,
                'os': os,
                'browser': browser,
                'ip_address': ip_address,
                'location': location,
                'first_seen': first_seen,
                'last_seen': last_seen,
                'is_suspicious': is_suspicious
            })

        return pd.DataFrame(devices)

    def generate_merchants(self) -> pd.DataFrame:
        """Generate merchants with fraud indicators"""
        merchants = []
        fraud_merchant_count = int(self.config["merchants"] * self.fraud_ratios["merchants"])

        print(f"Generating {self.config['merchants']} merchants ({fraud_merchant_count} fraudulent)...")

        categories = [
            'grocery', 'gas_station', 'restaurant', 'retail', 'online',
            'pharmacy', 'hotel', 'airline', 'entertainment', 'other'
        ]

        for i in tqdm(range(self.config["merchants"]), desc="Merchants"):
            is_fraudulent = i < fraud_merchant_count

            merchant_id = f"merch_{i+1:08d}"

            if is_fraudulent:
                # Fraudulent merchant names (often generic)
                merchant_names = [
                    "Quick Shop LLC", "Fast Mart Inc", "Easy Buy Corp",
                    "Simple Store", "Basic Retail", "Generic Shop"
                ]
                merchant_name = random.choice(merchant_names) + f" #{random.randint(100, 999)}"
            else:
                merchant_name = self.fake.company()

            category = random.choice(categories)
            address = self.fake.address()

            registration_date = self.fake.date_between(start_date='-10y', end_date='now')

            # Volume and risk score
            if is_fraudulent:
                volume_last_30d = random.uniform(500000, 5000000)  # Suspiciously high
                risk_score = random.uniform(70, 95)
                is_verified = random.choices([True, False], weights=[20, 80])[0]  # Mostly unverified
            else:
                volume_last_30d = np.random.lognormal(10, 1.5)
                risk_score = random.uniform(10, 40)
                is_verified = random.choices([True, False], weights=[85, 15])[0]  # Mostly verified

            merchants.append({
                'merchant_id': merchant_id,
                'merchant_name': merchant_name,
                'category': category,
                'address': address,
                'registration_date': registration_date,
                'volume_last_30d': round(volume_last_30d, 2),
                'risk_score': risk_score,
                'is_verified': is_verified,
                'is_fraudulent': is_fraudulent
            })

        return pd.DataFrame(merchants)

    def generate_fraud_scenarios(self, accounts: pd.DataFrame, devices: pd.DataFrame) -> Dict:
        """Generate specific fraud scenarios with their patterns"""
        scenarios = {}

        fraud_accounts = accounts[accounts['is_fraudulent']].copy()
        suspicious_devices = devices[devices['is_suspicious']].copy()

        for scenario_key, scenario_config in self.fraud_scenarios.items():
            print(f"Generating {scenario_config.name}...")

            # Select accounts for this scenario
            scenario_account_count = min(scenario_config.account_count, len(fraud_accounts))
            scenario_accounts = fraud_accounts.sample(n=scenario_account_count)

            if scenario_config.pattern == "star":
                # Account takeover: one device accessing many accounts
                scenarios[scenario_key] = self._create_star_pattern(scenario_accounts, suspicious_devices)
            elif scenario_config.pattern == "circular":
                # Money laundering: circular transaction flows
                scenarios[scenario_key] = self._create_circular_pattern(scenario_accounts)
            elif scenario_config.pattern == "bipartite":
                # Credit card fraud: cards and merchants
                scenarios[scenario_key] = self._create_bipartite_pattern(scenario_accounts)
            elif scenario_config.pattern == "clique":
                # Synthetic identity: densely connected accounts
                scenarios[scenario_key] = self._create_clique_pattern(scenario_accounts)
            elif scenario_config.pattern == "dense":
                # Merchant collusion: highly connected merchants
                scenarios[scenario_key] = self._create_dense_pattern(scenario_accounts)

        return scenarios

    def _create_star_pattern(self, accounts: pd.DataFrame, devices: pd.DataFrame) -> Dict:
        """Create star pattern for account takeover"""
        # Select a few devices that will access many accounts
        takeover_devices = devices.sample(n=min(10, len(devices)))

        device_account_relationships = []
        for _, device in takeover_devices.iterrows():
            # Each device accesses 20-50 accounts
            num_accounts = random.randint(20, min(50, len(accounts)))
            target_accounts = accounts.sample(n=num_accounts)

            for _, account in target_accounts.iterrows():
                device_account_relationships.append({
                    'device_id': device['device_id'],
                    'account_id': account['account_id'],
                    'first_login': self.fake.date_time_between(start_date='-30d', end_date='-1d'),
                    'last_login': self.fake.date_time_between(start_date='-7d', end_date='now'),
                    'login_count': random.randint(5, 50),
                    'failed_attempts': random.randint(0, 20)
                })

        return {'device_account_usage': pd.DataFrame(device_account_relationships)}

    def _create_circular_pattern(self, accounts: pd.DataFrame) -> Dict:
        """Create circular patterns for money laundering"""
        # Create cycles of 3-8 accounts
        cycles = []
        remaining_accounts = accounts.copy()

        while len(remaining_accounts) >= 3:
            cycle_size = random.randint(3, min(8, len(remaining_accounts)))
            cycle_accounts = remaining_accounts.sample(n=cycle_size)
            remaining_accounts = remaining_accounts.drop(cycle_accounts.index)

            # Create circular relationships
            account_list = cycle_accounts['account_id'].tolist()
            for i in range(len(account_list)):
                next_i = (i + 1) % len(account_list)
                cycles.append({
                    'account1_id': account_list[i],
                    'account2_id': account_list[next_i],
                    'relationship_type': 'money_laundering',
                    'confidence': random.uniform(0.8, 0.95),
                    'first_observed': self.fake.date_time_between(start_date='-60d', end_date='-30d'),
                    'last_observed': self.fake.date_time_between(start_date='-7d', end_date='now')
                })

        return {'account_relationships': pd.DataFrame(cycles)}

    def _create_bipartite_pattern(self, accounts: pd.DataFrame) -> Dict:
        """Create bipartite patterns for credit card fraud"""
        # Not implemented in detail for brevity
        return {'pattern': 'bipartite'}

    def _create_clique_pattern(self, accounts: pd.DataFrame) -> Dict:
        """Create clique patterns for synthetic identity"""
        # Not implemented in detail for brevity
        return {'pattern': 'clique'}

    def _create_dense_pattern(self, accounts: pd.DataFrame) -> Dict:
        """Create dense patterns for merchant collusion"""
        # Not implemented in detail for brevity
        return {'pattern': 'dense'}

    def generate_transactions(self, accounts: pd.DataFrame, devices: pd.DataFrame,
                            merchants: pd.DataFrame, fraud_scenarios: Dict) -> pd.DataFrame:
        """Generate transactions with fraud patterns"""
        transactions = []
        transaction_id = 1

        fraud_transaction_count = int(self.config["transactions"] * self.fraud_ratios["transactions"])
        normal_transaction_count = self.config["transactions"] - fraud_transaction_count

        print(f"Generating {self.config['transactions']} transactions ({fraud_transaction_count} fraudulent)...")

        # Generate normal transactions
        for _ in tqdm(range(normal_transaction_count), desc="Normal transactions"):
            transaction = self._generate_normal_transaction(
                transaction_id, accounts, devices, merchants
            )
            transactions.append(transaction)
            transaction_id += 1

        # Generate fraud transactions based on scenarios
        fraud_per_scenario = fraud_transaction_count // len(self.fraud_scenarios)

        for scenario_name, scenario_data in fraud_scenarios.items():
            for _ in tqdm(range(fraud_per_scenario), desc=f"Fraud: {scenario_name}"):
                transaction = self._generate_fraud_transaction(
                    transaction_id, accounts, devices, merchants, scenario_name, scenario_data
                )
                transactions.append(transaction)
                transaction_id += 1

        return pd.DataFrame(transactions)

    def _generate_normal_transaction(self, transaction_id: int, accounts: pd.DataFrame,
                                   devices: pd.DataFrame, merchants: pd.DataFrame) -> Dict:
        """Generate a normal transaction"""
        from_account = accounts.sample(n=1).iloc[0]

        # Transaction type probabilities
        transaction_type = random.choices(
            ['transfer', 'deposit', 'withdrawal', 'payment'],
            weights=[30, 20, 20, 30]
        )[0]

        if transaction_type == 'transfer':
            to_account = accounts.sample(n=1).iloc[0]['account_id']
        else:
            to_account = None

        # Amount (normal distribution)
        amount = abs(np.random.normal(500, 200))
        amount = max(1.0, min(amount, 10000))  # Clamp between $1 and $10k

        # Device and merchant
        device = devices.sample(n=1).iloc[0]
        merchant = merchants.sample(n=1).iloc[0] if transaction_type == 'payment' else None

        # Timestamp (random over last 90 days)
        timestamp = self.fake.date_time_between(start_date='-90d', end_date='now')

        # Risk score (low for normal transactions)
        risk_score = random.uniform(0.1, 0.3)

        return {
            'transaction_id': f"txn_{transaction_id:012d}",
            'from_account_id': from_account['account_id'],
            'to_account_id': to_account,
            'amount': round(amount, 2),
            'currency': 'USD',
            'transaction_type': transaction_type,
            'merchant_id': merchant['merchant_id'] if merchant is not None else None,
            'device_id': device['device_id'],
            'ip_address': device['ip_address'],
            'timestamp': timestamp,
            'is_flagged': False,
            'risk_score': risk_score,
            'is_fraudulent': False
        }

    def _generate_fraud_transaction(self, transaction_id: int, accounts: pd.DataFrame,
                                  devices: pd.DataFrame, merchants: pd.DataFrame,
                                  scenario_name: str, scenario_data: Dict) -> Dict:
        """Generate a fraudulent transaction based on scenario"""
        # Select fraudulent accounts
        fraud_accounts = accounts[accounts['is_fraudulent']]
        from_account = fraud_accounts.sample(n=1).iloc[0]

        # Higher amounts for fraud
        amount = random.uniform(1000, 50000)

        # Often round numbers
        if random.random() < 0.4:
            amount = random.choice([1000, 5000, 10000, 25000, 50000])

        # Use suspicious devices
        suspicious_devices = devices[devices['is_suspicious']]
        device = suspicious_devices.sample(n=1).iloc[0]

        # Recent timestamp (fraud is often recent)
        timestamp = self.fake.date_time_between(start_date='-7d', end_date='now')

        # High risk score
        risk_score = random.uniform(0.7, 0.95)

        transaction_type = random.choices(
            ['transfer', 'payment', 'withdrawal'],
            weights=[50, 30, 20]
        )[0]

        to_account = None
        merchant_id = None

        if transaction_type == 'transfer':
            to_account = fraud_accounts.sample(n=1).iloc[0]['account_id']
        elif transaction_type == 'payment':
            fraud_merchants = merchants[merchants['is_fraudulent']]
            merchant_id = fraud_merchants.sample(n=1).iloc[0]['merchant_id']

        return {
            'transaction_id': f"txn_{transaction_id:012d}",
            'from_account_id': from_account['account_id'],
            'to_account_id': to_account,
            'amount': round(amount, 2),
            'currency': 'USD',
            'transaction_type': transaction_type,
            'merchant_id': merchant_id,
            'device_id': device['device_id'],
            'ip_address': device['ip_address'],
            'timestamp': timestamp,
            'is_flagged': random.choices([True, False], weights=[20, 80])[0],  # 20% flagged
            'risk_score': risk_score,
            'is_fraudulent': True
        }

    def generate_all_data(self) -> Dict[str, pd.DataFrame]:
        """Generate all fraud detection data"""
        print(f"Starting fraud detection data generation for {self.scale} scale...")
        print(f"Target counts: {self.config}")

        # Generate core entities
        customers = self.generate_customers()
        accounts = self.generate_accounts(customers)
        devices = self.generate_devices()
        merchants = self.generate_merchants()

        # Generate fraud scenarios
        fraud_scenarios = self.generate_fraud_scenarios(accounts, devices)

        # Generate transactions with fraud patterns
        transactions = self.generate_transactions(accounts, devices, merchants, fraud_scenarios)

        # Compile all data
        all_data = {
            'customers': customers,
            'accounts': accounts,
            'devices': devices,
            'merchants': merchants,
            'transactions': transactions
        }

        # Add relationship tables from scenarios
        for scenario_name, scenario_data in fraud_scenarios.items():
            for table_name, table_data in scenario_data.items():
                if isinstance(table_data, pd.DataFrame):
                    all_data[f"{scenario_name}_{table_name}"] = table_data

        print(f"\nFraud detection data generation complete!")
        print(f"Generated tables: {list(all_data.keys())}")
        print(f"Total rows: {sum(len(df) for df in all_data.values())}")

        return all_data

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Generate fraud detection demo data')
    parser.add_argument('--scale', choices=['small', 'medium', 'large'],
                       default='medium', help='Data scale')
    parser.add_argument('--output-dir', default='./data',
                       help='Output directory for generated data')

    args = parser.parse_args()

    generator = FraudDetectionDataGenerator(scale=args.scale)
    data = generator.generate_all_data()

    # Save data to CSV files
    os.makedirs(args.output_dir, exist_ok=True)
    for table_name, df in data.items():
        output_file = os.path.join(args.output_dir, f"fraud_{table_name}.csv")
        df.to_csv(output_file, index=False)
        print(f"Saved {len(df)} rows to {output_file}")

    print(f"All fraud detection data saved to {args.output_dir}")