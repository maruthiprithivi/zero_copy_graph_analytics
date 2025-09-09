# Customer 360 Demo - Terraform Outputs
# All output values for the deployment

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.main.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.main.public_dns
}

output "ssh_command" {
  description = "SSH command to connect to the EC2 instance"
  value       = "ssh -i ${var.key_pair_name}.pem ubuntu@${aws_instance.main.public_ip}"
}

output "streamlit_url" {
  description = "URL for the Streamlit dashboard"
  value       = "http://${aws_instance.main.public_ip}:8501"
}

output "puppygraph_url" {
  description = "URL for the PuppyGraph Web UI"
  value       = "http://${aws_instance.main.public_ip}:8081"
}

output "vpc_id" {
  description = "ID of the VPC being used (existing or created)"
  value       = local.vpc_id
}

output "subnet_id" {
  description = "ID of the subnet being used (existing or created)"
  value       = local.subnet_id
}

output "security_group_id" {
  description = "ID of the created security group"
  value       = aws_security_group.main.id
}

output "key_pair_name" {
  description = "Name of the SSH key pair"
  value       = aws_key_pair.main.key_name
}

output "instance_type" {
  description = "EC2 instance type used"
  value       = aws_instance.main.instance_type
}

output "deployment_info" {
  description = "Summary of deployment information"
  value = {
    region         = var.aws_region
    vpc_type       = var.use_existing_vpc ? "existing" : "new"
    instance_type  = var.instance_type
    customer_scale = var.customer_scale
    ssh_access     = "ssh -i ${var.key_pair_name}.pem ubuntu@${aws_instance.main.public_ip}"
    dashboard_url  = "http://${aws_instance.main.public_ip}:8501"
    puppygraph_url = "http://${aws_instance.main.public_ip}:8081"
  }
}