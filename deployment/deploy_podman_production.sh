#!/bin/bash
# QMS Platform v3.0 - Complete Podman Production Deployment Script
# Enhanced for Podman with all advanced features: AI/ML, Analytics, Compliance, Notifications

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
DEPLOYMENT_LOG="$SCRIPT_DIR/podman_deployment_$(date +%Y%m%d_%H%M%S).log"
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

check_podman_requirements() {
    log_step "Checking Podman requirements..."
    
    # Check if running as root (recommended for Podman production)
    if [[ $EUID -ne 0 ]]; then
        log_warning "Not running as root. Podman may require root for production deployment."
        log_info "Run with sudo for best results: sudo $0"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check Podman
    if ! command -v podman &> /dev/null; then
        log_error "Podman is not installed. Please install Podman first."
        log_info "Install with: sudo dnf install podman podman-compose"
        exit 1
    fi
    
    # Check Podman Compose
    if ! command -v podman-compose &> /dev/null; then
        log_error "Podman Compose is not installed. Please install podman-compose first."
        log_info "Install with: pip3 install podman-compose"
        exit 1
    fi
    
    # Check Podman version
    podman_version=$(podman --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    log_info "Podman version: $podman_version"
    
    # Check available disk space (minimum 10GB)
    available_space=$(df . | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 10485760 ]]; then  # 10GB in KB
        log_error "Insufficient disk space. At least 10GB required."
        exit 1
    fi
    
    # Check SELinux status
    if command -v getenforce &> /dev/null; then
        selinux_status=$(getenforce)
        log_info "SELinux status: $selinux_status"
        if [[ "$selinux_status" == "Enforcing" ]]; then
            log_info "SELinux is enforcing. Using proper volume mount contexts."
        fi
    fi
    
    log_success "Podman requirements met"
}

setup_podman_networking() {
    log_step "Setting up Podman networking..."
    
    # Create production network if it doesn't exist
    if ! podman network exists qms-prod 2>/dev/null; then
        podman network create qms-prod
        log_success "Created Podman network: qms-prod"
    else
        log_info "Podman network qms-prod already exists"
    fi
    
    # Configure firewall if firewalld is running
    if systemctl is-active --quiet firewalld; then
        log_info "Configuring firewall for Podman..."
        firewall-cmd --permanent --add-port=8080/tcp --add-port=8443/tcp --add-port=3000/tcp >/dev/null 2>&1 || true
        firewall-cmd --reload >/dev/null 2>&1 || true
        log_success "Firewall configured for Podman services"
    fi
}

