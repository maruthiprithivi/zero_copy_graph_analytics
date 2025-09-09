#!/bin/bash
#
# Customer 360 Demo - Single Deployment Script
# Easy one-command deployment to AWS
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="customer360-demo"
TERRAFORM_DIR="."
REMOTE_USER="ubuntu"
APP_DIR="/opt/customer360"
SSH_KEY_FILE=""  # Will be set based on Terraform output

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check for required commands
    local required_commands=("terraform" "aws" "ssh" "scp")
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            print_error "$cmd is not installed. Please install it first."
            exit 1
        fi
        print_status "✓ $cmd is available"
    done
    
    # Check for required files
    local required_files=("main.tf" "terraform.tfvars" ".env")
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "$file is missing. Please create it first."
            print_status "Run 'cp ${file}.example ${file}' and edit the values"
            exit 1
        fi
        print_status "✓ $file exists"
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    print_success "All prerequisites met!"
}

# Setup SSH key permissions and location
setup_ssh_key() {
    print_header "Setting up SSH Key"
    
    # Check if key exists and set permissions
    if [ -f "$SSH_KEY_FILE" ]; then
        print_status "Found SSH key: $SSH_KEY_FILE"
        chmod 600 "$SSH_KEY_FILE"
        print_status "Set SSH key permissions to 600"
    else
        print_error "SSH key not found: $SSH_KEY_FILE"
        print_status "This key should be created by Terraform"
        exit 1
    fi
    
    print_success "SSH key ready for use"
}

# Deploy infrastructure
deploy_infrastructure() {
    print_header "Deploying Infrastructure"
    
    cd $TERRAFORM_DIR
    
    print_status "Initializing Terraform..."
    terraform init
    
    print_status "Planning infrastructure changes..."
    terraform plan
    
    echo -n "Deploy infrastructure? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_status "Applying Terraform configuration..."
        terraform apply -auto-approve
        
        # Get outputs
        export EC2_IP=$(terraform output -raw ec2_public_ip)
        export EC2_DNS=$(terraform output -raw ec2_public_dns)
        export SSH_KEY_FILE=$(terraform output -raw key_pair_name).pem
        
        print_success "Infrastructure deployed successfully!"
        print_status "EC2 Public IP: $EC2_IP"
        print_status "EC2 Public DNS: $EC2_DNS"
    else
        print_warning "Infrastructure deployment skipped"
        exit 0
    fi
}

# Wait for EC2 to be ready
wait_for_ec2() {
    print_header "Waiting for EC2 Instance"
    
    if [ -z "$EC2_IP" ]; then
        print_error "EC2_IP not set. Run terraform output ec2_public_ip"
        exit 1
    fi
    
    print_status "Waiting for EC2 instance to be ready..."
    
    # Wait for SSH to be available
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Attempt $attempt/$max_attempts - Testing SSH connection..."
        
        if ssh -i "$SSH_KEY_FILE" -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
               $REMOTE_USER@$EC2_IP "echo 'SSH Ready'" &> /dev/null; then
            print_success "SSH connection established!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "EC2 instance not ready after $max_attempts attempts"
            exit 1
        fi
        
        sleep 10
        ((attempt++))
    done
    
    # Wait for user-data script to complete
    print_status "Waiting for system setup to complete..."
    
    local setup_complete=false
    local setup_attempts=20
    local setup_attempt=1
    
    while [ $setup_attempt -le $setup_attempts ] && [ "$setup_complete" = false ]; do
        print_status "Checking setup status... ($setup_attempt/$setup_attempts)"
        
        if ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no \
               $REMOTE_USER@$EC2_IP "docker ps | grep puppygraph" &> /dev/null; then
            print_success "System setup completed!"
            setup_complete=true
            break
        fi
        
        sleep 15
        ((setup_attempt++))
    done
    
    if [ "$setup_complete" = false ]; then
        print_warning "Setup may still be in progress. Check /var/log/user-data.log on the EC2 instance"
    fi
}

# Upload application files
upload_application() {
    print_header "Uploading Application Files"
    
    # Create remote directory
    ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no \
        $REMOTE_USER@$EC2_IP "sudo mkdir -p $APP_DIR && sudo chown $REMOTE_USER:$REMOTE_USER $APP_DIR"
    
    # Upload Python files
    local app_files=("generator.py" "clickhouse.py" "queries.py" "app.py" "requirements.txt" ".env")
    
    for file in "${app_files[@]}"; do
        if [ -f "$file" ]; then
            print_status "Uploading $file..."
            scp -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no "$file" $REMOTE_USER@$EC2_IP:$APP_DIR/
        else
            print_warning "$file not found, skipping"
        fi
    done
    
    print_success "Application files uploaded!"
}

# Install dependencies and setup application
setup_application() {
    print_header "Setting Up Application"
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no $REMOTE_USER@$EC2_IP << EOF
        cd $APP_DIR
        python3 -m pip install --user -r requirements.txt
        export PATH=\$PATH:\$HOME/.local/bin
        echo 'export PATH=\$PATH:\$HOME/.local/bin' >> ~/.bashrc
EOF
    
    print_success "Dependencies installed!"
}

# Generate sample data
generate_data() {
    print_header "Generating Sample Data"
    
    echo -n "Generate sample data? This may take several minutes. (y/N): "
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_status "Generating sample data (this will take a few minutes)..."
        
        ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no $REMOTE_USER@$EC2_IP << EOF
            cd $APP_DIR
            export PATH=\$PATH:\$HOME/.local/bin
            python3 generator.py --scale 1000000 --output data
EOF
        
        print_success "Sample data generated!"
    else
        print_warning "Data generation skipped. You can run it later with:"
        print_status "ssh ubuntu@$EC2_IP 'cd $APP_DIR && python3 generator.py'"
    fi
}

