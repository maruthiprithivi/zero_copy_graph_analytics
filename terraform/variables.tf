# Terraform Variables for Customer 360 Demo Infrastructure
# Comprehensive variable definitions with validation and descriptions

#============================================================================
# General Configuration Variables
#============================================================================

variable "project_name" {
  description = "Name of the project used for resource naming"
  type        = string
  default     = "customer360-demo"
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "aws_region" {
  description = "AWS region for infrastructure deployment"
  type        = string
  default     = "us-west-2"
  
  validation {
    condition = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "AWS region must be a valid region format (e.g., us-west-2)."
  }
}

variable "environment" {
  description = "Environment name (dev/staging/prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "owner_email" {
  description = "Email of the infrastructure owner for tagging and notifications"
  type        = string
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.owner_email))
    error_message = "Owner email must be a valid email address."
  }
}

variable "aws_assume_role_arn" {
  description = "ARN of IAM role to assume for cross-account deployments"
  type        = string
  default     = ""
}

#============================================================================
# EC2 Instance Configuration
#============================================================================

variable "instance_type" {
  description = "EC2 instance type for PuppyGraph deployment"
  type        = string
  default     = "r5.2xlarge"  # 8 vCPUs, 64 GB RAM - optimal for PuppyGraph production workloads
  
  validation {
    condition = can(regex("^[a-z][0-9]+[a-z]*\\.[a-z0-9]+$", var.instance_type))
    error_message = "Instance type must be a valid EC2 instance type format."
  }
}

variable "root_volume_size" {
  description = "Size of root EBS volume in GB"
  type        = number
  default     = 100
  
  validation {
    condition     = var.root_volume_size >= 50 && var.root_volume_size <= 1000
    error_message = "Root volume size must be between 50 and 1000 GB."
  }
}

variable "root_volume_type" {
  description = "Type of EBS root volume"
  type        = string
  default     = "gp3"
  
  validation {
    condition     = contains(["gp2", "gp3", "io1", "io2"], var.root_volume_type)
    error_message = "Root volume type must be one of: gp2, gp3, io1, io2."
  }
}

variable "root_volume_iops" {
  description = "IOPS for root volume (only for gp3, io1, io2)"
  type        = number
  default     = 3000
  
  validation {
    condition     = var.root_volume_iops >= 100 && var.root_volume_iops <= 16000
    error_message = "Root volume IOPS must be between 100 and 16000."
  }
}

variable "root_volume_throughput" {
  description = "Throughput for root volume in MB/s (only for gp3)"
  type        = number
  default     = 250
  
  validation {
    condition     = var.root_volume_throughput >= 125 && var.root_volume_throughput <= 1000
    error_message = "Root volume throughput must be between 125 and 1000 MB/s."
  }
}

variable "enable_monitoring" {
  description = "Enable detailed CloudWatch monitoring for EC2 instances"
  type        = bool
  default     = true
}

variable "enable_eip" {
  description = "Enable Elastic IP for consistent public IP (recommended for production)"
  type        = bool
  default     = false  # Set to true for production environments
}

#============================================================================
# ClickHouse Cloud Configuration
#============================================================================

variable "clickhouse_host" {
  description = "ClickHouse Cloud host endpoint"
  type        = string
  sensitive   = true
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.clickhouse_host))
    error_message = "ClickHouse host must be a valid hostname."
  }
}

variable "clickhouse_port" {
  description = "ClickHouse Cloud port (typically 8443 for secure connections)"
  type        = number
  default     = 8443
  sensitive   = true
  
  validation {
    condition     = var.clickhouse_port > 0 && var.clickhouse_port <= 65535
    error_message = "ClickHouse port must be between 1 and 65535."
  }
}

variable "clickhouse_user" {
  description = "ClickHouse username"
  type        = string
  default     = "default"
  sensitive   = true
}

variable "clickhouse_password" {
  description = "ClickHouse password"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.clickhouse_password) >= 8
    error_message = "ClickHouse password must be at least 8 characters long."
  }
}

variable "clickhouse_database" {
  description = "ClickHouse database name"
  type        = string
  default     = "customer360"
  
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.clickhouse_database))
    error_message = "ClickHouse database name must start with letter and contain only letters, numbers, and underscores."
  }
}

#============================================================================
# PuppyGraph Configuration
#============================================================================

variable "puppygraph_username" {
  description = "PuppyGraph admin username"
  type        = string
  default     = "puppygraph"
  
  validation {
    condition     = length(var.puppygraph_username) >= 3
    error_message = "PuppyGraph username must be at least 3 characters long."
  }
}

variable "puppygraph_password" {
  description = "PuppyGraph admin password"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.puppygraph_password) >= 12
    error_message = "PuppyGraph password must be at least 12 characters long for security."
  }
}

