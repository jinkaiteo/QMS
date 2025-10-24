#!/bin/bash
# QMS Platform v3.0 - Monitoring Script

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to print status
print_header() {
    echo -e "${BLUE}🔍 QMS Platform v3.0 Health Monitor - $(date)${NC}"
    echo "=" * 60
}

print_section() {
    echo -e "\n${BLUE}$1${NC}"
    echo "-" * 40
}

print_ok() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Clear screen and show header
clear
print_header

# Check if monitoring should run continuously
CONTINUOUS=${1:-false}
INTERVAL=${2:-30}

monitor_containers() {
    print_section "📦 Container Status"
    
    containers=("qms-db-prod" "qms-redis-prod" "qms-minio-prod" "qms-app-prod" "qms-nginx-prod")
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container.*Up"; then
            status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$container" | awk '{print $2, $3}')
            print_ok "$container: $status"
        else
            print_error "$container: Not running or unhealthy"
        fi
    done
}

monitor_resources() {
    print_section "💾 Resource Usage"
    
    # CPU and Memory usage
    echo "System Resources:"
    echo "  CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)% used"
    echo "  Memory: $(free -h | awk '/^Mem/ {print $3 "/" $2 " (" $3/$2*100 "%)"}')"
    echo "  Disk: $(df -h . | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')"
    
    # Container resource usage
    echo ""
    echo "Container Resources:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep qms-
}

