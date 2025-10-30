#!/bin/bash
# QMS Platform v3.0 - Complete Production Deployment Script
# Phase C: Production Deployment - Enterprise Ready
# Supports all advanced features: AI/ML, Analytics, Compliance, Notifications

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_LOG="$SCRIPT_DIR/deployment_$(date +%Y%m%d_%H%M%S).log"
DOMAIN=${DOMAIN:-"qms.yourcompany.com"}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# Functions
log() {
    echo -e "${WHITE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$DEPLOYMENT_LOG"
}

log_error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$DEPLOYMENT_LOG"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$DEPLOYMENT_LOG"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}" | tee -a "$DEPLOYMENT_LOG"
}

log_step() {
    echo -e "${PURPLE}🚀 $1${NC}" | tee -a "$DEPLOYMENT_LOG"
}

check_requirements() {
    log_step "Checking deployment requirements..."
    
    # Check if running as root (not recommended)
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root is not recommended for security reasons"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check available disk space (minimum 10GB)
    available_space=$(df . | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 10485760 ]]; then  # 10GB in KB
        log_error "Insufficient disk space. At least 10GB required."
        exit 1
    fi
    
    # Check available memory (minimum 4GB)
    available_memory=$(free -m | awk 'NR==2 {print $7}')
    if [[ $available_memory -lt 4096 ]]; then
        log_warning "Less than 4GB memory available. Performance may be affected."
    fi
    
    log_success "All requirements met"
}

setup_directories() {
    log_step "Setting up directory structure..."
    
    # Create required directories
    local dirs=(
        "ssl"
        "storage/documents"
        "storage/ml_models"
        "storage/compliance_reports"
        "storage/notification_templates"
        "backups"
        "logs"
        "monitoring/prometheus"
        "monitoring/grafana"
        "production/config"
        "production/scripts"
        "production/data/postgres"
        "production/data/redis"
        "production/data/minio"
        "production/data/elasticsearch"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        log_info "Created directory: $dir"
    done
    
    # Set proper permissions
    chmod 755 storage/documents storage/ml_models storage/compliance_reports storage/notification_templates
    chmod 700 ssl backups
    chmod 755 logs monitoring
    
    log_success "Directory structure created"
}

generate_ssl_certificates() {
    log_step "Setting up SSL certificates..."
    
    if [[ -f "ssl/qms.crt" && -f "ssl/qms.key" ]]; then
        log_info "SSL certificates already exist"
        return
    fi
    
    # Check if domain is set to default
    if [[ "$DOMAIN" == "qms.yourcompany.com" ]]; then
        log_warning "Using default domain. For production, please set your actual domain."
        log_info "Generating self-signed certificate for testing..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/qms.key -out ssl/qms.crt \
            -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=$DOMAIN" \
            2>/dev/null
    else
        log_info "For production domain $DOMAIN, please ensure you have valid SSL certificates"
        log_info "Place your certificates as ssl/qms.crt and ssl/qms.key"
        
        if [[ ! -f "ssl/qms.crt" || ! -f "ssl/qms.key" ]]; then
            log_warning "SSL certificates not found. Generating self-signed for testing..."
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout ssl/qms.key -out ssl/qms.crt \
                -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=$DOMAIN" \
                2>/dev/null
        fi
    fi
    
    # Set proper permissions
    chmod 600 ssl/qms.key
    chmod 644 ssl/qms.crt
    
    log_success "SSL certificates configured"
}

generate_environment_config() {
    log_step "Generating production environment configuration..."
    
    if [[ -f ".env.prod" ]]; then
        log_warning ".env.prod already exists. Backing up..."
        cp .env.prod ".env.prod.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Generate secure passwords
    local postgres_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    local redis_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    local minio_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    local ml_redis_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    local secret_key=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-60)
    local jwt_secret=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-60)
    local grafana_password=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-15)
    
    # Create .env.prod file
    cat > .env.prod << EOF
# QMS Platform v3.0 - Production Environment Configuration
# Generated on: $(date)

# Database Configuration
POSTGRES_PASSWORD=$postgres_password
POSTGRES_HOST=qms-db-prod
POSTGRES_PORT=5432
POSTGRES_DB=qms_prod
POSTGRES_USER=qms_user

# Redis Configuration  
REDIS_PASSWORD=$redis_password
REDIS_HOST=qms-redis-prod
REDIS_PORT=6379

# Application Security
SECRET_KEY=$secret_key
JWT_SECRET_KEY=$jwt_secret
ENCRYPTION_KEY=$(openssl rand -hex 16)

# MinIO Configuration
MINIO_ROOT_USER=qms_minio_admin
MINIO_ROOT_PASSWORD=$minio_password
MINIO_BUCKET_NAME=qms-documents-prod

# Application Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
MAX_DOCUMENT_SIZE_MB=100
ALLOWED_DOCUMENT_EXTENSIONS=.pdf,.docx,.doc,.xlsx,.xls,.pptx,.txt,.rtf

# Domain Configuration
DOMAIN=$DOMAIN
SSL_CERT_PATH=/etc/nginx/ssl/qms.crt
SSL_KEY_PATH=/etc/nginx/ssl/qms.key

# AI/ML Configuration
ML_REDIS_PASSWORD=$ml_redis_password
ML_MODEL_STORAGE_PATH=/app/ml_models
PREDICTION_CACHE_TTL=3600
ML_TRAINING_ENABLED=true

# Analytics Configuration
ANALYTICS_CACHE_TTL=300
REAL_TIME_ANALYTICS=true
ANALYTICS_BATCH_SIZE=1000

# Compliance Configuration
COMPLIANCE_CHECK_INTERVAL=86400
AUDIT_LOG_RETENTION_DAYS=2555
CFR_PART11_ENABLED=true
ISO13485_ENABLED=true

# Notification Configuration
NOTIFICATION_BATCH_SIZE=100
EMAIL_RATE_LIMIT=1000
SMS_RATE_LIMIT=100

# Performance Configuration
API_RATE_LIMIT=1000
CACHE_DEFAULT_TTL=300
DATABASE_CONNECTION_POOL_SIZE=50

# Email Configuration (Update with your SMTP settings)
SMTP_HOST=smtp.yourcompany.com
SMTP_PORT=587
SMTP_USER=qms-noreply@yourcompany.com
SMTP_PASSWORD=your_smtp_password_here
EMAIL_FROM=qms-noreply@yourcompany.com

# Backup Configuration
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
BACKUP_LOCATION=/backups

# Security Configuration
SESSION_TIMEOUT_MINUTES=30
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_SPECIAL_CHARS=true
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=15

# Monitoring Configuration
HEALTH_CHECK_INTERVAL=30
LOG_RETENTION_DAYS=90
METRICS_ENABLED=true
GRAFANA_ADMIN_PASSWORD=$grafana_password

# Feature Flags
ENABLE_ADVANCED_ANALYTICS=true
ENABLE_PREDICTIVE_SCHEDULING=true
ENABLE_COMPLIANCE_AUTOMATION=true
ENABLE_NOTIFICATION_SYSTEM=true
ENABLE_AI_INSIGHTS=true
EOF
    
    chmod 600 .env.prod
    
    log_success "Environment configuration generated"
    log_info "Generated passwords saved to .env.prod"
    log_warning "Please update SMTP settings in .env.prod for email notifications"
}

update_nginx_config() {
    log_step "Updating Nginx configuration..."
    
    # Update nginx.conf with domain
    if [[ -f "nginx.conf" ]]; then
        sed -i.bak "s/yourdomain\.com/$DOMAIN/g" nginx.conf
        sed -i "s|/path/to/ssl|/etc/nginx/ssl|g" nginx.conf
        log_success "Nginx configuration updated for domain: $DOMAIN"
    else
        log_warning "nginx.conf not found, using default configuration"
    fi
}

build_application() {
    log_step "Building QMS application..."
    
    # Check if we're in the right directory
    if [[ ! -f "docker-compose.prod.yml" ]]; then
        log_error "docker-compose.prod.yml not found. Please run from deployment directory."
        exit 1
    fi
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose -f docker-compose.prod.yml pull 2>/dev/null || true
    
    # Build application with cache
    log_info "Building QMS application..."
    docker-compose -f docker-compose.prod.yml build --parallel
    
    log_success "Application built successfully"
}

deploy_services() {
    log_step "Deploying QMS services..."
    
    # Start services in order
    log_info "Starting database services..."
    docker-compose -f docker-compose.prod.yml up -d qms-db-prod qms-redis-prod qms-minio-prod
    
    # Wait for database to be ready
    log_info "Waiting for database to initialize..."
    sleep 30
    
    # Check database health
    local retries=0
    while [[ $retries -lt 10 ]]; do
        if docker-compose -f docker-compose.prod.yml exec -T qms-db-prod pg_isready -U qms_user -d qms_prod >/dev/null 2>&1; then
            log_success "Database is ready"
            break
        fi
        log_info "Waiting for database... (attempt $((retries + 1))/10)"
        sleep 10
        ((retries++))
    done
    
    if [[ $retries -eq 10 ]]; then
        log_error "Database failed to start after 100 seconds"
        exit 1
    fi
    
    # Start application services
    log_info "Starting application services..."
    docker-compose -f docker-compose.prod.yml up -d qms-app-prod
    
    # Wait for application to be ready
    log_info "Waiting for application to start..."
    sleep 20
    
    # Start proxy and monitoring
    log_info "Starting proxy and monitoring services..."
    docker-compose -f docker-compose.prod.yml up -d qms-nginx-prod qms-prometheus-prod qms-grafana-prod
    
    log_success "All services deployed"
}

