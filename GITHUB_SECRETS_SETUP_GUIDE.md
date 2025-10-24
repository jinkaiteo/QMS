# QMS GitHub Secrets Setup - Complete Guide

## 🎯 **Quick Start**

This guide will walk you through setting up all required GitHub Secrets for the QMS system's staging and production environments.

## 📋 **Prerequisites**

### 1. Install GitHub CLI
```bash
# macOS
brew install gh

# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh

# Windows
winget install --id GitHub.cli
```

### 2. Authenticate GitHub CLI
```bash
gh auth login
# Follow the prompts to authenticate with your GitHub account
```

### 3. Required Permissions
- **Repository admin** access to configure secrets
- **Organization owner** (if using organization-level secrets)

## 🚀 **Automated Setup (Recommended)**

### Step 1: Generate Secrets Template
```bash
cd scripts
python setup_github_secrets.py --template
```

This creates `secrets_template.json` with all required secrets.

### Step 2: Edit Template
```bash
# Edit the template file with your actual values
nano secrets_template.json

# Replace all "CHANGE_THIS_*" values with real secrets
# Update database URLs, API keys, etc.
```

### Step 3: Create GitHub Environments
```bash
python create_environments.py \
  --repo-owner YOUR_ORG \
  --repo-name qms-system \
  --reviewers user1 user2 user3 \
  --branch-protection
```

### Step 4: Apply Secrets
```bash
export GITHUB_TOKEN=your_github_token_here

python setup_github_secrets.py \
  --apply secrets_template.json \
  --repo-owner YOUR_ORG \
  --repo-name qms-system
```

### Step 5: Validate Configuration
```bash
python validate_secrets.py \
  --repo-owner YOUR_ORG \
  --repo-name qms-system \
  --output validation_report.json
```

## 🔧 **Manual Setup**

### Step 1: Create Environments

1. Go to your GitHub repository
2. Click **Settings** → **Environments**
3. Create **staging** environment:
   - No reviewers required
   - Allow main branch deployments
4. Create **production** environment:
   - Add 2+ reviewers from QA/DevOps team
   - Restrict to main branch only

### Step 2: Configure Repository Secrets

Go to **Settings** → **Secrets and variables** → **Actions**:

```bash
# Security Scanning
SNYK_TOKEN=your-snyk-token-here
DOCKER_REGISTRY_USERNAME=your-github-username  
DOCKER_REGISTRY_PASSWORD=your-github-token
```

### Step 3: Configure Staging Environment Secrets

In **Environments** → **staging**:

```bash
# Database & Cache
STAGING_DATABASE_URL=postgresql://qms_user:staging_pass@staging-db:5432/qms_staging
STAGING_REDIS_URL=redis://:staging_redis_pass@staging-redis:6379/0

# Security
STAGING_SECRET_KEY=staging-jwt-secret-32-chars-minimum
STAGING_ENCRYPTION_KEY=base64-encoded-fernet-key

# Object Storage  
STAGING_MINIO_ACCESS_KEY=staging-minio-access
STAGING_MINIO_SECRET_KEY=staging-minio-secret-key

# Testing
STAGING_TEST_USERNAME=staging-test-user
STAGING_TEST_PASSWORD=StagingTest123!

# Deployment
STAGING_KUBECONFIG=base64-encoded-kubeconfig
```

### Step 4: Configure Production Environment Secrets

In **Environments** → **production**:

```bash
# Database & Cache (Use strong passwords!)
PRODUCTION_DATABASE_URL=postgresql://qms_user:STRONG_PROD_PASSWORD@prod-db:5432/qms_prod
PRODUCTION_REDIS_URL=redis://:STRONG_REDIS_PASSWORD@prod-redis:6379/0

# Security (Use cryptographically secure values!)
PRODUCTION_SECRET_KEY=production-jwt-secret-32-chars-cryptographically-secure
PRODUCTION_ENCRYPTION_KEY=base64-encoded-production-fernet-key

# Object Storage
PRODUCTION_MINIO_ACCESS_KEY=prod-minio-access
PRODUCTION_MINIO_SECRET_KEY=production-minio-secret-very-secure

# Deployment & Monitoring
PRODUCTION_KUBECONFIG=base64-encoded-production-kubeconfig
PRODUCTION_BACKUP_KEY=base64-encoded-backup-encryption-key
PRODUCTION_MONITORING_KEY=monitoring-service-api-key
```

## 🔐 **Secret Generation Guide**

