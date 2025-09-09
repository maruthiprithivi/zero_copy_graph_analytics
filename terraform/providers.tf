# AWS Provider configuration
# Configured for best practices and security in 2025

provider "aws" {
  region = var.aws_region
  
  # Default tags applied to all resources for consistent tagging
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner_email
      CreatedAt   = timestamp()
      # 2025 compliance tags
      DataClassification = "Internal"
      BackupRequired     = "true"
      MonitoringEnabled  = "true"
    }
  }
  
  # Assume role if specified (useful for cross-account deployments)
  dynamic "assume_role" {
    for_each = var.aws_assume_role_arn != "" ? [1] : []
    content {
      role_arn = var.aws_assume_role_arn
    }
  }
}

# Random provider for generating secure values
provider "random" {}

# TLS provider for SSH key management
provider "tls" {}

# Local provider for file operations
provider "local" {}

# Null provider for triggers and provisioners
provider "null" {}