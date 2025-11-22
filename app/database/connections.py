#!/usr/bin/env python3
"""
Database Connections Module
Real-time connections to ClickHouse and PuppyGraph for live demo queries
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
import clickhouse_connect
from neo4j import GraphDatabase
import pandas as pd
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Standardized query result structure"""
    data: List[Dict[str, Any]]
    execution_time: float
    row_count: int
    query_text: str
    database_type: str
    status: str
    error: Optional[str] = None

class ClickHouseConnection:
    """Real ClickHouse database connection"""

    def __init__(self, host: str = "localhost", port: int = 8123,
                 username: str = "default", password: str = "",
                 database: str = "demo"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.client = None

    def connect(self) -> bool:
        """Establish connection to ClickHouse"""
        try:
            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database
            )
            # Test connection
            self.client.query("SELECT 1")
            logger.info(f"Connected to ClickHouse at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {str(e)}")
            return False

    def execute_query(self, query: str, parameters: Dict = None) -> QueryResult:
        """Execute SQL query with timing and error handling"""
        start_time = time.time()

        try:
            if not self.client:
                if not self.connect():
                    raise ConnectionError("Failed to establish ClickHouse connection")

            # Execute query with parameters
            if parameters:
                result = self.client.query(query, parameters=parameters)
            else:
                result = self.client.query(query)

            execution_time = time.time() - start_time

            # Convert to list of dictionaries
            if result.result_rows:
                columns = result.column_names
                data = [dict(zip(columns, row)) for row in result.result_rows]
            else:
                data = []

            return QueryResult(
                data=data,
                execution_time=execution_time,
                row_count=len(data),
                query_text=query,
                database_type="ClickHouse",
                status="success"
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"ClickHouse query failed: {str(e)}")

            return QueryResult(
                data=[],
                execution_time=execution_time,
                row_count=0,
                query_text=query,
                database_type="ClickHouse",
                status="error",
                error=str(e)
            )

    def close(self):
        """Close connection"""
        if self.client:
            self.client.close()
            self.client = None

