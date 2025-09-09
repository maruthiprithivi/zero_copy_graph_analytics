# Customer 360 Demo - Simplified Terraform Infrastructure
# Single file deployment for ClickHouse + PuppyGraph on AWS

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project   = var.project_prefix
      ManagedBy = "Terraform"
      Owner     = var.owner_email
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Data sources for existing VPC (if using existing)
data "aws_vpc" "existing" {
  count = var.use_existing_vpc ? 1 : 0
  id    = var.existing_vpc_id
}

data "aws_subnet" "existing" {
  count = var.use_existing_vpc ? 1 : 0
  id    = var.existing_subnet_id
}

# VPC and networking (create new VPC only if not using existing)
resource "aws_vpc" "main" {
  count = var.use_existing_vpc ? 0 : 1

  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_prefix}-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  count  = var.use_existing_vpc ? 0 : 1
  vpc_id = aws_vpc.main[0].id

  tags = {
    Name = "${var.project_prefix}-igw"
  }
}

resource "aws_subnet" "public" {
  count = var.use_existing_vpc ? 0 : 1

  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = var.subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_prefix}-public-subnet"
  }
}

resource "aws_route_table" "public" {
  count  = var.use_existing_vpc ? 0 : 1
  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }

  tags = {
    Name = "${var.project_prefix}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count = var.use_existing_vpc ? 0 : 1

  subnet_id      = aws_subnet.public[0].id
  route_table_id = aws_route_table.public[0].id
}

# Local values to reference VPC/subnet regardless of source
locals {
  vpc_id    = var.use_existing_vpc ? data.aws_vpc.existing[0].id : aws_vpc.main[0].id
  subnet_id = var.use_existing_vpc ? data.aws_subnet.existing[0].id : aws_subnet.public[0].id
}

# Security group
resource "aws_security_group" "main" {
  name        = "${var.project_prefix}-sg"
  description = "Security group for Customer 360 demo"
  vpc_id      = local.vpc_id

  # SSH access
  dynamic "ingress" {
    for_each = var.allowed_ssh_ips
    content {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
      description = "SSH from ${ingress.value}"
    }
  }

  # Streamlit
  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = var.allowed_app_ips
    description = "Streamlit dashboard"
  }

  # PuppyGraph Web UI
  ingress {
    from_port   = 8081
    to_port     = 8081
    protocol    = "tcp"
    cidr_blocks = var.allowed_app_ips
    description = "PuppyGraph Web UI"
  }

  # PuppyGraph Cypher
  ingress {
    from_port   = 7687
    to_port     = 7687
    protocol    = "tcp"
    cidr_blocks = var.allowed_app_ips
    description = "PuppyGraph Cypher"
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_prefix}-sg"
  }
}

# SSH key pair
resource "aws_key_pair" "main" {
  key_name   = var.key_pair_name
  public_key = tls_private_key.main.public_key_openssh

  tags = {
    Name = var.key_pair_name
  }
}

resource "tls_private_key" "main" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_file" "private_key" {
  content         = tls_private_key.main.private_key_pem
  filename        = "${var.key_pair_name}.pem"
  file_permission = "0600"
}

# EC2 instance
resource "aws_instance" "main" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.main.key_name
  subnet_id              = local.subnet_id
  vpc_security_group_ids = [aws_security_group.main.id]

  user_data = templatefile("${path.module}/user_data.sh", {
    clickhouse_host     = var.clickhouse_host
    clickhouse_password = var.clickhouse_password
    customer_scale      = var.customer_scale
  })

  root_block_device {
    volume_type = var.root_volume_type
    volume_size = var.root_volume_size
    encrypted   = true
  }

  tags = {
    Name = "${var.project_prefix}-server"
  }
}

