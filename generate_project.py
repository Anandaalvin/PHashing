#!/usr/bin/env python3
"""
Script to create the complete project structure for duplicate-detection-enterprise
Run this script to generate all folders and empty files
"""

import os
import sys
from pathlib import Path

# =============================================
# KONFIGURASI
# =============================================
PROJECT_NAME = "duplicate-detection-enterprise2"

# Struktur folder lengkap
STRUCTURE = {
    "src": {
        "__init__.py": "",
        "main.py": "# FastAPI entry point\n",
        "core": {
            "__init__.py": "",
            "domain": {
                "__init__.py": "",
                "claim.py": "# Claim domain entity\n",
                "photo.py": "# Photo domain entity\n",
                "hash.py": "# PhotoHash value object\n",
            },
            "usecases": {
                "__init__.py": "",
                "detect_duplicate.py": "# Detect duplicate use case\n",
            },
            "ports": {
                "__init__.py": "",
                "repositories.py": "# Repository interfaces\n",
                "services.py": "# Service interfaces\n",
            },
        },
        "infrastructure": {
            "__init__.py": "",
            "persistence": {
                "__init__.py": "",
                "postgres_repositories.py": "# PostgreSQL implementations\n",
                "elasticsearch_hash_repo.py": "# Elasticsearch implementation\n",
            },
            "cache": {
                "__init__.py": "",
                "redis_cache.py": "# Redis cache implementation\n",
            },
            "storage": {
                "__init__.py": "",
                "s3_storage.py": "# S3/MinIO storage implementation\n",
            },
            "messaging": {
                "__init__.py": "",
                "kafka_producer.py": "# Kafka messaging implementation\n",
            },
            "container.py": "# Dependency injection container\n",
        },
        "api": {
            "__init__.py": "",
            "routes": {
                "__init__.py": "",
                "upload.py": "# Photo upload routes\n",
                "health.py": "# Health check routes\n",
            },
            "middlewares": {
                "__init__.py": "",
                "logging.py": "# Request logging middleware\n",
                "rate_limit.py": "# Rate limiting middleware\n",
            },
            "dtos": {
                "__init__.py": "",
                "requests.py": "# Request/response DTOs\n",
            },
        },
        "worker": {
            "__init__.py": "",
            "celery_app.py": "# Celery application\n",
            "tasks": {
                "__init__.py": "",
                "process_photo.py": "# Photo processing tasks\n",
            },
            "consumers": {
                "__init__.py": "",
                "kafka_consumer.py": "# Kafka consumers\n",
            },
        },
    },
    "tests": {
        "__init__.py": "",
        "unit": {
            "__init__.py": "",
            "test_domain.py": "# Domain unit tests\n",
            "test_usecases.py": "# Use case unit tests\n",
        },
        "integration": {
            "__init__.py": "",
            "test_api.py": "# API integration tests\n",
        },
        "conftest.py": "# Pytest fixtures\n",
    },
    "migrations": {
        "versions": {
            ".gitkeep": "",
        },
        "env.py": "# Alembic environment\n",
    },
    "deployments": {
        "docker": {
            "Dockerfile.api": "# Dockerfile for API service\n",
            "Dockerfile.worker": "# Dockerfile for worker service\n",
            "docker-compose.yml": "# Docker Compose configuration\n",
        },
        "kubernetes": {
            "namespace.yaml": "# Kubernetes namespace\n",
            "configmap.yaml": "# Kubernetes ConfigMap\n",
            "secrets.yaml": "# Kubernetes Secrets\n",
            "api-deployment.yaml": "# API deployment\n",
            "worker-deployment.yaml": "# Worker deployment\n",
        },
    },
    "monitoring": {
        "prometheus": {
            "prometheus.yml": "# Prometheus configuration\n",
        },
        "grafana": {
            "dashboards": {
                ".gitkeep": "",
            },
        },
    },
    "scripts": {
        "init_elasticsearch.py": "# Elasticsearch initialization script\n",
    },
}

# Root level files
ROOT_FILES = {
    ".env.example": "# Environment variables example\n",
    "requirements.txt": "# Production dependencies\n",
    "requirements-dev.txt": "# Development dependencies\n",
    "Makefile": "# Make commands\n",
    "README.md": "# Project documentation\n",
    ".gitignore": "# Git ignore file\n",
    "pyproject.toml": "# Python project configuration\n",
    "alembic.ini": "# Alembic configuration\n",
}