# Load data into ClickHouse
load_data() {
    print_header "Loading Data into ClickHouse"
    
    echo -n "Load data into ClickHouse? (y/N): "
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_status "Creating ClickHouse tables and loading data..."
        
        ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no $REMOTE_USER@$EC2_IP << EOF
            cd $APP_DIR
            export PATH=\$PATH:\$HOME/.local/bin
            python3 clickhouse.py --init --load --schema --status
EOF
        
        print_success "Data loaded into ClickHouse!"
    else
        print_warning "Data loading skipped. You can run it later with:"
        print_status "ssh ubuntu@$EC2_IP 'cd $APP_DIR && python3 clickhouse.py --init --load'"
    fi
}

# Start Streamlit dashboard
start_dashboard() {
    print_header "Starting Dashboard"
    
    print_status "Starting Streamlit dashboard..."
    
    # Start Streamlit in background
    ssh -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no $REMOTE_USER@$EC2_IP << EOF
        cd $APP_DIR
        export PATH=\$PATH:\$HOME/.local/bin
        # Kill any existing streamlit processes
        pkill -f streamlit || true
        # Start streamlit in background
        nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &
        echo "Streamlit started with PID: \$!"
EOF
    
    print_success "Dashboard started!"
    print_status "Dashboard URL: http://$EC2_IP:8501"
    print_status "PuppyGraph UI: http://$EC2_IP:8081"
}

# Display final information
display_summary() {
    print_header "Deployment Complete!"
    
    echo -e "${GREEN}🎉 Customer 360 Demo deployed successfully!${NC}\n"
    
    echo -e "${BLUE}📋 Access Information:${NC}"
    echo -e "   • Dashboard:      http://$EC2_IP:8501"
    echo -e "   • PuppyGraph UI:  http://$EC2_IP:8081"
    echo -e "   • SSH Access:     ssh -i ~/.ssh/customer360-key.pem ubuntu@$EC2_IP"
    
    echo -e "\n${BLUE}🔧 Useful Commands:${NC}"
    echo -e "   • Check logs:     ssh ubuntu@$EC2_IP 'tail -f $APP_DIR/streamlit.log'"
    echo -e "   • Restart app:    ssh ubuntu@$EC2_IP 'cd $APP_DIR && streamlit run app.py --server.port 8501 --server.address 0.0.0.0'"
    echo -e "   • Generate data:  ssh ubuntu@$EC2_IP 'cd $APP_DIR && python3 generator.py'"
    echo -e "   • Load data:      ssh ubuntu@$EC2_IP 'cd $APP_DIR && python3 clickhouse.py --init --load'"
    
    echo -e "\n${BLUE}🧹 Cleanup:${NC}"
    echo -e "   • Destroy infra:  terraform destroy"
    
    echo -e "\n${YELLOW}⏱️  Note: Allow a few minutes for all services to fully start${NC}\n"
}

# Main deployment flow
main() {
    print_header "Customer 360 Demo - One-Click Deployment"
    
    # Get EC2 IP if infrastructure already exists
    if [ -f "terraform.tfstate" ]; then
        EC2_IP=$(terraform output -raw ec2_public_ip 2>/dev/null || true)
        EC2_DNS=$(terraform output -raw ec2_public_dns 2>/dev/null || true)
        SSH_KEY_FILE=$(terraform output -raw key_pair_name 2>/dev/null || echo "customer360-key").pem
    fi
    
    check_prerequisites
    
    # Deploy infrastructure if not already done
    if [ -z "$EC2_IP" ]; then
        deploy_infrastructure
    else
        print_status "Using existing infrastructure: $EC2_IP"
    fi
    
    setup_ssh_key
    wait_for_ec2
    upload_application
    setup_application
    generate_data
    load_data
    start_dashboard
    display_summary
    
    print_success "🚀 Deployment completed successfully!"
}

# Handle script arguments
case "${1:-}" in
    "check")
        check_prerequisites
        ;;
    "infra")
        check_prerequisites
        deploy_infrastructure
        ;;
    "upload")
        upload_application
        ;;
    "data")
        generate_data
        load_data
        ;;
    "start")
        start_dashboard
        ;;
    "status")
        if [ -n "$EC2_IP" ] || [ -f "terraform.tfstate" ]; then
            EC2_IP=${EC2_IP:-$(terraform output -raw ec2_public_ip)}
            echo "Dashboard: http://$EC2_IP:8501"
            echo "PuppyGraph: http://$EC2_IP:8081"
            echo "SSH: ssh -i $(terraform output -raw key_pair_name 2>/dev/null || echo "customer360-key").pem ubuntu@$EC2_IP"
        else
            echo "No deployment found"
        fi
        ;;
    "destroy")
        print_warning "This will destroy all infrastructure and data!"
        echo -n "Are you sure? (y/N): "
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            terraform destroy
            print_success "Infrastructure destroyed"
        fi
        ;;
    "help"|"-h"|"--help")
        echo "Customer 360 Demo Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (none)    Full deployment (default)"
        echo "  check     Check prerequisites only"
        echo "  infra     Deploy infrastructure only"
        echo "  upload    Upload application files only"
        echo "  data      Generate and load data only"
        echo "  start     Start dashboard only"
        echo "  status    Show deployment status"
        echo "  destroy   Destroy all infrastructure"
        echo "  help      Show this help"
        ;;
    *)
        main
        ;;
esac