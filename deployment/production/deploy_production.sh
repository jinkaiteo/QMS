#!/bin/bash

# QMS Platform v3.0 - Production Deployment Script
# Automated deployment for pharmaceutical production environments

set -e

echo "🚀 QMS Platform v3.0 - Production Deployment"
echo "============================================"
echo ""

# Environment check
if [ ! -f ".env.prod" ]; then
    echo "❌ Production environment file not found!"
    echo "Please ensure .env.prod exists with all required variables."
    exit 1
fi

echo "📋 Pre-deployment checks..."

# Check required tools
command -v podman >/dev/null 2>&1 || { echo "❌ Podman is required but not installed."; exit 1; }
command -v podman-compose >/dev/null 2>&1 || { echo "❌ Podman-compose is required but not installed."; exit 1; }

echo "✅ Required tools available"

# Load environment variables
source .env.prod

# Validate critical environment variables
REQUIRED_VARS=("POSTGRES_PASSWORD" "REDIS_PASSWORD" "SECRET_KEY" "JWT_SECRET_KEY" "MINIO_ROOT_USER" "MINIO_ROOT_PASSWORD")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# Create required directories
echo "🏗️ Creating production directories..."
mkdir -p {data,logs,backups,monitoring}/{postgres,redis,minio,app,nginx}
mkdir -p ssl

# Set proper permissions
chmod 700 data/postgres
chmod 755 logs data backups monitoring

echo "✅ Directory structure ready"

# Backup existing deployment if running
if podman ps -q --filter "name=qms-.*-production" | grep -q .; then
    echo "🔄 Backing up current deployment..."
    ./scripts/backup_production.sh
    
    echo "⏹️ Stopping existing services..."
    podman-compose -f docker-compose.production.yml down
fi

# Pull latest images
echo "📥 Pulling latest container images..."
podman-compose -f docker-compose.production.yml pull

# Start production deployment
echo "🚀 Starting QMS Platform production services..."
podman-compose -f docker-compose.production.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 60

# Health checks
echo "🏥 Running health checks..."
./scripts/health_check.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 PRODUCTION DEPLOYMENT SUCCESSFUL!"
    echo "=================================="
    echo ""
    echo "🌐 Access Points:"
    echo "  • QMS Platform: https://qms-platform.local"
    echo "  • API Documentation: https://qms-platform.local/docs"
    echo "  • Monitoring: http://monitoring.qms-platform.local/grafana"
    echo "  • MinIO Console: https://qms-platform.local:9001"
    echo ""
    echo "📊 Service Status:"
    podman ps --filter name=qms-.*-production --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "📋 Post-deployment tasks:"
    echo "  1. Configure DNS for qms-platform.local"
    echo "  2. Set up SSL certificates from CA"
    echo "  3. Configure monitoring alerts"
    echo "  4. Schedule automated backups"
    echo "  5. Perform user acceptance testing"
    echo ""
    echo "✅ QMS Platform v3.0 is now running in production!"
else
    echo ""
    echo "⚠️ PRODUCTION DEPLOYMENT ISSUES DETECTED"
    echo "======================================="
    echo ""
    echo "Please review the health check output and resolve any issues."
    echo "Check service logs: podman-compose -f docker-compose.production.yml logs"
    exit 1
fi