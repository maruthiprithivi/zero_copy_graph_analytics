# Secret Management for Customer 360 Demo

This directory contains template files and documentation for managing sensitive configuration data like passwords, API keys, and connection strings.

## Important Security Notice

**NEVER commit actual secrets to version control!**

- All files ending with `.secret`, `.key`, or `.pem` are automatically ignored by Git
- Always use the template files (`.example`) as starting points
- Store production secrets in a secure secret management system

## File Structure

```
secrets/
├── README.md                    # This file
├── .env.example                # Environment variables template
├── terraform.tfvars.example    # Terraform variables template
├── .env                        # Actual env vars (NEVER COMMIT)
└── terraform.tfvars.secret     # Actual terraform vars (NEVER COMMIT)
```

## Setup Instructions

### 1. Create Environment Configuration

```bash
# Copy template and configure
cp secrets/.env.example secrets/.env
# Edit secrets/.env with your actual values
```

### 2. Create Terraform Variables

```bash
# Copy template and configure
cp secrets/terraform.tfvars.example secrets/terraform.tfvars.secret
# Edit secrets/terraform.tfvars.secret with your actual values
```

## Required Secrets

### ClickHouse Cloud Credentials

You need the following from your ClickHouse Cloud console:

- **Host**: Your ClickHouse Cloud endpoint (e.g., `abc123.clickhouse.cloud`)
- **Password**: Your database password
- **User**: Usually `default` unless you created custom users
- **Database**: Target database name (recommend `customer360`)

### PuppyGraph Configuration

- **Password**: Strong password for PuppyGraph admin access
- **Username**: Admin username (default: `puppygraph`)

### AWS Configuration

- **Owner Email**: Your email for resource tagging and notifications
- **SSH Access**: Your IP address for secure SSH access to EC2
- **App Access**: IP ranges allowed to access the applications

## Security Configuration Examples

### Development Environment

```hcl
# Relaxed security for development
allowed_ssh_cidrs = ["0.0.0.0/0"]  # Allow SSH from anywhere (not recommended)
allowed_app_cidrs = ["0.0.0.0/0"]  # Allow app access from anywhere
```

### Production Environment

```hcl
# Strict security for production
allowed_ssh_cidrs = ["203.0.113.1/32"]        # Your specific IP only
allowed_app_cidrs = ["10.0.0.0/8", "172.16.0.0/12"]  # Corporate networks only
```

## Password Security Requirements

### Strong Password Guidelines

All passwords should meet these criteria:

- Minimum 16 characters length
- Mix of uppercase, lowercase, numbers, and symbols
- No dictionary words or personal information
- Unique for each service

### Example Strong Passwords

```bash
# PuppyGraph password example
puppygraph_password = "Xk9#mP4$nQ8@vL2&wR7!"

# ClickHouse password (use what ClickHouse Cloud provides)
clickhouse_password = "Ch1ckH0use$ecur3P@ssw0rd2024!"
```

## IP Address Configuration

### Finding Your IP Address

```bash
# Get your current public IP
curl -s https://checkip.amazonaws.com/
# or
curl -s https://ipinfo.io/ip
```

### CIDR Notation Examples

```bash
# Single IP address
"203.0.113.1/32"

# IP range (office network)
"203.0.113.0/24"

# Multiple ranges
["203.0.113.1/32", "198.51.100.0/24"]
```

## Environment-Specific Configuration

### Development Setup

```bash
# .env for development
ENABLE_DEBUG_QUERIES=true
LOG_LEVEL=DEBUG
CUSTOMER_SCALE=1000000
```

### Production Setup

```bash
# .env for production
ENABLE_DEBUG_QUERIES=false
LOG_LEVEL=INFO
CUSTOMER_SCALE=100000000
ENABLE_CLOUDWATCH_METRICS=true
```

## Secret Rotation

### Regular Rotation Schedule

- **ClickHouse passwords**: Every 90 days
- **PuppyGraph passwords**: Every 90 days
- **SSH keys**: Every 180 days
- **AWS access keys**: Every 90 days

### Rotation Process

1. Generate new credentials
2. Update secrets files
3. Re-deploy infrastructure: `./scripts/deploy.sh`
4. Verify all services work correctly
5. Revoke old credentials

## Backup and Recovery

### Secrets Backup

**Never store secrets in plain text backups!**

For production environments, use:

- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- Encrypted local storage with proper key management

### Recovery Process

1. Restore secrets from secure backup
2. Update configuration files
3. Re-deploy services
4. Test all connections

## Troubleshooting

### Common Issues

1. **ClickHouse connection fails**
   ```bash
   # Test connection
   ping your-clickhouse-host
   telnet your-clickhouse-host 8443
   ```

2. **SSH access denied**
   ```bash
   # Check your current IP
   curl -s https://checkip.amazonaws.com/
   # Update allowed_ssh_cidrs in terraform.tfvars.secret
   ```

3. **PuppyGraph authentication fails**
   ```bash
   # Verify password in browser at http://EC2_IP:8081
   # Check puppygraph service logs
   ssh -i key.pem ubuntu@EC2_IP 'sudo journalctl -u puppygraph -f'
   ```

### Security Incident Response

If secrets are compromised:

1. **Immediate**: Revoke compromised credentials
2. **Emergency**: Stop affected services
3. **Recovery**: Generate new credentials
4. **Prevention**: Update security practices

## Compliance and Auditing

### Security Checklist

- [ ] All secrets use template files as base
- [ ] No secrets committed to version control
- [ ] Strong passwords for all services
- [ ] IP access properly restricted
- [ ] Regular password rotation scheduled
- [ ] Backup strategy implemented
- [ ] Incident response plan documented

### Audit Trail

Monitor these events:

- Secret access and updates
- Failed authentication attempts
- SSH login attempts
- Application access patterns
- AWS API calls (CloudTrail)

## Additional Security Measures

### Multi-Factor Authentication

Enable MFA where supported:
- AWS Console access
- ClickHouse Cloud console
- GitHub/GitLab repository access

### Network Security

Consider additional protections:
- VPN for remote access
- AWS Security Groups restrictions
- Network ACLs for additional filtering
- AWS WAF for web application protection

### Monitoring and Alerts

Set up alerts for:
- Failed login attempts
- Unusual access patterns
- High resource usage
- Security group changes
- New user creations