#!/bin/bash
# Simple EC2 setup script for Customer 360 Demo

set -e
exec > >(tee /var/log/user-data.log) 2>&1

echo "Starting Customer 360 setup at $(date)"

# Update system
apt-get update -y

# Install essential packages
apt-get install -y docker.io python3-pip git curl

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Start Docker
systemctl enable docker
systemctl start docker

# Install Python dependencies
pip3 install -r /dev/stdin << 'EOF'
pandas==2.2.0
numpy==1.26.3
clickhouse-driver==0.2.6
neo4j==5.17.0
faker==24.0.0
streamlit==1.31.0
plotly==5.19.0
python-dotenv==1.0.1
pydantic==2.6.1
tqdm==4.66.2
requests==2.31.0
EOF

# Create app directory
mkdir -p /opt/customer360
chown -R ubuntu:ubuntu /opt/customer360

# Create environment file
cat > /opt/customer360/.env << EOF
CLICKHOUSE_HOST=${clickhouse_host}
CLICKHOUSE_PORT=8443
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=${clickhouse_password}
CLICKHOUSE_DATABASE=customer360
PUPPYGRAPH_HOST=localhost
PUPPYGRAPH_PASSWORD=puppygraph123
CUSTOMER_SCALE=${customer_scale}
STREAMLIT_PORT=8501
EOF

chown ubuntu:ubuntu /opt/customer360/.env

# Start PuppyGraph using Docker
docker run -d \
  --name puppygraph \
  --restart unless-stopped \
  -p 8081:8081 \
  -p 7687:7687 \
  -p 8182:8182 \
  -e PUPPYGRAPH_PASSWORD=puppygraph123 \
  puppygraph/puppygraph:stable

echo "Setup completed at $(date)"
echo "PuppyGraph will be available at port 8081"
echo "Waiting for application deployment..."