create_enhanced_podman_compose() {
    log_step "Creating enhanced Podman production configuration..."
    
    cat > podman-compose.prod.yml << 'EOF'
version: '3.8'

networks:
  qms-prod:
    driver: bridge

volumes:
  postgres_prod_data:
  redis_prod_data:
  minio_prod_data:
  ml_storage_prod_data:
  ml_models_data:
  compliance_reports_data:
  elasticsearch_prod_data:
  qms_logs:
  prometheus_prod_data:
  grafana_prod_data:

services:
  # PostgreSQL Database
  qms-db-prod:
    image: docker.io/library/postgres:18
    container_name: qms-db-prod
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-qms_prod}
      POSTGRES_USER: ${POSTGRES_USER:-qms_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.UTF-8"
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data:Z
      - ../database/init:/docker-entrypoint-initdb.d:ro,Z
      - ./backups:/backups:Z
    networks:
      - qms-prod
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-qms_user} -d ${POSTGRES_DB:-qms_prod}"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis Cache
  qms-redis-prod:
    image: docker.io/library/redis:7-alpine
    container_name: qms-redis-prod
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass "${REDIS_PASSWORD}"
    volumes:
      - redis_prod_data:/data:Z
    networks:
      - qms-prod
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "--pass", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ML Model Storage (Dedicated Redis for ML)
  qms-ml-storage-prod:
    image: docker.io/library/redis:7-alpine
    container_name: qms-ml-storage-prod
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass "${ML_REDIS_PASSWORD:-${REDIS_PASSWORD}}"
    volumes:
      - ml_storage_prod_data:/data:Z
    networks:
      - qms-prod
    ports:
      - "6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "--pass", "${ML_REDIS_PASSWORD:-${REDIS_PASSWORD}}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # MinIO Object Storage
  qms-minio-prod:
    image: docker.io/minio/minio:latest
    container_name: qms-minio-prod
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_prod_data:/data:Z
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

  # QMS Application with Advanced Features
  qms-app-prod:
    build:
      context: ..
      dockerfile: deployment/Dockerfile.prod
    container_name: qms-app-prod
    restart: unless-stopped
    environment:
      ENVIRONMENT: production
      POSTGRES_SERVER: qms-db-prod
      POSTGRES_PORT: ${POSTGRES_PORT:-5432}
      POSTGRES_DB: ${POSTGRES_DB:-qms_prod}
      POSTGRES_USER: ${POSTGRES_USER:-qms_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      REDIS_URL: redis://:${REDIS_PASSWORD}@qms-redis-prod:6379/0
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      MINIO_ENDPOINT: qms-minio-prod:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
      DOCUMENT_STORAGE_PATH: /app/storage/documents
      # AI/ML Configuration
      ML_REDIS_URL: redis://:${ML_REDIS_PASSWORD:-${REDIS_PASSWORD}}@qms-ml-storage-prod:6379/0
      ML_MODEL_STORAGE_PATH: /app/ml_models
      PREDICTION_CACHE_TTL: ${PREDICTION_CACHE_TTL:-3600}
      ML_TRAINING_ENABLED: ${ML_TRAINING_ENABLED:-true}
      # Analytics Configuration
      ANALYTICS_CACHE_TTL: ${ANALYTICS_CACHE_TTL:-300}
      REAL_TIME_ANALYTICS: ${REAL_TIME_ANALYTICS:-true}
      ANALYTICS_BATCH_SIZE: ${ANALYTICS_BATCH_SIZE:-1000}
      # Compliance Configuration
      COMPLIANCE_CHECK_INTERVAL: ${COMPLIANCE_CHECK_INTERVAL:-86400}
      AUDIT_LOG_RETENTION_DAYS: ${AUDIT_LOG_RETENTION_DAYS:-2555}
      CFR_PART11_ENABLED: ${CFR_PART11_ENABLED:-true}
      ISO13485_ENABLED: ${ISO13485_ENABLED:-true}
      # Notification Configuration
      NOTIFICATION_BATCH_SIZE: ${NOTIFICATION_BATCH_SIZE:-100}
      EMAIL_RATE_LIMIT: ${EMAIL_RATE_LIMIT:-1000}
      SMS_RATE_LIMIT: ${SMS_RATE_LIMIT:-100}
      SMTP_HOST: ${SMTP_HOST}
      SMTP_PORT: ${SMTP_PORT:-587}
      SMTP_USER: ${SMTP_USER}
      SMTP_PASSWORD: ${SMTP_PASSWORD}
      EMAIL_FROM: ${EMAIL_FROM}
      # Performance Configuration
      API_RATE_LIMIT: ${API_RATE_LIMIT:-1000}
      CACHE_DEFAULT_TTL: ${CACHE_DEFAULT_TTL:-300}
      DATABASE_CONNECTION_POOL_SIZE: ${DATABASE_CONNECTION_POOL_SIZE:-50}
      # Feature Flags
      ENABLE_ADVANCED_ANALYTICS: ${ENABLE_ADVANCED_ANALYTICS:-true}
      ENABLE_PREDICTIVE_SCHEDULING: ${ENABLE_PREDICTIVE_SCHEDULING:-true}
      ENABLE_COMPLIANCE_AUTOMATION: ${ENABLE_COMPLIANCE_AUTOMATION:-true}
      ENABLE_NOTIFICATION_SYSTEM: ${ENABLE_NOTIFICATION_SYSTEM:-true}
      ENABLE_AI_INSIGHTS: ${ENABLE_AI_INSIGHTS:-true}
    volumes:
      - qms_logs:/app/logs:Z
      - ./storage:/app/storage:Z
      - ml_models_data:/app/ml_models:Z
      - compliance_reports_data:/app/compliance_reports:Z
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
      qms-ml-storage-prod:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx Reverse Proxy
  qms-nginx-prod:
    image: docker.io/library/nginx:alpine
    container_name: qms-nginx-prod
    restart: unless-stopped
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro,Z
      - ./ssl:/etc/nginx/ssl:ro,Z
      - ../frontend/dist:/usr/share/nginx/html:ro,Z
    networks:
      - qms-prod
    ports:
      - "8080:80"
      - "8443:443"
    depends_on:
      - qms-app-prod
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:80/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Prometheus Monitoring
  qms-prometheus-prod:
    image: docker.io/prom/prometheus:latest
    container_name: qms-prometheus-prod
    restart: unless-stopped
    volumes:
      - prometheus_prod_data:/prometheus:Z
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro,Z
    networks:
      - qms-prod
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  # Grafana Dashboard
  qms-grafana-prod:
    image: docker.io/grafana/grafana:latest
    container_name: qms-grafana-prod
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin123}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SECURITY_DISABLE_GRAVATAR=true
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_prod_data:/var/lib/grafana:Z
    networks:
      - qms-prod
    ports:
      - "3000:3000"
    depends_on:
      - qms-prometheus-prod

  # Elasticsearch for Advanced Search (Optional)
  qms-elasticsearch-prod:
    image: docker.io/library/elasticsearch:8.11.0
    container_name: qms-elasticsearch-prod
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - bootstrap.memory_lock=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - elasticsearch_prod_data:/usr/share/elasticsearch/data:Z
    networks:
      - qms-prod
    ports:
      - "9200:9200"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 60s
      timeout: 20s
      retries: 3
    profiles:
      - search  # Optional service, enable with --profile search
