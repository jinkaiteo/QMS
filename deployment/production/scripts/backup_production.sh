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
