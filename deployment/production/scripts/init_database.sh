#!/bin/bash
# Database Initialization Script for QMS Platform v3.0

set -e

echo "🗄️ Initializing QMS Production Database..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
timeout=60
count=0
until docker exec qms-db-prod pg_isready -U qms_user -d qms_prod &>/dev/null; do
    if [ $count -ge $timeout ]; then
        echo "❌ Timeout waiting for PostgreSQL"
        exit 1
    fi
    echo "Waiting for PostgreSQL... ($count/$timeout)"
    sleep 2
    ((count++))
done

echo "✅ PostgreSQL is ready"

# Check if database is already initialized
if docker exec qms-db-prod psql -U qms_user -d qms_prod -c "SELECT COUNT(*) FROM users;" &>/dev/null; then
    echo "ℹ️  Database appears to be already initialized"
    read -p "Do you want to skip initialization? (y/n): " skip_init
    if [[ $skip_init =~ ^[Yy]$ ]]; then
        echo "⏭️  Skipping database initialization"
        exit 0
    fi
fi

echo "📋 Running database initialization scripts..."

# Phase 1: Foundation
echo "🏗️  Phase 1: Creating foundation tables..."
if docker exec qms-db-prod psql -U qms_user -d qms_prod -f /docker-entrypoint-initdb.d/01_create_extensions.sql; then
    echo "✅ Extensions created"
else
    echo "❌ Failed to create extensions"
    exit 1
fi

if docker exec qms-db-prod psql -U qms_user -d qms_prod -f /docker-entrypoint-initdb.d/02_create_core_tables.sql; then
    echo "✅ Core tables created"
else
    echo "❌ Failed to create core tables"
    exit 1
fi

if docker exec qms-db-prod psql -U qms_user -d qms_prod -f /docker-entrypoint-initdb.d/03_insert_default_data.sql; then
    echo "✅ Default data inserted"
else
    echo "❌ Failed to insert default data"
    exit 1
fi

# Phase 2: EDMS
echo "📄 Phase 2: Creating EDMS tables..."
if docker exec qms-db-prod psql -U qms_user -d qms_prod -f /docker-entrypoint-initdb.d/04_create_edms_tables.sql; then
    echo "✅ EDMS tables created"
else
    echo "❌ Failed to create EDMS tables"
    exit 1
fi

if docker exec qms-db-prod psql -U qms_user -d qms_prod -f /docker-entrypoint-initdb.d/05_insert_edms_data.sql; then
    echo "✅ EDMS default data inserted"
else
    echo "❌ Failed to insert EDMS data"
    exit 1
fi

# Phase 3: QRM
echo "🔍 Phase 3: Creating QRM tables..."
if docker exec qms-db-prod psql -U qms_user -d qms_prod -f /docker-entrypoint-initdb.d/06_create_qrm_tables.sql; then
    echo "✅ QRM tables created"
else
    echo "❌ Failed to create QRM tables"
    exit 1
fi

# Create production admin user
echo "👤 Creating production admin user..."
docker exec qms-db-prod psql -U qms_user -d qms_prod -c "
-- Create production organization if not exists
INSERT INTO organizations (name, code, address, phone, email) 
VALUES ('Production Organization', 'PROD', '123 Production Street, Production City, PC 12345', '+1-555-0100', 'admin@production.com')
ON CONFLICT (code) DO NOTHING;

-- Create admin user if not exists  
INSERT INTO users (username, email, password_hash, first_name, last_name, organization_id, status) 
VALUES ('admin', 'admin@production.com', '\$2b\$12\$efs4ShH.UZ9C3h.YkUHnoOWOnPxSyGsH.I84Fb0jkXjXZ26V4JuES', 'System', 'Administrator', 1, 'ACTIVE')
ON CONFLICT (username) DO UPDATE SET
    email = EXCLUDED.email,
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    status = EXCLUDED.status;

-- Assign admin role to user
INSERT INTO user_roles (user_id, role_id, assigned_by) 
VALUES (1, 1, 1)
ON CONFLICT DO NOTHING;
"

if [ $? -eq 0 ]; then
    echo "✅ Admin user created successfully"
else
    echo "❌ Failed to create admin user"
    exit 1
fi

# Verify database initialization
echo "🔍 Verifying database initialization..."
table_count=$(docker exec qms-db-prod psql -U qms_user -d qms_prod -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
user_count=$(docker exec qms-db-prod psql -U qms_user -d qms_prod -t -c "SELECT COUNT(*) FROM users;")
doc_type_count=$(docker exec qms-db-prod psql -U qms_user -d qms_prod -t -c "SELECT COUNT(*) FROM document_types;")

echo "📊 Database Statistics:"
echo "  - Tables created: $table_count"
echo "  - Users: $user_count"
echo "  - Document types: $doc_type_count"

if [ "$table_count" -ge 26 ] && [ "$user_count" -ge 1 ] && [ "$doc_type_count" -ge 5 ]; then
    echo "✅ Database initialization completed successfully!"
    echo ""
    echo "🔐 Default Admin Credentials:"
    echo "  Username: admin"
    echo "  Password: Admin123!"
    echo ""
    echo "⚠️  SECURITY WARNING: Change the default password immediately after first login!"
else
    echo "❌ Database initialization verification failed"
    echo "Expected: 26+ tables, 1+ users, 5+ document types"
    echo "Actual: $table_count tables, $user_count users, $doc_type_count document types"
    exit 1
fi