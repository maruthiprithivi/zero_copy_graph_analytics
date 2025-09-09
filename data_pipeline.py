#!/usr/bin/env python3
"""
Customer 360 Data Pipeline - Unified Generation and Ingestion
Configurable via environment variables for flexible data operations
"""

import os
import sys
import logging
import argparse
from typing import Optional
from dotenv import load_dotenv

from generator import Customer360Generator
from clickhouse import ClickHouseClient

# Setup logging
def setup_logging():
    load_dotenv()
    level = logging.DEBUG if os.getenv('VERBOSE_LOGGING', 'true').lower() == 'true' else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data_pipeline.log')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


class DataPipeline:
    """Unified data pipeline for generation and ingestion"""
    
    def __init__(self):
        """Initialize pipeline with environment configuration"""
        load_dotenv()
        
        self.operation_mode = os.getenv('OPERATION_MODE', 'both').lower()
        self.generate_data_enabled = os.getenv('GENERATE_DATA', 'true').lower() == 'true'
        self.ingest_data_enabled = os.getenv('INGEST_DATA', 'true').lower() == 'true'
        self.validate_after_load = os.getenv('VALIDATE_DATA_AFTER_LOAD', 'true').lower() == 'true'
        
        self.generator = None
        self.clickhouse_client = None
        
        logger.info("Data Pipeline initialized")
        logger.info(f"  - Operation mode: {self.operation_mode}")
        logger.info(f"  - Generate data: {self.generate_data_enabled}")
        logger.info(f"  - Ingest data: {self.ingest_data_enabled}")
    
    def run_data_generation(self, scale: Optional[int] = None, output_dir: Optional[str] = None) -> bool:
        """Run data generation phase"""
        if not self.generate_data_enabled:
            logger.info("Data generation disabled by configuration")
            return True
        
        try:
            logger.info("="*60)
            logger.info("STARTING DATA GENERATION PHASE")
            logger.info("="*60)
            
            # Initialize generator
            self.generator = Customer360Generator(scale=scale)
            
            # Generate all data
            data = self.generator.generate_all(output_dir=output_dir)
            
            # Log summary
            total_records = sum(len(df) for df in data.values())
            logger.info(f"✓ Data generation completed successfully")
            logger.info(f"  - Total records generated: {total_records:,}")
            
            for table_name, df in data.items():
                logger.info(f"  - {table_name}: {len(df):,} records")
            
            return True
            
        except Exception as e:
            logger.error(f"Data generation failed: {e}")
            return False
    
    def run_data_ingestion(self, data_dir: Optional[str] = None) -> bool:
        """Run data ingestion phase"""
        if not self.ingest_data_enabled:
            logger.info("Data ingestion disabled by configuration")
            return True
        
        try:
            logger.info("="*60)
            logger.info("STARTING DATA INGESTION PHASE")
            logger.info("="*60)
            
            # Initialize ClickHouse client
            self.clickhouse_client = ClickHouseClient()
            
            # Create database and tables
            logger.info("Setting up database and tables...")
            self.clickhouse_client.create_database()
            self.clickhouse_client.create_tables()
            
            # Load data
            data_directory = data_dir or os.getenv('DATA_OUTPUT_DIR', 'data')
            logger.info(f"Loading data from: {data_directory}")
            
            # Check if we're loading from batch files or single files
            if self._has_batch_files(data_directory):
                logger.info("Detected batch files, using batch loading")
                self.clickhouse_client.load_batch_files(data_directory)
            else:
                logger.info("Using standard parquet file loading")
                self.clickhouse_client.load_data_from_parquet(data_directory)
            
            # Validate data if requested
            if self.validate_after_load:
                self._validate_loaded_data()
            
            logger.info("✓ Data ingestion completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Data ingestion failed: {e}")
            return False
    
    def _has_batch_files(self, data_dir: str) -> bool:
        """Check if data directory contains batch files"""
        if not os.path.exists(data_dir):
            return False
        
        # Look for subdirectories with batch files
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path):
                batch_files = [f for f in os.listdir(item_path) if f.endswith('.parquet')]
                if batch_files:
                    return True
        
        return False
    
    def _validate_loaded_data(self):
        """Validate data after loading"""
        logger.info("Validating loaded data...")
        
        if not self.clickhouse_client:
            logger.warning("Cannot validate - ClickHouse client not initialized")
            return
        
        try:
            counts = self.clickhouse_client.get_table_counts()
            total_rows = sum(counts.values())
            
            logger.info("Data validation results:")
            for table, count in counts.items():
                logger.info(f"  - {table}: {count:,} rows")
            logger.info(f"  - Total: {total_rows:,} rows")
            
            # Basic validation checks
            if total_rows == 0:
                logger.warning("⚠️ No data found in any tables!")
            elif any(count == 0 for count in counts.values()):
                empty_tables = [table for table, count in counts.items() if count == 0]
                logger.warning(f"⚠️ Empty tables detected: {empty_tables}")
            else:
                logger.info("✓ All tables contain data")
            
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
    
    def run_pipeline(self, scale: Optional[int] = None, data_dir: Optional[str] = None):
        """Run the complete pipeline based on operation mode"""
        start_time = logger.handlers[0].formatter.formatTime(logger.makeRecord(
            '', 0, '', 0, '', (), None
        )[:3])
        
        logger.info("="*60)
        logger.info("CUSTOMER 360 DATA PIPELINE STARTED")
        logger.info("="*60)
        
        success = True
        
        # Determine what operations to run
        should_generate = self.operation_mode in ['generate', 'both']
        should_ingest = self.operation_mode in ['ingest', 'both']
        
        # Run generation phase
        if should_generate:
            if not self.run_data_generation(scale=scale, output_dir=data_dir):
                success = False
        
        # Run ingestion phase
        if should_ingest and success:
            if not self.run_data_ingestion(data_dir=data_dir):
                success = False
        
        # Final summary
        logger.info("="*60)
        if success:
            logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        else:
            logger.error("❌ PIPELINE FAILED!")
        logger.info("="*60)
        
        return success


