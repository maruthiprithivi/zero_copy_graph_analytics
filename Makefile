# PuppyGraph + ClickHouse Demo Makefile
# Simplified commands for local and hybrid deployments

.DEFAULT_GOAL := help
.PHONY: help local hybrid generate-local generate-hybrid init-schemas status clean destroy test-e2e clean-data

# Colors for output
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
BLUE := \033[34m
NC := \033[0m # No Color

help: ## Show available commands
	@echo "$(BLUE)PuppyGraph + ClickHouse Demo Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Deployments:$(NC)"
	@echo "  make local           - Start local deployment (ClickHouse + PuppyGraph in Docker)"
	@echo "  make hybrid          - Start hybrid deployment (Local PuppyGraph + ClickHouse Cloud)"
	@echo ""
	@echo "$(GREEN)Data Generation:$(NC)"
	@echo "  make generate-local  - Generate data (runs inside ClickHouse container)"
	@echo "  make generate-hybrid - Generate data (runs on local machine, ingests to cloud)"
	@echo ""
	@echo "$(GREEN)Operations:$(NC)"
	@echo "  make init-schemas    - Initialize and verify PuppyGraph schemas"
	@echo "  make status          - Check deployment status"
	@echo "  make logs            - Show container logs"
	@echo "  make clean           - Stop containers and clean up"
	@echo "  make destroy         - Destroy all resources (WARNING!)"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test-e2e             - Run full E2E test suite"
	@echo "  make test-comprehensive   - Run comprehensive E2E with all stages and metrics"
	@echo "  make test-comprehensive-quick - Quick comprehensive test (skip data/schema)"
	@echo "  make test-customer360     - Run Customer 360 tests only"
	@echo "  make test-fraud           - Run Fraud Detection tests only"
	@echo "  make clean-data           - Clean all data from ClickHouse"
	@echo ""

# Check prerequisites
check-docker:
	@which docker >/dev/null || (echo "$(RED)Docker is required but not installed$(NC)" && exit 1)
	@docker info >/dev/null 2>&1 || (echo "$(RED)Docker is not running$(NC)" && exit 1)

check-python:
	@which python3 >/dev/null || (echo "$(RED)Python 3 is required but not installed$(NC)" && exit 1)

check-hybrid-env:
	@if [ ! -f deployments/hybrid/.env ]; then \
		echo "$(RED)Error: deployments/hybrid/.env not found!$(NC)"; \
		echo "$(YELLOW)Please create it from the template:$(NC)"; \
		echo "  cp deployments/hybrid/.env.example deployments/hybrid/.env"; \
		echo "  # Then edit with your ClickHouse Cloud credentials"; \
		exit 1; \
	fi

# Local deployment (all services in Docker)
local: check-docker ## Start local deployment
	@echo "$(GREEN)Starting local deployment...$(NC)"
	@echo "$(YELLOW)Starting ClickHouse and PuppyGraph in Docker$(NC)"
	cd deployments/local && docker-compose up -d --build
	@echo ""
	@echo "$(GREEN)Local deployment started!$(NC)"
	@echo "Services:"
	@echo "  - PuppyGraph UI: $(BLUE)http://localhost:8081$(NC)"
	@echo "  - ClickHouse HTTP: $(BLUE)http://localhost:8123$(NC)"
	@echo "  - ClickHouse Native: $(BLUE)localhost:9000$(NC)"
	@echo ""
	@echo "$(YELLOW)Next step: Generate data with 'make generate-local'$(NC)"

# Hybrid deployment (local PuppyGraph + ClickHouse Cloud)
hybrid: check-docker check-hybrid-env ## Start hybrid deployment
	@echo "$(GREEN)Starting hybrid deployment...$(NC)"
	@echo "$(YELLOW)Starting PuppyGraph locally (will connect to ClickHouse Cloud)$(NC)"
	cd deployments/hybrid && docker-compose --env-file .env up -d
	@echo ""
	@echo "$(GREEN)Hybrid deployment started!$(NC)"
	@echo "Services:"
	@echo "  - PuppyGraph UI: $(BLUE)http://localhost:8081$(NC)"
	@echo "  - ClickHouse Cloud: Check your cloud console"
	@echo ""
	@echo "$(YELLOW)Next step: Generate data with 'make generate-hybrid'$(NC)"

# Data generation for local deployment
generate-local: ## Generate data in local deployment
	@echo "$(GREEN)Generating data in local deployment...$(NC)"
	@if ! docker ps | grep -q clickhouse-local; then \
		echo "$(RED)Error: Local deployment not running!$(NC)"; \
		echo "Start it first with: make local"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Entering ClickHouse container to generate data...$(NC)"
	@echo ""
	docker exec -it clickhouse-local bash -c "cd /app && python3 generate_data.py --customers 100000 --use-case both"
	@echo ""
	@echo "$(GREEN)Data generation complete!$(NC)"

# Schema initialization
init-schemas: ## Initialize and verify PuppyGraph schemas
	@echo "$(GREEN)Initializing PuppyGraph schemas...$(NC)"
	@if ! docker ps | grep -q puppygraph; then \
		echo "$(RED)Error: PuppyGraph is not running!$(NC)"; \
		echo "Start it first with: make local or make hybrid"; \
		exit 1; \
	fi
	@bash deployments/local/scripts/init-schemas.sh
	@echo ""

# Data generation for hybrid deployment
generate-hybrid: check-python check-hybrid-env ## Generate data for hybrid deployment
	@echo "$(GREEN)Generating data for hybrid deployment...$(NC)"
	@echo "$(YELLOW)Running data generator on local machine...$(NC)"
	@echo "$(YELLOW)Connecting to ClickHouse Cloud...$(NC)"
	@echo ""
	@export $$(cat deployments/hybrid/.env | grep -v '^#' | xargs) && \
		python3 generate_data.py --customers 100000 --use-case both
	@echo ""
	@echo "$(GREEN)Data generation complete!$(NC)"
	@echo "$(YELLOW)Data has been ingested into ClickHouse Cloud$(NC)"

# Status checking
status: ## Check deployment status
	@echo "$(GREEN)Checking deployment status...$(NC)"
	@echo ""
	@echo "$(BLUE)Docker containers:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -E "(clickhouse|puppygraph|NAMES)" || echo "No demo containers running"
	@echo ""
	@echo "$(BLUE)Health checks:$(NC)"
	@curl -s http://localhost:8081 >/dev/null && echo "[OK] PuppyGraph: http://localhost:8081" || echo "[FAIL] PuppyGraph: Not responding"
	@curl -s http://localhost:8123/ping >/dev/null && echo "[OK] ClickHouse (local): http://localhost:8123" || echo "[INFO] ClickHouse local: Not running (may be using cloud)"

# View logs
logs: ## Show container logs
	@echo "$(GREEN)Showing container logs...$(NC)"
	@if docker ps | grep -q clickhouse-local; then \
		cd deployments/local && docker-compose logs -f; \
	elif docker ps | grep -q puppygraph-hybrid; then \
		cd deployments/hybrid && docker-compose logs -f; \
	else \
		echo "$(RED)No containers running$(NC)"; \
	fi

# Cleanup
clean: ## Stop containers and clean up
	@echo "$(YELLOW)Stopping all demo containers...$(NC)"
	@cd deployments/local && docker-compose down -v 2>/dev/null || true
	@cd deployments/hybrid && docker-compose down -v 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

# Dangerous - destroy everything
destroy: ## Destroy all resources (WARNING!)
	@echo "$(RED)WARNING: This will destroy ALL resources!$(NC)"
	@echo "$(RED)WARNING: This action cannot be undone!$(NC)"
	@read -p "Are you sure you want to continue? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	@echo "$(YELLOW)Destroying all resources...$(NC)"
	@cd deployments/local && docker-compose down -v 2>/dev/null || true
	@cd deployments/hybrid && docker-compose down -v 2>/dev/null || true
	@docker system prune -f --volumes
	@echo "$(GREEN)All resources destroyed!$(NC)"

# Quick start helpers
local-quick: local ## Quick local setup
	@echo "$(YELLOW)Waiting for services to start...$(NC)"
	@sleep 15
	@make generate-local
	@make status

hybrid-quick: hybrid ## Quick hybrid setup
	@echo "$(YELLOW)Waiting for PuppyGraph to start...$(NC)"
	@sleep 10
	@make generate-hybrid
	@make status

# E2E Testing
test-e2e: check-docker ## Run full E2E test suite
	@echo "$(GREEN)Running E2E Test Suite...$(NC)"
	@bash test/scripts/run_e2e_tests.sh
	@echo "$(GREEN)E2E tests complete!$(NC)"

test-e2e-quick: check-docker ## Run E2E tests (skip start if services running)
	@echo "$(GREEN)Running E2E Test Suite (quick mode)...$(NC)"
	@bash test/scripts/run_e2e_tests.sh --skip-start
	@echo "$(GREEN)E2E tests complete!$(NC)"

# Comprehensive Testing (with metrics)
test-comprehensive: check-docker check-python ## Run comprehensive E2E test with all stages
	@echo "$(GREEN)Running Comprehensive E2E Test Suite...$(NC)"
	@echo "$(YELLOW)This will run: data loading, schema loading, queries, verification$(NC)"
	@python3 test/comprehensive_test_runner.py --deployment local --use-case all --verbose
	@echo "$(GREEN)Comprehensive tests complete!$(NC)"

test-comprehensive-quick: check-docker check-python ## Run comprehensive E2E tests (skip data/schema loading)
	@echo "$(GREEN)Running Comprehensive E2E Test Suite (quick mode)...$(NC)"
	@python3 test/comprehensive_test_runner.py --deployment local --use-case all --skip-data-loading --skip-schema-loading --verbose
	@echo "$(GREEN)Comprehensive tests complete!$(NC)"

test-customer360: check-docker check-python ## Run tests for Customer 360 only
	@echo "$(GREEN)Running Customer 360 Test Suite...$(NC)"
	@python3 test/comprehensive_test_runner.py --deployment local --use-case customer-360 --skip-data-loading --skip-schema-loading
	@echo "$(GREEN)Customer 360 tests complete!$(NC)"

test-fraud: check-docker check-python ## Run tests for Fraud Detection only
	@echo "$(GREEN)Running Fraud Detection Test Suite...$(NC)"
	@python3 test/comprehensive_test_runner.py --deployment local --use-case fraud-detection --skip-data-loading --skip-schema-loading
	@echo "$(GREEN)Fraud Detection tests complete!$(NC)"

# Clean data from ClickHouse
clean-data: ## Clean all data from ClickHouse (keeps schema)
	@echo "$(YELLOW)Cleaning data from ClickHouse...$(NC)"
	@if docker ps | grep -q clickhouse-local; then \
		echo "Truncating tables..."; \
		docker exec clickhouse-local clickhouse-client --query "TRUNCATE TABLE IF EXISTS customers" 2>/dev/null || true; \
		docker exec clickhouse-local clickhouse-client --query "TRUNCATE TABLE IF EXISTS products" 2>/dev/null || true; \
		docker exec clickhouse-local clickhouse-client --query "TRUNCATE TABLE IF EXISTS transactions" 2>/dev/null || true; \
		docker exec clickhouse-local clickhouse-client --query "TRUNCATE TABLE IF EXISTS interactions" 2>/dev/null || true; \
		echo "$(GREEN)ClickHouse data cleaned!$(NC)"; \
	else \
		echo "$(RED)ClickHouse container not running$(NC)"; \
	fi
	@if [ -d "data" ]; then \
		echo "Removing local data files..."; \
		rm -rf data/*; \
		echo "$(GREEN)Local data files removed!$(NC)"; \
	fi