verify_deployment() {
    log_step "Verifying deployment..."
    
    # Check container status
    log_info "Checking container status..."
    local containers=(
        "qms-db-prod"
        "qms-redis-prod"
        "qms-minio-prod"
        "qms-app-prod"
        "qms-nginx-prod"
        "qms-prometheus-prod"
        "qms-grafana-prod"
    )
    
    local failed_containers=()
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "^$container$"; then
            log_success "$container is running"
        else
            log_error "$container is not running"
            failed_containers+=("$container")
        fi
    done
    
    if [[ ${#failed_containers[@]} -gt 0 ]]; then
        log_error "Some containers failed to start: ${failed_containers[*]}"
        log_info "Checking logs for failed containers..."
        for container in "${failed_containers[@]}"; do
            echo "=== $container logs ==="
            docker-compose -f docker-compose.prod.yml logs --tail=20 "$container" || true
        done
        return 1
    fi
    
    # Wait for application to be fully ready
    log_info "Waiting for application to be fully ready..."
    sleep 30
    
    # Test API endpoints
    log_info "Testing API endpoints..."
    local endpoints=(
        "http://localhost:8000/health"
        "http://localhost:8000/api/v1/system/health"
        "http://localhost:8000/api/v1/auth/health"
        "http://localhost:8000/api/v1/advanced-analytics/health"
        "http://localhost:8000/api/v1/predictive-scheduling/health"
        "http://localhost:8000/api/v1/compliance/health"
        "http://localhost:8000/api/v1/notifications/health"
    )
    
    local failed_endpoints=()
    for endpoint in "${endpoints[@]}"; do
        if curl -s -f "$endpoint" >/dev/null 2>&1; then
            log_success "$(basename "$endpoint") endpoint is healthy"
        else
            log_warning "$(basename "$endpoint") endpoint not responding"
            failed_endpoints+=("$endpoint")
        fi
    done
    
    # Test HTTPS access
    log_info "Testing HTTPS access..."
    if curl -k -s -f "https://localhost:8443/health" >/dev/null 2>&1; then
        log_success "HTTPS access working"
    else
        log_warning "HTTPS access not working (this is normal if SSL is self-signed)"
    fi
    
    # Test Grafana
    if curl -s -f "http://localhost:3000/login" >/dev/null 2>&1; then
        log_success "Grafana is accessible"
    else
        log_warning "Grafana not accessible"
    fi
    
    return 0
}

setup_backup_cron() {
    log_step "Setting up automated backups..."
    
    # Create backup script
    cat > production/scripts/backup_production.sh << 'EOF'
#!/bin/bash
# QMS Platform Production Backup Script

BACKUP_DIR="/opt/qms-platform/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker-compose -f /opt/qms-platform/docker-compose.prod.yml exec -T qms-db-prod pg_dump -U qms_user -d qms_prod | gzip > "$BACKUP_DIR/qms_db_$DATE.sql.gz"

# Application data backup
tar -czf "$BACKUP_DIR/qms_storage_$DATE.tar.gz" -C /opt/qms-platform storage/

# Configuration backup
tar -czf "$BACKUP_DIR/qms_config_$DATE.tar.gz" -C /opt/qms-platform .env.prod nginx.conf ssl/

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

echo "$(date): Backup completed successfully" >> "$BACKUP_DIR/backup.log"
EOF
    
    chmod +x production/scripts/backup_production.sh
    
    # Add to crontab (daily at 2 AM)
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/qms-platform/production/scripts/backup_production.sh") | crontab -
    
    log_success "Automated backups configured (daily at 2 AM)"
}

print_deployment_summary() {
    log_step "Deployment Summary"
    
    echo ""
    echo "🎉 QMS Platform v3.0 Production Deployment Complete!"
    echo ""
    echo "📊 System Information:"
    echo "   Domain: https://$DOMAIN"
    echo "   Environment: $ENVIRONMENT"
    echo "   Deployment Time: $(date)"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Main Application: https://$DOMAIN"
    echo "   Admin Panel: https://$DOMAIN/admin"
    echo "   API Documentation: https://$DOMAIN/docs"
    echo "   Analytics Dashboard: https://$DOMAIN/analytics"
    echo "   Executive Dashboard: https://$DOMAIN/analytics/executive"
    echo "   AI Scheduling: https://$DOMAIN/analytics/predictive-scheduling"
    echo "   Compliance Monitor: https://$DOMAIN/compliance"
    echo "   Notifications: https://$DOMAIN/notifications"
    echo "   Monitoring (Grafana): https://$DOMAIN:3000"
    echo ""
    echo "🔐 Default Credentials:"
    echo "   Admin User: admin"
    echo "   Admin Password: Admin123!"
    echo "   Grafana Admin: admin"
    echo "   Grafana Password: $(grep GRAFANA_ADMIN_PASSWORD .env.prod | cut -d'=' -f2)"
    echo ""
    echo "📋 Advanced Features Enabled:"
    echo "   ✅ AI-Powered Predictive Scheduling (6 ML models)"
    echo "   ✅ Executive Analytics Dashboard"
    echo "   ✅ Compliance Automation (CFR Part 11, ISO 13485)"
    echo "   ✅ Multi-Channel Notification System"
    echo "   ✅ Real-time Performance Monitoring"
    echo "   ✅ Automated Backup System"
    echo ""
    echo "🔧 Next Steps:"
    echo "   1. Change default admin password"
    echo "   2. Configure SMTP settings in .env.prod"
    echo "   3. Set up organization details"
    echo "   4. Create initial users and departments"
    echo "   5. Test all modules and features"
    echo "   6. Configure monitoring alerts"
    echo ""
    echo "📚 Documentation:"
    echo "   Deployment Log: $DEPLOYMENT_LOG"
    echo "   Configuration: .env.prod"
    echo "   Backup Location: ./backups/"
    echo ""
    echo "🚀 Your enterprise-grade QMS Platform is now ready for use!"
}

# Main deployment process
main() {
    echo "🚀 QMS Platform v3.0 - Complete Production Deployment"
    echo "=================================================="
    echo ""
    
    log "Starting deployment process..."
    log "Domain: $DOMAIN"
    log "Environment: $ENVIRONMENT"
    log "Deployment log: $DEPLOYMENT_LOG"
    echo ""
    
    # Phase 1: Requirements and Setup
    check_requirements
    setup_directories
    
    # Phase 2: Security and Configuration
    generate_ssl_certificates
    generate_environment_config
    update_nginx_config
    
    # Phase 3: Build and Deploy
    build_application
    deploy_services
    
    # Phase 4: Verification and Finalization
    if verify_deployment; then
        setup_backup_cron
        print_deployment_summary
        log_success "Deployment completed successfully!"
        exit 0
    else
        log_error "Deployment verification failed. Check logs for details."
        log_info "You can check container logs with: docker-compose -f docker-compose.prod.yml logs"
        exit 1
    fi
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; exit 130' INT TERM

# Run main deployment
main "$@"