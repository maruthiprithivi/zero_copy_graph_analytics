# Terraform Outputs for Customer 360 Demo
# Provides access to important resource information after deployment

#============================================================================
# EC2 Instance Information
#============================================================================

output "ec2_instance_id" {
  description = "ID of the EC2 instance running Customer 360 services"
  value       = module.ec2_instance.id
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = var.enable_eip ? aws_eip.main[0].public_ip : module.ec2_instance.public_ip
}

output "ec2_private_ip" {
  description = "Private IP address of the EC2 instance"
  value       = module.ec2_instance.private_ip
}

output "ec2_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = module.ec2_instance.public_dns
}

output "ec2_availability_zone" {
  description = "Availability zone where the EC2 instance is launched"
  value       = module.ec2_instance.availability_zone
}

output "ec2_instance_type" {
  description = "Instance type of the EC2 instance"
  value       = var.instance_type
}

#============================================================================
# SSH Access Information
#============================================================================

output "ssh_connection_command" {
  description = "SSH command to connect to the EC2 instance"
  value       = "ssh -i ${module.key_pair.private_key_filename} ubuntu@${var.enable_eip ? aws_eip.main[0].public_ip : module.ec2_instance.public_ip}"
}

output "ssh_private_key_path" {
  description = "Path to the SSH private key file"
  value       = module.key_pair.private_key_filename
  sensitive   = true
}

output "ssh_key_name" {
  description = "Name of the SSH key pair"
  value       = module.key_pair.key_pair_name
}

#============================================================================
# Application Access URLs
#============================================================================

output "streamlit_url" {
  description = "URL to access the Streamlit Customer 360 dashboard"
  value       = "http://${var.enable_eip ? aws_eip.main[0].public_ip : module.ec2_instance.public_ip}:${var.streamlit_port}"
}

output "puppygraph_web_url" {
  description = "URL to access the PuppyGraph Web UI"
  value       = "http://${var.enable_eip ? aws_eip.main[0].public_ip : module.ec2_instance.public_ip}:${var.puppygraph_web_port}"
}

output "puppygraph_cypher_endpoint" {
  description = "Cypher endpoint for PuppyGraph (Neo4j Bolt protocol)"
  value       = "bolt://${var.enable_eip ? aws_eip.main[0].public_ip : module.ec2_instance.public_ip}:${var.puppygraph_cypher_port}"
}

output "puppygraph_gremlin_endpoint" {
  description = "Gremlin endpoint for PuppyGraph"
  value       = "ws://${var.enable_eip ? aws_eip.main[0].public_ip : module.ec2_instance.public_ip}:${var.puppygraph_gremlin_port}/gremlin"
}

#============================================================================
# Network Information
#============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnets
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnets
}

output "security_group_id" {
  description = "ID of the security group for EC2 instance"
  value       = module.security_group.security_group_id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = module.vpc.igw_id
}

#============================================================================
# IAM Information
#============================================================================

output "ec2_instance_profile_name" {
  description = "Name of the EC2 instance profile"
  value       = module.iam.instance_profile_name
}

output "ec2_role_arn" {
  description = "ARN of the EC2 IAM role"
  value       = module.iam.role_arn
}

#============================================================================
# CloudWatch Information
#============================================================================

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = var.enable_cloudwatch_logs ? aws_cloudwatch_log_group.main[0].name : null
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = var.enable_cloudwatch_logs ? aws_cloudwatch_log_group.main[0].arn : null
}

#============================================================================
# Configuration Information
#============================================================================

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "customer_scale" {
  description = "Number of customers configured for data generation"
  value       = var.customer_scale
}

output "aws_region" {
  description = "AWS region where resources are deployed"
  value       = var.aws_region
}

#============================================================================
# Deployment Summary
#============================================================================

output "deployment_summary" {
  description = "Summary of the deployed infrastructure"
  value = {
    project_name     = var.project_name
    environment      = var.environment
    aws_region       = var.aws_region
    ec2_instance_id  = module.ec2_instance.id
    instance_type    = var.instance_type
    public_ip        = var.enable_eip ? aws_eip.main[0].public_ip : module.ec2_instance.public_ip
    customer_scale   = var.customer_scale
    deployment_time  = timestamp()
  }
}

#============================================================================
# Service Status Commands
#============================================================================

output "service_status_commands" {
  description = "Commands to check service status on the EC2 instance"
  value = {
    ssh_connect       = "ssh -i ${module.key_pair.private_key_filename} ubuntu@${var.enable_eip ? aws_eip.main[0].public_ip : module.ec2_instance.public_ip}"
    puppygraph_status = "sudo systemctl status puppygraph.service"
    streamlit_status  = "sudo systemctl status streamlit.service"
    puppygraph_logs   = "sudo journalctl -u puppygraph.service -f"
    streamlit_logs    = "sudo journalctl -u streamlit.service -f"
    user_data_log     = "sudo cat /var/log/user-data.log"
    application_logs  = "tail -f /opt/customer360/logs/*.log"
  }
}

#============================================================================
# Cost Information (estimated)
#============================================================================

output "estimated_monthly_cost" {
  description = "Estimated monthly AWS cost for the infrastructure (USD, us-west-2 pricing)"
  value = {
    ec2_cost = {
      "r5.xlarge"   = "~$180/month"
      "r5.2xlarge"  = "~$360/month"
      "r5.4xlarge"  = "~$720/month"
    }[var.instance_type]
    
    ebs_cost = "~$${var.root_volume_size * 0.10}/month (${var.root_volume_size}GB gp3)"
    
    data_transfer = "Variable based on usage"
    
    cloudwatch = var.enable_monitoring ? "~$5-15/month" : "$0/month"
    
    total_estimate = {
      "r5.xlarge"   = "~$190-210/month"
      "r5.2xlarge"  = "~$370-390/month"
      "r5.4xlarge"  = "~$730-750/month"
    }[var.instance_type]
  }
}

#============================================================================
# Security Information
#============================================================================

output "security_configuration" {
  description = "Security configuration summary"
  value = {
    ssh_access_from     = var.allowed_ssh_cidrs
    app_access_from     = var.allowed_app_cidrs
    vpc_flow_logs       = var.enable_vpc_flow_logs
    ebs_encryption      = true
    imds_v2_enforced    = true
    termination_protection = var.enable_termination_protection
  }
  sensitive = true
}

#============================================================================
# Next Steps Information
#============================================================================

output "next_steps" {
  description = "Next steps after deployment"
  value = [
    "1. Wait for EC2 initialization to complete (check user data logs)",
    "2. Verify PuppyGraph is running: systemctl status puppygraph.service",
    "3. Access PuppyGraph Web UI: http://${var.enable_eip ? aws_eip.main[0].public_ip : module.ec2_instance.public_ip}:${var.puppygraph_web_port}",
    "4. Deploy application code to /opt/customer360/",
    "5. Start data generation and ingestion",
    "6. Access Streamlit dashboard: http://${var.enable_eip ? aws_eip.main[0].public_ip : module.ec2_instance.public_ip}:${var.streamlit_port}",
    "7. Configure monitoring and alerts as needed",
    "8. Review security settings for production use"
  ]
}