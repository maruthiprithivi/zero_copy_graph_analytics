# Customer 360 Demo

Clean and comprehensive Customer 360 solution using ClickHouse Cloud + PuppyGraph with one-click AWS deployment.

## Quick Start

1. **Configure:** Copy templates and add your credentials
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   cp .env.example .env
   ```

2. **Deploy:** Single command deployment to AWS
   ```bash
   ./deploy.sh
   ```

3. **Access:** Open your dashboards
   - Customer 360 Dashboard: `http://YOUR-EC2-IP:8501`
   - PuppyGraph UI: `http://YOUR-EC2-IP:8081`

## Architecture

```
                    ┌─────────────────┐
                    │  ClickHouse     │
                    │    Cloud        │
                    │ (External SaaS) │
                    │                 │
                    │ • Customer Data │
                    │ • Transactions  │
                    │ • Interactions  │
                    └────────▲────────┘
                             │
                             │ Queries data via
                             │ HTTPS/Port 8443
                             │
           ┌─────────────────┴─────────────────┐
           │         AWS EC2 Instance          │
           │          (r5.xlarge)              │
           │                                   │
           │  ┌──────────────┐  ┌──────────┐   │
           │  │  PuppyGraph  │  │ Streamlit│   │
           │  │ Graph Engine │◄─┤ Dashboard│   │
           │  │              │  │          │   │
           │  │ • Zero ETL   │  │ • UI     │   │
           │  │ • Cypher     │  │ • Charts │   │
           │  │ • Real-time  │  │ • Search │   │
           │  └──────────────┘  └──────────┘   │
           │                                   │
           │  • Docker Runtime                 │
           │  • Ubuntu 22.04                   │
           └───────────────────────────────────┘
                             │
                       External Access
                             │
                    ┌────────▼─────────┐
                    │      Users       │
                    │                  │
                    │ :8501 Streamlit  │
                    │ :8081 PuppyGraph │
                    └──────────────────┘
```

## Repository Structure

```
customer360-demo/
├── Python Application
│   ├── app.py              # Streamlit dashboard (5 pages: Dashboard, Search, Recommendations, Analytics, About)
│   ├── clickhouse.py       # ClickHouse operations (database setup, data loading, querying)
│   ├── queries.py          # Graph queries using Cypher (8 analytical methods)
│   ├── generator.py        # Synthetic data generation (scalable: 1M-100M customers)
│   └── data_pipeline.py    # End-to-end pipeline orchestration
│
├── Infrastructure & Deployment
│   ├── deploy.sh           # One-click deployment script with full automation
│   ├── main.tf             # Terraform main configuration (EC2, VPC, Security Groups)
│   ├── variables.tf        # Terraform variables with validation rules
│   ├── outputs.tf          # Terraform outputs (IPs, URLs, SSH commands)
│   ├── user_data.sh        # EC2 instance bootstrap script
│   └── terraform/          # Modular Terraform structure
│       ├── ec2/            # EC2 instance module
│       ├── iam/            # IAM roles and policies
│       └── networking/     # VPC, subnets, security groups
│
├── Configuration
│   ├── config/
│   │   └── puppygraph/
│   │       ├── schema.json         # Graph schema (5 vertices, 9 edges)
│   │       └── puppygraph.properties # PuppyGraph engine settings
│   ├── secrets/
│   │   ├── README.md              # Security and secret management guide
│   │   ├── .env.example           # Environment variables template
│   │   └── terraform.tfvars.example # Terraform configuration template
│   ├── .env.example               # Main environment template
│   └── terraform.tfvars.example   # Main Terraform template
│
├── Dependencies & Development
│   ├── requirements.txt    # Production dependencies (31 essential packages)
│   ├── pyproject.toml     # Development dependencies and tooling configuration
│   └── .gitignore         # Comprehensive ignore rules for secrets, cache, etc.
```

### Key Files Explained

