# 🚀 QMS Platform v3.0 - Production Deployment Guide

## 📋 Overview
This guide provides comprehensive instructions for deploying the complete QMS Platform v3.0 to production environments for pharmaceutical organizations.

## 🎯 Deployment Scope
- **Phase 1**: Foundation (Users, Auth, Audit)
- **Phase 2**: EDMS (Electronic Document Management)  
- **Phase 3**: QRM (Quality Risk Management)
- **Complete Integration**: All modules working seamlessly
- **Production Grade**: Enterprise scalability and security

---

## 🏗️ Infrastructure Requirements

### **Minimum Production Requirements**
```yaml
Server Specifications:
  CPU: 4 cores (8 recommended)
  RAM: 8GB (16GB recommended)
  Storage: 100GB SSD (500GB recommended)
  Network: 1Gbps connection

Database:
  PostgreSQL: 14+ with 10GB initial space
  Backup Storage: 3x database size
  Connection Pool: 20-50 connections

File Storage:
  Document Storage: 100GB initial (scalable)
  Backup Storage: 2x document storage
  Access: High-speed file system or object storage

Load Balancer:
  SSL/TLS termination
  Health check support
  Session affinity (optional)
```

### **Recommended Production Architecture**
```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
│                   (nginx/HAProxy)                       │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│                 QMS Application                         │
│              (Docker Container)                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │   Phase 1   │ │   Phase 2   │ │   Phase 3   │      │
│  │ Foundation  │ │    EDMS     │ │     QRM     │      │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│                   Data Layer                            │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ │
│ │  PostgreSQL   │ │     Redis     │ │    MinIO      │ │
│ │   Database    │ │     Cache     │ │ File Storage  │ │
│ └───────────────┘ └───────────────┘ └───────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🐳 Container Deployment

### **Production Docker Compose**
Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

networks:
  qms-prod:
    driver: bridge

volumes:
  postgres_prod_data:
  redis_prod_data:
  minio_prod_data:
  qms_logs:

services:
  # PostgreSQL Database
  qms-db-prod:
    image: postgres:18
    container_name: qms-db-prod
    restart: unless-stopped
    environment:
      POSTGRES_DB: qms_prod
      POSTGRES_USER: qms_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.UTF-8"
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d:ro
      - ./backups:/backups
    networks:
      - qms-prod
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U qms_user -d qms_prod"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis Cache
  qms-redis-prod:
    image: redis:7-alpine
    container_name: qms-redis-prod
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_prod_data:/data
    networks:
      - qms-prod
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "--pass", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # MinIO Object Storage
  qms-minio-prod:
    image: minio/minio:latest
    container_name: qms-minio-prod
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_prod_data:/data
    networks:
      - qms-prod
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 60s
      timeout: 20s
      retries: 3

  # QMS Application
  qms-app-prod:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: qms-app-prod
    restart: unless-stopped
    environment:
      ENVIRONMENT: production
      DATABASE_URL: postgresql://qms_user:${POSTGRES_PASSWORD}@qms-db-prod:5432/qms_prod
      REDIS_URL: redis://:${REDIS_PASSWORD}@qms-redis-prod:6379
      SECRET_KEY: ${SECRET_KEY}
      MINIO_ENDPOINT: qms-minio-prod:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
      DOCUMENT_STORAGE_PATH: /app/storage/documents
    volumes:
      - qms_logs:/app/logs
      - ./storage:/app/storage
    networks:
      - qms-prod
    ports:
      - "8000:8000"
    depends_on:
      qms-db-prod:
        condition: service_healthy
      qms-redis-prod:
        condition: service_healthy
      qms-minio-prod:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx Reverse Proxy
  qms-nginx-prod:
    image: nginx:alpine
    container_name: qms-nginx-prod
    restart: unless-stopped
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - qms-prod
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - qms-app-prod
```

