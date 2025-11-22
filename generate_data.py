#!/usr/bin/env python3
"""
Data Generation CLI - Configurable data generator for Customer 360 & Fraud Detection

Usage:
  # Using environment variables
  export CUSTOMER_SCALE=1000000
  python generate_data.py

  # Using command-line parameters
  python generate_data.py --customers 1000000 --use-case customer360

  # Using a data config file
  python generate_data.py --env-file data.env

  # Combining both (CLI params override env vars)
  python generate_data.py --env-file data.env --customers 500000
"""

import os
import sys
import click
from dotenv import load_dotenv

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

@click.command()
@click.option('--env-file',
              type=click.Path(exists=True),
              help='Path to environment file with configuration (e.g., data.env)')
@click.option('--customers',
              type=int,
              help='Number of customers to generate (overrides CUSTOMER_SCALE env var)')
@click.option('--seed',
              type=int,
              help='Random seed for reproducible data (overrides RANDOM_SEED env var)')
@click.option('--batch-size',
              type=int,
              help='Batch size for file generation (overrides BATCH_FILE_SIZE env var)')
@click.option('--output-dir',
              type=click.Path(),
              help='Output directory for generated data (overrides DATA_OUTPUT_DIR env var)')
@click.option('--compression',
              type=click.Choice(['snappy', 'gzip', 'lz4']),
              help='Parquet compression format (overrides PARQUET_COMPRESSION env var)')
@click.option('--use-case',
              type=click.Choice(['customer360', 'fraud-detection', 'both']),
              default='both',
              help='Which use case data to generate')
@click.option('--overwrite/--no-overwrite',
              default=None,
              help='Overwrite existing data files (overrides OVERWRITE_EXISTING_DATA env var)')
@click.option('--verbose',
              is_flag=True,
              help='Enable verbose debug logging')
