#!/bin/bash
# QMS Platform v3.0 - Quick Production Deployment Script

set -e

echo "🚀 QMS Platform v3.0 - Quick Production Deployment"
echo "=" * 60

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Check if we're in the deployment directory
if [ ! -f "docker-compose.prod.yml" ]; then
    print_error "Please run this script from the deployment directory"
    exit 1
fi

print_info "Starting quick production deployment setup..."

# Step 1: Environment Configuration
if [ ! -f ".env.prod" ]; then
    print_info "Creating production environment file..."
    cp .env.prod.template .env.prod
    print_warning "IMPORTANT: You must edit .env.prod with your production values!"
    echo ""
    echo "Required changes in .env.prod:"
    echo "  1. Set POSTGRES_PASSWORD to a strong password (20+ characters)"
    echo "  2. Set REDIS_PASSWORD to a strong password (20+ characters)"
    echo "  3. Set MINIO_ROOT_PASSWORD to a strong password (20+ characters)"
    echo "  4. Set SECRET_KEY to a random string (50+ characters)"
    echo "  5. Set JWT_SECRET_KEY to a different random string (50+ characters)"
    echo "  6. Configure SMTP settings for email notifications"
    echo ""
    read -p "Press Enter when you have edited .env.prod..."
else
    print_success ".env.prod already exists"
fi

# Step 2: Generate secure keys if needed
print_info "Checking environment configuration..."

# Check for placeholder values
if grep -q "your_secure.*password_here" .env.prod; then
    print_error "Found placeholder values in .env.prod!"
    print_info "Generating secure passwords for you..."
    
    # Generate secure passwords
    POSTGRES_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    MINIO_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
    JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
    
    # Update .env.prod with generated values
    sed -i "s/your_secure_database_password_here_minimum_20_characters/$POSTGRES_PASS/g" .env.prod
    sed -i "s/your_secure_redis_password_here_minimum_20_characters/$REDIS_PASS/g" .env.prod
    sed -i "s/your_secure_minio_password_here_minimum_20_characters/$MINIO_PASS/g" .env.prod
    sed -i "s/your_256_bit_secret_key_here_make_it_very_long_and_random_at_least_50_characters/$SECRET_KEY/g" .env.prod
    sed -i "s/your_jwt_secret_key_here_also_very_long_and_random_different_from_secret_key/$JWT_SECRET/g" .env.prod
    
    print_success "Generated secure passwords and keys"
fi

# Step 3: SSL Certificate Setup
print_info "Setting up SSL certificates..."
mkdir -p ssl

if [ ! -f "ssl/qms.crt" ] || [ ! -f "ssl/qms.key" ]; then
    print_warning "SSL certificates not found"
    echo "Choose SSL setup:"
    echo "1) Generate self-signed certificate (for testing)"
    echo "2) I have my own certificates"
    echo "3) Set up Let's Encrypt (requires domain)"
    read -p "Enter choice (1-3): " ssl_choice
    
    case $ssl_choice in
        1)
            print_info "Generating self-signed certificate..."
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout ssl/qms.key \
                -out ssl/qms.crt \
                -subj "/C=US/ST=Production/L=City/O=QMS/CN=qms.local"
            chmod 600 ssl/qms.key
            chmod 644 ssl/qms.crt
            print_success "Self-signed certificate generated"
            ;;
        2)
            print_info "Please place your certificate files:"
            echo "  - Certificate: ssl/qms.crt"
            echo "  - Private key: ssl/qms.key"
            read -p "Press Enter when certificates are in place..."
            ;;
        3)
            echo "To set up Let's Encrypt:"
            echo "1. sudo apt install certbot"
            echo "2. sudo certbot certonly --standalone -d yourdomain.com"
            echo "3. sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/qms.crt"
            echo "4. sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/qms.key"
            read -p "Press Enter when Let's Encrypt certificates are in place..."
            ;;
    esac
else
    print_success "SSL certificates found"
fi

# Step 4: Create necessary directories
print_info "Creating required directories..."
mkdir -p storage/documents backups logs
chmod 755 storage/documents
print_success "Directories created"

# Step 5: Deploy the platform
print_info "Deploying QMS Platform v3.0..."
if docker-compose -f docker-compose.prod.yml up -d; then
    print_success "Services started successfully"
else
    print_error "Failed to start services"
    exit 1
fi

# Step 6: Wait for services to be ready
print_info "Waiting for services to initialize..."
sleep 30

# Step 7: Initialize database
print_info "Initializing production database..."
if ./init_database.sh; then
    print_success "Database initialized successfully"
else
    print_error "Database initialization failed"
    exit 1
fi

# Step 8: Run verification
print_info "Running deployment verification..."
if ./verify_deployment.sh; then
    print_success "Deployment verification passed"
else
    print_warning "Some verification tests failed - check output above"
fi

# Step 9: Show deployment summary
print_success "QMS Platform v3.0 deployment completed!"
echo ""
echo "🌐 Access Information:"
echo "  - HTTPS: https://localhost (or your domain)"
echo "  - API Documentation: https://localhost/docs"
echo "  - MinIO Console: http://localhost:9001"
echo ""
echo "🔐 Default Admin Credentials:"
echo "  - Username: admin"
echo "  - Password: Admin123!"
echo ""
print_warning "CRITICAL: Change the admin password immediately!"
echo ""
echo "🔧 Next Steps:"
echo "1. Access https://localhost and login with admin/Admin123!"
echo "2. Change the default admin password"
echo "3. Create your organizational users"
echo "4. Configure document types and quality event types"
echo "5. Set up automated backups: ./backup.sh"
echo "6. Monitor system health: ./monitor.sh"
echo ""
echo "📊 System Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""
print_success "Production deployment completed successfully! 🎉"

# Step 10: Optional - Run continuous monitoring
echo ""
read -p "Would you like to start continuous monitoring? (y/n): " start_monitoring
if [[ $start_monitoring =~ ^[Yy]$ ]]; then
    print_info "Starting continuous monitoring (Press Ctrl+C to stop)..."
    ./monitor.sh true 30
fi