class PuppyGraphConnection:
    """Real PuppyGraph/Neo4j database connection"""

    def __init__(self, uri: str = "bolt://localhost:7687",
                 username: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None

    def connect(self) -> bool:
        """Establish connection to PuppyGraph"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Connected to PuppyGraph at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PuppyGraph: {str(e)}")
            return False

    def execute_query(self, cypher: str, parameters: Dict = None) -> QueryResult:
        """Execute Cypher query with timing and error handling"""
        start_time = time.time()

        try:
            if not self.driver:
                if not self.connect():
                    raise ConnectionError("Failed to establish PuppyGraph connection")

            with self.driver.session() as session:
                if parameters:
                    result = session.run(cypher, parameters)
                else:
                    result = session.run(cypher)

                # Convert to list of dictionaries
                data = []
                for record in result:
                    row = {}
                    for key in record.keys():
                        value = record[key]
                        # Handle Neo4j node/relationship objects
                        if hasattr(value, '__dict__'):
                            row[key] = dict(value)
                        else:
                            row[key] = value
                    data.append(row)

            execution_time = time.time() - start_time

            return QueryResult(
                data=data,
                execution_time=execution_time,
                row_count=len(data),
                query_text=cypher,
                database_type="PuppyGraph",
                status="success"
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"PuppyGraph query failed: {str(e)}")

            return QueryResult(
                data=[],
                execution_time=execution_time,
                row_count=0,
                query_text=cypher,
                database_type="PuppyGraph",
                status="error",
                error=str(e)
            )

    def close(self):
        """Close connection"""
        if self.driver:
            self.driver.close()
            self.driver = None

class DatabaseManager:
    """Manages both ClickHouse and PuppyGraph connections"""

    def __init__(self, clickhouse_config: Dict = None, puppygraph_config: Dict = None):
        # Default configurations
        self.ch_config = clickhouse_config or {
            'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
            'port': int(os.getenv('CLICKHOUSE_PORT', '8123')),
            'username': os.getenv('CLICKHOUSE_USER', 'default'),
            'password': os.getenv('CLICKHOUSE_PASSWORD', ''),
            'database': os.getenv('CLICKHOUSE_DATABASE', 'demo')
        }

        self.pg_config = puppygraph_config or {
            'uri': os.getenv('PUPPYGRAPH_URI', 'bolt://localhost:7687'),
            'username': os.getenv('PUPPYGRAPH_USER', 'neo4j'),
            'password': os.getenv('PUPPYGRAPH_PASSWORD', 'password')
        }

        self.clickhouse = ClickHouseConnection(**self.ch_config)
        self.puppygraph = PuppyGraphConnection(**self.pg_config)
        self._connections_tested = False

    def test_connections(self) -> Tuple[bool, bool]:
        """Test both database connections"""
        ch_status = self.clickhouse.connect()
        pg_status = self.puppygraph.connect()
        self._connections_tested = True
        return ch_status, pg_status

    def execute_customer_analysis(self, persona_id: str, parameters: Dict) -> Tuple[QueryResult, QueryResult]:
        """Execute customer analysis queries on both databases"""

        # Build ClickHouse transaction analysis query
        ch_query = self._build_clickhouse_customer_query(persona_id, parameters)

        # Build PuppyGraph network analysis query
        pg_query = self._build_puppygraph_network_query(persona_id, parameters)

        # Execute both queries
        ch_result = self.clickhouse.execute_query(ch_query, parameters)
        pg_result = self.puppygraph.execute_query(pg_query, parameters)

        return ch_result, pg_result

    def _build_clickhouse_customer_query(self, persona_id: str, parameters: Dict) -> str:
        """Build ClickHouse SQL query for customer transactions"""
        date_start = parameters.get('date_start', '2024-01-01')
        date_end = parameters.get('date_end', '2024-12-31')
        min_amount = parameters.get('min_amount', 0)
        max_amount = parameters.get('max_amount', 10000)

        return f"""
        SELECT
            customer_id,
            transaction_date,
            product_name,
            amount,
            channel,
            category
        FROM customer_transactions
        WHERE customer_id = '{persona_id}'
          AND transaction_date >= '{date_start}'
          AND transaction_date <= '{date_end}'
          AND amount >= {min_amount}
          AND amount <= {max_amount}
        ORDER BY transaction_date DESC
        LIMIT 100
        """

    def _build_puppygraph_network_query(self, persona_id: str, parameters: Dict) -> str:
        """Build PuppyGraph Cypher query for network analysis"""
        network_depth = parameters.get('network_depth', 2)

        return f"""
        MATCH (c:Customer {{id: '{persona_id}'}})
        OPTIONAL MATCH (c)-[r:INFLUENCES|FOLLOWS|RECOMMENDS*1..{network_depth}]-(connected:Customer)
        WHERE r IS NOT NULL
        RETURN
            c.id as customer_id,
            c.name as customer_name,
            connected.id as connected_id,
            connected.name as connected_name,
            type(r[0]) as relationship_type,
            r[0].strength as influence_strength,
            r[0].interactions as interaction_count
        ORDER BY r[0].strength DESC
        LIMIT 50
        """

    def get_connection_status(self) -> Dict[str, Any]:
        """Get status of database connections"""
        if not self._connections_tested:
            ch_status, pg_status = self.test_connections()
        else:
            ch_status = self.clickhouse.client is not None
            pg_status = self.puppygraph.driver is not None

        return {
            'clickhouse': {
                'connected': ch_status,
                'host': self.ch_config['host'],
                'port': self.ch_config['port'],
                'database': self.ch_config['database']
            },
            'puppygraph': {
                'connected': pg_status,
                'uri': self.pg_config['uri']
            },
            'overall_status': 'ready' if (ch_status and pg_status) else 'partial' if (ch_status or pg_status) else 'disconnected'
        }

    def close_all_connections(self):
        """Close all database connections"""
        self.clickhouse.close()
        self.puppygraph.close()

# Global database manager instance
db_manager = DatabaseManager()