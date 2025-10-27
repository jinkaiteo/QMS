#!/bin/bash
# ============================================================================
# Training Management System Database Initialization Script
# QMS Platform v3.0 - Production Database Setup
# ============================================================================

set -e  # Exit on any error

# Configuration
DB_NAME="${DB_NAME:-qms_production}"
DB_USER="${DB_USER:-qms_user}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
POSTGRES_ADMIN_USER="${POSTGRES_ADMIN_USER:-postgres}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if PostgreSQL is running
check_postgres() {
    log "Checking PostgreSQL connection..."
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
        success "PostgreSQL is running and accepting connections"
    else
        error "Cannot connect to PostgreSQL at $DB_HOST:$DB_PORT"
        exit 1
    fi
}

# Create database and user if they don't exist
create_database_and_user() {
    log "Creating database and user..."
    
    # Check if database exists
    DB_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")
    
    if [ "$DB_EXISTS" = "1" ]; then
        warning "Database '$DB_NAME' already exists"
    else
        log "Creating database '$DB_NAME'..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -c "CREATE DATABASE $DB_NAME;"
        success "Database '$DB_NAME' created successfully"
    fi
    
    # Check if user exists
    USER_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'")
    
    if [ "$USER_EXISTS" = "1" ]; then
        warning "User '$DB_USER' already exists"
    else
        log "Creating user '$DB_USER'..."
        if [ -z "$DB_PASSWORD" ]; then
            read -s -p "Enter password for database user '$DB_USER': " DB_PASSWORD
            echo
        fi
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
        success "User '$DB_USER' created successfully"
    fi
    
    # Grant privileges
    log "Granting privileges to '$DB_USER'..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -d "$DB_NAME" -c "GRANT ALL ON SCHEMA public TO $DB_USER;"
    success "Privileges granted successfully"
}

# Run the training schema script
create_training_schema() {
    log "Creating training management schema..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SCHEMA_FILE="$SCRIPT_DIR/training_schema.sql"
    
    if [ ! -f "$SCHEMA_FILE" ]; then
        error "Schema file not found: $SCHEMA_FILE"
        exit 1
    fi
    
    log "Executing training schema from: $SCHEMA_FILE"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SCHEMA_FILE"
    
    if [ $? -eq 0 ]; then
        success "Training schema created successfully"
    else
        error "Failed to create training schema"
        exit 1
    fi
}

# Verify schema installation
verify_installation() {
    log "Verifying schema installation..."
    
    # Check if main tables exist
    TABLES=(
        "training_programs"
        "training_assignments" 
        "training_documents"
        "training_modules"
        "training_prerequisites"
        "training_assignment_history"
        "training_session_logs"
    )
    
    for table in "${TABLES[@]}"; do
        TABLE_EXISTS=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='$table'")
        if [ "$TABLE_EXISTS" = "1" ]; then
            success "Table '$table' exists"
        else
            error "Table '$table' not found"
            exit 1
        fi
    done
    
    # Check if views exist
    VIEWS=(
        "training_dashboard_stats"
        "program_statistics"
    )
    
    for view in "${VIEWS[@]}"; do
        VIEW_EXISTS=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT 1 FROM information_schema.views WHERE table_name='$view'")
        if [ "$VIEW_EXISTS" = "1" ]; then
            success "View '$view' exists"
        else
            error "View '$view' not found"
            exit 1
        fi
    done
    
    # Test sample data
    log "Checking sample data..."
    SAMPLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT COUNT(*) FROM training_programs")
    success "Sample training programs: $SAMPLE_COUNT"
    
    # Test dashboard view
    log "Testing dashboard statistics view..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT * FROM training_dashboard_stats;"
    success "Dashboard statistics view working"
}

# Create connection string file for backend
create_connection_config() {
    log "Creating database connection configuration..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    CONFIG_FILE="$SCRIPT_DIR/../backend/.env.production"
    
    cat > "$CONFIG_FILE" << EOF
# Training Management System Database Configuration
# Generated on $(date)

# Database Connection
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD

# Application Configuration
NODE_ENV=production
API_VERSION=v1
JWT_SECRET=your-production-jwt-secret-here
JWT_EXPIRES_IN=24h

# CORS Configuration
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Logging
LOG_LEVEL=info
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100

# Session Configuration
SESSION_SECRET=your-session-secret-here
SESSION_MAX_AGE=86400000
EOF

    success "Database configuration written to: $CONFIG_FILE"
    warning "Please update JWT_SECRET, CORS_ORIGINS, and other production values in $CONFIG_FILE"
}

# Backup current database (if exists)
backup_existing_database() {
    if [ "$1" = "--backup" ]; then
        log "Creating backup of existing database..."
        BACKUP_FILE="backup_${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql"
        PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null || true
        if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
            success "Backup created: $BACKUP_FILE"
        else
            warning "No existing database to backup or backup failed"
            rm -f "$BACKUP_FILE"
        fi
    fi
}

# Main execution
main() {
    echo "============================================================================"
    echo "Training Management System Database Initialization"
    echo "QMS Platform v3.0"
    echo "============================================================================"
    echo
    
    log "Starting database initialization with the following configuration:"
    echo "  Database Name: $DB_NAME"
    echo "  Database User: $DB_USER"
    echo "  Database Host: $DB_HOST"
    echo "  Database Port: $DB_PORT"
    echo
    
    # Backup if requested
    backup_existing_database "$1"
    
    # Execute setup steps
    check_postgres
    create_database_and_user
    create_training_schema
    verify_installation
    create_connection_config
    
    echo
    echo "============================================================================"
    success "Training Management System database initialization completed successfully!"
    echo "============================================================================"
    echo
    log "Next steps:"
    echo "  1. Review and update configuration in backend/.env.production"
    echo "  2. Update JWT_SECRET and other production secrets"
    echo "  3. Configure CORS_ORIGINS for your domain"
    echo "  4. Test backend API connection"
    echo "  5. Run backend integration tests"
    echo
    log "Database connection string:"
    echo "  postgresql://$DB_USER:[password]@$DB_HOST:$DB_PORT/$DB_NAME"
    echo
}

# Help message
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Initialize Training Management System database for QMS Platform v3.0"
    echo
    echo "Options:"
    echo "  --backup    Create backup of existing database before initialization"
    echo "  --help      Show this help message"
    echo
    echo "Environment Variables:"
    echo "  DB_NAME             Database name (default: qms_production)"
    echo "  DB_USER             Database user (default: qms_user)"
    echo "  DB_PASSWORD         Database password (will prompt if not set)"
    echo "  DB_HOST             Database host (default: localhost)"
    echo "  DB_PORT             Database port (default: 5432)"
    echo "  POSTGRES_ADMIN_USER Admin user for database creation (default: postgres)"
    echo
    echo "Examples:"
    echo "  $0                  # Basic initialization"
    echo "  $0 --backup        # Initialize with backup of existing database"
    echo "  DB_NAME=qms_test $0 # Initialize with custom database name"
    echo
}

# Parse command line arguments
case "${1:-}" in
    --help)
        show_help
        exit 0
        ;;
    --backup)
        main --backup
        ;;
    "")
        main
        ;;
    *)
        error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac