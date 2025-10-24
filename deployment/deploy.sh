#!/bin/bash
# QMS Platform v3.0 - Production Deployment Script

set -e  # Exit on any error

echo "🚀 Starting QMS Platform v3.0 Production Deployment"
echo "=" * 60

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_info "Prerequisites check passed"

# Create deployment directory structure
print_info "Creating deployment directory structure..."
mkdir -p ssl storage/documents backups logs

# Check if .env.prod exists
if [ ! -f ".env.prod" ]; then
    print_warning ".env.prod not found. Creating from template..."
    cp .env.prod.template .env.prod
    print_error "Please edit .env.prod with your production values before continuing!"
    print_info "Required changes:"
    echo "  - Set secure passwords for POSTGRES_PASSWORD, REDIS_PASSWORD, MINIO_ROOT_PASSWORD"
    echo "  - Set SECRET_KEY and JWT_SECRET_KEY to long random strings"
    echo "  - Configure SMTP settings for email notifications"
    echo "  - Update server name in nginx.conf"
    exit 1
fi

print_status ".env.prod found"

# SSL Certificate setup
print_info "Checking SSL certificates..."
if [ ! -f "ssl/qms.crt" ] || [ ! -f "ssl/qms.key" ]; then
    print_warning "SSL certificates not found"
    echo "Choose SSL certificate option:"
    echo "1) Generate self-signed certificate (for testing)"
    echo "2) I will provide my own certificates"
    echo "3) Exit and set up Let's Encrypt manually"
    read -p "Enter choice (1-3): " ssl_choice
    
    case $ssl_choice in
        1)
            print_info "Generating self-signed certificate..."
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout ssl/qms.key \
                -out ssl/qms.crt \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=qms.yourcompany.com"
            chmod 600 ssl/qms.key
            chmod 644 ssl/qms.crt
            print_status "Self-signed certificate generated"
            ;;
        2)
            print_info "Please place your certificate files:"
            echo "  - Certificate: ssl/qms.crt"
            echo "  - Private key: ssl/qms.key"
            read -p "Press Enter when certificates are in place..."
            if [ ! -f "ssl/qms.crt" ] || [ ! -f "ssl/qms.key" ]; then
                print_error "Certificate files not found!"
                exit 1
            fi
            ;;
        3)
            print_info "Please set up Let's Encrypt and place certificates in ssl/ directory"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
else
    print_status "SSL certificates found"
fi

# Build and start services
print_info "Building and starting QMS services..."
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

print_info "Waiting for services to be healthy..."
sleep 30

# Check service health
print_info "Checking service health..."
for service in qms-db-prod qms-redis-prod qms-minio-prod qms-app-prod; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "$service.*Up.*healthy"; then
        print_status "$service is healthy"
    else
        print_error "$service is not healthy"
        docker-compose -f docker-compose.prod.yml logs $service
        exit 1
    fi
done

# Initialize database
print_info "Initializing production database..."
./init_database.sh

# Run deployment verification
print_info "Running deployment verification..."
./verify_deployment.sh

print_status "QMS Platform v3.0 deployment completed successfully!"
echo ""
print_info "Access your QMS Platform at:"
echo "  - HTTPS: https://qms.yourcompany.com"
echo "  - HTTP (redirects to HTTPS): http://qms.yourcompany.com"
echo "  - API Documentation: https://qms.yourcompany.com/docs"
echo ""
print_info "Default admin credentials:"
echo "  - Username: admin"
echo "  - Password: Admin123!"
echo ""
print_warning "IMPORTANT: Change the default admin password immediately!"
echo ""
print_info "Next steps:"
echo "  1. Change default admin password"
echo "  2. Create additional users and roles"
echo "  3. Configure document types and categories"
echo "  4. Set up quality event types"
echo "  5. Configure email notifications"
echo "  6. Set up automated backups"
echo ""
print_status "Deployment completed successfully! 🎉"