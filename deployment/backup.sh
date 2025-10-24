#!/bin/bash
# QMS Platform v3.0 - Backup Script

set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PREFIX="qms_prod_backup_${DATE}"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "📦 QMS Platform Backup - $(date)"
echo "=" * 50

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Function to log with timestamp
log_info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $1${NC}"
}

# Check if containers are running
if ! docker-compose -f docker-compose.prod.yml ps | grep -q "qms-db-prod.*Up"; then
    log_error "PostgreSQL container is not running"
    exit 1
fi

log_info "Starting backup process..."

# 1. Database Backup
log_info "Creating database backup..."
docker exec qms-db-prod pg_dump -U qms_user -d qms_prod > ${BACKUP_DIR}/${BACKUP_PREFIX}_database.sql

if [ $? -eq 0 ]; then
    log_success "Database backup created: ${BACKUP_PREFIX}_database.sql"
    # Compress database backup
    gzip ${BACKUP_DIR}/${BACKUP_PREFIX}_database.sql
    log_success "Database backup compressed"
else
    log_error "Database backup failed"
    exit 1
fi

# 2. Document Storage Backup
log_info "Creating document storage backup..."
if [ -d "storage/documents" ] && [ "$(ls -A storage/documents 2>/dev/null)" ]; then
    tar -czf ${BACKUP_DIR}/${BACKUP_PREFIX}_documents.tar.gz -C storage documents/
    log_success "Document storage backup created: ${BACKUP_PREFIX}_documents.tar.gz"
else
    log_warning "No documents found to backup"
    touch ${BACKUP_DIR}/${BACKUP_PREFIX}_documents_empty.txt
fi

# 3. Configuration Backup
log_info "Creating configuration backup..."
tar -czf ${BACKUP_DIR}/${BACKUP_PREFIX}_config.tar.gz \
    .env.prod \
    nginx.conf \
    docker-compose.prod.yml \
    ssl/ \
    --exclude=ssl/*.key 2>/dev/null || true

log_success "Configuration backup created: ${BACKUP_PREFIX}_config.tar.gz"

# 4. MinIO Data Backup (if accessible)
log_info "Attempting MinIO data backup..."
if docker exec qms-minio-prod mc --version &>/dev/null; then
    # Configure MinIO client
    docker exec qms-minio-prod mc alias set local http://localhost:9000 \
        $(grep MINIO_ROOT_USER .env.prod | cut -d= -f2) \
        $(grep MINIO_ROOT_PASSWORD .env.prod | cut -d= -f2) &>/dev/null
    
    # Backup MinIO data
    docker exec qms-minio-prod mc cp --recursive local/qms-documents-prod /tmp/minio_backup/ &>/dev/null
    docker cp qms-minio-prod:/tmp/minio_backup ${BACKUP_DIR}/${BACKUP_PREFIX}_minio_data
    log_success "MinIO data backup created"
else
    log_warning "MinIO client not available for data backup"
fi

# 5. Application Logs Backup
log_info "Creating logs backup..."
if [ -d "logs" ] && [ "$(ls -A logs 2>/dev/null)" ]; then
    tar -czf ${BACKUP_DIR}/${BACKUP_PREFIX}_logs.tar.gz logs/
    log_success "Logs backup created: ${BACKUP_PREFIX}_logs.tar.gz"
else
    log_warning "No logs found to backup"
fi

# 6. Create backup manifest
log_info "Creating backup manifest..."
cat > ${BACKUP_DIR}/${BACKUP_PREFIX}_manifest.txt << EOF
QMS Platform v3.0 Backup Manifest
Generated: $(date)
Backup ID: ${BACKUP_PREFIX}

Backup Contents:
- Database: ${BACKUP_PREFIX}_database.sql.gz
- Documents: ${BACKUP_PREFIX}_documents.tar.gz
- Configuration: ${BACKUP_PREFIX}_config.tar.gz
- MinIO Data: ${BACKUP_PREFIX}_minio_data/ (if available)
- Logs: ${BACKUP_PREFIX}_logs.tar.gz (if available)

System Information:
- Hostname: $(hostname)
- OS: $(uname -a)
- Docker Version: $(docker --version)
- Disk Usage: $(df -h .)

Database Statistics:
$(docker exec qms-db-prod psql -U qms_user -d qms_prod -c "
SELECT 
    'Users: ' || COUNT(*) 
FROM users
UNION ALL
SELECT 
    'Documents: ' || COUNT(*) 
FROM documents WHERE is_deleted = FALSE
UNION ALL
SELECT 
    'Quality Events: ' || COUNT(*) 
FROM quality_events WHERE is_deleted = FALSE
UNION ALL
SELECT 
    'CAPAs: ' || COUNT(*) 
FROM capas WHERE is_deleted = FALSE;
" -t 2>/dev/null || echo "Database stats unavailable")

Backup Size:
$(du -sh ${BACKUP_DIR}/${BACKUP_PREFIX}* 2>/dev/null | awk '{print "- " $2 ": " $1}')

EOF

log_success "Backup manifest created: ${BACKUP_PREFIX}_manifest.txt"

# 7. Calculate total backup size
TOTAL_SIZE=$(du -sh ${BACKUP_DIR}/${BACKUP_PREFIX}* | awk '{sum+=$1} END {print sum "B"}' 2>/dev/null || echo "Unknown")

log_success "Backup process completed successfully!"
echo ""
echo "📊 Backup Summary:"
echo "  - Backup ID: ${BACKUP_PREFIX}"
echo "  - Total Size: ${TOTAL_SIZE}"
echo "  - Location: ${BACKUP_DIR}/"
echo "  - Files:"
ls -la ${BACKUP_DIR}/${BACKUP_PREFIX}* | awk '{print "    " $9 " (" $5 " bytes)"}'

# 8. Cleanup old backups (keep last 30 days by default)
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."

find ${BACKUP_DIR} -name "qms_prod_backup_*" -type f -mtime +${RETENTION_DAYS} -delete
OLD_DIRS=$(find ${BACKUP_DIR} -name "qms_prod_backup_*_minio_data" -type d -mtime +${RETENTION_DAYS})
if [ ! -z "$OLD_DIRS" ]; then
    echo "$OLD_DIRS" | xargs rm -rf
fi

log_success "Old backups cleaned up"

echo ""
log_info "Backup retention policy: ${RETENTION_DAYS} days"
log_info "Current backup count: $(ls -1 ${BACKUP_DIR}/qms_prod_backup_*.sql.gz 2>/dev/null | wc -l)"

echo ""
echo "🔄 To restore from this backup:"
echo "  1. Stop QMS services: docker-compose -f docker-compose.prod.yml down"
echo "  2. Restore database: gunzip -c ${BACKUP_DIR}/${BACKUP_PREFIX}_database.sql.gz | docker exec -i qms-db-prod psql -U qms_user -d qms_prod"
echo "  3. Restore documents: tar -xzf ${BACKUP_DIR}/${BACKUP_PREFIX}_documents.tar.gz -C storage/"
echo "  4. Start services: docker-compose -f docker-compose.prod.yml up -d"

log_success "Backup completed successfully! 🎉"