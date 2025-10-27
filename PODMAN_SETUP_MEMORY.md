# 🐳 QMS Podman Setup - Complete Memory Documentation

## 📊 **Current Podman Environment Snapshot**
**Date**: $(date)
**System**: QMS Platform v3.0 with Training Management Integration

## 🏗️ **Container Architecture**

### **Production Environment (qms-prod)**
```
Network: deployment_qms-prod
Services: 6 containers total
Status: Infrastructure operational, application layer issues
```

#### **✅ Database Layer - OPERATIONAL**
```yaml
qms-db-prod:
  image: postgres:18
  status: Up 8+ minutes (healthy)
  ports: "0.0.0.0:5432->5432/tcp"
  database: qms_prod
  user: qms_user
  password: xYMSN0tb6CFZsy2DcBuUTO91W
  network: deployment_qms-prod
  health: ✅ WORKING
  training_tables: 6 tables integrated
```

#### **✅ Cache Layer - OPERATIONAL**  
```yaml
qms-redis-prod:
  image: redis:7-alpine
  status: Up 8+ minutes (healthy)
  ports: "0.0.0.0:6379->6379/tcp"
  network: deployment_qms-prod
  health: ✅ WORKING (PONG response)
```

#### **✅ Storage Layer - OPERATIONAL**
```yaml
qms-minio-prod:
  image: minio/minio:latest
  status: Up 8+ minutes (healthy)
  ports: "0.0.0.0:9000-9001->9000-9001/tcp"
  network: deployment_qms-prod
  health: ✅ WORKING
```

#### **❌ Application Layer - NEEDS ATTENTION**
```yaml
qms-app-prod:
  image: localhost/deployment_qms-app-prod:latest
  status: Exited (3) - failing to start
  ports: "0.0.0.0:8000->8000/tcp"
  network: deployment_qms-prod
  issue: Database connection/environment variables
  health: ❌ NOT WORKING
```

#### **⚠️ Monitoring Layer - PARTIAL**
```yaml
qms-prometheus-prod:
  image: prom/prometheus:latest
  status: Up 2+ days
  ports: "0.0.0.0:9090->9090/tcp"
  network: deployment_qms-prod
  health: ⚠️ Container up, service not responding

qms-grafana-prod:
  image: grafana/grafana:latest  
  status: Up 2+ days
  ports: "0.0.0.0:3000->3000/tcp"
  network: deployment_qms-prod
  health: ⚠️ Container up, service not responding
```

### **Development Environment (qms-dev) - AVAILABLE**
```yaml
# All development containers exist but are stopped
# Can be restarted for development work

qms-db-dev:
  image: postgres:18
  status: Exited (0) 2 days ago (healthy)
  ports: "0.0.0.0:5432->5432/tcp"
  
qms-redis-dev:
  image: redis:7-alpine
  status: Exited (0) 2 days ago (healthy)
  ports: "0.0.0.0:6379->6379/tcp"
  
qms-minio-dev:
  image: minio/minio:latest
  status: Exited (0) 2 days ago (healthy)
  ports: "0.0.0.0:9000-9001->9000-9001/tcp"
  
qms-elasticsearch-dev:
  image: elasticsearch:8.11.0
  status: Exited (143) 2 days ago (healthy)
  ports: "0.0.0.0:9200->9200/tcp"
  
qms-pgadmin-dev:
  image: dpage/pgadmin4:latest
  status: Exited (1) 2 days ago
  ports: "0.0.0.0:5050->80/tcp"
```

## 🌐 **Network Configuration**

### **Networks Available**
```
deployment_qms-prod  - Production network (bridge)
qms_01_qms-dev      - Development network (bridge) 
podman              - Default podman network (bridge)
```

### **Port Allocation**
```
3000: Grafana (production)
3001: Mock API (training system)
3002: Frontend (not running)
3003: Frontend (not running)
5432: PostgreSQL (production)
6379: Redis (production)
8000: Backend API (not working)
9000-9001: MinIO (production)
9090: Prometheus (production)
9200: Elasticsearch (development - stopped)
5050: PgAdmin (development - stopped)
```

## 📁 **Deployment Configuration**

### **Configuration Files**
```
deployment/
├── docker-compose.prod.yml     # Production orchestration
├── podman-compose.prod.yml     # Podman variant
├── .env.prod                   # Production environment
├── .env.prod.template          # Template for env vars
├── Dockerfile.prod             # Production container build
└── deploy.sh                   # Deployment script
```

### **Key Environment Variables**
```bash
# From .env.prod
POSTGRES_SERVER=qms-db-prod
POSTGRES_PORT=5432
POSTGRES_DB=qms_prod
POSTGRES_USER=qms_user
POSTGRES_PASSWORD=xYMSN0tb6CFZsy2DcBuUTO91W
REDIS_URL=redis://qms-redis-prod:6379
MINIO_ENDPOINT=qms-minio-prod:9000
```

## 🗄️ **Database Status**

### **PostgreSQL Configuration**
```sql
Database: qms_prod
Host: localhost:5432
User: qms_user
Password: xYMSN0tb6CFZsy2DcBuUTO91W
Status: ✅ Healthy and accepting connections

Existing Tables:
- users (18 total existing QMS tables)
- departments
- audit_logs
- [... other QMS tables ...]

Training Integration Tables:
✅ training_modules
✅ training_programs  
✅ training_assignments
✅ training_documents
✅ training_prerequisites
✅ training_dashboard_stats (view)
```