def generate(env_file, customers, seed, batch_size, output_dir, compression, use_case, overwrite, verbose):
    """
    Generate realistic data for Customer 360 and Fraud Detection use cases.

    This tool generates data based on configuration from:
    1. Environment file (--env-file)
    2. System environment variables
    3. Command-line parameters (highest priority)
    """

    # Load environment file if specified
    if env_file:
        click.echo(f"Loading configuration from: {env_file}")
        load_dotenv(env_file, override=True)
    else:
        load_dotenv()

    # Override environment variables with CLI parameters
    if customers:
        os.environ['CUSTOMER_SCALE'] = str(customers)
    if seed:
        os.environ['RANDOM_SEED'] = str(seed)
    if batch_size:
        os.environ['BATCH_FILE_SIZE'] = str(batch_size)
    if output_dir:
        os.environ['DATA_OUTPUT_DIR'] = output_dir
    if compression:
        os.environ['PARQUET_COMPRESSION'] = compression
    if overwrite is not None:
        os.environ['OVERWRITE_EXISTING_DATA'] = 'true' if overwrite else 'false'
    if verbose:
        os.environ['VERBOSE_LOGGING'] = 'true'

    # Set use case flags
    if use_case == 'customer360':
        os.environ['GENERATE_CUSTOMER_360'] = 'true'
        os.environ['GENERATE_FRAUD_DETECTION'] = 'false'
    elif use_case == 'fraud-detection':
        os.environ['GENERATE_CUSTOMER_360'] = 'false'
        os.environ['GENERATE_FRAUD_DETECTION'] = 'true'
    else:  # both
        os.environ['GENERATE_CUSTOMER_360'] = 'true'
        os.environ['GENERATE_FRAUD_DETECTION'] = 'true'

    # Display configuration
    customer_scale = os.getenv('CUSTOMER_SCALE', '1000000')
    click.echo("\nData Generation Configuration:")
    click.echo(f"  Customers: {int(customer_scale):,}")
    click.echo(f"  Seed: {os.getenv('RANDOM_SEED', '42')}")
    click.echo(f"  Batch size: {int(os.getenv('BATCH_FILE_SIZE', '100000')):,}")
    click.echo(f"  Output dir: {os.getenv('DATA_OUTPUT_DIR', 'data')}")
    click.echo(f"  Compression: {os.getenv('PARQUET_COMPRESSION', 'snappy')}")
    click.echo(f"  Use case: {use_case}")
    click.echo(f"  Overwrite: {os.getenv('OVERWRITE_EXISTING_DATA', 'false')}")
    click.echo(f"  Verbose: {os.getenv('VERBOSE_LOGGING', 'false')}")
    click.echo()

    # Import and run the appropriate generators
    try:
        generated_data = []

        if os.getenv('GENERATE_CUSTOMER_360', 'true').lower() == 'true':
            click.echo("Generating Customer 360 data...")
            from app.data.generator import Customer360Generator
            generator = Customer360Generator()
            data = generator.generate_all()
            generated_data.append(('customer360', data))
            click.echo("Customer 360 data generation complete!\n")

        if os.getenv('GENERATE_FRAUD_DETECTION', 'true').lower() == 'true':
            click.echo("Generating Fraud Detection data...")
            # Import fraud detection generator
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'use-cases', 'fraud-detection'))
            from generator import FraudDetectionDataGenerator

            # Determine scale based on customer count
            customer_scale = int(os.getenv('CUSTOMER_SCALE', '1000000'))
            if customer_scale <= 100000:
                scale = 'small'
            elif customer_scale <= 1000000:
                scale = 'medium'
            else:
                scale = 'large'

            fraud_gen = FraudDetectionDataGenerator(scale=scale)
            fraud_data = fraud_gen.generate_all_data()
            generated_data.append(('fraud_detection', fraud_data))
            click.echo("Fraud Detection data generation complete!\n")

        click.echo("All data generation complete!")
        click.echo(f"Data saved to: {os.getenv('DATA_OUTPUT_DIR', 'data')}\n")

        # Ingest data into ClickHouse (optional)
        ingest_data = os.getenv('INGEST_TO_CLICKHOUSE', 'true').lower() == 'true'

        if ingest_data:
            click.echo("Ingesting data into ClickHouse...")
            try:
                from app.database.clickhouse import ClickHouseClient
                import clickhouse_connect

                # Test connection first
                try:
                    client_test = clickhouse_connect.get_client(
                        host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
                        port=int(os.getenv('CLICKHOUSE_PORT', '8123')),
                        username=os.getenv('CLICKHOUSE_USER', 'default'),
                        password=os.getenv('CLICKHOUSE_PASSWORD', '')
                    )
                    client_test.query("SELECT 1")
                    click.echo("ClickHouse connection established successfully")
                except Exception as conn_error:
                    click.echo(f"Warning: Could not connect to ClickHouse: {conn_error}", err=True)
                    click.echo("Data has been generated and saved to files, but not ingested into database.")
                    sys.exit(0)

                # Ingest the data
                client = ClickHouseClient()
                click.echo("Creating tables if not exist...")
                client.create_tables()

                for use_case, data in generated_data:
                    click.echo(f"\nIngesting {use_case} data...")
                    for table_name, df in data.items():
                        click.echo(f"  Ingesting {table_name}: {len(df):,} records...")
                        client.insert_dataframe(table_name, df)

                click.echo("\nData ingestion complete!")
                click.echo("You can now query the data using ClickHouse or PuppyGraph")

            except ImportError as ie:
                click.echo(f"Warning: Could not import required modules: {ie}", err=True)
                click.echo("Data has been generated and saved to files.")
        else:
            click.echo("Skipping data ingestion (INGEST_TO_CLICKHOUSE=false)")
            click.echo(f"Data files saved to: {os.getenv('DATA_OUTPUT_DIR', 'data')}")

    except Exception as e:
        click.echo(f"Error during data generation: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    generate()