### **Production Dockerfile**
Create `Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Create necessary directories
RUN mkdir -p /app/logs /app/storage/documents

# Create non-root user
RUN groupadd -g 1000 qms && \
    useradd -r -u 1000 -g qms qms && \
    chown -R qms:qms /app

USER qms

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

---

## 🔐 Security Configuration

### **Environment Variables (.env.prod)**
```bash
# Database Configuration
POSTGRES_PASSWORD=your_secure_database_password_here
POSTGRES_HOST=qms-db-prod
POSTGRES_PORT=5432
POSTGRES_DB=qms_prod
POSTGRES_USER=qms_user

# Redis Configuration  
REDIS_PASSWORD=your_secure_redis_password_here
REDIS_HOST=qms-redis-prod
REDIS_PORT=6379

# Application Security
SECRET_KEY=your_256_bit_secret_key_here_make_it_very_long_and_random
JWT_SECRET_KEY=your_jwt_secret_key_here_also_very_long_and_random
ENCRYPTION_KEY=your_encryption_key_for_sensitive_data_here

# MinIO Configuration
MINIO_ROOT_USER=qms_minio_admin
MINIO_ROOT_PASSWORD=your_secure_minio_password_here
MINIO_BUCKET_NAME=qms-documents-prod

# Application Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
MAX_DOCUMENT_SIZE_MB=100
ALLOWED_DOCUMENT_EXTENSIONS=.pdf,.docx,.doc,.xlsx,.xls,.pptx,.txt

# SSL/TLS Configuration
SSL_CERT_PATH=/etc/nginx/ssl/qms.crt
SSL_KEY_PATH=/etc/nginx/ssl/qms.key

# Email Configuration (for notifications)
SMTP_HOST=your_smtp_server
SMTP_PORT=587
SMTP_USER=your_smtp_username
SMTP_PASSWORD=your_smtp_password
EMAIL_FROM=qms-noreply@yourcompany.com

# Backup Configuration
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
BACKUP_LOCATION=/backups
```

### **SSL/TLS Certificate Setup**
```bash
# Create SSL directory
mkdir -p ssl

# Generate self-signed certificate (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/qms.key \
    -out ssl/qms.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=qms.yourcompany.com"

# Set proper permissions
chmod 600 ssl/qms.key
chmod 644 ssl/qms.crt
```

### **Nginx Configuration**
Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream qms_app {
        server qms-app-prod:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=1r/s;

    server {
        listen 80;
        server_name qms.yourcompany.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name qms.yourcompany.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/qms.crt;
        ssl_certificate_key /etc/nginx/ssl/qms.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

        # File upload size
        client_max_body_size 100M;

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://qms_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Document upload (stricter rate limiting)
        location /api/v1/documents/upload {
            limit_req zone=upload burst=5 nodelay;
            proxy_pass http://qms_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://qms_app;
            access_log off;
        }

        # Static files (if any)
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

---

## 🗄️ Database Setup

### **Production Database Initialization**
```bash
# Create production database initialization script
cat > init_production_db.sh << 'EOF'
#!/bin/bash

echo "🗄️ Initializing QMS Production Database..."

# Wait for PostgreSQL to be ready
until docker exec qms-db-prod pg_isready -U qms_user -d qms_prod; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

echo "✅ PostgreSQL is ready"

# Run initialization scripts in order
echo "📋 Running database initialization scripts..."

# Phase 1: Foundation
docker exec qms-db-prod psql -U qms_user -d qms_prod -f /docker-entrypoint-initdb.d/01_create_extensions.sql
docker exec qms-db-prod psql -U qms_user -d qms_prod -f /docker-entrypoint-initdb.d/02_create_core_tables.sql
docker exec qms-db-prod psql -U qms_user -d qms_prod -f /docker-entrypoint-initdb.d/03_insert_default_data.sql

# Phase 2: EDMS
docker exec qms-db-prod psql -U qms_user -d qms_prod -f /docker-entrypoint-initdb.d/04_create_edms_tables.sql
docker exec qms-db-prod psql -U qms_user -d qms_prod -f /docker-entrypoint-initdb.d/05_insert_edms_data.sql

# Phase 3: QRM
docker exec qms-db-prod psql -U qms_user -d qms_prod -f /docker-entrypoint-initdb.d/06_create_qrm_tables.sql

# Create admin user
echo "👤 Creating admin user..."
docker exec qms-db-prod psql -U qms_user -d qms_prod -c "
INSERT INTO organizations (name, code, address, phone, email) 
VALUES ('Production Organization', 'PROD', '123 Production St', '+1-555-0100', 'admin@production.com')
ON CONFLICT (code) DO NOTHING;

INSERT INTO users (username, email, password_hash, first_name, last_name, organization_id, status) 
VALUES ('admin', 'admin@production.com', '\$2b\$12\$VMy7V4K9OHkXNP7VJZ9LSOzHuBU4E8A5wY3ZtZzKqP9M7t2nCY1aG', 'Admin', 'User', 1, 'ACTIVE')
ON CONFLICT (username) DO NOTHING;

INSERT INTO user_roles (user_id, role_id, assigned_by) 
VALUES (1, 1, 1)
ON CONFLICT DO NOTHING;
"

echo "✅ Database initialization complete!"
EOF

chmod +x init_production_db.sh
```

### **Database Backup Script**
```bash
# Create automated backup script
cat > backup_database.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="qms_prod_backup_${DATE}.sql"

echo "📦 Starting database backup..."

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

# Create database backup
docker exec qms-db-prod pg_dump -U qms_user -d qms_prod > ${BACKUP_DIR}/${BACKUP_FILE}

# Compress backup
gzip ${BACKUP_DIR}/${BACKUP_FILE}

echo "✅ Backup completed: ${BACKUP_FILE}.gz"

# Clean up old backups (keep last 30 days)
find ${BACKUP_DIR} -name "qms_prod_backup_*.sql.gz" -mtime +30 -delete

echo "🧹 Old backups cleaned up"
EOF

chmod +x backup_database.sh

# Add to crontab for daily backups
echo "0 2 * * * /path/to/backup_database.sh" | crontab -
```

---

## 🚀 Deployment Steps

### **Step 1: Server Preparation**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
sudo mkdir -p /opt/qms
sudo chown $USER:$USER /opt/qms
cd /opt/qms
```

### **Step 2: Application Deployment**
```bash
# Clone or copy application code
git clone https://github.com/yourusername/qms-platform.git .
# OR copy files from development environment

# Set up environment
cp .env.example .env.prod
# Edit .env.prod with production values

# Create required directories
mkdir -p storage/documents backups ssl nginx logs

# Set proper permissions
chmod 700 .env.prod
chmod -R 755 storage
chmod -R 700 ssl
```

### **Step 3: SSL Certificate Setup**
```bash
# Option 1: Let's Encrypt (recommended for production)
sudo apt install certbot
sudo certbot certonly --standalone -d qms.yourcompany.com
sudo cp /etc/letsencrypt/live/qms.yourcompany.com/fullchain.pem ssl/qms.crt
sudo cp /etc/letsencrypt/live/qms.yourcompany.com/privkey.pem ssl/qms.key

# Option 2: Self-signed certificate (for testing)
./generate_ssl_cert.sh
```

### **Step 4: Start Services**
```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# Initialize database
./init_production_db.sh

# Check application health
curl -k https://qms.yourcompany.com/health
```

### **Step 5: Verify Deployment**
```bash
# Test all endpoints
curl -k https://qms.yourcompany.com/api/v1/system/health

# Test authentication
curl -k -X POST https://qms.yourcompany.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123!"}'

# Check database connection
docker exec qms-db-prod psql -U qms_user -d qms_prod -c "SELECT COUNT(*) FROM users;"

# Verify document storage
docker exec qms-app-prod ls -la /app/storage/documents/
```

---

## 📊 Monitoring & Maintenance

