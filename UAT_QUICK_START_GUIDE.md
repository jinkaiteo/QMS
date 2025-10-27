# 🚀 QMS Platform UAT - Quick Start Guide

## 📊 **Current Environment Status**

### ✅ **Backend Services**
```
✅ FastAPI Backend: http://localhost:8000 (Running)
✅ PostgreSQL Database: Connected and operational
✅ Redis Cache: Active
✅ MinIO Storage: Operational
✅ Elasticsearch: Running
```

### 🎯 **Frontend Status**
```
✅ Vite Dev Server: Process running (PID: 3486178)
✅ Port 5173: Should be accessible
✅ Node.js: Active with hot reload
✅ Frontend Build: Ready for testing
```

### 🔧 **Authentication Enhancements Deployed**
```
✅ IP Address Capture: Real client IPs (not 127.0.0.1)
✅ User Agent Detection: Browser identification working
✅ Token Blacklisting: Secure logout implemented
✅ Token Rotation: Refresh token security active
✅ Audit Logging: Complete context capture
✅ System Health: Real-time timestamps
```

## 🧪 **Immediate UAT Actions**

### **Step 1: Verify Frontend Access (2 minutes)**
```bash
# Option A: Open browser directly
Browser: http://localhost:5173

# Option B: Check from terminal
curl -I http://localhost:5173

# Option C: If port 5173 fails, try alternative
Browser: http://localhost:3000
```

### **Step 2: Quick Authentication Test (5 minutes)**
```
1. Open: http://localhost:5173
2. Login with test credentials
3. Check browser network tab for real IP in requests
4. Logout and verify session termination
5. Try accessing protected endpoint after logout
```

### **Step 3: Permission System Validation (10 minutes)**
```
# Test different user roles:
1. QA Manager Login:
   - Should see all modules
   - Access all documents/CAPAs
   - Can complete others' CAPA actions

2. Department Employee Login:
   - Limited module access
   - Only department documents visible
   - Cannot access other departments

3. Regular User Login:
   - Basic access only
   - Own documents/assignments only
   - Cannot perform management actions
```

### **Step 4: System Health Verification (3 minutes)**
```
1. API Health: http://localhost:8000/api/v1/system/health
   - Check for real timestamp (not 2024-01-01)
   - Verify database connectivity
   
2. API Docs: http://localhost:8000/docs
   - Confirm all endpoints available
   - Test authentication endpoints
```

## 🎯 **Critical UAT Test Cases**

### **Priority 1: Authentication Security (15 minutes)**

#### **Test A: Real Context Capture**
```
✅ Expected: Real IP addresses in audit logs
✅ Expected: Actual browser User-Agent strings
✅ Expected: No hardcoded "127.0.0.1" or "FastAPI Test"

Test Steps:
1. Open browser dev tools → Network tab
2. Login to application
3. Check request headers for X-Forwarded-For
4. Verify backend logs show real IP/User-Agent
```

#### **Test B: Token Security**
```
✅ Expected: Tokens invalidated after logout
✅ Expected: Refresh tokens rotate securely
✅ Expected: Old tokens rejected

Test Steps:
1. Login → Save access token from response
2. Make API call with token (should work)
3. Logout from application
4. Retry API call with same token (should fail: 401)
```

### **Priority 2: Permission Enforcement (20 minutes)**

#### **Test C: Document Access Control**
```
✅ Expected: Role-based document access
✅ Expected: Department/organization boundaries respected
✅ Expected: Ownership access preserved

Test Users Needed:
- QA Manager (global access)
- Department Employee (limited access)
- Other Department Employee (no access to first dept)
```

#### **Test D: CAPA Management**
```
✅ Expected: Assigned users can complete own actions
✅ Expected: Managers can complete others' actions
✅ Expected: Non-managers cannot complete others' actions

Test Steps:
1. Create CAPA assigned to Employee A
2. Login as Employee A → Complete action (should work)
3. Create new CAPA assigned to Employee A  
4. Login as Manager → Complete Employee A's action (should work)
5. Login as Employee B → Try completing Employee A's action (should fail)
```

### **Priority 3: System Health (10 minutes)**

#### **Test E: Real-time Monitoring**
```
✅ Expected: Current timestamps in health checks
✅ Expected: Accurate system status reporting

Test Steps:
1. Call /api/v1/system/health multiple times
2. Verify different timestamps each call
3. Check timestamp format: 2025-10-27T07:XX:XXZ
4. Confirm no hardcoded "2024-01-01" values
```

## 📋 **UAT Checklist - Quick Validation**

### **✅ Authentication Enhancements**
- [ ] Real IP addresses captured (not 127.0.0.1)
- [ ] Actual User-Agent strings logged (not "FastAPI Test")  
- [ ] Token blacklisting working (logout invalidates tokens)
- [ ] Refresh token rotation functional
- [ ] Complete audit trail with context

### **✅ Permission System**
- [ ] Document access based on roles/departments
- [ ] CAPA management with override permissions
- [ ] Quality event access hierarchy working
- [ ] Proper access denial for unauthorized users

### **✅ System Health**
- [ ] Real-time timestamps (current date/time)
- [ ] Health endpoint accurate status
- [ ] System info endpoint functional
- [ ] No hardcoded test values

### **✅ User Experience**
- [ ] Frontend loads and functions normally
- [ ] No performance degradation
- [ ] Smooth login/logout experience
- [ ] Appropriate error messages

## 🚨 **Common Issues & Quick Fixes**

### **Frontend Not Accessible**
```bash
# Check if Vite is running
ps aux | grep vite

# Restart if needed
cd frontend && npm run dev

# Check port binding
netstat -tulpn | grep 5173
```

### **Backend API Issues**
```bash
# Check backend status
ps aux | grep uvicorn

# Restart if needed  
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Database Connection Issues**
```bash
# Check database container
podman ps | grep postgres

# Restart if needed
podman start qms-db-dev
```

## ⏱️ **UAT Time Estimates**

### **Quick Validation (30 minutes)**
- Frontend accessibility check: 5 minutes
- Authentication testing: 10 minutes  
- Permission spot checks: 10 minutes
- System health verification: 5 minutes

### **Comprehensive UAT (2-3 hours)**
- Full authentication test suite: 45 minutes
- Complete permission matrix testing: 60 minutes
- Performance and compliance testing: 45 minutes
- Documentation and sign-off: 30 minutes

## 🎯 **Success Criteria Summary**

### **Must Pass (Critical)**
✅ All 11 TODO fixes functional and tested  
✅ No security regressions or vulnerabilities  
✅ Permission system enforces proper access control  
✅ Real-time monitoring and audit capabilities  

### **Should Pass (Important)**  
✅ User experience remains smooth with enhancements  
✅ Performance within acceptable limits  
✅ Comprehensive audit trail for compliance  
✅ Cross-browser compatibility maintained  

### **UAT Sign-off Requirements**
✅ All Priority 1 & 2 test cases pass  
✅ No critical or high-severity issues  
✅ Performance benchmarks met  
✅ Pharmaceutical compliance verified  

---

**Ready to Start UAT**: ✅ **YES**  
**Environment Status**: 🟢 **OPERATIONAL**  
**Test Coverage**: 📋 **COMPREHENSIVE**  
**Expected Duration**: ⏱️ **30 minutes (quick) - 3 hours (full)**

Let's begin UAT! 🚀