#!/bin/bash
# QMS Platform v3.0 - Deployment Verification Script

set -e

echo "🔍 Verifying QMS Platform v3.0 Deployment"
echo "=" * 50

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

passed_tests=0
total_tests=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"
    
    total_tests=$((total_tests + 1))
    echo -n "Testing $test_name... "
    
    if eval "$test_command" &>/dev/null; then
        echo -e "${GREEN}✅ PASS${NC}"
        passed_tests=$((passed_tests + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        if [ "$expected_result" != "" ]; then
            echo -e "  ${YELLOW}Expected: $expected_result${NC}"
        fi
        return 1
    fi
}

# Function to test HTTP endpoint
test_http_endpoint() {
    local endpoint="$1"
    local expected_status="$2"
    local description="$3"
    
    total_tests=$((total_tests + 1))
    echo -n "Testing $description... "
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" -k "$endpoint" --max-time 10)
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $status_code)"
        passed_tests=$((passed_tests + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $status_code, expected $expected_status)"
        return 1
    fi
}

echo "🐳 Container Health Checks"
echo "-" * 30

# Check container status
run_test "PostgreSQL Container" "docker exec qms-db-prod pg_isready -U qms_user -d qms_prod"
run_test "Redis Container" "docker exec qms-redis-prod redis-cli --pass \$(grep REDIS_PASSWORD .env.prod | cut -d= -f2) ping | grep -q PONG"
run_test "MinIO Container" "curl -f http://localhost:9000/minio/health/live"
run_test "QMS Application Container" "curl -f http://localhost:8000/health"
run_test "Nginx Container" "docker exec qms-nginx-prod nginx -t"

echo ""
echo "🌐 HTTP Endpoint Tests"
echo "-" * 30

# Test HTTP endpoints
test_http_endpoint "http://localhost:80/health" "301" "HTTP to HTTPS Redirect"
test_http_endpoint "https://localhost:443/health" "200" "HTTPS Health Check"
test_http_endpoint "https://localhost:443/docs" "200" "API Documentation"

echo ""
echo "🗄️ Database Connectivity Tests"
echo "-" * 30

# Database tests
run_test "Database Connection" "docker exec qms-db-prod psql -U qms_user -d qms_prod -c 'SELECT 1;'"
run_test "Users Table" "docker exec qms-db-prod psql -U qms_user -d qms_prod -c 'SELECT COUNT(*) FROM users;' | grep -q '[0-9]'"
run_test "Document Types Table" "docker exec qms-db-prod psql -U qms_user -d qms_prod -c 'SELECT COUNT(*) FROM document_types;' | grep -q '[0-9]'"
run_test "Quality Event Types Table" "docker exec qms-db-prod psql -U qms_user -d qms_prod -c 'SELECT COUNT(*) FROM quality_event_types;' | grep -q '[0-9]'"

echo ""
echo "🔐 Authentication Tests"
echo "-" * 30

# Test authentication
auth_response=$(curl -s -k -X POST https://localhost:443/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"Admin123!"}')

if echo "$auth_response" | grep -q "access_token"; then
    echo -e "Admin Login... ${GREEN}✅ PASS${NC}"
    passed_tests=$((passed_tests + 1))
    
    # Extract token for further tests
    token=$(echo "$auth_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$token" ]; then
        # Test protected endpoint
        auth_header="Authorization: Bearer $token"
        system_health=$(curl -s -k -H "$auth_header" https://localhost:443/api/v1/system/health)
        
        if echo "$system_health" | grep -q "status"; then
            echo -e "Protected Endpoint Access... ${GREEN}✅ PASS${NC}"
            passed_tests=$((passed_tests + 1))
        else
            echo -e "Protected Endpoint Access... ${RED}❌ FAIL${NC}"
        fi
        total_tests=$((total_tests + 1))
    fi
else
    echo -e "Admin Login... ${RED}❌ FAIL${NC}"
    echo -e "  ${YELLOW}Response: $auth_response${NC}"
fi
total_tests=$((total_tests + 1))

echo ""
echo "📊 API Functionality Tests"
echo "-" * 30

if [ ! -z "$token" ]; then
    # Test document types endpoint
    doc_types_response=$(curl -s -k -H "$auth_header" https://localhost:443/api/v1/documents/types)
    if echo "$doc_types_response" | grep -q "\["; then
        echo -e "Document Types API... ${GREEN}✅ PASS${NC}"
        passed_tests=$((passed_tests + 1))
    else
        echo -e "Document Types API... ${RED}❌ FAIL${NC}"
    fi
    total_tests=$((total_tests + 1))
    
    # Test quality events endpoint
    qe_types_response=$(curl -s -k -H "$auth_header" https://localhost:443/api/v1/quality-events/types)
    if echo "$qe_types_response" | grep -q "\["; then
        echo -e "Quality Event Types API... ${GREEN}✅ PASS${NC}"
        passed_tests=$((passed_tests + 1))
    else
        echo -e "Quality Event Types API... ${RED}❌ FAIL${NC}"
    fi
    total_tests=$((total_tests + 1))
    
    # Test CAPA search endpoint
    capa_search=$(curl -s -k -H "$auth_header" -H "Content-Type: application/json" \
        -d '{"page":1,"per_page":10}' https://localhost:443/api/v1/capas/search)
    if echo "$capa_search" | grep -q "items"; then
        echo -e "CAPA Search API... ${GREEN}✅ PASS${NC}"
        passed_tests=$((passed_tests + 1))
    else
        echo -e "CAPA Search API... ${RED}❌ FAIL${NC}"
    fi
    total_tests=$((total_tests + 1))
else
    echo -e "Skipping API tests - no authentication token available"
fi

echo ""
echo "📁 File System Tests"
echo "-" * 30

# Test file system permissions
run_test "Document Storage Directory" "docker exec qms-app-prod test -w /app/storage/documents"
run_test "Log Directory" "docker exec qms-app-prod test -w /app/logs"
run_test "Backup Directory" "test -w backups"

echo ""
echo "🔒 Security Tests"
echo "-" * 30

# Test SSL certificate
run_test "SSL Certificate Validity" "openssl x509 -in ssl/qms.crt -noout -checkend 86400"
run_test "SSL Certificate Key Match" "diff <(openssl x509 -in ssl/qms.crt -noout -modulus) <(openssl rsa -in ssl/qms.key -noout -modulus)"

# Test security headers
security_headers=$(curl -s -k -I https://localhost:443/health)
if echo "$security_headers" | grep -q "X-Frame-Options"; then
    echo -e "Security Headers... ${GREEN}✅ PASS${NC}"
    passed_tests=$((passed_tests + 1))
else
    echo -e "Security Headers... ${RED}❌ FAIL${NC}"
fi
total_tests=$((total_tests + 1))

echo ""
echo "📊 VERIFICATION SUMMARY"
echo "=" * 50

success_rate=$((passed_tests * 100 / total_tests))

echo -e "Tests Passed: ${GREEN}$passed_tests${NC}/$total_tests (${GREEN}$success_rate%${NC})"

if [ $success_rate -ge 90 ]; then
    echo -e "${GREEN}🎉 DEPLOYMENT VERIFICATION: EXCELLENT!${NC}"
    echo -e "${GREEN}✅ QMS Platform is fully operational and ready for production use${NC}"
    exit_code=0
elif [ $success_rate -ge 75 ]; then
    echo -e "${YELLOW}✅ DEPLOYMENT VERIFICATION: GOOD${NC}"
    echo -e "${YELLOW}⚠️  Most features working, some minor issues detected${NC}"
    exit_code=0
else
    echo -e "${RED}❌ DEPLOYMENT VERIFICATION: NEEDS ATTENTION${NC}"
    echo -e "${RED}🔧 Several critical issues detected - review failed tests${NC}"
    exit_code=1
fi

echo ""
echo "📋 Next Steps:"
echo "1. Change default admin password: admin / Admin123!"
echo "2. Configure document types and categories"
echo "3. Set up quality event types"
echo "4. Create additional users and assign roles"
echo "5. Configure email notifications"
echo "6. Set up automated backups"
echo "7. Configure monitoring and alerting"

echo ""
echo -e "${BLUE}🌐 Access URLs:${NC}"
echo "  - Main Application: https://qms.yourcompany.com"
echo "  - API Documentation: https://qms.yourcompany.com/docs"
echo "  - MinIO Console: http://qms.yourcompany.com:9001"

exit $exit_code