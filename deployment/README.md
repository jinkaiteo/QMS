# 🚀 QMS Platform v3.0 - Production Deployment

## Overview
This directory contains all the necessary files and scripts for deploying the complete QMS Platform v3.0 to a production environment.

## 📋 Contents

### Core Deployment Files
- `docker-compose.prod.yml` - Production Docker Compose configuration
- `Dockerfile.prod` - Production Docker image definition
- `nginx.conf` - Nginx reverse proxy configuration
- `.env.prod.template` - Environment variables template

### Deployment Scripts
- `deploy.sh` - Main deployment automation script
- `init_database.sh` - Database initialization script
- `verify_deployment.sh` - Deployment verification and testing
- `backup.sh` - Automated backup script
- `monitor.sh` - System monitoring and health checks

### Documentation
- `README.md` - This file
- `PRODUCTION_DEPLOYMENT_GUIDE.md` - Comprehensive deployment guide

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.prod.template .env.prod

# Edit with your production values
nano .env.prod
```

**Required Changes:**
- Set secure passwords for `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `MINIO_ROOT_PASSWORD`
- Set long random strings for `SECRET_KEY` and `JWT_SECRET_KEY`
- Configure SMTP settings for notifications
- Update server name in `nginx.conf`

### 3. Deploy
```bash
# Make scripts executable
chmod +x *.sh

# Run deployment
./deploy.sh
```

### 4. Verify
```bash
# Run verification tests
./verify_deployment.sh

# Check system health
./monitor.sh
```

## 📊 System Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 100GB SSD
- **Network**: 1Gbps connection

### Recommended for Production
- **CPU**: 8 cores
- **RAM**: 16GB
- **Storage**: 500GB SSD
- **Network**: 1Gbps connection
- **Load Balancer**: For high availability

## 🔐 Security Configuration

### SSL/TLS Setup
Choose one option:

**Option 1: Let's Encrypt (Recommended)**
```bash
# Install certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d qms.yourcompany.com

# Copy certificates
sudo cp /etc/letsencrypt/live/qms.yourcompany.com/fullchain.pem ssl/qms.crt
sudo cp /etc/letsencrypt/live/qms.yourcompany.com/privkey.pem ssl/qms.key
```

**Option 2: Self-signed (Testing Only)**
```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/qms.key \
    -out ssl/qms.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=qms.yourcompany.com"
```

### Firewall Configuration
```bash
# Allow required ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (redirects to HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## 🔄 Operations

### Daily Operations
```bash
# Check system health
./monitor.sh

# View live monitoring
./monitor.sh true 30  # Updates every 30 seconds

# Create backup
./backup.sh

# View logs
docker-compose -f docker-compose.prod.yml logs -f qms-app-prod
```

### Maintenance Commands
```bash
# Restart application only
docker-compose -f docker-compose.prod.yml restart qms-app-prod

# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Update application (after code changes)
docker-compose -f docker-compose.prod.yml build --no-cache qms-app-prod
docker-compose -f docker-compose.prod.yml up -d qms-app-prod

# View service status
docker-compose -f docker-compose.prod.yml ps
```

### Backup and Restore
```bash
# Create backup
./backup.sh

# List backups
ls -la backups/

# Restore from backup (replace TIMESTAMP with actual timestamp)
gunzip -c backups/qms_prod_backup_TIMESTAMP_database.sql.gz | \
    docker exec -i qms-db-prod psql -U qms_user -d qms_prod
```

## 📈 Monitoring

### Health Monitoring
```bash
# One-time health check
./monitor.sh

# Continuous monitoring (updates every 30 seconds)
./monitor.sh true 30

# Check specific service
curl -k https://localhost/health
```

### Log Monitoring
```bash
# Application logs
docker logs qms-app-prod --follow

# Database logs
docker logs qms-db-prod --follow

# Nginx logs
docker logs qms-nginx-prod --follow

# All service logs
docker-compose -f docker-compose.prod.yml logs --follow
```

### Performance Monitoring
```bash
# Container resource usage
docker stats

# System resources
htop

# Disk usage
df -h
du -sh storage/ backups/
```

## 🛠️ Troubleshooting

### Common Issues

**Application won't start:**
```bash
# Check logs
docker logs qms-app-prod

# Check configuration
docker exec qms-app-prod env | grep -E "(DATABASE|REDIS)"

# Restart application
docker-compose -f docker-compose.prod.yml restart qms-app-prod
```

**Database connection issues:**
```bash
# Check PostgreSQL
docker exec qms-db-prod pg_isready -U qms_user -d qms_prod

# Test connection from app
docker exec qms-app-prod nc -zv qms-db-prod 5432

# Restart database
docker-compose -f docker-compose.prod.yml restart qms-db-prod
```

**File upload failures:**
```bash
# Check storage permissions
docker exec qms-app-prod ls -la /app/storage/

# Check MinIO
curl -f http://localhost:9000/minio/health/live

# Check nginx file limits
grep client_max_body_size nginx.conf
```

**SSL certificate issues:**
```bash
# Check certificate validity
openssl x509 -in ssl/qms.crt -text -noout

# Test SSL
curl -I https://localhost:443/health
```

### Getting Help
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Run verification: `./verify_deployment.sh`
3. Check monitoring: `./monitor.sh`
4. Review troubleshooting section in main deployment guide

## 🔧 Configuration Reference

### Environment Variables
See `.env.prod.template` for all available configuration options.

### Key Settings
- `POSTGRES_PASSWORD`: Database password
- `SECRET_KEY`: Application secret key (minimum 50 characters)
- `JWT_SECRET_KEY`: JWT signing key (different from SECRET_KEY)
- `MINIO_ROOT_PASSWORD`: Object storage password
- `SMTP_*`: Email notification settings

### Docker Compose Services
- `qms-db-prod`: PostgreSQL database
- `qms-redis-prod`: Redis cache
- `qms-minio-prod`: MinIO object storage
- `qms-app-prod`: QMS application
- `qms-nginx-prod`: Nginx reverse proxy

## 📋 Post-Deployment Checklist

### Immediate Tasks
- [ ] Change default admin password (admin/Admin123!)
- [ ] Configure document types and categories
- [ ] Set up quality event types
- [ ] Create additional users and assign roles
- [ ] Test document upload/download
- [ ] Test quality event creation
- [ ] Test CAPA workflow

### Security Tasks
- [ ] Review user permissions
- [ ] Configure password policies
- [ ] Set up SSL certificate auto-renewal
- [ ] Configure firewall rules
- [ ] Enable security monitoring

### Operational Tasks
- [ ] Set up automated backups (cron job)
- [ ] Configure monitoring alerts
- [ ] Document admin procedures
- [ ] Train support staff
- [ ] Plan disaster recovery

## 🎯 Success Criteria

Your deployment is successful when:
- ✅ All containers are running and healthy
- ✅ HTTPS access works with valid SSL certificate
- ✅ Admin login works (admin/Admin123!)
- ✅ All API endpoints respond correctly
- ✅ Document upload/download works
- ✅ Database backup completes successfully
- ✅ Monitoring shows all systems healthy

## 📞 Support

For deployment support:
1. Review the comprehensive deployment guide
2. Check troubleshooting section
3. Run verification script for detailed diagnostics
4. Check application logs for specific error messages

## 🎉 Congratulations!

Once deployed successfully, you'll have a complete, production-ready QMS Platform v3.0 with:
- Complete pharmaceutical quality management
- 21 CFR Part 11 compliance
- Enterprise-grade security and scalability
- Comprehensive audit trails
- Integrated document and quality management

**Welcome to world-class pharmaceutical quality management!** 🚀