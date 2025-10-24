# 🚀 QMS Platform v3.0 - Production Deployment Checklist

## Pre-Deployment Checklist

### 🔧 System Requirements Verification
- [ ] Server meets minimum requirements (4 CPU, 8GB RAM, 100GB SSD)
- [ ] Docker and Docker Compose installed
- [ ] Firewall configured (ports 80, 443, 22)
- [ ] Domain name configured (DNS pointing to server)
- [ ] SSL certificate ready or Let's Encrypt available

### 🔐 Security Configuration
- [ ] Environment variables configured in `.env.prod`
- [ ] Strong passwords set (min 20 characters)
- [ ] SSL certificates installed in `ssl/` directory
- [ ] Server hardening completed
- [ ] Backup storage configured

### 📋 Configuration Steps
1. **Copy environment template**: `cp .env.prod.template .env.prod`
2. **Edit production values**: Update all passwords and keys
3. **Configure SSL**: Place certificates in `ssl/` directory
4. **Update nginx.conf**: Change server_name to your domain
5. **Create directories**: `mkdir -p ssl storage/documents backups logs`

## 🚀 Deployment Steps

### Step 1: Environment Configuration
```bash
# Edit .env.prod with production values
nano .env.prod

# Required changes:
# - POSTGRES_PASSWORD: Strong password (20+ chars)
# - REDIS_PASSWORD: Strong password (20+ chars) 
# - MINIO_ROOT_PASSWORD: Strong password (20+ chars)
# - SECRET_KEY: Random string (50+ chars)
# - JWT_SECRET_KEY: Different random string (50+ chars)
# - SMTP settings for email notifications
```

### Step 2: SSL Certificate Setup
Choose one option:

**Option A: Let's Encrypt (Recommended)**
```bash
sudo certbot certonly --standalone -d yourdomain.com
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/qms.crt
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/qms.key
```

**Option B: Self-signed (Testing)**
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/qms.key -out ssl/qms.crt \
    -subj "/CN=yourdomain.com"
```

### Step 3: Deploy QMS Platform
```bash
# Run deployment script
./deploy.sh
```

### Step 4: Verify Deployment
```bash
# Run comprehensive verification
./verify_deployment.sh

# Check system health
./monitor.sh
```

## ✅ Post-Deployment Tasks

### Immediate Tasks
- [ ] Change default admin password (admin/Admin123!)
- [ ] Create organizational users and roles
- [ ] Configure document types and categories
- [ ] Set up quality event types
- [ ] Test document upload/download
- [ ] Test quality event workflow
- [ ] Test CAPA creation and approval

### Security Tasks
- [ ] Review user permissions and roles
- [ ] Configure password policies
- [ ] Set up automated backups
- [ ] Configure monitoring alerts
- [ ] Review security headers and settings

### Operational Tasks
- [ ] Document admin procedures
- [ ] Train support staff
- [ ] Set up monitoring dashboards
- [ ] Configure log rotation
- [ ] Plan disaster recovery procedures

## 🎯 Success Criteria

Your deployment is successful when:
- ✅ All containers running and healthy
- ✅ HTTPS access works with valid SSL
- ✅ Admin login successful (admin/Admin123!)
- ✅ All API endpoints responding
- ✅ Document management working
- ✅ Quality event creation working
- ✅ CAPA workflow functional
- ✅ Backup script working
- ✅ Monitoring showing all systems healthy

## 🆘 Troubleshooting

### Common Issues
1. **Containers won't start**: Check `.env.prod` values and Docker logs
2. **SSL certificate errors**: Verify certificate files and permissions
3. **Database connection fails**: Check PostgreSQL container and credentials
4. **Application 500 errors**: Check application logs and database connectivity
5. **File upload fails**: Check storage permissions and MinIO configuration

### Quick Diagnostics
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs

# Test connectivity
curl -k https://localhost/health

# Run verification
./verify_deployment.sh
```

## 📞 Support

For deployment issues:
1. Check this checklist for missed steps
2. Review logs: `docker-compose -f docker-compose.prod.yml logs`
3. Run verification: `./verify_deployment.sh`
4. Check troubleshooting section in main guide

## 🎉 Success!

Once all items are checked and verified:
- Your QMS Platform v3.0 is production ready
- All pharmaceutical quality management features are operational
- The system is compliant with 21 CFR Part 11 requirements
- You have a world-class quality management platform!

**Welcome to enterprise pharmaceutical quality management!** 🚀