def main():
    """Main entry point with command line argument support"""
    parser = argparse.ArgumentParser(
        description='Customer 360 Data Pipeline - Generate and/or ingest data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run full pipeline (generate + ingest)
  %(prog)s --mode generate          # Only generate data
  %(prog)s --mode ingest            # Only ingest existing data
  %(prog)s --scale 10000000         # Generate 10M customers
  %(prog)s --data-dir /path/to/data # Use custom data directory

Environment variables (see .env file):
  OPERATION_MODE: both, generate, ingest
  GENERATE_DATA: true/false
  INGEST_DATA: true/false
  CUSTOMER_SCALE: 1000000, 10000000, 100000000
  DATA_OUTPUT_DIR: data directory path
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['both', 'generate', 'ingest'],
        help='Operation mode (overrides OPERATION_MODE env var)'
    )
    
    parser.add_argument(
        '--scale',
        type=int,
        choices=[1_000_000, 10_000_000, 100_000_000],
        help='Number of customers to generate (overrides CUSTOMER_SCALE env var)'
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        help='Data directory path (overrides DATA_OUTPUT_DIR env var)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate data after loading (overrides VALIDATE_DATA_AFTER_LOAD)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Override environment variables with command line arguments
    if args.mode:
        os.environ['OPERATION_MODE'] = args.mode
    
    if args.scale:
        os.environ['CUSTOMER_SCALE'] = str(args.scale)
    
    if args.data_dir:
        os.environ['DATA_OUTPUT_DIR'] = args.data_dir
    
    if args.validate:
        os.environ['VALIDATE_DATA_AFTER_LOAD'] = 'true'
    
    if args.verbose:
        os.environ['VERBOSE_LOGGING'] = 'true'
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run pipeline
    try:
        pipeline = DataPipeline()
        success = pipeline.run_pipeline(
            scale=args.scale,
            data_dir=args.data_dir
        )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()