#!/usr/bin/env python3
"""
ClickHouse Integration for Customer 360 Demo
Enhanced database operations with existence checks and configuration
"""

import os
import glob
import time
import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from clickhouse_driver import Client
from dotenv import load_dotenv
from tqdm import tqdm

# Setup logging
def setup_logging():
    load_dotenv()
    level = logging.DEBUG if os.getenv('VERBOSE_LOGGING', 'true').lower() == 'true' else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('clickhouse.log')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


class ClickHouseClient:
    """Simple ClickHouse client for Customer 360 demo"""
    
    def __init__(self):
        """Initialize ClickHouse connection from environment variables"""
        load_dotenv()
        
        self.host = os.getenv('CLICKHOUSE_HOST')
        self.port = int(os.getenv('CLICKHOUSE_PORT', 8443))
        self.user = os.getenv('CLICKHOUSE_USER', 'default')
        self.password = os.getenv('CLICKHOUSE_PASSWORD')
        self.database = os.getenv('CLICKHOUSE_DATABASE', 'customer360')
        
        # Configuration options
        self.batch_size = int(os.getenv('INGESTION_BATCH_SIZE', 10000))
        self.create_db_if_not_exists = os.getenv('CREATE_DATABASE_IF_NOT_EXISTS', 'true').lower() == 'true'
        self.check_table_exists = os.getenv('CHECK_TABLE_EXISTS', 'true').lower() == 'true'
        self.drop_existing = os.getenv('DROP_EXISTING_TABLES', 'false').lower() == 'true'
        self.truncate_before_load = os.getenv('TRUNCATE_BEFORE_LOAD', 'false').lower() == 'true'
        self.skip_existing = os.getenv('SKIP_EXISTING_TABLES', 'false').lower() == 'true'
        self.retry_attempts = int(os.getenv('INGESTION_RETRY_ATTEMPTS', 3))
        self.retry_delay = int(os.getenv('INGESTION_RETRY_DELAY', 5))
        
        if not all([self.host, self.password]):
            raise ValueError("Missing ClickHouse credentials in environment variables")
        
        # Initialize client without database first to check if it exists
        self.client = Client(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            secure=True,
            verify=True
        )
        
        # Check and create database if needed
        if self.create_db_if_not_exists:
            self._ensure_database_exists()
        
        # Reconnect with database specified
        self.client = Client(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            secure=True,
            verify=True
        )
        
        logger.info(f"Connected to ClickHouse: {self.host}:{self.port}/{self.database}")
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a query and return results"""
        try:
            result = self.client.execute(query, params or {})
            return result
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def _ensure_database_exists(self):
        """Ensure database exists, create if needed"""
        try:
            # Check if database exists
            result = self.client.execute(
                "SELECT 1 FROM system.databases WHERE name = %(database)s",
                {'database': self.database}
            )
            
            if not result:
                logger.info(f"Database '{self.database}' does not exist, creating...")
                self.client.execute(f"CREATE DATABASE {self.database}")
                logger.info(f"✓ Database '{self.database}' created successfully")
            else:
                logger.info(f"Database '{self.database}' already exists")
                
        except Exception as e:
            logger.error(f"Failed to check/create database: {e}")
            raise
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            result = self.client.execute(f"EXISTS TABLE {table_name}")
            return result[0][0] == 1
        except Exception as e:
            logger.error(f"Failed to check table existence: {e}")
            return False
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get row count for a table"""
        try:
            result = self.client.execute(f"SELECT COUNT(*) FROM {table_name}")
            return result[0][0]
        except Exception:
            return 0
    
    def create_database(self):
        """Create the customer360 database if it doesn't exist"""
        self._ensure_database_exists()
    
    def create_tables(self):
        """Create all required tables with existence checking"""
        
        # Table definitions
        table_definitions = {
            'customers': """
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id String,
                    email String,
                    name String,
                    segment String,
                    ltv Decimal(10,2),
                    registration_date Date,
                    created_at DateTime
                ) ENGINE = MergeTree()
                ORDER BY customer_id
            """,
            'products': """
                CREATE TABLE IF NOT EXISTS products (
                    product_id String,
                    name String,
                    category String,
                    brand String,
                    price Decimal(10,2),
                    launch_date Date,
                    created_at DateTime
                ) ENGINE = MergeTree()
                ORDER BY product_id
            """,
            'transactions': """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id String,
                    customer_id String,
                    product_id String,
                    amount Decimal(10,2),
                    quantity UInt32,
                    timestamp DateTime,
                    channel String,
                    status String
                ) ENGINE = MergeTree()
                ORDER BY (customer_id, timestamp)
            """,
            'interactions': """
                CREATE TABLE IF NOT EXISTS interactions (
                    interaction_id String,
                    customer_id String,
                    product_id String,
                    type String,
                    timestamp DateTime,
                    duration UInt32,
                    device String,
                    session_id String
                ) ENGINE = MergeTree()
                ORDER BY (customer_id, timestamp)
            """
        }
        
        for table_name, ddl in table_definitions.items():
            try:
                # Check if table exists
                table_exists = self.check_table_exists(table_name)
                row_count = self.get_table_row_count(table_name) if table_exists else 0
                
                if table_exists:
                    logger.info(f"Table '{table_name}' exists with {row_count:,} rows")
                    
                    if self.drop_existing:
                        logger.warning(f"Dropping existing table '{table_name}'")
                        self.client.execute(f"DROP TABLE {table_name}")
                        self.client.execute(ddl)
                        logger.info(f"✓ Table '{table_name}' recreated")
                    elif self.truncate_before_load:
                        logger.warning(f"Truncating table '{table_name}'")
                        self.client.execute(f"TRUNCATE TABLE {table_name}")
                        logger.info(f"✓ Table '{table_name}' truncated")
                    else:
                        logger.info(f"✓ Table '{table_name}' ready (existing)")
                else:
                    logger.info(f"Creating new table '{table_name}'")
                    self.client.execute(ddl)
                    logger.info(f"✓ Table '{table_name}' created successfully")
                    
            except Exception as e:
                logger.error(f"Failed to handle table '{table_name}': {e}")
                raise
    
    def load_data_from_parquet(self, data_dir: str = "data", batch_size: int = 10000):
        """Load data from Parquet files into ClickHouse tables"""
        
        tables = ['customers', 'products', 'transactions', 'interactions']
        
        for table in tables:
            file_path = os.path.join(data_dir, f"{table}.parquet")
            
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue
            
            logger.info(f"Loading {table} from {file_path}...")
            
            # Read Parquet file
            df = pd.read_parquet(file_path)
            
            # Convert data types for ClickHouse
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
            if 'registration_date' in df.columns:
                df['registration_date'] = pd.to_datetime(df['registration_date']).dt.date
            if 'launch_date' in df.columns:
                df['launch_date'] = pd.to_datetime(df['launch_date']).dt.date
            
            # Insert data in batches
            total_rows = len(df)
            inserted_rows = 0
            
            for i in range(0, total_rows, batch_size):
                batch = df.iloc[i:i + batch_size]
                
                # Convert to list of tuples for insertion
                data = [tuple(row) for row in batch.values]
                
                # Insert batch
                self.client.execute(f"INSERT INTO {table} VALUES", data)
                inserted_rows += len(batch)
                
                if inserted_rows % 50000 == 0:
                    logger.info(f"  Inserted {inserted_rows:,}/{total_rows:,} rows")
            
            logger.info(f"✅ Loaded {table}: {inserted_rows:,} rows")
    
    def load_batch_files(self, data_dir: str):
        """Load data from batch parquet files"""
        tables = ['customers', 'products', 'transactions', 'interactions']
        
        for table in tables:
            table_dir = os.path.join(data_dir, table)
            
            if not os.path.exists(table_dir):
                logger.warning(f"Batch directory not found: {table_dir}")
                continue
            
            # Get all batch files for this table
            batch_files = sorted([
                f for f in os.listdir(table_dir) 
                if f.endswith('.parquet') and f.startswith(f"{table}_batch_")
            ])
            
            if not batch_files:
                logger.warning(f"No batch files found for {table} in {table_dir}")
                continue
            
            # Check if we should skip this table
            if self.skip_existing:
                existing_rows = self.get_table_row_count(table)
                if existing_rows > 0:
                    logger.info(f"Skipping {table} - already has {existing_rows:,} rows")
                    continue
            
            logger.info(f"Loading {table} from {len(batch_files)} batch files...")
            
            total_inserted = 0
            failed_batches = []
            
            # Load each batch file with progress tracking
            show_progress = os.getenv('SHOW_PROGRESS_BARS', 'true').lower() == 'true'
            batch_iterator = tqdm(batch_files, desc=f"Loading {table}") if show_progress else batch_files
            
            for batch_file in batch_iterator:
                batch_path = os.path.join(table_dir, batch_file)
                
                success = False
                for attempt in range(self.retry_attempts):
                    try:
                        # Read batch file
                        df = pd.read_parquet(batch_path)
                        
                        # Convert data types for ClickHouse
                        df = self._prepare_dataframe_for_clickhouse(df)
                        
                        # Insert batch with smaller sub-batches
                        batch_inserted = self._insert_dataframe_in_batches(table, df)
                        total_inserted += batch_inserted
                        
                        logger.debug(f"✓ Loaded {batch_file}: {batch_inserted:,} rows")
                        success = True
                        break
                        
                    except Exception as e:
                        logger.warning(f"Attempt {attempt + 1} failed for {batch_file}: {e}")
                        if attempt < self.retry_attempts - 1:
                            time.sleep(self.retry_delay)
                        else:
                            logger.error(f"Failed to load {batch_file} after {self.retry_attempts} attempts")
                            failed_batches.append(batch_file)
                
                if not success:
                    failed_batches.append(batch_file)
            
            # Summary for this table
            if failed_batches:
                logger.warning(f"⚠️ {table}: Loaded {total_inserted:,} rows, {len(failed_batches)} batches failed")
                for failed_batch in failed_batches:
                    logger.warning(f"   Failed: {failed_batch}")
            else:
                logger.info(f"✅ {table}: Successfully loaded {total_inserted:,} rows from all batches")
    
    def _prepare_dataframe_for_clickhouse(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare DataFrame for ClickHouse insertion"""
        # Convert timestamp columns
        for col in df.columns:
            if 'timestamp' in col.lower():
                df[col] = pd.to_datetime(df[col])
            elif 'date' in col.lower() and col != 'created_at':
                df[col] = pd.to_datetime(df[col]).dt.date
            elif col == 'created_at':
                df[col] = pd.to_datetime(df[col])
        
        return df
    
    def _insert_dataframe_in_batches(self, table_name: str, df: pd.DataFrame) -> int:
        """Insert DataFrame in smaller batches"""
        total_rows = len(df)
        inserted_rows = 0
        
        for i in range(0, total_rows, self.batch_size):
            batch = df.iloc[i:i + self.batch_size]
            
            # Convert to list of tuples for insertion
            data = [tuple(row) for row in batch.values]
            
            # Insert batch
            self.client.execute(f"INSERT INTO {table_name} VALUES", data)
            inserted_rows += len(batch)
            
            # Log progress for large batches
            if total_rows > self.batch_size * 2 and inserted_rows % (self.batch_size * 5) == 0:
                logger.debug(f"  Inserted {inserted_rows:,}/{total_rows:,} rows")
        
        return inserted_rows
    
    def get_table_counts(self) -> Dict[str, int]:
        """Get row counts for all tables"""
        tables = ['customers', 'products', 'transactions', 'interactions']
        counts = {}
        
        for table in tables:
            try:
                result = self.client.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = result[0][0]
            except Exception as e:
                logger.error(f"Failed to count {table}: {e}")
                counts[table] = 0
        
        return counts
    
    def run_sample_queries(self):
        """Run sample analytical queries to verify data"""
        
        queries = {
            "Customer Segments": """
                SELECT segment, COUNT(*) as customers, ROUND(AVG(ltv), 2) as avg_ltv
                FROM customers 
                GROUP BY segment 
                ORDER BY avg_ltv DESC
            """,
            
            "Top Product Categories": """
                SELECT category, COUNT(*) as products, ROUND(AVG(price), 2) as avg_price
                FROM products 
                GROUP BY category 
                ORDER BY products DESC 
                LIMIT 10
            """,
            
            "Transaction Volume by Channel": """
                SELECT channel, COUNT(*) as transactions, ROUND(SUM(amount), 2) as total_revenue
                FROM transactions 
                WHERE status = 'completed'
                GROUP BY channel 
                ORDER BY total_revenue DESC
            """,
            
            "Most Active Customers": """
                SELECT c.name, c.segment, COUNT(t.transaction_id) as transactions, 
                       ROUND(SUM(t.amount), 2) as total_spent
                FROM customers c
                JOIN transactions t ON c.customer_id = t.customer_id
                WHERE t.status = 'completed'
                GROUP BY c.customer_id, c.name, c.segment
                ORDER BY total_spent DESC
                LIMIT 10
            """
        }
        
        for query_name, query in queries.items():
            try:
                logger.info(f"\n📊 {query_name}:")
                result = self.client.execute(query)
                
                for row in result[:5]:  # Show first 5 rows
                    print(f"   {row}")
                    
                if len(result) > 5:
                    print(f"   ... and {len(result) - 5} more rows")
                    
            except Exception as e:
                logger.error(f"Query failed: {e}")
    
    def create_graph_schema_file(self, output_path: str = "puppygraph-schema.json"):
        """Create PuppyGraph schema configuration file"""
        
        schema = {
            "catalogs": [
                {
                    "name": "clickhouse",
                    "type": "clickhouse",
                    "jdbc": {
                        "url": f"jdbc:clickhouse://{self.host}:{self.port}/{self.database}?ssl=true",
                        "username": self.user,
                        "password": self.password,
                        "driverClassName": "com.clickhouse.jdbc.ClickHouseDriver"
                    }
                }
            ],
            "graph": {
                "vertices": [
                    {
                        "label": "Customer",
                        "mappedTableSource": {
                            "catalog": "clickhouse",
                            "schema": "default",
                            "table": "customers",
                            "metaFields": {"id": "customer_id"}
                        },
                        "properties": {
                            "email": {"column": "email", "type": "STRING"},
                            "name": {"column": "name", "type": "STRING"},
                            "segment": {"column": "segment", "type": "STRING"},
                            "ltv": {"column": "ltv", "type": "DOUBLE"}
                        }
                    },
                    {
                        "label": "Product",
                        "mappedTableSource": {
                            "catalog": "clickhouse",
                            "schema": "default",
                            "table": "products",
                            "metaFields": {"id": "product_id"}
                        },
                        "properties": {
                            "name": {"column": "name", "type": "STRING"},
                            "category": {"column": "category", "type": "STRING"},
                            "brand": {"column": "brand", "type": "STRING"},
                            "price": {"column": "price", "type": "DOUBLE"}
                        }
                    }
                ],
                "edges": [
                    {
                        "label": "PURCHASED",
                        "mappedTableSource": {
                            "catalog": "clickhouse",
                            "schema": "default",
                            "table": "transactions",
                            "metaFields": {
                                "id": "transaction_id",
                                "from": "customer_id",
                                "to": "product_id"
                            },
                            "predicate": "status = 'completed'"
                        },
                        "properties": {
                            "amount": {"column": "amount", "type": "DOUBLE"},
                            "timestamp": {"column": "timestamp", "type": "TIMESTAMP"},
                            "channel": {"column": "channel", "type": "STRING"}
                        }
                    },
                    {
                        "label": "VIEWED",
                        "mappedTableSource": {
                            "catalog": "clickhouse",
                            "schema": "default",
                            "table": "interactions",
                            "metaFields": {
                                "id": "interaction_id",
                                "from": "customer_id",
                                "to": "product_id"
                            },
                            "predicate": "type = 'view'"
                        },
                        "properties": {
                            "timestamp": {"column": "timestamp", "type": "TIMESTAMP"},
                            "duration": {"column": "duration", "type": "INTEGER"},
                            "device": {"column": "device", "type": "STRING"}
                        }
                    }
                ]
            }
        }
        
        import json
        with open(output_path, 'w') as f:
            json.dump(schema, f, indent=2)
        
        logger.info(f"Created PuppyGraph schema: {output_path}")


def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ClickHouse operations for Customer 360 demo')
    parser.add_argument('--init', action='store_true', help='Initialize database and tables')
    parser.add_argument('--load', action='store_true', help='Load data from Parquet files')
    parser.add_argument('--data-dir', default='data', help='Directory containing Parquet files')
    parser.add_argument('--schema', action='store_true', help='Create PuppyGraph schema file')
    parser.add_argument('--query', action='store_true', help='Run sample queries')
    parser.add_argument('--status', action='store_true', help='Show table counts')
    
    args = parser.parse_args()
    
    if not any([args.init, args.load, args.schema, args.query, args.status]):
        parser.print_help()
        return
    
    try:
        # Initialize client
        client = ClickHouseClient()
        
        if args.init:
            client.create_database()
            client.create_tables()
            print("✅ Database and tables initialized")
        
        if args.load:
            client.load_data_from_parquet(args.data_dir)
            print("✅ Data loaded successfully")
        
        if args.schema:
            client.create_graph_schema_file()
            print("✅ PuppyGraph schema file created")
        
        if args.query:
            client.run_sample_queries()
        
        if args.status:
            counts = client.get_table_counts()
            print("\n📊 Table Status:")
            for table, count in counts.items():
                print(f"   {table}: {count:,} rows")
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise


if __name__ == "__main__":
    main()