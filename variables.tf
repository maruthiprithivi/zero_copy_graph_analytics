# Customer 360 Demo - Terraform Variables
# Clean variable definitions for flexible deployment

#============================================================================
# AWS Configuration
#============================================================================

variable "aws_profile" {
  description = "AWS profile to use for authentication"
  type        = string
  default     = "default"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "ap-southeast-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "AWS region must be a valid region format (e.g., us-west-2)."
  }
}

#============================================================================
# VPC Configuration - Support existing or new
#============================================================================

variable "use_existing_vpc" {
  description = "Whether to use an existing VPC (true) or create new one (false)"
  type        = bool
  default     = true
}

variable "existing_vpc_id" {
  description = "ID of existing VPC to use (required if use_existing_vpc is true)"
  type        = string
  default     = ""

  validation {
    condition     = var.use_existing_vpc == false || (var.use_existing_vpc == true && var.existing_vpc_id != "")
    error_message = "existing_vpc_id must be provided when use_existing_vpc is true."
  }
}

variable "existing_subnet_id" {
  description = "ID of existing public subnet to use (required if use_existing_vpc is true)"
  type        = string
  default     = ""

  validation {
    condition     = var.use_existing_vpc == false || (var.use_existing_vpc == true && var.existing_subnet_id != "")
    error_message = "existing_subnet_id must be provided when use_existing_vpc is true."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for new VPC (used only if use_existing_vpc is false)"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "subnet_cidr" {
  description = "CIDR block for new public subnet (used only if use_existing_vpc is false)"
  type        = string
  default     = "10.0.1.0/24"

  validation {
    condition     = can(cidrhost(var.subnet_cidr, 0))
    error_message = "Subnet CIDR must be a valid IPv4 CIDR block."
  }
}

#============================================================================
# Project Configuration
#============================================================================

variable "project_prefix" {
  description = "Prefix for all resource names"
  type        = string
  default     = "customer360"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_prefix))
    error_message = "Project prefix must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "owner_email" {
  description = "Owner email for resource tagging"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.owner_email))
    error_message = "Owner email must be a valid email address."
  }
}

#============================================================================
# EC2 Instance Configuration
#============================================================================

variable "instance_type" {
  description = "EC2 instance type for PuppyGraph deployment"
  type        = string
  default     = "r5.xlarge" # 4 vCPUs, 32 GB RAM

  validation {
    condition     = can(regex("^[a-z][0-9]+[a-z]*\\.[a-z0-9]+$", var.instance_type))
    error_message = "Instance type must be a valid EC2 instance type format."
  }
}

variable "key_pair_name" {
  description = "Name for the SSH key pair to be created"
  type        = string
  default     = "customer360-key"

  validation {
    condition     = can(regex("^[a-zA-Z0-9-_.]+$", var.key_pair_name))
    error_message = "Key pair name must contain only letters, numbers, hyphens, underscores, and dots."
  }
}

variable "root_volume_size" {
  description = "Size of root EBS volume in GB"
  type        = number
  default     = 50

  validation {
    condition     = var.root_volume_size >= 20 && var.root_volume_size <= 1000
    error_message = "Root volume size must be between 20 and 1000 GB."
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

variable "clickhouse_password" {
  description = "ClickHouse Cloud password"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.clickhouse_password) >= 8
    error_message = "ClickHouse password must be at least 8 characters long."
  }
}

variable "customer_scale" {
  description = "Number of customers to generate for the demo"
  type        = number
  default     = 1000000

  validation {
    condition     = contains([1000000, 10000000, 100000000], var.customer_scale)
    error_message = "Customer scale must be one of: 1000000 (1M), 10000000 (10M), or 100000000 (100M)."
  }
}

#============================================================================
# Network Security Configuration
#============================================================================

variable "allowed_ssh_ips" {
  description = "List of CIDR blocks allowed to SSH to EC2 instance"
  type        = list(string)

  validation {
    condition = length(var.allowed_ssh_ips) > 0 && alltrue([
      for cidr in var.allowed_ssh_ips : can(cidrhost(cidr, 0))
    ])
    error_message = "At least one SSH CIDR must be provided and all must be valid IPv4 CIDR blocks."
  }
}

variable "allowed_app_ips" {
  description = "List of CIDR blocks allowed to access applications (Streamlit, PuppyGraph)"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Restrict this in production

  validation {
    condition = alltrue([
      for cidr in var.allowed_app_ips : can(cidrhost(cidr, 0))
    ])
    error_message = "All application CIDR blocks must be valid IPv4 CIDR blocks."
  }
}