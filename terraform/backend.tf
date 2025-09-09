# Terraform Backend Configuration for Remote State Management
# Uses S3 for state storage and DynamoDB for state locking

# IMPORTANT: Before running terraform init, you must:
# 1. Create the S3 bucket manually or with a separate Terraform configuration
# 2. Create the DynamoDB table for state locking
# 3. Update the bucket name and region to match your setup

terraform {
  backend "s3" {
    # S3 bucket for storing Terraform state
    # Change this to your actual bucket name
    bucket = "customer360-terraform-state-CHANGE-ME"
    
    # Key path within the bucket
    key = "infrastructure/terraform.tfstate"
    
    # AWS region where the bucket is located
    # Change this to match your bucket's region
    region = "us-west-2"
    
    # Enable server-side encryption
    encrypt = true
    
    # DynamoDB table for state locking (prevents concurrent runs)
    # Change this to your actual table name
    dynamodb_table = "customer360-terraform-lock-CHANGE-ME"
    
    # Use the default AWS profile (or specify a different one)
    # profile = "default"
  }
}

# To set up the backend infrastructure, create these resources manually
# or use a separate bootstrap Terraform configuration:

# S3 Bucket for state storage:
# aws s3 mb s3://customer360-terraform-state-YOUR-UNIQUE-SUFFIX --region us-west-2
# aws s3api put-bucket-versioning --bucket customer360-terraform-state-YOUR-UNIQUE-SUFFIX --versioning-configuration Status=Enabled
# aws s3api put-bucket-encryption --bucket customer360-terraform-state-YOUR-UNIQUE-SUFFIX --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
# aws s3api put-public-access-block --bucket customer360-terraform-state-YOUR-UNIQUE-SUFFIX --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# DynamoDB table for locking:
# aws dynamodb create-table \
#   --table-name customer360-terraform-lock-YOUR-UNIQUE-SUFFIX \
#   --attribute-definitions AttributeName=LockID,AttributeType=S \
#   --key-schema AttributeName=LockID,KeyType=HASH \
#   --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
#   --region us-west-2

# Alternative: Use the bootstrap configuration below to create the backend resources

/*
# Bootstrap configuration (run this first with local state)
# Save as backend-bootstrap.tf in a separate directory

provider "aws" {
  region = "us-west-2"  # Change to your preferred region
}

# Generate a random suffix for unique naming
resource "random_id" "suffix" {
  byte_length = 4
}

# S3 bucket for Terraform state
resource "aws_s3_bucket" "terraform_state" {
  bucket = "customer360-terraform-state-${random_id.suffix.hex}"
  
  tags = {
    Name        = "Customer360 Terraform State"
    Environment = "shared"
    Purpose     = "terraform-backend"
  }
}

# Enable versioning for state history
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption at rest
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_lock" {
  name           = "customer360-terraform-lock-${random_id.suffix.hex}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "Customer360 Terraform Lock"
    Environment = "shared"
    Purpose     = "terraform-backend"
  }
}

# Output the backend configuration
output "backend_config" {
  value = {
    bucket         = aws_s3_bucket.terraform_state.bucket
    dynamodb_table = aws_dynamodb_table.terraform_lock.name
    region         = "us-west-2"
  }
}

output "backend_configuration_hcl" {
  value = <<-EOT
    terraform {
      backend "s3" {
        bucket         = "${aws_s3_bucket.terraform_state.bucket}"
        key            = "infrastructure/terraform.tfstate"
        region         = "us-west-2"
        encrypt        = true
        dynamodb_table = "${aws_dynamodb_table.terraform_lock.name}"
      }
    }
  EOT
}
*/