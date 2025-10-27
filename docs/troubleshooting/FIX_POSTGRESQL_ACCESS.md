# 🔐 Fix PostgreSQL Access - Password Solutions

## 🎯 Multiple Solutions to Get PostgreSQL Access

### **Solution 1: Use System Authentication (Easiest)**
```bash
# Switch to postgres system user (no password needed)
sudo -u postgres psql

# Once inside PostgreSQL, you can:
# 1. Create your database
CREATE DATABASE qms_production;

# 2. Create your user with a password you choose
CREATE USER qms_user WITH PASSWORD 'your_chosen_password';

# 3. Grant privileges
GRANT ALL PRIVILEGES ON DATABASE qms_production TO qms_user;
\q
```

### **Solution 2: Reset PostgreSQL Password**
```bash
# Stop PostgreSQL
sudo systemctl stop postgresql

# Start in single-user mode (no authentication)
sudo -u postgres postgres --single -D /var/lib/postgresql/data

# In the PostgreSQL prompt that opens:
ALTER USER postgres PASSWORD 'new_password_here';
# Press Ctrl+D to exit

# Start PostgreSQL normally
sudo systemctl start postgresql

# Now you can use the new password
psql -U postgres -h localhost
```

### **Solution 3: Modify Authentication Settings**
```bash
# Edit PostgreSQL authentication config
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Change this line:
# local   all             postgres                                peer
# To this:
local   all             postgres                                trust

# Restart PostgreSQL
sudo systemctl restart postgresql

# Now you can access without password:
psql -U postgres

# Don't forget to change it back to 'peer' or 'md5' after setup!
```

### **Solution 4: Use Docker PostgreSQL (Clean Start)**
```bash
# Run PostgreSQL in Docker with known credentials
docker run --name postgres-qms \
  -e POSTGRES_DB=qms_production \
  -e POSTGRES_USER=qms_user \
  -e POSTGRES_PASSWORD=qms_password \
  -p 5432:5432 \
  -d postgres:13

# Test connection
psql -h localhost -U qms_user -d qms_production
# Password: qms_password
```

## 🚀 **Quick Setup with Known Credentials**

### **Option A: Use System Auth (Recommended)**
```bash
# 1. Access PostgreSQL as system user
sudo -u postgres psql

# 2. Run these commands inside PostgreSQL:
CREATE DATABASE qms_production;
CREATE USER qms_user WITH PASSWORD 'tms_password_2024';
GRANT ALL PRIVILEGES ON DATABASE qms_production TO qms_user;
GRANT ALL ON SCHEMA public TO qms_user;
\q

# 3. Test new connection
psql -h localhost -U qms_user -d qms_production
# Enter password: tms_password_2024
```

### **Option B: Modified Setup Script**
```bash
# Set known credentials and run setup
export DB_NAME="qms_production"
export DB_USER="qms_user"
export DB_PASSWORD="tms_password_2024"
export POSTGRES_ADMIN_USER="postgres"

# Run setup script (it will use sudo -u postgres for database creation)
./database/init_training_database.sh
```

## 🛠️ **Manual Database Setup (If Script Fails)**

### **Step 1: Create Database Manually**
```bash
# Access PostgreSQL
sudo -u postgres psql

# Create everything manually:
CREATE DATABASE qms_production;
CREATE USER qms_user WITH PASSWORD 'tms_password_2024';
GRANT ALL PRIVILEGES ON DATABASE qms_production TO qms_user;
GRANT ALL ON SCHEMA public TO qms_user;
\q
```

### **Step 2: Run Schema Only**
```bash
# Connect with your new credentials
psql -h localhost -U qms_user -d qms_production

# Run the schema file
\i database/training_schema.sql

# Verify it worked
\dt
SELECT * FROM training_programs;
\q
```

### **Step 3: Create Config File**
```bash
# Create backend/.env.production manually
cat > backend/.env.production << EOF
# Training Management System Database Configuration
DATABASE_URL=postgresql://qms_user:tms_password_2024@localhost:5432/qms_production
DB_HOST=localhost
DB_PORT=5432
DB_NAME=qms_production
DB_USER=qms_user
DB_PASSWORD=tms_password_2024

# Application Configuration
NODE_ENV=production
API_VERSION=v1
JWT_SECRET=your-production-jwt-secret-here
JWT_EXPIRES_IN=24h

# CORS Configuration
CORS_ORIGINS=https://your-domain.com
EOF
```

## 🔍 **Troubleshooting Common Issues**

### **PostgreSQL Not Installed**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
```

### **PostgreSQL Not Running**
```bash
# Check status
sudo systemctl status postgresql

# Start if stopped
sudo systemctl start postgresql

# Enable auto-start
sudo systemctl enable postgresql
```

### **Connection Issues**
```bash
# Check if PostgreSQL is listening
sudo netstat -tlnp | grep 5432

# Check authentication method
sudo cat /etc/postgresql/*/main/pg_hba.conf | grep local
```

## 🎯 **Recommended Quick Solution**

**For immediate setup, I recommend Option A:**

```bash
# 1. Access PostgreSQL (no password needed)
sudo -u postgres psql

# 2. Create database and user
CREATE DATABASE qms_production;
CREATE USER qms_user WITH PASSWORD 'tms_password_2024';
GRANT ALL PRIVILEGES ON DATABASE qms_production TO qms_user;
GRANT ALL ON SCHEMA public TO qms_user;
\q

# 3. Test connection
psql -h localhost -U qms_user -d qms_production

# 4. Run schema setup
\i database/training_schema.sql

# 5. Verify
SELECT COUNT(*) FROM training_programs;
```

## 🎉 **After Access is Restored**

Once you have database access, you can:

1. **✅ Run the full setup script**
2. **✅ Or follow the manual steps above**
3. **✅ Continue with backend integration**

**Let me know which approach works for you, and I'll help you complete the database setup!** 🚀

## 📞 **Need More Help?**

Tell me:
- Which operating system you're using?
- How PostgreSQL was installed?
- Any error messages you're seeing?

I'll provide specific guidance for your situation! 💪