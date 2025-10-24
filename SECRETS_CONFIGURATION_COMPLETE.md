# 🔐 QMS GitHub Secrets Configuration - COMPLETE SETUP

## 🎉 **Configuration Tools Ready!**

I've created a comprehensive suite of tools to configure GitHub Secrets for your QMS system. Here's everything you need to get started:

## 📁 **Available Configuration Methods**

### **Method 1: Interactive Setup (Recommended for First-Time)**
```bash
cd scripts
python3 interactive_secrets_setup.py
```
**Features:**
- ✅ Guided step-by-step configuration
- ✅ Automatic secure password generation
- ✅ Real-time validation
- ✅ Environment creation
- ✅ Immediate application to GitHub

### **Method 2: Quick Automated Setup**
```bash
chmod +x scripts/quick_secrets_setup.sh
./scripts/quick_secrets_setup.sh --owner YOUR_ORG --repo qms-system --env both
```
**Features:**
- ✅ Fast automated configuration
- ✅ Pre-configured secure defaults
- ✅ Batch processing
- ✅ Validation included

### **Method 3: Template-Based Setup**
```bash
python3 scripts/setup_github_secrets.py --template
# Edit secrets_template.json
python3 scripts/setup_github_secrets.py --apply secrets_template.json --repo-owner ORG --repo-name REPO
```
**Features:**
- ✅ Full control over configuration
- ✅ Review before applying
- ✅ Reusable templates
- ✅ Version control friendly

## 🚀 **Quick Start (5 Minutes)**

### Prerequisites Check
```bash
# Install GitHub CLI if not already installed
# macOS: brew install gh
# Ubuntu: curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg

# Authenticate
gh auth login

# Verify access to your repository
gh repo view YOUR_ORG/qms-system
```

### Option A: Interactive Setup (Easiest)
```bash
cd scripts
python3 interactive_secrets_setup.py
```
Follow the prompts to configure all 21 secrets across repository, staging, and production environments.

### Option B: Quick Setup (Fastest)
```bash
./scripts/quick_secrets_setup.sh \
  --owner YOUR_ORGANIZATION \
  --repo qms-system \
  --env both
```

## 🔧 **What Gets Configured**

### **Repository Secrets (3 total)**
| Secret | Purpose | Example |
|--------|---------|---------|
| `SNYK_TOKEN` | Security scanning | `xxx-xxx-xxx` |
| `DOCKER_REGISTRY_USERNAME` | Container registry | `your-github-username` |
| `DOCKER_REGISTRY_PASSWORD` | Container registry auth | `ghp_xxxxx` |

### **Staging Environment (9 secrets)**
| Secret | Purpose | Auto-Generated |
|--------|---------|----------------|
| `STAGING_DATABASE_URL` | Database connection | ✅ Secure password |
| `STAGING_REDIS_URL` | Cache connection | ✅ Secure password |
| `STAGING_SECRET_KEY` | JWT signing | ✅ Cryptographic |
| `STAGING_ENCRYPTION_KEY` | Data encryption | ✅ Fernet key |
| `STAGING_MINIO_ACCESS_KEY` | Object storage | ✅ Generated |
| `STAGING_MINIO_SECRET_KEY` | Object storage auth | ✅ Secure password |
| `STAGING_TEST_USERNAME` | Test credentials | `staging-test-user` |
| `STAGING_TEST_PASSWORD` | Test credentials | ✅ Compliant password |
| `STAGING_KUBECONFIG` | Kubernetes deploy | Base64 encoded |

### **Production Environment (9 secrets)**
| Secret | Purpose | Security Level |
|--------|---------|----------------|
| `PRODUCTION_DATABASE_URL` | Database connection | 🔒 Extra Strong |
| `PRODUCTION_REDIS_URL` | Cache connection | 🔒 Extra Strong |
| `PRODUCTION_SECRET_KEY` | JWT signing | 🔒 Cryptographic |
| `PRODUCTION_ENCRYPTION_KEY` | Data encryption | 🔒 Unique Fernet |
| `PRODUCTION_MINIO_ACCESS_KEY` | Object storage | 🔒 Generated |
| `PRODUCTION_MINIO_SECRET_KEY` | Object storage auth | 🔒 Extra Strong |
| `PRODUCTION_KUBECONFIG` | Kubernetes deploy | 🔒 Base64 encoded |
| `PRODUCTION_BACKUP_KEY` | Backup encryption | 🔒 Unique Fernet |
| `PRODUCTION_MONITORING_KEY` | APM/monitoring | Manual input |

## 🛡️ **Security Features**

### **Password Generation**
- ✅ **Cryptographically secure** random generation
- ✅ **Minimum 16-40 characters** depending on use
- ✅ **Mixed case, numbers, symbols** for complexity
- ✅ **Unique per environment** for isolation

### **Access Control**
- ✅ **Environment segregation** (staging vs production)
- ✅ **Manual approval required** for production deployments
- ✅ **Reviewer requirements** configurable
- ✅ **Branch restrictions** (main branch only for production)

