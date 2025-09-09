#!/bin/bash

# Customer 360 Demo - Build Script
# Usage: ./build.sh [config-file]

set -e  # Exit on any error

CONFIG_FILE=${1:-"config.tfvars"}

echo "🚀 Customer 360 Demo Deployment"
echo "================================"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file '$CONFIG_FILE' not found!"
    echo "   Create it from the template or specify a different file:"
    echo "   ./build.sh my-config.tfvars"
    exit 1
fi

# Validate required values are filled
echo "🔍 Validating configuration..."
if grep -q '""' "$CONFIG_FILE"; then
    echo "❌ Found empty values in $CONFIG_FILE"
    echo "   Please fill in all required values (marked with empty quotes)"
    exit 1
fi

echo "✅ Configuration looks good"

# Initialize Terraform
echo "🏗️  Initializing Terraform..."
terraform init

# Plan deployment
echo "📋 Planning deployment..."
terraform plan -var-file="$CONFIG_FILE" -out=tfplan

# Ask for confirmation
echo ""
read -p "🤔 Deploy the infrastructure? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying infrastructure..."
    terraform apply tfplan
    
    echo ""
    echo "🎉 Deployment complete!"
    echo "📊 Check outputs for connection details:"
    terraform output
else
    echo "❌ Deployment cancelled"
    rm -f tfplan
fi
