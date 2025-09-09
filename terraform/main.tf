# Main Terraform configuration for Customer 360 Demo Infrastructure
# Deploys complete AWS infrastructure for ClickHouse + PuppyGraph demo

#============================================================================
# Local Variables and Data Sources
#============================================================================

locals {
  # Common naming convention
  common_name = "${var.project_name}-${var.environment}"
  
  # Consolidated tags for all resources
  common_tags = merge(
    {
      Project             = var.project_name
      Environment         = var.environment
      ManagedBy          = "Terraform"
      Owner              = var.owner_email
      CreatedAt          = timestamp()
      CustomerScale      = var.customer_scale
      ClickHouseHost     = var.clickhouse_host
      # 2025 compliance and governance tags
      DataClassification = "Internal"
      BackupRequired     = var.enable_automated_backups ? "true" : "false"
      MonitoringEnabled  = var.enable_monitoring ? "true" : "false"
      CostCenter         = var.environment == "prod" ? "Production" : "Development"
    },
    var.additional_tags
  )
  
  # Calculate optimal subnet configuration based on AZs
  azs = length(var.availability_zones) > 0 ? var.availability_zones : slice(data.aws_availability_zones.available.names, 0, min(3, length(data.aws_availability_zones.available.names)))
  
  # Generate subnet CIDRs dynamically
  public_subnet_cidrs  = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 8, i + 101)]
  private_subnet_cidrs = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 8, i + 1)]
}

# Data source for available AZs
data "aws_availability_zones" "available" {
  state = "available"
}

# Data source for latest Ubuntu 22.04 LTS AMI
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

  filter {
    name   = "state"
    values = ["available"]
  }
}

# Current AWS account and region information
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

#============================================================================
# VPC and Networking Infrastructure
#============================================================================

# VPC using terraform-aws-modules for best practices
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${local.common_name}-vpc"
  cidr = var.vpc_cidr

  azs             = local.azs
  private_subnets = local.private_subnet_cidrs
  public_subnets  = local.public_subnet_cidrs

  # Internet connectivity
  enable_nat_gateway     = true
  single_nat_gateway     = var.environment != "prod" # Multiple NAT gateways for prod
  enable_vpn_gateway     = false
  enable_dns_hostnames   = true
  enable_dns_support     = true
  
  # Enhanced networking features for 2025
  enable_dhcp_options              = true
  dhcp_options_domain_name         = "${var.aws_region}.compute.internal"
  dhcp_options_domain_name_servers = ["AmazonProvidedDNS"]

  # VPC Flow Logs for security monitoring
  enable_flow_log                      = var.enable_vpc_flow_logs
  create_flow_log_cloudwatch_iam_role  = var.enable_vpc_flow_logs
  create_flow_log_cloudwatch_log_group = var.enable_vpc_flow_logs
  flow_log_cloudwatch_log_group_retention_in_days = var.log_retention_days

  # Security enhancements
  map_public_ip_on_launch = false # Only specific subnets get public IPs

  tags = local.common_tags
  
  # Subnet-specific tags
  public_subnet_tags = merge(local.common_tags, {
    Type = "public"
    Tier = "dmz"
  })
  
  private_subnet_tags = merge(local.common_tags, {
    Type = "private"
    Tier = "application"
  })
}

#============================================================================
# Security Groups
#============================================================================

# Main security group for EC2 instances
module "security_group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "${local.common_name}-main-sg"
  description = "Security group for Customer 360 EC2 instances"
  vpc_id      = module.vpc.vpc_id

  # SSH access (restricted to specific CIDRs)
  ingress_with_cidr_blocks = concat(
    length(var.allowed_ssh_cidrs) > 0 ? [
      for cidr in var.allowed_ssh_cidrs : {
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        description = "SSH access from ${cidr}"
        cidr_blocks = cidr
      }
    ] : [],
    [
      # Streamlit application
      {
        from_port   = var.streamlit_port
        to_port     = var.streamlit_port
        protocol    = "tcp"
        description = "Streamlit Customer 360 Dashboard"
        cidr_blocks = join(",", var.allowed_app_cidrs)
      },
      # PuppyGraph Web UI
      {
        from_port   = var.puppygraph_web_port
        to_port     = var.puppygraph_web_port
        protocol    = "tcp"
        description = "PuppyGraph Web UI"
        cidr_blocks = join(",", var.allowed_app_cidrs)
      },
      # PuppyGraph Cypher endpoint (Neo4j Bolt protocol)
      {
        from_port   = var.puppygraph_cypher_port
        to_port     = var.puppygraph_cypher_port
        protocol    = "tcp"
        description = "PuppyGraph Cypher/Bolt endpoint"
        cidr_blocks = join(",", var.allowed_app_cidrs)
      },
      # PuppyGraph Gremlin endpoint
      {
        from_port   = var.puppygraph_gremlin_port
        to_port     = var.puppygraph_gremlin_port
        protocol    = "tcp"
        description = "PuppyGraph Gremlin endpoint"
        cidr_blocks = join(",", var.allowed_app_cidrs)
      }
    ]
  )

  # Allow all outbound traffic
  egress_rules = ["all-all"]

  tags = merge(local.common_tags, {
    Name = "${local.common_name}-main-sg"
    Type = "security-group"
  })
}

