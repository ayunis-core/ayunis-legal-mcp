.PHONY: help build up down logs clean migrate import-bgb test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker containers
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "Services starting..."
	@echo "Store API: http://localhost:8000"
	@echo "Store API Docs: http://localhost:8000/docs"
	@echo "MCP Server: http://localhost:8001"

down: ## Stop all services
	docker-compose down

logs: ## Show logs from all services
	docker-compose logs -f

logs-store: ## Show logs from store API
	docker-compose logs -f store-api

logs-mcp: ## Show logs from MCP server
	docker-compose logs -f mcp-server

logs-db: ## Show logs from database
	docker-compose logs -f postgres

clean: ## Stop and remove all containers, networks, and volumes
	docker-compose down -v

restart: down up ## Restart all services

migrate: ## Run database migrations
	docker-compose exec store-api alembic upgrade head

import-bgb: ## Import German Civil Code (BGB)
	curl -X POST http://localhost:8000/legal-texts/gesetze-im-internet/bgb

test: ## Run tests
	docker-compose exec store-api pytest

shell-store: ## Open shell in store API container
	docker-compose exec store-api /bin/bash

shell-mcp: ## Open shell in MCP server container
	docker-compose exec mcp-server /bin/bash

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U legal_mcp -d legal_mcp_db

dev: ## Start development environment (with live reload)
	docker-compose up

ps: ## Show running containers
	docker-compose ps