# =============================================
# FUNGSI PEMBUAT FOLDER DAN FILE
# =============================================

def create_structure(base_path: Path, structure: dict):
    """Recursively create folders and files from structure dict"""
    for name, content in structure.items():
        current_path = base_path / name
        
        if isinstance(content, dict):
            # It's a folder
            current_path.mkdir(exist_ok=True)
            print(f"📁 Created folder: {current_path}")
            create_structure(current_path, content)
        else:
            # It's a file
            if not current_path.exists():
                with open(current_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"📄 Created file: {current_path}")
            else:
                print(f"⚠️ File already exists: {current_path}")

def create_root_files(base_path: Path, files: dict):
    """Create files in root directory"""
    for filename, content in files.items():
        file_path = base_path / filename
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📄 Created root file: {file_path}")
        else:
            print(f"⚠️ Root file already exists: {file_path}")

def create_gitignore(base_path: Path):
    """Create .gitignore with Python-specific ignores"""
    content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env
.venv
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/
.dmypy.json
dmypy.json
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# Distribution
dist/
build/
*.egg-info/

# Docker
*.pid
*.sock

# Project specific
data/
temp/
"""
    gitignore_path = base_path / ".gitignore"
    if not gitignore_path.exists():
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📄 Created .gitignore")

def create_requirements_txt(base_path: Path):
    """Create requirements.txt with basic dependencies"""
    content = """# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6

# Database
asyncpg==0.29.0
elasticsearch==8.11.0
redis==5.0.1
sqlalchemy==2.0.23
alembic==1.12.1

# Image Processing
Pillow==10.1.0
imagehash==4.3.1
opencv-python==4.8.1.78
numpy==1.26.2

# Messaging
celery==5.3.4
kafka-python==2.0.2
aiokafka==0.8.1

# Storage
boto3==1.34.0
aioboto3==12.0.0

# Monitoring
prometheus-client==0.19.0
structlog==24.1.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Utils
python-dotenv==1.0.0
uuid==1.30
tenacity==8.2.3
httpx==0.25.2
"""
    req_path = base_path / "requirements.txt"
    if not req_path.exists():
        with open(req_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📄 Created requirements.txt")

def create_requirements_dev_txt(base_path: Path):
    """Create requirements-dev.txt with development dependencies"""
    content = """# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
factory-boy==3.3.0
faker==20.1.0

# Linting
black==23.12.0
flake8==6.1.0
mypy==1.7.0
isort==5.13.0

# Dev tools
ipython==8.18.0
watchdog==3.0.0
"""
    req_path = base_path / "requirements-dev.txt"
    if not req_path.exists():
        with open(req_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📄 Created requirements-dev.txt")

def create_makefile(base_path: Path):
    """Create Makefile with useful commands"""
    content = """.PHONY: help install dev test lint format docker-up docker-down clean

help:
\t@echo "Available commands:"
\t@echo "  make install     - Install dependencies"
\t@echo "  make dev         - Run development server"
\t@echo "  make test        - Run tests"
\t@echo "  make lint        - Run linters"
\t@echo "  make format      - Format code"
\t@echo "  make docker-up   - Start all services"
\t@echo "  make docker-down - Stop all services"
\t@echo "  make clean       - Clean cache files"

install:
\tpip install -r requirements.txt -r requirements-dev.txt

dev:
\tuvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
\tpytest tests/ -v --cov=src --cov-report=term-missing

lint:
\tflake8 src/ tests/
\tmypy src/

format:
\tblack src/ tests/
\tisort src/ tests/

docker-up:
\tdocker-compose -f deployments/docker/docker-compose.yml up -d

docker-down:
\tdocker-compose -f deployments/docker/docker-compose.yml down

clean:
\tfind . -type d -name "__pycache__" -exec rm -rf {} +
\tfind . -type f -name "*.pyc" -delete
\tfind . -type f -name ".coverage" -delete
"""
    makefile_path = base_path / "Makefile"
    if not makefile_path.exists():
        with open(makefile_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📄 Created Makefile")

def create_readme(base_path: Path):
    """Create README.md"""
    content = """# Duplicate Detection Service"""