monitor_database() {
    print_section "🗄️ Database Health"
    
    # Database connectivity
    if docker exec qms-db-prod pg_isready -U qms_user -d qms_prod &>/dev/null; then
        print_ok "PostgreSQL: Connected"
        
        # Database statistics
        stats=$(docker exec qms-db-prod psql -U qms_user -d qms_prod -t -c "
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
        " 2>/dev/null)
        
        echo "Database Statistics:"
        echo "$stats" | sed 's/^/  /'
        
        # Connection count
        connections=$(docker exec qms-db-prod psql -U qms_user -d qms_prod -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null)
        echo "  Active Connections: $connections"
        
    else
        print_error "PostgreSQL: Connection failed"
    fi
    
    # Redis connectivity
    if docker exec qms-redis-prod redis-cli --pass $(grep REDIS_PASSWORD .env.prod | cut -d= -f2) ping 2>/dev/null | grep -q PONG; then
        print_ok "Redis: Connected"
        
        # Redis info
        redis_info=$(docker exec qms-redis-prod redis-cli --pass $(grep REDIS_PASSWORD .env.prod | cut -d= -f2) info memory 2>/dev/null | grep used_memory_human)
        echo "  Memory Usage: $(echo $redis_info | cut -d: -f2)"
    else
        print_error "Redis: Connection failed"
    fi
}

monitor_application() {
    print_section "🚀 Application Health"
    
    # Health endpoint
    health_response=$(curl -s -k https://localhost:443/health --max-time 5)
    if echo "$health_response" | grep -q "healthy\|ok"; then
        print_ok "Application: Healthy"
        echo "  Response: $health_response"
    else
        print_error "Application: Health check failed"
        echo "  Response: $health_response"
    fi
    
    # API endpoints test
    if curl -s -k https://localhost:443/docs --max-time 5 >/dev/null; then
        print_ok "API Documentation: Accessible"
    else
        print_warning "API Documentation: Not accessible"
    fi
    
    # Check recent application logs for errors
    recent_errors=$(docker logs qms-app-prod --since="5m" 2>&1 | grep -i error | wc -l)
    if [ "$recent_errors" -eq 0 ]; then
        print_ok "Application Logs: No recent errors"
    else
        print_warning "Application Logs: $recent_errors errors in last 5 minutes"
    fi
}

monitor_storage() {
    print_section "📁 Storage Health"
    
    # Document storage
    if docker exec qms-app-prod test -d /app/storage/documents; then
        doc_count=$(docker exec qms-app-prod find /app/storage/documents -type f | wc -l)
        doc_size=$(docker exec qms-app-prod du -sh /app/storage/documents 2>/dev/null | cut -f1 || echo "0B")
        print_ok "Document Storage: $doc_count files, $doc_size"
    else
        print_error "Document Storage: Directory not accessible"
    fi
    
    # MinIO health
    if curl -s http://localhost:9000/minio/health/live --max-time 5 >/dev/null; then
        print_ok "MinIO: Healthy"
    else
        print_warning "MinIO: Health check failed"
    fi
    
    # Backup directory
    if [ -d "backups" ]; then
        backup_count=$(ls -1 backups/qms_prod_backup_*.sql.gz 2>/dev/null | wc -l)
        backup_size=$(du -sh backups 2>/dev/null | cut -f1 || echo "0B")
        print_ok "Backups: $backup_count backups, $backup_size total"
        
        # Check latest backup age
        if [ "$backup_count" -gt 0 ]; then
            latest_backup=$(ls -t backups/qms_prod_backup_*.sql.gz | head -1)
            backup_age=$(stat -c %Y "$latest_backup" 2>/dev/null || echo 0)
            current_time=$(date +%s)
            age_hours=$(( (current_time - backup_age) / 3600 ))
            
            if [ "$age_hours" -lt 48 ]; then
                print_ok "Latest Backup: $age_hours hours ago"
            else
                print_warning "Latest Backup: $age_hours hours ago (consider running backup)"
            fi
        fi
    else
        print_warning "Backup directory not found"
    fi
}

monitor_security() {
    print_section "🔒 Security Status"
    
    # SSL certificate check
    if [ -f "ssl/qms.crt" ]; then
        if openssl x509 -in ssl/qms.crt -noout -checkend 2592000 &>/dev/null; then # 30 days
            expiry_date=$(openssl x509 -in ssl/qms.crt -noout -enddate | cut -d= -f2)
            print_ok "SSL Certificate: Valid (expires $expiry_date)"
        else
            print_error "SSL Certificate: Expires within 30 days!"
        fi
    else
        print_error "SSL Certificate: Not found"
    fi
    
    # Check for security headers
    security_headers=$(curl -s -k -I https://localhost:443/health --max-time 5)
    if echo "$security_headers" | grep -q "X-Frame-Options"; then
        print_ok "Security Headers: Present"
    else
        print_warning "Security Headers: Missing or incomplete"
    fi
    
    # Check failed login attempts (if logs are available)
    failed_logins=$(docker logs qms-app-prod --since="1h" 2>&1 | grep -i "failed\|unauthorized" | wc -l)
    if [ "$failed_logins" -eq 0 ]; then
        print_ok "Security: No failed login attempts in last hour"
    elif [ "$failed_logins" -lt 10 ]; then
        print_warning "Security: $failed_logins failed login attempts in last hour"
    else
        print_error "Security: $failed_logins failed login attempts in last hour (investigate!)"
    fi
}

show_summary() {
    print_section "📊 Quick Summary"
    
    # Overall health score
    total_checks=5
    passed_checks=0
    
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "qms-app-prod.*Up" && ((passed_checks++))
    docker exec qms-db-prod pg_isready -U qms_user -d qms_prod &>/dev/null && ((passed_checks++))
    curl -s -k https://localhost:443/health --max-time 5 >/dev/null && ((passed_checks++))
    [ -f "ssl/qms.crt" ] && openssl x509 -in ssl/qms.crt -noout -checkend 2592000 &>/dev/null && ((passed_checks++))
    curl -s http://localhost:9000/minio/health/live --max-time 5 >/dev/null && ((passed_checks++))
    
    health_percentage=$((passed_checks * 100 / total_checks))
    
    if [ "$health_percentage" -eq 100 ]; then
        print_ok "Overall Health: $health_percentage% (Excellent)"
    elif [ "$health_percentage" -ge 80 ]; then
        print_ok "Overall Health: $health_percentage% (Good)"
    elif [ "$health_percentage" -ge 60 ]; then
        print_warning "Overall Health: $health_percentage% (Needs Attention)"
    else
        print_error "Overall Health: $health_percentage% (Critical Issues)"
    fi
    
    echo ""
    echo "🌐 Quick Access URLs:"
    echo "  - Main App: https://qms.yourcompany.com"
    echo "  - API Docs: https://qms.yourcompany.com/docs"
    echo "  - MinIO Console: http://qms.yourcompany.com:9001"
}

# Main monitoring function
run_monitoring() {
    monitor_containers
    monitor_resources
    monitor_database
    monitor_application
    monitor_storage
    monitor_security
    show_summary
    
    if [ "$CONTINUOUS" = "true" ]; then
        echo ""
        echo -e "${YELLOW}⏰ Next check in $INTERVAL seconds... (Press Ctrl+C to stop)${NC}"
    fi
}

# Handle continuous monitoring
if [ "$CONTINUOUS" = "true" ]; then
    echo -e "${BLUE}🔄 Starting continuous monitoring (every $INTERVAL seconds)${NC}"
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    trap 'echo -e "\n${YELLOW}👋 Monitoring stopped by user${NC}"; exit 0' INT
    
    while true; do
        run_monitoring
        sleep "$INTERVAL"
        clear
        print_header
    done
else
    run_monitoring
fi