# Additional security group for internal communication
resource "aws_security_group" "internal" {
  name        = "${local.common_name}-internal-sg"
  description = "Internal communication security group"
  vpc_id      = module.vpc.vpc_id

  # Allow all internal traffic within the VPC
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "Internal VPC communication"
  }

  # Allow ICMP for ping and troubleshooting
  ingress {
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = [var.vpc_cidr]
    description = "ICMP within VPC"
  }

  tags = merge(local.common_tags, {
    Name = "${local.common_name}-internal-sg"
    Type = "security-group"
  })
}

#============================================================================
# SSH Key Pair Management
#============================================================================

# SSH key pair (create new or use existing)
module "key_pair" {
  source  = "terraform-aws-modules/key-pair/aws"
  version = "~> 2.0"

  key_name           = var.ssh_key_name != "" ? var.ssh_key_name : "${local.common_name}-key"
  create_private_key = var.ssh_key_name == ""
  
  # Save private key locally for easy access
  private_key_algorithm = "RSA"
  private_key_rsa_bits  = 4096

  tags = merge(local.common_tags, {
    Name = var.ssh_key_name != "" ? var.ssh_key_name : "${local.common_name}-key"
    Type = "ssh-key-pair"
  })
}

# Save private key to file if created
resource "local_file" "private_key" {
  count = var.ssh_key_name == "" ? 1 : 0
  
  content  = module.key_pair.private_key_pem
  filename = "${path.module}/../secrets/${local.common_name}-key.pem"
  
  # Secure file permissions
  file_permission = "0600"
}

#============================================================================
# IAM Roles and Policies
#============================================================================

# IAM module for EC2 permissions
module "iam" {
  source = "./modules/iam"
  
  project_name  = var.project_name
  environment   = var.environment
  common_tags   = local.common_tags
  
  # CloudWatch permissions for monitoring
  enable_cloudwatch_logs = var.enable_cloudwatch_logs
  
  # S3 permissions for backups (if enabled)
  enable_s3_backup = var.enable_automated_backups
  
  # Systems Manager permissions for maintenance
  enable_ssm = true
}

#============================================================================
# EC2 Instance
#============================================================================

# Main EC2 instance for Customer 360 demo
module "ec2_instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "~> 5.0"

  name = "${local.common_name}-server"

  # Instance configuration
  instance_type               = var.instance_type
  key_name                   = module.key_pair.key_pair_name
  monitoring                 = var.enable_detailed_monitoring
  vpc_security_group_ids     = [module.security_group.security_group_id, aws_security_group.internal.id]
  subnet_id                  = module.vpc.public_subnets[0]
  associate_public_ip_address = !var.enable_eip # Use public IP if no EIP
  
  # Use latest Ubuntu 22.04 LTS AMI
  ami = data.aws_ami.ubuntu.id

  # IAM instance profile for AWS service access
  iam_instance_profile = module.iam.instance_profile_name

  # Advanced instance configuration for 2025
  disable_api_termination = var.enable_termination_protection
  
  # Instance metadata service configuration (IMDSv2)
  metadata_options = {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # Enforce IMDSv2 for security
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }

  # User data script for automated setup
  user_data = templatefile("${path.module}/${var.user_data_script_path}", {
    # ClickHouse configuration
    clickhouse_host     = var.clickhouse_host
    clickhouse_port     = var.clickhouse_port
    clickhouse_user     = var.clickhouse_user
    clickhouse_password = var.clickhouse_password
    clickhouse_database = var.clickhouse_database
    
    # PuppyGraph configuration
    puppygraph_username = var.puppygraph_username
    puppygraph_password = var.puppygraph_password
    puppygraph_memory   = var.puppygraph_memory_limit
    
    # Application configuration
    customer_scale    = var.customer_scale
    batch_size       = var.batch_size
    streamlit_port   = var.streamlit_port
    
    # System configuration
    aws_region      = var.aws_region
    environment     = var.environment
    project_name    = var.project_name
    log_group_name  = var.enable_cloudwatch_logs ? aws_cloudwatch_log_group.main[0].name : ""
  })

  # EBS root volume configuration
  root_block_device = [
    {
      volume_type = var.root_volume_type
      volume_size = var.root_volume_size
      iops        = contains(["gp3", "io1", "io2"], var.root_volume_type) ? var.root_volume_iops : null
      throughput  = var.root_volume_type == "gp3" ? var.root_volume_throughput : null
      encrypted   = true
      kms_key_id  = aws_kms_key.main.arn
      
      tags = merge(local.common_tags, {
        Name = "${local.common_name}-root-volume"
        Type = "ebs-volume"
      })
    }
  ]

  tags = merge(local.common_tags, {
    Name = "${local.common_name}-server"
    Type = "ec2-instance"
    Role = "application-server"
  })
}