### **Database Access Commands**
```bash
# Connect to production database
podman exec -it qms-db-prod psql -U qms_user -d qms_prod

# Check training tables
podman exec qms-db-prod psql -U qms_user -d qms_prod -c "\dt training_*"

# View training dashboard
podman exec qms-db-prod psql -U qms_user -d qms_prod -c "SELECT * FROM training_dashboard_stats;"
```

## 🚀 **Deployment Commands**

### **Starting/Stopping Services**
```bash
# Production environment
cd deployment/
podman-compose -f docker-compose.prod.yml up -d
podman-compose -f docker-compose.prod.yml down

# Individual containers
podman start qms-db-prod qms-redis-prod qms-minio-prod
podman stop qms-db-prod qms-redis-prod qms-minio-prod

# Check status
podman ps -a
podman logs qms-app-prod
```

### **Development Environment**
```bash
# Start development stack
cd deployment/
podman-compose -f docker-compose.dev.yml up -d

# Or individual dev containers
podman start qms-db-dev qms-redis-dev qms-minio-dev qms-elasticsearch-dev
```

## 🔧 **Common Maintenance Tasks**

### **Database Operations**
```bash
# Backup database
podman exec qms-db-prod pg_dump -U qms_user qms_prod > backup_$(date +%Y%m%d).sql

# Restore database
podman exec -i qms-db-prod psql -U qms_user -d qms_prod < backup_file.sql

# Check database size
podman exec qms-db-prod psql -U qms_user -d qms_prod -c "SELECT pg_database_size('qms_prod');"
```

### **Container Management**
```bash
# View container resources
podman stats

# Clean up unused containers/images
podman system prune

# View container logs
podman logs --tail=50 qms-app-prod

# Inspect container configuration
podman inspect qms-db-prod
```

## 🎯 **Training Management Integration Status**

### **Database Integration - COMPLETE**
```sql
-- Training tables successfully integrated
-- Foreign keys properly linked to existing users, departments, audit_logs
-- Sample data can be added using existing user/department IDs
-- Views and indexes optimized for performance
```

### **API Integration Status**
```
✅ Mock API: Fully operational on port 3001
❌ Production Backend: Container failing (environment issues)
✅ Frontend Config: Ready for integration
✅ Authentication: Working via mock API
```

## 🛡️ **Backup and Recovery**

### **Data Persistence**
```bash
# Database data persisted in:
podman volume ls | grep postgres

# MinIO data persisted in:
podman volume ls | grep minio

# Redis data (if persistent):
podman volume ls | grep redis
```

### **Recovery Procedures**
```bash
# 1. Database recovery
podman exec qms-db-prod pg_dump -U qms_user qms_prod > emergency_backup.sql

# 2. Container recreation
podman stop qms-db-prod
podman rm qms-db-prod
# Restart with docker-compose to restore

# 3. Network issues
podman network rm deployment_qms-prod
podman-compose -f docker-compose.prod.yml up -d
```

## ⚠️ **Known Issues and Workarounds**

### **Current Issues**
1. **Backend Container Failing**
   - **Symptom**: qms-app-prod exits with code 3
   - **Cause**: Database connection environment variables
   - **Workaround**: Use mock API for training functionality
   - **Fix**: Restore original container or fix environment

2. **Monitoring Services Not Responding**
   - **Symptom**: Prometheus/Grafana containers up but services down
   - **Impact**: No metrics/monitoring
   - **Priority**: Medium (operational, not critical)

### **Working Solutions**
1. **Training Management System**
   - **Status**: ✅ Fully operational via mock API
   - **Database**: ✅ Training tables integrated
   - **Frontend**: ✅ Configured and ready
   - **Access**: Mock API on port 3001

## 📚 **Reference Commands**

### **Quick Status Check**
```bash
# Complete system status
podman ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Network status
podman network ls

# Database connection test
podman exec qms-db-prod psql -U qms_user -d qms_prod -c "SELECT 'DB OK' as status;"

# Training system test
curl -s http://localhost:3001/health
```

### **Emergency Commands**
```bash
# Stop all containers
podman stop $(podman ps -q)

# Remove all containers (data preserved in volumes)
podman rm $(podman ps -aq)

# Recreate from compose
cd deployment && podman-compose -f docker-compose.prod.yml up -d

# Nuclear option - complete reset (DESTROYS DATA)
podman system reset
```

## 📋 **Architecture Diagram**
```
┌─── QMS Platform v3.0 ───┐
│                         │
├─ Production (qms-prod)  │
│  ├─ PostgreSQL:5432 ✅  │
│  ├─ Redis:6379     ✅  │
│  ├─ MinIO:9000     ✅  │
│  ├─ Backend:8000   ❌  │
│  ├─ Prometheus:9090 ⚠️ │
│  └─ Grafana:3000   ⚠️ │
│                         │
├─ Development (qms-dev)  │
│  ├─ PostgreSQL     ⏸️  │
│  ├─ Redis          ⏸️  │
│  ├─ MinIO          ⏸️  │
│  ├─ Elasticsearch  ⏸️  │
│  └─ PgAdmin        ⏸️  │
│                         │
├─ Training System        │
│  ├─ Database Tables ✅  │
│  ├─ Mock API:3001   ✅  │
│  └─ Frontend Ready  ✅  │
│                         │
└─ External Services      │
   ├─ Frontend:3002   ❌  │
   └─ Frontend:3003   ❌  │
```

---

**Memory Saved**: ✅ **Complete Podman setup documented**
**Infrastructure**: 🟢 **Solid and recoverable**
**Training Integration**: ✅ **Successfully preserved**
**Recovery Time**: ⏰ **Minutes with this documentation**

This memory file contains everything needed to understand, maintain, and recover your QMS Podman environment! 🚀