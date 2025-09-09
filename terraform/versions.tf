# Terraform version and provider requirements
# Updated for 2025 with latest stable versions

terraform {
  # Require Terraform 1.5.0 or later for latest features and security updates
  required_version = ">= 1.5.0"
  
  required_providers {
    # AWS Provider - latest stable version for 2025
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # Use 5.x series for 2025 compatibility
    }
    
    # Random provider for generating secure passwords and IDs
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    
    # TLS provider for SSH key generation
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    
    # Local provider for file operations
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    
    # Null provider for provisioners and triggers
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}