**Core Application Files:**
- **app.py** (21KB): Multi-page Streamlit dashboard with customer search, 360-degree view, recommendations, and analytics
- **clickhouse.py** (24KB): Complete ClickHouse integration with table management, data loading, and query execution
- **queries.py** (12KB): Graph analytics using Cypher queries for customer insights, recommendations, and relationship analysis
- **generator.py** (16KB): Synthetic data generator creating realistic customer, product, transaction, and interaction data
- **data_pipeline.py** (10KB): Orchestrates the entire data generation and ingestion process

**Infrastructure Files:**
- **deploy.sh** (10KB): Comprehensive deployment automation with prerequisite checking, infrastructure deployment, and application setup
- **main.tf**: AWS infrastructure definition supporting both new and existing VPC deployment
- **user_data.sh**: EC2 bootstrap script for Docker, PuppyGraph, and system setup

**Configuration Files:**
- **schema.json** (650 lines): Complete graph schema defining Customer, Product, Transaction, Interaction, and SupportTicket vertices with their relationships
- **puppygraph.properties**: PuppyGraph engine configuration for ClickHouse connectivity and performance optimization

## Features

### Data Generation
- **Scalable:** Generate 1M, 10M, or 100M customer records
- **Realistic:** Using Faker library for authentic customer profiles, transactions, and interactions
- **Optimized:** Batch processing and Parquet format for efficient storage and loading

### Graph Analytics  
- **Real-time Queries:** Live graph traversals using Cypher queries
- **Customer 360:** Complete customer view with purchase history, interactions, and relationships
- **Recommendations:** Product recommendations based on customer behavior and similar customers
- **Segment Analysis:** Customer segmentation and behavior analysis

### Interactive Dashboard
- **Multi-page UI:** 5 comprehensive pages for different analytical views
- **Search & Filter:** Advanced customer and product search capabilities
- **Visualizations:** Interactive charts and graphs using Plotly
- **Real-time Updates:** Live data updates with caching for performance

### Cloud-Native Architecture
- **ClickHouse Cloud:** Managed analytics database for high-performance queries
- **PuppyGraph:** Zero-ETL graph engine for real-time graph analytics
- **AWS Deployment:** Automated EC2 deployment with proper security configuration
- **Docker Runtime:** Containerized services for easy management

## Installation & Deployment

### Prerequisites

Before deployment, ensure you have:

- **AWS CLI configured** with valid credentials
- **Terraform installed** (version 1.0+)
- **SSH access** configured for your AWS account
- **ClickHouse Cloud instance** with credentials
- **Valid AWS credentials** with EC2, VPC, and IAM permissions

### Configuration Setup

1. **Copy configuration templates:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   cp .env.example .env
   ```

2. **Edit terraform.tfvars with your AWS and ClickHouse details:**
   ```hcl
   aws_region = "us-east-1"
   instance_type = "r5.xlarge"
   
   # ClickHouse Cloud Configuration
   clickhouse_host = "your-cluster.clickhouse.cloud"
   clickhouse_password = "your-secure-password"
   
   # Security Configuration  
   owner_email = "your-email@company.com"
   allowed_ssh_ips = ["YOUR-IP/32"]  # Your IP for SSH access
   
   # Data Scale Configuration
   customer_scale = 1000000  # 1M customers (options: 1000000, 10000000, 100000000)
   ```

3. **Edit .env with application settings:**
   ```bash
   CLICKHOUSE_HOST=your-cluster.clickhouse.cloud
   CLICKHOUSE_PORT=8443
   CLICKHOUSE_PASSWORD=your-secure-password
   CLICKHOUSE_DATABASE=customer360
   
   PUPPYGRAPH_HOST=localhost
   PUPPYGRAPH_PASSWORD=secure-puppygraph-password
   
   CUSTOMER_SCALE=1000000
   ```

### Deployment Options

#### Option 1: Full Automated Deployment (Recommended)
```bash
./deploy.sh
```

This single command will:
1. Check all prerequisites
2. Deploy AWS infrastructure via Terraform
3. Wait for EC2 instance to be ready
4. Upload and configure the application
5. Generate sample data
6. Load data into ClickHouse
7. Start all services
8. Provide access URLs

#### Option 2: Step-by-Step Deployment
```bash
# Check prerequisites only
./deploy.sh check

