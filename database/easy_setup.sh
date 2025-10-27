#!/bin/bash
# ============================================================================
# SUPER EASY TMS Database Setup - Just Run This One Command!
# ============================================================================

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 TMS Database Setup - Super Easy Mode${NC}"
echo "=============================================="

# Fixed credentials (no prompting needed)
DB_NAME="qms_production"
DB_USER="qms_user"
DB_PASSWORD="tms_password_2024"

echo -e "${BLUE}📋 Using these credentials:${NC}"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo ""

# Step 1: Create database and user
echo -e "${BLUE}Step 1: Creating database and user...${NC}"
sudo -u postgres psql << EOF
-- Drop existing database/user if they exist
DROP DATABASE IF EXISTS $DB_NAME;
DROP USER IF EXISTS $DB_USER;

-- Create fresh database and user
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Connect to the database and grant schema permissions
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;

-- Verify connection works
SELECT 'Database and user created successfully!' as status;
EOF

echo -e "${GREEN}✅ Database and user created successfully!${NC}"

# Step 2: Install schema
echo -e "${BLUE}Step 2: Installing TMS schema...${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_FILE="$SCRIPT_DIR/training_schema.sql"

if [ ! -f "$SCHEMA_FILE" ]; then
    echo -e "${RED}❌ Schema file not found: $SCHEMA_FILE${NC}"
    exit 1
fi

# Install schema using the qms_user
PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d "$DB_NAME" -f "$SCHEMA_FILE"

echo -e "${GREEN}✅ Schema installed successfully!${NC}"

# Step 3: Verify installation
echo -e "${BLUE}Step 3: Verifying installation...${NC}"

PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d "$DB_NAME" << EOF
-- Check tables
SELECT 'Tables created: ' || COUNT(*) as status 
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'training_%';

-- Check sample data
SELECT 'Sample programs: ' || COUNT(*) as status FROM training_programs;

-- Test dashboard view
SELECT 'Dashboard working: ' || 
       CASE WHEN total_programs IS NOT NULL THEN 'YES' ELSE 'NO' END as status
FROM training_dashboard_stats;
EOF

echo -e "${GREEN}✅ Installation verified!${NC}"

# Step 4: Create configuration file
echo -e "${BLUE}Step 4: Creating configuration file...${NC}"

CONFIG_FILE="$SCRIPT_DIR/../backend/.env.production"
mkdir -p "$(dirname "$CONFIG_FILE")"

cat > "$CONFIG_FILE" << EOF
# Training Management System Database Configuration
# Generated automatically on $(date)

# Database Connection
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
DB_HOST=localhost
DB_PORT=5432
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD

# Application Configuration
NODE_ENV=production
API_VERSION=v1
JWT_SECRET=tms-jwt-secret-$(date +%s)
JWT_EXPIRES_IN=24h

# CORS Configuration
CORS_ORIGINS=http://localhost:3002,http://localhost:3003

# Logging
LOG_LEVEL=info
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
EOF

echo -e "${GREEN}✅ Configuration file created: $CONFIG_FILE${NC}"

# Step 5: Final test
echo -e "${BLUE}Step 5: Final connection test...${NC}"

if PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d "$DB_NAME" -c "SELECT 'Connection successful!' as test;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Connection test passed!${NC}"
else
    echo -e "${RED}❌ Connection test failed!${NC}"
    exit 1
fi

# Success message
echo ""
echo "=============================================="
echo -e "${GREEN}🎉 TMS Database Setup Complete!${NC}"
echo "=============================================="
echo ""
echo -e "${BLUE}📊 Database Information:${NC}"
echo "  Database Name: $DB_NAME"
echo "  Username: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo "  Host: localhost"
echo "  Port: 5432"
echo ""
echo -e "${BLUE}🔗 Connection String:${NC}"
echo "  postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
echo ""
echo -e "${BLUE}📁 Configuration File:${NC}"
echo "  $CONFIG_FILE"
echo ""
echo -e "${BLUE}🧪 Test Your Database:${NC}"
echo "  psql -h localhost -U $DB_USER -d $DB_NAME"
echo "  Password: $DB_PASSWORD"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "  1. Update JWT_SECRET in $CONFIG_FILE"
echo "  2. Test backend API connection"
echo "  3. Begin backend service integration"
echo ""
echo -e "${GREEN}✅ Ready for TMS backend integration!${NC}"