### **Health Monitoring Script**
```bash
cat > monitor_qms.sh << 'EOF'
#!/bin/bash

echo "🔍 QMS Health Check - $(date)"

# Check container status
echo "📦 Container Status:"
docker-compose -f docker-compose.prod.yml ps

# Check application health
echo "🏥 Application Health:"
curl -s -k https://qms.yourcompany.com/health | jq '.'

# Check database connectivity
echo "🗄️ Database Health:"
docker exec qms-db-prod pg_isready -U qms_user -d qms_prod

# Check disk usage
echo "💾 Disk Usage:"
df -h | grep -E "(storage|backups)"

# Check recent logs for errors
echo "📋 Recent Errors:"
docker logs qms-app-prod --since="1h" | grep -i error | tail -5

echo "✅ Health check complete"
EOF

chmod +x monitor_qms.sh

# Schedule health checks
echo "*/15 * * * * /opt/qms/monitor_qms.sh >> /var/log/qms_health.log" | crontab -
```

### **Log Management**
```bash
# Set up log rotation
cat > /etc/logrotate.d/qms << 'EOF'
/opt/qms/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF

# Configure Docker log limits
echo '{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "5"
  }
}' | sudo tee /etc/docker/daemon.json

sudo systemctl restart docker
```

---

## 🔧 Troubleshooting Guide

### **Common Issues & Solutions**

**Issue**: Application won't start
```bash
# Check logs
docker logs qms-app-prod

# Check environment variables
docker exec qms-app-prod env | grep -E "(DATABASE|REDIS|MINIO)"

# Restart application
docker-compose -f docker-compose.prod.yml restart qms-app-prod
```

**Issue**: Database connection errors
```bash
# Check PostgreSQL status
docker exec qms-db-prod pg_isready -U qms_user -d qms_prod

# Check network connectivity
docker exec qms-app-prod nc -zv qms-db-prod 5432

# Reset database connection
docker-compose -f docker-compose.prod.yml restart qms-db-prod qms-app-prod
```

**Issue**: File upload failures
```bash
# Check storage permissions
docker exec qms-app-prod ls -la /app/storage/documents/

# Check MinIO status
curl -k http://localhost:9000/minio/health/live

# Check nginx file size limits
grep client_max_body_size nginx/nginx.conf
```

**Issue**: SSL certificate problems
```bash
# Check certificate validity
openssl x509 -in ssl/qms.crt -text -noout

# Renew Let's Encrypt certificate
sudo certbot renew

# Test SSL configuration
curl -k -I https://qms.yourcompany.com
```

---

## 📋 Production Checklist

### **Pre-Deployment Checklist**
- [ ] Server meets minimum requirements
- [ ] SSL certificates obtained and configured
- [ ] Environment variables properly set
- [ ] Database backup strategy in place
- [ ] Monitoring and alerting configured
- [ ] Security hardening completed
- [ ] Network firewall rules configured
- [ ] DNS records pointing to server

### **Post-Deployment Checklist**
- [ ] All services started successfully
- [ ] Database initialized with default data
- [ ] Admin user created and accessible
- [ ] All API endpoints responding
- [ ] SSL certificate working
- [ ] File upload/download working
- [ ] Backup script tested
- [ ] Monitoring alerts working
- [ ] User access testing completed
- [ ] Documentation provided to users

### **Go-Live Checklist**
- [ ] User training completed
- [ ] Data migration completed (if applicable)
- [ ] Integration testing with external systems
- [ ] Performance testing under load
- [ ] Disaster recovery plan tested
- [ ] Support procedures documented
- [ ] Compliance validation completed
- [ ] Business acceptance sign-off received

---

## 🎉 **PRODUCTION DEPLOYMENT SUCCESS!**

**Following this guide will result in a fully functional, secure, and scalable QMS Platform v3.0 deployment ready for pharmaceutical production use.**

**Key Benefits:**
- ✅ **Enterprise Security** - SSL/TLS, authentication, audit trails
- ✅ **High Availability** - Health checks, monitoring, auto-restart
- ✅ **Scalable Architecture** - Container-based, load balancer ready
- ✅ **Data Protection** - Automated backups, encryption at rest
- ✅ **Compliance Ready** - 21 CFR Part 11 audit trails and controls
- ✅ **Production Support** - Monitoring, logging, troubleshooting tools

**The QMS Platform is now ready to deliver world-class quality management capabilities to pharmaceutical organizations!** 🚀