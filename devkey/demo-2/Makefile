# Marathon Planning Multi-Agent System — Makefile
#
# End-to-end workflow: setup, test, deploy, demo, teardown.
#
# Usage:
#   make setup          — Install deps + configure env
#   make test           — Run unit tests
#   make deploy         — Full deploy (infra + agents + planner)
#   make demo-solo      — Run solo demo (Planner + Evaluator)
#   make demo-full      — Run full team demo (all 3 agents)
#   make teardown       — Destroy all deployed resources
#   make local          — Run agents locally
#
# Prerequisites:
#   - uv (https://docs.astral.sh/uv/)
#   - gcloud CLI, authenticated
#   - terraform >= 1.0

.PHONY: help setup env auth install test lint \
        deploy infra deploy-simulator deploy-planner \
        local local-planner local-simulator local-full \
        demo-health demo-solo demo-full demo-all \
        teardown teardown-infra teardown-agents \
        clean

# ============================================================================
# CONFIG
# ============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Load .env if it exists
ifneq (,$(wildcard .env))
  include .env
  export
endif

PROJECT   ?= $(GOOGLE_CLOUD_PROJECT)
REGION    ?= $(or $(GOOGLE_CLOUD_LOCATION),us-central1)
TF_DIR    := terraform
DEMO_DIR  := demo/deploy

# ============================================================================
# HELP
# ============================================================================

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# SETUP
# ============================================================================

setup: install env ## Install dependencies and prepare .env
	@echo "Done. Edit .env with your project values, then run: make auth"

install: ## Install Python dependencies
	uv sync --all-groups --extra dev

env: ## Create .env from example (if missing)
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env — edit it with your GCP project values"; \
	else \
		echo ".env already exists"; \
	fi

auth: ## Authenticate with Google Cloud
	gcloud auth application-default login
	@echo "Authenticated. Set your project:"
	@echo "  gcloud config set project $(PROJECT)"

# ============================================================================
# TEST & LINT
# ============================================================================

test: ## Run all unit tests
	uv run pytest --tb=short

test-verbose: ## Run tests with verbose output
	uv run pytest -v --tb=long

lint: ## Run linter
	uv run ruff check src/ tests/

lint-fix: ## Auto-fix lint issues
	uv run ruff check --fix src/ tests/

# ============================================================================
# DEPLOY (full pipeline)
# ============================================================================

deploy: infra deploy-simulator deploy-planner ## Deploy everything (infra + agents + Cloud Run)
	@echo ""
	@echo "========================================="
	@echo " All resources deployed successfully"
	@echo "========================================="
	@echo " Run 'make demo-health' to verify"

infra: ## Deploy infrastructure (GCS bucket, IAM, Artifact Registry, Cloud Run)
	@echo "--- Deploying infrastructure with Terraform ---"
	cd $(TF_DIR) && terraform init && terraform apply

deploy-simulator: ## Deploy Simulator Agent to Agent Engine
	@echo "--- Deploying Simulator Agent to Agent Engine ---"
	uv run python -m src.simulator_agent.runtime.deploy
	@echo ""
	@echo "Copy the SIMULATOR_AGENT_RESOURCE_NAME to .env and terraform.tfvars"

deploy-planner: ## Build and deploy Planner Agent to Cloud Run
	@echo "--- Building and deploying Planner Agent ---"
	gcloud builds submit \
		--config=cloudbuild.yaml \
		--project=$(PROJECT) \
		--substitutions=_REGION=$(REGION)

# ============================================================================
# LOCAL DEVELOPMENT
# ============================================================================

local-planner: ## Run Planner Agent locally (port 8084)
	uv run python -m src.planner_agent.runtime.local_server

local-simulator: ## Run Simulator Agent locally (port 8089)
	uv run python -m src.simulator_agent.runtime.local_server

local-full: ## Run Planner with local Simulator (both agents locally)
	@echo "Start the Simulator first in another terminal: make local-simulator"
	@echo "Then press Enter to start the Planner..."
	@read _
	SIMULATOR_AGENT_RESOURCE_NAME=local:8089 uv run python -m src.planner_agent.runtime.local_server

# ============================================================================
# DEMO
# ============================================================================

demo-health: ## Health check deployed endpoints
	uv run python -m demo.test_endpoints --health-only

demo-solo: ## Run solo demo (Planner + Evaluator only)
	uv run python -m demo.test_endpoints --solo

demo-full: ## Run full team demo (Planner + Evaluator + Simulator)
	uv run python -m demo.test_endpoints --full

demo-all: ## Run both demo modes
	uv run python -m demo.test_endpoints

# ============================================================================
# TEARDOWN
# ============================================================================

teardown: teardown-agents teardown-infra ## Destroy all deployed resources
	@echo ""
	@echo "========================================="
	@echo " All resources destroyed"
	@echo "========================================="

teardown-infra: ## Destroy Terraform-managed infrastructure
	@echo "--- Destroying infrastructure ---"
	cd $(TF_DIR) && terraform destroy

teardown-agents: ## Delete agents from Agent Engine
	@echo "--- Deleting agents from Agent Engine ---"
	uv run python -m src.utils.delete_agents --all

# ============================================================================
# CLEAN
# ============================================================================

clean: ## Remove local build artifacts
	rm -rf .venv/ .pytest_cache/ .ruff_cache/ __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd $(TF_DIR) && rm -rf .terraform/ .terraform.lock.hcl *.tfstate *.tfstate.*
	@echo "Cleaned build artifacts"