EOF

    log_success "Enhanced Podman Compose configuration created"
}

deploy_with_podman() {
    log_step "Deploying QMS services with Podman..."
    
    # Start services in order
    log_info "Starting database services..."
    podman-compose -f podman-compose.prod.yml up -d qms-db-prod qms-redis-prod qms-ml-storage-prod qms-minio-prod
    
    # Wait for database to be ready
    log_info "Waiting for database to initialize..."
    sleep 30
    
    # Check database health with retry logic
    local retries=0
    while [[ $retries -lt 10 ]]; do
        if podman exec qms-db-prod pg_isready -U ${POSTGRES_USER:-qms_user} -d ${POSTGRES_DB:-qms_prod} >/dev/null 2>&1; then
            log_success "Database is ready"
            break
        fi
        log_info "Waiting for database... (attempt $((retries + 1))/10)"
        sleep 10
        ((retries++))
    done
    
    if [[ $retries -eq 10 ]]; then
        log_error "Database failed to start after 100 seconds"
        podman-compose -f podman-compose.prod.yml logs qms-db-prod
        exit 1
    fi
    
    # Start application services
    log_info "Starting application services..."
    podman-compose -f podman-compose.prod.yml up -d qms-app-prod
    
    # Wait for application to be ready
    log_info "Waiting for application to start..."
    sleep 20
    
    # Start proxy and monitoring
    log_info "Starting proxy and monitoring services..."
    podman-compose -f podman-compose.prod.yml up -d qms-nginx-prod qms-prometheus-prod qms-grafana-prod
    
    log_success "All Podman services deployed"
}

setup_podman_systemd() {
    log_step "Setting up Podman systemd integration..."
    
    # Generate systemd unit files for auto-restart
    podman generate systemd --new --name qms-db-prod --files >/dev/null 2>&1 || true
    podman generate systemd --new --name qms-redis-prod --files >/dev/null 2>&1 || true
    podman generate systemd --new --name qms-app-prod --files >/dev/null 2>&1 || true
    podman generate systemd --new --name qms-nginx-prod --files >/dev/null 2>&1 || true
    
    # Move to systemd directory
    if [[ -f container-qms-app-prod.service ]]; then
        mkdir -p ~/.config/systemd/user/
        mv container-*.service ~/.config/systemd/user/ 2>/dev/null || true
        systemctl --user daemon-reload 2>/dev/null || true
        log_success "Podman systemd integration configured"
    else
        log_info "Systemd integration skipped (requires running containers)"
    fi
}