# Deploy infrastructure only
./deploy.sh infra

# Generate and load data only
./deploy.sh data

# Start services only
./deploy.sh start

# Check deployment status
./deploy.sh status
```

### VPC Configuration Options

**Using Existing VPC (Cost-effective):**
```hcl
use_existing_vpc = true
existing_vpc_id = "vpc-xxxxxxxxx"
existing_subnet_id = "subnet-xxxxxxxxx"
```

**Creating New VPC:**
```hcl
use_existing_vpc = false
vpc_cidr = "10.0.0.0/16"
subnet_cidr = "10.0.1.0/24"
```

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CLICKHOUSE_HOST` | ClickHouse Cloud endpoint | - | Yes |
| `CLICKHOUSE_PORT` | ClickHouse port | 8443 | No |
| `CLICKHOUSE_PASSWORD` | Database password | - | Yes |
| `CLICKHOUSE_DATABASE` | Target database name | customer360 | No |
| `PUPPYGRAPH_HOST` | PuppyGraph host | localhost | No |
| `PUPPYGRAPH_PASSWORD` | PuppyGraph admin password | - | Yes |
| `CUSTOMER_SCALE` | Number of customers to generate | 1000000 | No |

### Terraform Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `aws_region` | AWS deployment region | us-east-1 | No |
| `instance_type` | EC2 instance type | r5.xlarge | No |
| `clickhouse_host` | ClickHouse Cloud endpoint | - | Yes |
| `clickhouse_password` | ClickHouse password | - | Yes |
| `owner_email` | Email for resource tagging | - | Yes |
| `allowed_ssh_ips` | IPs allowed for SSH access | - | Yes |
| `customer_scale` | Customer data scale | 1000000 | No |

### Scale Options

Choose your data scale based on testing needs:

- **1M customers (1,000,000)**: Standard demo, fast generation (~10 minutes)
- **10M customers (10,000,000)**: Large-scale demo, moderate generation (~30 minutes)  
- **100M customers (100,000,000)**: Enterprise-scale demo, extended generation (~2 hours)

Update `CUSTOMER_SCALE` in both terraform.tfvars and .env files.

## Usage Examples

### Dashboard Navigation