variable "puppygraph_memory_limit" {
  description = "Memory limit for PuppyGraph JVM in GB"
  type        = number
  default     = 32  # Appropriate for r5.2xlarge with 64GB total RAM
  
  validation {
    condition     = var.puppygraph_memory_limit >= 4 && var.puppygraph_memory_limit <= 128
    error_message = "PuppyGraph memory limit must be between 4 and 128 GB."
  }
}

#============================================================================
# Data Scale Configuration
#============================================================================

variable "customer_scale" {
  description = "Number of customers to generate for the demo"
  type        = number
  default     = 1000000
  
  validation {
    condition     = contains([1000000, 10000000, 100000000], var.customer_scale)
    error_message = "Customer scale must be one of: 1000000 (1M), 10000000 (10M), or 100000000 (100M)."
  }
}

variable "batch_size" {
  description = "Batch size for data generation and loading operations"
  type        = number
  default     = 10000
  
  validation {
    condition     = var.batch_size >= 1000 && var.batch_size <= 100000
    error_message = "Batch size must be between 1000 and 100000."
  }
}

#============================================================================
# Networking and Security Configuration
#============================================================================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones (leave empty for automatic selection)"
  type        = list(string)
  default     = []
}

variable "ssh_key_name" {
  description = "Name of existing SSH key pair for EC2 access (leave empty to create new key pair)"
  type        = string
  default     = ""
}

variable "allowed_ssh_cidrs" {
  description = "List of CIDR blocks allowed to SSH to EC2 instances"
  type        = list(string)
  default     = []
  
  validation {
    condition = alltrue([
      for cidr in var.allowed_ssh_cidrs : can(cidrhost(cidr, 0))
    ])
    error_message = "All SSH CIDR blocks must be valid IPv4 CIDR blocks."
  }
}

variable "allowed_app_cidrs" {
  description = "List of CIDR blocks allowed to access applications (Streamlit, PuppyGraph)"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict this in production environments
  
  validation {
    condition = alltrue([
      for cidr in var.allowed_app_cidrs : can(cidrhost(cidr, 0))
    ])
    error_message = "All application CIDR blocks must be valid IPv4 CIDR blocks."
  }
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs for network monitoring"
  type        = bool
  default     = true
}

#============================================================================
# Application Configuration
#============================================================================

variable "streamlit_port" {
  description = "Port for Streamlit application"
  type        = number
  default     = 8501
  
  validation {
    condition     = var.streamlit_port > 1024 && var.streamlit_port <= 65535
    error_message = "Streamlit port must be between 1025 and 65535."
  }
}

variable "puppygraph_web_port" {
  description = "Port for PuppyGraph Web UI"
  type        = number
  default     = 8081
  
  validation {
    condition     = var.puppygraph_web_port > 1024 && var.puppygraph_web_port <= 65535
    error_message = "PuppyGraph web port must be between 1025 and 65535."
  }
}

variable "puppygraph_cypher_port" {
  description = "Port for PuppyGraph Cypher endpoint"
  type        = number
  default     = 7687
  
  validation {
    condition     = var.puppygraph_cypher_port > 1024 && var.puppygraph_cypher_port <= 65535
    error_message = "PuppyGraph Cypher port must be between 1025 and 65535."
  }
}

variable "puppygraph_gremlin_port" {
  description = "Port for PuppyGraph Gremlin endpoint"
  type        = number
  default     = 8182
  
  validation {
    condition     = var.puppygraph_gremlin_port > 1024 && var.puppygraph_gremlin_port <= 65535
    error_message = "PuppyGraph Gremlin port must be between 1025 and 65535."
  }
}

#============================================================================
# Monitoring and Logging Configuration
#============================================================================

variable "enable_cloudwatch_logs" {
  description = "Enable CloudWatch logs for application monitoring"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 14
  
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention period."
  }
}

variable "enable_performance_insights" {
  description = "Enable performance monitoring and insights"
  type        = bool
  default     = true
}

#============================================================================
# Backup and Disaster Recovery
#============================================================================

variable "enable_automated_backups" {
  description = "Enable automated backups for EC2 instances"
  type        = bool
  default     = false  # Set to true for production
}

variable "backup_retention_days" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 7
  
  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 365
    error_message = "Backup retention days must be between 1 and 365."
  }
}

#============================================================================
# Cost Optimization
#============================================================================

variable "enable_spot_instances" {
  description = "Use EC2 Spot instances for cost optimization (not recommended for production)"
  type        = bool
  default     = false
}

variable "spot_max_price" {
  description = "Maximum price for Spot instances (USD per hour)"
  type        = string
  default     = ""  # Use current Spot price if empty
}

#============================================================================
# Advanced Configuration
#============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "user_data_script_path" {
  description = "Path to custom user data script (relative to terraform directory)"
  type        = string
  default     = "modules/ec2/user_data.tpl"
}

variable "enable_termination_protection" {
  description = "Enable EC2 instance termination protection"
  type        = bool
  default     = false  # Set to true for production
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring (additional cost)"
  type        = bool
  default     = true
}