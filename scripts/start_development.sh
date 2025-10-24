#!/bin/bash
# QMS Development Startup Script
# Phase 1: Start development environment

set -e

echo "Starting QMS Development Environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please review and update .env file with your settings"
fi

# Create necessary directories
echo "Creating required directories..."
mkdir -p backend/app/logs
mkdir -p backend/app/uploads
mkdir -p backend/app/backups
mkdir -p backend/app/temp

# Start infrastructure services
echo "Starting infrastructure services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Check if database is ready
echo "Checking database connection..."
docker-compose -f docker-compose.dev.yml exec qms-db-dev pg_isready -U qms_user -d qms_dev

# Install Python dependencies
echo "Installing Python dependencies..."
cd backend
pip install -r requirements.txt

# Run database migrations (when Alembic is set up)
echo "Database is ready. You can now run the application."

echo "Development environment is ready!"
echo ""
echo "Services available:"
echo "- PostgreSQL: localhost:5432"
echo "- Redis: localhost:6379"
echo "- MinIO: http://localhost:9001 (admin/minioadmin123)"
echo "- pgAdmin: http://localhost:5050 (admin@qms.local/admin123)"
echo ""
echo "To start the API server:"
echo "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API docs: http://localhost:8000/api/v1/docs"