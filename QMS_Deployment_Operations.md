# QMS System - Deployment & Operations Guide

## Table of Contents
1. [Infrastructure Setup](#infrastructure-setup)
2. [Container Orchestration](#container-orchestration)
3. [Security Configuration](#security-configuration)
4. [Monitoring & Logging](#monitoring--logging)
5. [Backup & Recovery](#backup--recovery)
6. [Performance Optimization](#performance-optimization)
7. [Maintenance Procedures](#maintenance-procedures)

## Infrastructure Setup

### Server Requirements

#### Production Environment
```yaml
# Production Infrastructure Specifications
Servers:
  Load Balancer (2 nodes):
    - CPU: 4 cores
    - RAM: 8 GB
    - Storage: 100 GB SSD
    - OS: Ubuntu 20.04.6 LTS
    - Network: 1 Gbps
  
  Application Servers (3 nodes):
    - CPU: 8 cores
    - RAM: 32 GB
    - Storage: 500 GB SSD
    - OS: Ubuntu 20.04.6 LTS
    - Network: 1 Gbps
  
  Database Servers (2 nodes - Primary/Replica):
    - CPU: 16 cores
    - RAM: 64 GB
    - Storage: 2 TB NVMe SSD
    - OS: Ubuntu 20.04.6 LTS
    - Network: 10 Gbps
  
  Storage Server:
    - CPU: 8 cores
    - RAM: 16 GB
    - Storage: 10 TB (RAID 10)
    - OS: Ubuntu 20.04.6 LTS
    - Network: 10 Gbps

Network Architecture:
  - DMZ for load balancers
  - Internal network for application/database servers
  - Separate backup network
  - VPN access for administrators
```

### Base System Configuration
```bash
#!/bin/bash
# setup_qms_server.sh - Base server setup script

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y \
    podman \
    postgresql-client-14 \
    redis-tools \
    nginx \
    certbot \
    python3-certbot-nginx \
    fail2ban \
    ufw \
    htop \
    iotop \
    nethogs \
    ntp \
    logrotate

# Configure NTP for accurate timestamps (21 CFR Part 11 requirement)
cat > /etc/ntp.conf << EOF
driftfile /var/lib/ntp/ntp.drift
statistics loopstats peerstats clockstats
filegen loopstats file loopstats type day enable
filegen peerstats file peerstats type day enable
filegen clockstats file clockstats type day enable

# NTP servers for pharmaceutical compliance
server 0.pool.ntp.org iburst
server 1.pool.ntp.org iburst
server 2.pool.ntp.org iburst
server 3.pool.ntp.org iburst

# Restrict access
restrict -4 default kod notrap nomodify nopeer noquery limited
restrict -6 default kod notrap nomodify nopeer noquery limited
restrict 127.0.0.1
restrict ::1
EOF

systemctl enable ntp
systemctl start ntp

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[qms-auth]
enabled = true
filter = qms-auth
port = http,https
logpath = /var/log/qms/auth.log
maxretry = 5
bantime = 7200
EOF

systemctl enable fail2ban
systemctl start fail2ban

echo "Base system configuration completed"
```

## Container Orchestration

### Podman Configuration
```yaml
# podman-compose.yml - Production deployment
version: '3.8'

networks:
  qms-frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.1.0/24
  qms-backend:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.20.2.0/24
  qms-database:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.20.3.0/24

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/qms/data/postgres
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/qms/data/redis
  minio_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/qms/data/minio
  elasticsearch_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/qms/data/elasticsearch
  backup_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/qms/backups

services:
  # Frontend Service
  qms-frontend:
    image: qms/frontend:${QMS_VERSION:-latest}
    container_name: qms-frontend
    restart: always
    networks:
      - qms-frontend
    environment:
      - REACT_APP_API_URL=${API_URL}
      - REACT_APP_ENV=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m

  # API Service (Multiple instances for load balancing)
  qms-api-1:
    image: qms/api:${QMS_VERSION:-latest}
    container_name: qms-api-1
    restart: always
    networks:
      - qms-frontend
      - qms-backend
      - qms-database
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@qms-db:5432/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@qms-redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - ENVIRONMENT=production
    volumes:
      - /opt/qms/uploads:/app/uploads
      - /opt/qms/logs:/app/logs
    depends_on:
      - qms-db
      - qms-redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
    security_opt:
      - no-new-privileges:true

  qms-api-2:
    image: qms/api:${QMS_VERSION:-latest}
    container_name: qms-api-2
    restart: always
    networks:
      - qms-frontend
      - qms-backend
      - qms-database
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@qms-db:5432/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@qms-redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - ENVIRONMENT=production
    volumes:
      - /opt/qms/uploads:/app/uploads
      - /opt/qms/logs:/app/logs
    depends_on:
      - qms-db
      - qms-redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
    security_opt:
      - no-new-privileges:true

  # Background Workers
  qms-worker-1:
    image: qms/api:${QMS_VERSION:-latest}
    container_name: qms-worker-1
    restart: always
    command: celery worker -A app.celery -l info --concurrency=4
    networks:
      - qms-backend
      - qms-database
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@qms-db:5432/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@qms-redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@qms-redis:6379/1
    volumes:
      - /opt/qms/uploads:/app/uploads
      - /opt/qms/logs:/app/logs
    depends_on:
      - qms-db
      - qms-redis
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    security_opt:
      - no-new-privileges:true

  # Scheduler
  qms-scheduler:
    image: qms/api:${QMS_VERSION:-latest}
    container_name: qms-scheduler
    restart: always
    command: celery beat -A app.celery -l info
    networks:
      - qms-backend
      - qms-database
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@qms-db:5432/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@qms-redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@qms-redis:6379/1
    volumes:
      - /opt/qms/logs:/app/logs
    depends_on:
      - qms-db
      - qms-redis
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'
    security_opt:
      - no-new-privileges:true

  # Database
  qms-db:
    image: postgres:15
    container_name: qms-db
    restart: always
    networks:
      - qms-database
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_INITDB_ARGS=--encoding=UTF8 --locale=en_US.UTF-8
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - /opt/qms/db-init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
    security_opt:
      - no-new-privileges:true

  # Redis Cache
  qms-redis:
    image: redis:7-alpine
    container_name: qms-redis
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    networks:
      - qms-backend
      - qms-database
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '0.5'
    security_opt:
      - no-new-privileges:true

  # Object Storage (MinIO)
  qms-minio:
    image: minio/minio:latest
    container_name: qms-minio
    restart: always
    command: server /data --console-address ":9001"
    networks:
      - qms-backend
    environment:
      - MINIO_ROOT_USER=${MINIO_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_PASSWORD}
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    security_opt:
      - no-new-privileges:true

  # Search Engine
  qms-elasticsearch:
    image: elasticsearch:8.11.0
    container_name: qms-elasticsearch
    restart: always
    networks:
      - qms-backend
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms2g -Xmx2g
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
    security_opt:
      - no-new-privileges:true

  # Nginx Load Balancer
  qms-nginx:
    image: nginx:alpine
    container_name: qms-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    networks:
      - qms-frontend
    volumes:
      - /opt/qms/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /opt/qms/nginx/conf.d:/etc/nginx/conf.d:ro
      - /opt/qms/ssl:/etc/nginx/ssl:ro
      - /opt/qms/logs/nginx:/var/log/nginx
    depends_on:
      - qms-frontend
      - qms-api-1
      - qms-api-2
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
    security_opt:
      - no-new-privileges:true
```

### Load Balancer Configuration
```nginx
# /opt/qms/nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format for compliance
    log_format compliance '$remote_addr - $remote_user [$time_local] '
                         '"$request" $status $body_bytes_sent '
                         '"$http_referer" "$http_user_agent" '
                         '$request_time $upstream_response_time '
                         '$ssl_protocol $ssl_cipher';

    access_log /var/log/nginx/access.log compliance;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';" always;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate limiting for API
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=1r/s;

    # Upstream servers
    upstream qms_api {
        least_conn;
        server qms-api-1:8000 max_fails=3 fail_timeout=30s;
        server qms-api-2:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # Main server configuration
    server {
        listen 80;
        server_name qms.company.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name qms.company.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/qms.company.com.crt;
        ssl_certificate_key /etc/nginx/ssl/qms.company.com.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Frontend static files
        location / {
            proxy_pass http://qms-frontend:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://qms_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
            
            # Buffering for large file uploads
            proxy_buffering off;
            proxy_request_buffering off;
        }

        # Authentication endpoints (stricter rate limiting)
        location /api/v1/auth/ {
            limit_req zone=auth burst=5 nodelay;
            
            proxy_pass http://qms_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

This covers the comprehensive deployment and infrastructure setup. Would you like me to continue with the remaining sections on monitoring, backup procedures, and maintenance operations?