### Generate Strong Passwords
```bash
# JWT Secret (32+ characters)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Database Password (24 characters with symbols)
python3 -c "import secrets, string; chars=string.ascii_letters+string.digits+'!@#$%^&*'; print(''.join(secrets.choice(chars) for _ in range(24)))"

# Encryption Key (Fernet)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Encode Kubeconfig
```bash
# Encode kubeconfig for GitHub Secrets
cat ~/.kube/config | base64 -w 0
```

### Test Database Connections
```bash
# Test staging database
psql "postgresql://qms_user:password@staging-db:5432/qms_staging" -c "SELECT 1;"

# Test production database  
psql "postgresql://qms_user:password@prod-db:5432/qms_prod" -c "SELECT 1;"
```

## 🛡️ **Security Best Practices**

### 1. Use Unique Values
- **Different passwords** for each environment
- **Different encryption keys** for each environment  
- **Different API keys** where possible

### 2. Strong Password Requirements
- **Minimum 16 characters** for passwords
- **Mix of uppercase, lowercase, numbers, symbols**
- **No dictionary words or common patterns**

### 3. Regular Rotation
- **Quarterly rotation** for all secrets
- **Immediate rotation** after team member changes
- **Emergency rotation** if compromise suspected

### 4. Access Control
- **Limit secret access** to essential team members
- **Use environment protection** for production
- **Audit secret access** regularly

## 🔍 **Validation & Testing**

### Validate Secrets Configuration
```bash
# Check all secrets are configured
python validate_secrets.py --repo-owner ORG --repo-name REPO

# Test staging environment
curl -f https://qms-staging.company.com/health

# Test production environment  
curl -f https://qms.company.com/health
```

### Test CI/CD Pipeline
```bash
# Trigger CI pipeline
git push origin main

# Check workflow status
gh run list --repo ORG/REPO

# View specific run
gh run view RUN_ID --repo ORG/REPO
```

## 🚨 **Troubleshooting**

### Common Issues

**1. GitHub CLI Authentication Failed**
```bash
# Re-authenticate
gh auth logout
gh auth login --with-token < your-token-file
```

**2. Secret Not Found in Workflow**
```bash
# Check secret name (case-sensitive)
gh secret list --repo ORG/REPO
gh secret list --repo ORG/REPO --env staging
```

**3. Base64 Encoding Issues**
```bash
# Correct encoding (no line breaks)
echo -n "your-secret" | base64 -w 0
```

**4. Kubeconfig Connection Failed**
```bash
# Test kubeconfig locally
export KUBECONFIG=/path/to/kubeconfig
kubectl cluster-info
```

### Debug Workflow Failures
```bash
# View workflow logs
gh run view --log

# Check specific job
gh run view RUN_ID --job "Job Name"

# Download logs
gh run download RUN_ID
```

## 📊 **Validation Checklist**

### ✅ **Repository Level**
- [ ] SNYK_TOKEN configured
- [ ] DOCKER_REGISTRY_USERNAME configured  
- [ ] DOCKER_REGISTRY_PASSWORD configured

### ✅ **Staging Environment**
- [ ] All 9 staging secrets configured
- [ ] Database connection working
- [ ] Redis connection working
- [ ] MinIO access working
- [ ] Kubernetes access working
- [ ] API health check passing

### ✅ **Production Environment**  
- [ ] All 9 production secrets configured
- [ ] Strong, unique passwords used
- [ ] Database connection working
- [ ] Redis connection working
- [ ] MinIO access working
- [ ] Kubernetes access working
- [ ] API health check passing
- [ ] Reviewers configured for deployments

### ✅ **Security Validation**
- [ ] All secrets use strong, unique values
- [ ] No placeholder values remain
- [ ] Database passwords are strong (16+ chars)
- [ ] Encryption keys are properly generated
- [ ] Access is limited to essential team members
- [ ] Environment protection rules configured

## 🎯 **Next Steps**

After completing secrets configuration:

1. **Test Deployments**
   ```bash
   # Trigger staging deployment
   git push origin main
   
   # Test production deployment (with approval)
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Set Up Monitoring**
   - Configure APM tools (DataDog, New Relic)
   - Set up log aggregation
   - Configure alerting for failures

3. **Document Access**
   - Create access procedures
   - Document rotation schedule
   - Create incident response plan

4. **Regular Maintenance**
   - Schedule quarterly secret rotation
   - Review access permissions monthly
   - Update backup procedures

## 📞 **Support**

If you encounter issues:

1. **Check validation report**: `python validate_secrets.py`
2. **Review workflow logs**: `gh run view --log`
3. **Test individual components**: Database, Redis, MinIO, Kubernetes
4. **Verify secret values**: Ensure no placeholders remain

The secrets configuration is critical for secure operation of the QMS system across all environments! 🔐