**Customer 360 Dashboard (http://EC2-IP:8501):**
1. **Dashboard Page**: Overview metrics, customer segments, popular products
2. **Customer Search**: Search customers by name or email, view detailed profiles
3. **Recommendations**: Product recommendations based on customer behavior
4. **Analytics**: Advanced analytics including customer journeys and category affinity
5. **About**: System information and data statistics

### Manual Operations

**Generate Data Locally:**
```bash
python3 generator.py --scale 1000000 --output data
```

**Load Data into ClickHouse:**
```bash
python3 clickhouse.py --init --load --schema --status
```

**Run Sample Graph Queries:**
```bash
python3 queries.py
```

**Start Dashboard Locally:**
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Graph Query Examples

The system includes these analytical capabilities:

- **Customer 360 View**: Complete customer profile with purchase history and interactions
- **Product Recommendations**: Based on similar customer behavior and purchase patterns
- **Customer Journey Analysis**: Track customer interactions and purchase paths
- **Segment Analysis**: Customer segmentation based on lifetime value and behavior
- **Category Affinity**: Identify customer preferences across product categories
- **Similar Customer Discovery**: Find customers with similar purchase patterns

## Troubleshooting

### Common Issues

**1. ClickHouse Connection Fails**
```bash
# Test connection manually
ping your-clickhouse-host
telnet your-clickhouse-host 8443

# Check credentials in .env file
# Verify ClickHouse Cloud instance is running
```

**2. SSH Access Denied**
```bash
# Check your current IP
curl -s https://checkip.amazonaws.com/

# Update allowed_ssh_ips in terraform.tfvars
# Redeploy: terraform apply
```

**3. EC2 Instance Not Ready**
```bash
# Check instance logs
ssh -i customer360-key.pem ubuntu@EC2-IP 'tail -f /var/log/user-data.log'

# Check services status
ssh -i customer360-key.pem ubuntu@EC2-IP 'docker ps'
```

**4. Services Not Starting**
```bash
# Restart PuppyGraph
ssh -i customer360-key.pem ubuntu@EC2-IP 'docker restart puppygraph'

# Restart Streamlit
ssh -i customer360-key.pem ubuntu@EC2-IP 'cd /opt/customer360 && streamlit run app.py --server.port 8501 --server.address 0.0.0.0'
```

**5. Data Generation Issues**
```bash
# Check disk space
df -h

# Monitor generation progress
tail -f data_generation.log

# Restart generation with smaller scale
python3 generator.py --scale 100000
```

### Service Management

**Check Service Status:**
```bash
# All services
ssh ubuntu@EC2-IP 'docker ps && ps aux | grep streamlit'

# PuppyGraph logs
ssh ubuntu@EC2-IP 'docker logs puppygraph'

# Application logs
ssh ubuntu@EC2-IP 'tail -f /opt/customer360/streamlit.log'
```

**Restart Services:**
```bash
# Restart PuppyGraph
ssh ubuntu@EC2-IP 'docker restart puppygraph'

# Restart Dashboard
ssh ubuntu@EC2-IP 'pkill -f streamlit && cd /opt/customer360 && nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &'
```

### Infrastructure Issues

**Terraform Problems:**
```bash
# Reinitialize Terraform
terraform init -upgrade

# Check state
terraform show

# Fix state issues
terraform refresh
```

**AWS Resource Issues:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify region
aws configure get region

# Check resource limits
aws ec2 describe-account-attributes
```

### Performance Optimization

**For Large Datasets:**
- Increase EC2 instance size to `r5.2xlarge` or larger
- Use `c5.4xlarge` for CPU-intensive data generation
- Enable batch processing for data ingestion
- Configure ClickHouse connection pooling

**For High Availability:**
- Deploy in multiple availability zones
- Set up Application Load Balancer
- Configure auto-scaling groups
- Implement health checks

## Development

### Local Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd customer360-demo

# Install dependencies
pip install -r requirements.txt

# For development with full tooling
pip install -e .

# Run tests
pytest

# Code formatting
black .
ruff check .
```

### Development Tools

The project includes comprehensive development tooling:

- **Testing**: pytest with coverage reporting
- **Code Formatting**: black for consistent code style  
- **Linting**: ruff for fast Python linting
- **Type Checking**: mypy for static type checking
- **Pre-commit Hooks**: Automated code quality checks

### Project Structure for Development

When working on the codebase:

- **app.py**: Main Streamlit application - add new pages or modify existing ones
- **queries.py**: Graph analytical queries - add new Cypher queries for insights
- **generator.py**: Data generation - modify data patterns or add new data types
- **clickhouse.py**: Database operations - extend table schemas or optimize queries
- **config/puppygraph/schema.json**: Graph schema - add new vertices or edges

### Contributing Guidelines

1. **Follow Python coding standards**: Use black, ruff, and mypy
2. **Add tests**: All new features should include appropriate tests  
3. **Update documentation**: Modify this README for any new features or changes
4. **Security first**: Never commit credentials or sensitive information
5. **Performance aware**: Consider impact of changes on data generation and query performance

## Cleanup

**Destroy Infrastructure:**
```bash
./deploy.sh destroy
```

**Manual Cleanup:**
```bash
# Remove AWS resources
terraform destroy

# Clean local files  
rm -rf data/
rm -f customer360-key.pem
rm -f terraform.tfstate*
```

## Security Considerations

- All secrets are managed through template files and environment variables
- SSH access is restricted to specified IP addresses
- ClickHouse connections use SSL/TLS encryption
- AWS resources are tagged for proper resource management
- Security groups follow principle of least privilege

For detailed security configuration, see `secrets/README.md`.