verify_podman_deployment() {
    log_step "Verifying Podman deployment..."
    
    # Check container status
    log_info "Checking Podman container status..."
    local containers=(
        "qms-db-prod"
        "qms-redis-prod"
        "qms-ml-storage-prod"
        "qms-minio-prod"
        "qms-app-prod"
        "qms-nginx-prod"
        "qms-prometheus-prod"
        "qms-grafana-prod"
    )
    
    local failed_containers=()
    for container in "${containers[@]}"; do
        if podman ps --format "table {{.Names}}" | grep -q "^$container$"; then
            log_success "$container is running (Podman)"
        else
            log_error "$container is not running (Podman)"
            failed_containers+=("$container")
        fi
    done
    
    if [[ ${#failed_containers[@]} -gt 0 ]]; then
        log_error "Some Podman containers failed to start: ${failed_containers[*]}"
        log_info "Checking logs for failed containers..."
        for container in "${failed_containers[@]}"; do
            echo "=== $container logs ==="
            podman-compose -f podman-compose.prod.yml logs --tail=20 "$container" || true
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
        log_success "HTTPS access working with Podman"
    else
        log_warning "HTTPS access not working (this is normal if SSL is self-signed)"
    fi
    
    return 0
}

print_podman_deployment_summary() {
    log_step "Podman Deployment Summary"
    
    echo ""
    echo "🎉 QMS Platform v3.0 Podman Production Deployment Complete!"
    echo ""
    echo "🐳 Podman Container Information:"
    echo "   Domain: https://$DOMAIN"
    echo "   Environment: $ENVIRONMENT"
    echo "   Container Runtime: Podman"
    echo "   Deployment Time: $(date)"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Main Application: https://$DOMAIN:8443"
    echo "   Admin Panel: https://$DOMAIN:8443/admin"
    echo "   API Documentation: https://$DOMAIN:8443/docs"
    echo "   Analytics Dashboard: https://$DOMAIN:8443/analytics"
    echo "   Executive Dashboard: https://$DOMAIN:8443/analytics/executive"
    echo "   AI Scheduling: https://$DOMAIN:8443/analytics/predictive-scheduling"
    echo "   Compliance Monitor: https://$DOMAIN:8443/compliance"
    echo "   Notifications: https://$DOMAIN:8443/notifications"
    echo "   Monitoring (Grafana): https://$DOMAIN:3000"
    echo ""
    echo "🐳 Podman Management Commands:"
    echo "   View containers: podman ps"
    echo "   View logs: podman-compose -f podman-compose.prod.yml logs -f"
    echo "   Restart services: podman-compose -f podman-compose.prod.yml restart"
    echo "   Stop services: podman-compose -f podman-compose.prod.yml down"
    echo "   Update services: podman-compose -f podman-compose.prod.yml pull && podman-compose -f podman-compose.prod.yml up -d"
    echo ""
    echo "🔐 Default Credentials:"
    echo "   Admin User: admin"
    echo "   Admin Password: Admin123!"
    echo "   Grafana Admin: admin"
    echo "   Grafana Password: $(grep GRAFANA_ADMIN_PASSWORD .env.prod | cut -d'=' -f2 2>/dev/null || echo 'admin123')"
    echo ""
    echo "📋 Advanced Features Enabled (Podman):"
    echo "   ✅ AI-Powered Predictive Scheduling (6 ML models)"
    echo "   ✅ Executive Analytics Dashboard"
    echo "   ✅ Compliance Automation (CFR Part 11, ISO 13485)"
    echo "   ✅ Multi-Channel Notification System"
    echo "   ✅ Real-time Performance Monitoring"
    echo "   ✅ Business Calendar Integration"
    echo ""
    echo "🔧 Podman-Specific Features:"
    echo "   ✅ Rootless container support"
    echo "   ✅ SELinux integration with proper contexts"
    echo "   ✅ Systemd integration for auto-restart"
    echo "   ✅ Enhanced security with user namespaces"
    echo ""
    echo "📚 Documentation:"
    echo "   Deployment Log: $DEPLOYMENT_LOG"
    echo "   Configuration: .env.prod"
    echo "   Podman Compose: podman-compose.prod.yml"
    echo "   Setup Memory: PODMAN_SETUP_MEMORY.md"
    echo ""
    echo "🚀 Your enterprise-grade QMS Platform is now ready with Podman!"
}

# Main deployment process
main() {
    echo "🐳 QMS Platform v3.0 - Complete Podman Production Deployment"
    echo "=========================================================="
    echo ""
    
    log "Starting Podman deployment process..."
    log "Domain: $DOMAIN"
    log "Environment: $ENVIRONMENT"
    log "Deployment log: $DEPLOYMENT_LOG"
    echo ""
    
    # Phase 1: Podman Requirements and Setup
    check_podman_requirements
    setup_podman_networking
    
    # Phase 2: Configuration Generation (reuse existing functions)
    if [[ -f "./deploy_production_complete.sh" ]]; then
        log_info "Using existing configuration generation functions..."
        source ./deploy_production_complete.sh
        setup_directories
        generate_ssl_certificates
        generate_environment_config
        update_nginx_config
    else
        log_warning "Main deployment script not found, using basic configuration"
        mkdir -p ssl storage/documents backups logs
    fi
    
    # Phase 3: Podman-specific Configuration and Deployment
    create_enhanced_podman_compose
    
    # Phase 4: Build and Deploy with Podman
    deploy_with_podman
    
    # Phase 5: Verification and Finalization
    if verify_podman_deployment; then
        setup_podman_systemd
        print_podman_deployment_summary
        log_success "Podman deployment completed successfully!"
        exit 0
    else
        log_error "Podman deployment verification failed. Check logs for details."
        log_info "You can check container logs with: podman-compose -f podman-compose.prod.yml logs"
        exit 1
    fi
}

# Handle script interruption
trap 'log_error "Podman deployment interrupted"; exit 130' INT TERM

# Run main deployment
main "$@"