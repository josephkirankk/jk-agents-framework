# JK-Agents Framework Makefile
# Provides convenience targets for development, testing, and cleanup

.PHONY: help install dev test clean clean-all lint format check-deps run

# Default target
help:
	@echo "JK-Agents Framework - Available Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install     Install dependencies"
	@echo "  dev         Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  run         Start the FastAPI development server"
	@echo "  test        Run basic configuration tests"
	@echo "  lint        Run code quality checks"
	@echo "  format      Format code with black and isort"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean       Remove temporary files and cache"
	@echo "  clean-all   Full cleanup including demo data and virtual env"
	@echo "  clean-logs  Remove only log files"
	@echo "  clean-test  Remove only test artifacts"
	@echo ""
	@echo "Utilities:"
	@echo "  check-deps  Check for missing dependencies"
	@echo "  size        Show repository size"

# Installation targets
install:
	pip install -r requirements.txt

dev: install
	pip install pytest black isort

# Development targets
run:
	@echo "Starting FastAPI development server..."
	uvicorn api:app --reload --port 8000

test:
	@echo "Running configuration tests..."
	@if [ -f "config/agents_test.yaml" ]; then \
		python -c "import yaml; yaml.safe_load(open('config/agents_test.yaml'))" && echo "✓ YAML configuration is valid"; \
	else \
		echo "⚠ No test configuration found"; \
	fi
	@python -c "from app.config import AppConfig; print('✓ Configuration models load successfully')" || echo "✗ Configuration import failed"

lint:
	@echo "Running code quality checks..."
	@if command -v black >/dev/null 2>&1; then \
		black --check --diff .; \
	else \
		echo "⚠ black not installed, run 'make dev' first"; \
	fi
	@if command -v isort >/dev/null 2>&1; then \
		isort --check-only --diff .; \
	else \
		echo "⚠ isort not installed, run 'make dev' first"; \
	fi

format:
	@echo "Formatting code..."
	@if command -v black >/dev/null 2>&1; then \
		black .; \
	else \
		echo "⚠ black not installed, run 'make dev' first"; \
	fi
	@if command -v isort >/dev/null 2>&1; then \
		isort .; \
	else \
		echo "⚠ isort not installed, run 'make dev' first"; \
	fi

# Cleanup targets
clean:
	@echo "🧹 Cleaning temporary files..."
	@# Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	@# OS files
	find . -name ".DS_Store" -delete 2>/dev/null || true
	@# Log files
	rm -rf logs/* 2>/dev/null || true
	rm -f agentlog_*.log server.log 2>/dev/null || true
	@# Test artifacts
	rm -rf test_checkpoints/* test_chroma_db/* 2>/dev/null || true
	rm -f test_results*.json *_test_results.json multistep_supervisor_test_results.json 2>/dev/null || true
	@echo "✓ Cleanup complete"

clean-logs:
	@echo "🗑 Cleaning log files..."
	rm -rf logs/* 2>/dev/null || true
	rm -f agentlog_*.log server.log 2>/dev/null || true
	@echo "✓ Log files cleaned"

clean-test:
	@echo "🗑 Cleaning test artifacts..."
	rm -rf test_checkpoints/* test_chroma_db/* test_workflow_data/* 2>/dev/null || true
	rm -f test_results*.json *_test_results.json multistep_supervisor_test_results.json 2>/dev/null || true
	rm -f validation_report_*.md 2>/dev/null || true
	@echo "✓ Test artifacts cleaned"

clean-all: clean
	@echo "🧹 Full cleanup (including demo data and ChromaDB)..."
	@# Demo data
	rm -rf demo_data/* demo_core_flow/* demo_multi_agent/* 2>/dev/null || true
	@# ChromaDB development data
	rm -rf chroma_memory/* advanced_agent_memory/* 2>/dev/null || true
	@# Backup files
	rm -f .env.backup *.backup *.bak 2>/dev/null || true
	@# Virtual environment (with confirmation)
	@if [ -d ".venv" ]; then \
		echo "⚠️  Found virtual environment (.venv/)"; \
		read -p "Remove virtual environment? (y/N) " -n 1 -r; \
		echo; \
		if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
			rm -rf .venv; \
			echo "✓ Virtual environment removed"; \
			echo "⚠️  Remember to recreate: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"; \
		fi; \
	fi
	@echo "✓ Full cleanup complete"

# Utility targets
check-deps:
	@echo "Checking dependencies..."
	@python -c "import sys; print(f'Python: {sys.version}')"
	@python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')" 2>/dev/null || echo "✗ FastAPI not found"
	@python -c "import langchain; print(f'LangChain: {langchain.__version__}')" 2>/dev/null || echo "✗ LangChain not found"
	@python -c "import uvicorn; print(f'Uvicorn: {uvicorn.__version__}')" 2>/dev/null || echo "✗ Uvicorn not found"

size:
	@echo "Repository size:"
	@du -sh . 2>/dev/null || echo "Could not determine size"
	@echo ""
	@echo "Largest directories:"
	@du -sh */ 2>/dev/null | sort -hr | head -10 || echo "Could not analyze directories"

# Advanced cleanup with custom script
clean-script:
	@if [ -f "./cleanup.sh" ]; then \
		chmod +x ./cleanup.sh && ./cleanup.sh; \
	else \
		echo "cleanup.sh script not found"; \
	fi