# Elastic IP for consistent public IP (optional)
resource "aws_eip" "main" {
  count = var.enable_eip ? 1 : 0
  
  instance = module.ec2_instance.id
  domain   = "vpc"

  # Prevent EIP from being destroyed before EC2 instance
  depends_on = [module.vpc.igw_id]

  tags = merge(local.common_tags, {
    Name = "${local.common_name}-eip"
    Type = "elastic-ip"
  })
}

#============================================================================
# KMS Key for Encryption
#============================================================================

# KMS key for EBS encryption
resource "aws_kms_key" "main" {
  description             = "KMS key for ${local.common_name} EBS encryption"
  deletion_window_in_days = 7
  
  tags = merge(local.common_tags, {
    Name = "${local.common_name}-kms-key"
    Type = "kms-key"
  })
}

resource "aws_kms_alias" "main" {
  name          = "alias/${local.common_name}-ebs"
  target_key_id = aws_kms_key.main.key_id
}

#============================================================================
# CloudWatch Monitoring
#============================================================================

# CloudWatch log group for application logs
resource "aws_cloudwatch_log_group" "main" {
  count = var.enable_cloudwatch_logs ? 1 : 0
  
  name              = "/aws/ec2/${local.common_name}"
  retention_in_days = var.log_retention_days
  
  tags = merge(local.common_tags, {
    Name = "${local.common_name}-log-group"
    Type = "cloudwatch-log-group"
  })
}

# CloudWatch dashboard for monitoring
resource "aws_cloudwatch_dashboard" "main" {
  count = var.enable_monitoring ? 1 : 0
  
  dashboard_name = "${local.common_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization", "InstanceId", module.ec2_instance.id],
            [".", "NetworkIn", ".", "."],
            [".", "NetworkOut", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "EC2 Instance Metrics"
          period  = 300
        }
      }
    ]
  })
}

#============================================================================
# Backup Configuration
#============================================================================

# AWS Backup vault and plan (if enabled)
resource "aws_backup_vault" "main" {
  count = var.enable_automated_backups ? 1 : 0
  
  name        = "${local.common_name}-backup-vault"
  kms_key_arn = aws_kms_key.main.arn
  
  tags = merge(local.common_tags, {
    Name = "${local.common_name}-backup-vault"
    Type = "backup-vault"
  })
}

resource "aws_backup_plan" "main" {
  count = var.enable_automated_backups ? 1 : 0
  
  name = "${local.common_name}-backup-plan"

  rule {
    rule_name         = "${local.common_name}-daily-backup"
    target_vault_name = aws_backup_vault.main[0].name
    schedule          = "cron(0 5 ? * * *)" # 5 AM UTC daily

    lifecycle {
      cold_storage_after = 30
      delete_after       = var.backup_retention_days
    }

    recovery_point_tags = merge(local.common_tags, {
      BackupType = "automated"
    })
  }
  
  tags = local.common_tags
}

# Backup selection
resource "aws_backup_selection" "main" {
  count = var.enable_automated_backups ? 1 : 0
  
  iam_role_arn = module.iam.backup_role_arn
  name         = "${local.common_name}-backup-selection"
  plan_id      = aws_backup_plan.main[0].id

  resources = [
    module.ec2_instance.arn
  ]
}

#============================================================================
# SNS Topic for Notifications
#============================================================================

resource "aws_sns_topic" "alerts" {
  name = "${local.common_name}-alerts"
  
  tags = merge(local.common_tags, {
    Name = "${local.common_name}-alerts"
    Type = "sns-topic"
  })
}

resource "aws_sns_topic_subscription" "email" {
  count = var.owner_email != "" ? 1 : 0
  
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.owner_email
}