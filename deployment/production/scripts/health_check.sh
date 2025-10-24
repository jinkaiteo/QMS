#!/bin/bash

# QMS Platform Production Health Check

echo "🏥 QMS Platform Health Check - $(date)"
echo "=================================="

# Check all services
SERVICES=("qms-db-prod" "qms-redis-prod" "qms-minio-prod" "qms-app-prod" "qms-nginx-prod")
ALL_HEALTHY=true

for service in "${SERVICES[@]}"; do
    if podman ps --filter "name=$service" --filter "status=running" | grep -q "$service"; then
        echo "✅ $service: HEALTHY"
    else
        echo "❌ $service: UNHEALTHY"
        ALL_HEALTHY=false
    fi
done

# Check API endpoints
echo ""
echo "🔍 API Health Checks:"
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "✅ API Health: RESPONDING"
else
    echo "❌ API Health: NOT RESPONDING"
    ALL_HEALTHY=false
fi

# Check database connectivity
echo ""
echo "🗄️ Database Connectivity:"
if podman exec qms-db-prod pg_isready -U qms_user -d qms_prod > /dev/null 2>&1; then
    echo "✅ Database: CONNECTED"
else
    echo "❌ Database: CONNECTION FAILED"
    ALL_HEALTHY=false
fi

# Overall status
echo ""
if [ "$ALL_HEALTHY" = true ]; then
    echo "🎉 Overall Status: ALL SYSTEMS HEALTHY"
    exit 0
else
    echo "⚠️ Overall Status: ISSUES DETECTED"
    exit 1
fi
