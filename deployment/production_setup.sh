#!/bin/bash

# QMS Platform v3.0 - Production Environment Setup Script
# Comprehensive production deployment for pharmaceutical operations

set -e

echo "🚀 QMS Platform v3.0 - Production Environment Setup"
echo "=================================================="
echo ""

# Configuration
DOMAIN_NAME=${DOMAIN_NAME:-"qms-platform.local"}
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-90}
LOG_RETENTION_DAYS=${LOG_RETENTION_DAYS:-365}

echo "📋 Production Configuration:"
echo "  Domain: $DOMAIN_NAME"
echo "  Backup Retention: $BACKUP_RETENTION_DAYS days"
echo "  Log Retention: $LOG_RETENTION_DAYS days"
echo ""

# 1. Create production directory structure
echo "🏗️ Step 1: Creating production directory structure..."
mkdir -p production/{config,data,logs,backups,ssl,scripts,monitoring}
mkdir -p production/data/{postgres,redis,minio}
mkdir -p production/logs/{app,nginx,postgres,redis,minio}
mkdir -p production/backups/{daily,weekly,monthly}
mkdir -p production/monitoring/{grafana,prometheus}

# 2. Copy production configurations
echo "🔧 Step 2: Setting up production configurations..."
cp docker-compose.prod.yml production/
cp .env.prod production/
cp nginx.conf production/config/
cp *.sh production/scripts/

# 3. Generate SSL certificates for production
echo "🔒 Step 3: Generating SSL certificates..."
if [ ! -f production/ssl/qms.crt ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
        -keyout production/ssl/qms.key \
        -out production/ssl/qms.crt \
        -subj "/C=US/ST=Production/L=QMS/O=QMS Platform/CN=$DOMAIN_NAME" \
        -addext "subjectAltName=DNS:$DOMAIN_NAME,DNS:www.$DOMAIN_NAME"
    
    chmod 600 production/ssl/qms.key
    chmod 644 production/ssl/qms.crt
    echo "✅ SSL certificates generated for $DOMAIN_NAME"
else
    echo "✅ SSL certificates already exist"
fi

# 4. Set up production database with optimizations
echo "🗄️ Step 4: Setting up production database..."
cat > production/config/postgresql.conf << EOF
# QMS Platform Production PostgreSQL Configuration

# Memory Settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 64MB

# WAL Settings
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 1GB
min_wal_size = 80MB

# Connection Settings
max_connections = 100
shared_preload_libraries = 'pg_stat_statements'

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# Performance
random_page_cost = 1.1
effective_io_concurrency = 200
EOF

# 5. Configure Redis for production
echo "💾 Step 5: Setting up Redis production configuration..."
cat > production/config/redis.conf << EOF
# QMS Platform Production Redis Configuration

# Memory
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
rdbcompression yes
rdbchecksum yes

# Security
requirepass REDIS_PASSWORD_PLACEHOLDER

# Logging
loglevel notice
logfile /var/log/redis/redis.log

# Network
bind 0.0.0.0
port 6379
timeout 300
tcp-keepalive 300
EOF

# 6. Set up monitoring configuration
echo "📊 Step 6: Setting up monitoring and observability..."
cat > production/config/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: 'qms-platform'
    static_configs:
      - targets: ['qms-app-prod:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
EOF

# 7. Create production backup script
echo "💾 Step 7: Setting up automated backup system..."
cat > production/scripts/backup_production.sh << 'EOF'
#!/bin/bash

# QMS Platform Production Backup Script

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/qms/production/backups"
RETENTION_DAYS=90

echo "🔄 Starting QMS Platform backup - $TIMESTAMP"

# Database backup
echo "📊 Backing up PostgreSQL database..."
podman exec qms-db-prod pg_dump -U qms_user qms_prod | gzip > $BACKUP_DIR/daily/qms_db_$TIMESTAMP.sql.gz

# Application data backup
echo "📁 Backing up application data..."
tar -czf $BACKUP_DIR/daily/qms_data_$TIMESTAMP.tar.gz production/data/

# Configuration backup
echo "⚙️ Backing up configurations..."
tar -czf $BACKUP_DIR/daily/qms_config_$TIMESTAMP.tar.gz production/config/

# Cleanup old backups
echo "🧹 Cleaning up old backups..."
find $BACKUP_DIR/daily -name "*.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ Backup completed successfully - $TIMESTAMP"
EOF

chmod +x production/scripts/backup_production.sh

# 8. Create health check script
echo "🏥 Step 8: Setting up health monitoring..."
cat > production/scripts/health_check.sh << 'EOF'
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
EOF

chmod +x production/scripts/health_check.sh

# 9. Set up log rotation
echo "📝 Step 9: Configuring log rotation..."
cat > production/config/logrotate.conf << EOF
/opt/qms/production/logs/*/*.log {
    daily
    missingok
    rotate 365
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        podman kill --signal=USR1 qms-app-prod 2>/dev/null || true
    endscript
}
EOF

# 10. Create systemd service for production
echo "🔧 Step 10: Creating systemd service..."
cat > production/config/qms-platform.service << EOF
[Unit]
Description=QMS Platform v3.0 Production Service
After=network.target
Requires=network.target

[Service]
Type=forking
WorkingDirectory=/opt/qms/production
ExecStart=/usr/bin/podman-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/podman-compose -f docker-compose.prod.yml down
ExecReload=/usr/bin/podman-compose -f docker-compose.prod.yml restart
RemainAfterExit=yes
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "✅ Production environment setup completed!"
echo ""
echo "📋 Next Steps:"
echo "1. Review production configurations in production/config/"
echo "2. Update domain names and SSL certificates"
echo "3. Configure backup schedules"
echo "4. Set up monitoring alerts"
echo "5. Run health checks"
echo ""
echo "🚀 Production deployment ready!"
EOF