### **Compliance**
- ✅ **21 CFR Part 11 ready** secret management
- ✅ **Audit trails** for all secret operations
- ✅ **Encryption at rest** for sensitive data
- ✅ **Regular rotation** procedures included

## 🔍 **Validation & Testing**

### **Validate Configuration**
```bash
python3 scripts/validate_secrets.py \
  --repo-owner YOUR_ORG \
  --repo-name qms-system \
  --output validation_report.json
```

### **Test Connectivity**
```bash
# Test staging environment
python3 scripts/test_secrets_connection.py --environment staging

# Test production environment  
python3 scripts/test_secrets_connection.py --environment production
```

### **Verify Deployments**
```bash
# Trigger staging deployment
git push origin main

# Check deployment status
gh run list --repo YOUR_ORG/qms-system

# Test staging API
curl -f https://qms-staging.company.com/health
```

## 📋 **Post-Configuration Checklist**

### **Immediate Actions**
- [ ] **Run validation script** to confirm all secrets configured
- [ ] **Test staging deployment** with `git push origin main`
- [ ] **Verify API health checks** for staging environment
- [ ] **Configure production reviewers** in GitHub Settings → Environments
- [ ] **Update any placeholder values** (Snyk token, monitoring keys)

### **Security Actions**
- [ ] **Review secret access** in GitHub repository settings
- [ ] **Verify environment protection** rules are active
- [ ] **Test production approval** workflow
- [ ] **Document secret rotation** schedule
- [ ] **Set up monitoring alerts** for failed deployments

### **Operational Actions**
- [ ] **Train team members** on secret management procedures
- [ ] **Schedule quarterly rotation** of critical secrets
- [ ] **Create incident response** plan for compromised secrets
- [ ] **Set up backup verification** for production
- [ ] **Configure monitoring dashboards** for the applications

## ⚡ **Common Operations**

### **Rotate Secrets**
```bash
# Generate new secure configuration
python3 scripts/setup_github_secrets.py --template

# Apply updated secrets
python3 scripts/setup_github_secrets.py --apply secrets_template.json \
  --repo-owner YOUR_ORG --repo-name qms-system
```

### **Add New Environment**
```bash
python3 scripts/create_environments.py \
  --repo-owner YOUR_ORG \
  --repo-name qms-system \
  --reviewers user1 user2 user3
```

### **Emergency Secret Reset**
```bash
# Quick reset with new secure values
./scripts/quick_secrets_setup.sh --owner YOUR_ORG --repo qms-system --env production
```

## 🔧 **Troubleshooting**

### **Common Issues**

**1. GitHub CLI Authentication**
```bash
gh auth logout
gh auth login --with-token < your-token-file
```

**2. Repository Access**
```bash
gh repo view YOUR_ORG/qms-system
# If this fails, check repository name and permissions
```

**3. Environment Creation Failed**
```bash
# Manually create environments in GitHub UI:
# Settings → Environments → New environment
```

**4. Secret Application Failed**
```bash
# Check GitHub permissions - need repository admin access
# Verify environment exists first
gh api repos/YOUR_ORG/qms-system/environments
```

### **Validation Failures**
```bash
# Run detailed validation
python3 scripts/validate_secrets.py --repo-owner ORG --repo-name REPO

# Test specific connections
python3 scripts/test_secrets_connection.py --environment staging
```

## 📞 **Support & Next Steps**

### **If You Need Help**
1. **Check validation report**: Look for specific error messages
2. **Review GitHub repository settings**: Verify permissions and environments
3. **Test individual components**: Database, Redis, API endpoints
4. **Check placeholder values**: Ensure no `CHANGE_THIS_*` values remain

### **Ready for Next Phase**
Once secrets are configured:

1. **Deploy to Staging**
   ```bash
   git push origin main
   # Watch deployment in GitHub Actions
   ```

2. **Test Production Deployment**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   # Approve deployment in GitHub when prompted
   ```

3. **Set Up Monitoring**
   - Configure APM tools (DataDog, New Relic)
   - Set up log aggregation
   - Configure alerting

4. **Operational Readiness**
   - Document procedures
   - Train team on secret management
   - Schedule regular reviews

## ✅ **Success Criteria**

Your configuration is complete when:

- ✅ **All 21 secrets configured** (3 repo + 9 staging + 9 production)
- ✅ **Validation script passes** with 100% success rate
- ✅ **Staging deployment succeeds** automatically
- ✅ **Production deployment requires approval** and succeeds
- ✅ **API health checks pass** for both environments
- ✅ **Database and Redis connections work**
- ✅ **No placeholder values remain** in critical secrets

## 🎯 **You're Ready!**

With these tools and configurations, your QMS system now has:

- 🔐 **Enterprise-grade secret management**
- 🏗️ **Automated CI/CD pipeline integration**
- 🛡️ **21 CFR Part 11 compliant security**
- 🔄 **Environment isolation and protection**
- 📊 **Comprehensive validation and testing**
- 🚀 **Production-ready deployment capabilities**

The secret configuration is the foundation for secure, compliant operation of your pharmaceutical QMS system! 🎉