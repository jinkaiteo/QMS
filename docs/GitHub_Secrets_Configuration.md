# GitHub Secrets Configuration Guide

## Overview

This guide provides step-by-step instructions for configuring GitHub Secrets for the QMS system's staging and production environments. These secrets are essential for secure CI/CD pipeline operation and deployment.

## Required Secrets by Environment

### 🔒 **Repository-Level Secrets (Global)**

These secrets apply to all environments and workflows:

| Secret Name | Description | Example/Format |
|-------------|-------------|----------------|
| `GITHUB_TOKEN` | Automatically provided by GitHub Actions | `ghp_xxxxxxxxxxxx` |
| `SNYK_TOKEN` | Snyk security scanning API token | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `DOCKER_REGISTRY_USERNAME` | Container registry username | `github-user` |
| `DOCKER_REGISTRY_PASSWORD` | Container registry password/token | `ghp_xxxxxxxxxxxx` |

### 🧪 **Staging Environment Secrets**

Configure these in GitHub → Settings → Environments → staging:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `STAGING_DATABASE_URL` | Staging database connection string | `postgresql://user:pass@staging-db:5432/qms_staging` |
| `STAGING_REDIS_URL` | Staging Redis connection string | `redis://staging-redis:6379/0` |
| `STAGING_SECRET_KEY` | JWT secret key for staging | `staging-jwt-secret-key-32-chars` |
| `STAGING_ENCRYPTION_KEY` | Data encryption key | `base64-encoded-32-byte-key` |
| `STAGING_MINIO_ACCESS_KEY` | Staging object storage access key | `minio-staging-access` |
| `STAGING_MINIO_SECRET_KEY` | Staging object storage secret | `minio-staging-secret-key` |
| `STAGING_TEST_USERNAME` | Test user for staging validation | `staging-test-user` |
| `STAGING_TEST_PASSWORD` | Test user password | `StagingTest123!` |
| `STAGING_KUBECONFIG` | Kubernetes config for staging cluster | `base64-encoded-kubeconfig` |

### 🚀 **Production Environment Secrets**

Configure these in GitHub → Settings → Environments → production:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `PRODUCTION_DATABASE_URL` | Production database connection string | `postgresql://user:pass@prod-db:5432/qms_prod` |
| `PRODUCTION_REDIS_URL` | Production Redis connection string | `redis://prod-redis:6379/0` |
| `PRODUCTION_SECRET_KEY` | JWT secret key for production | `prod-jwt-secret-key-32-chars-strong` |
| `PRODUCTION_ENCRYPTION_KEY` | Data encryption key | `base64-encoded-32-byte-key` |
| `PRODUCTION_MINIO_ACCESS_KEY` | Production object storage access key | `minio-prod-access` |
| `PRODUCTION_MINIO_SECRET_KEY` | Production object storage secret | `minio-prod-secret-key` |
| `PRODUCTION_KUBECONFIG` | Kubernetes config for production cluster | `base64-encoded-kubeconfig` |
| `PRODUCTION_BACKUP_KEY` | Database backup encryption key | `base64-encoded-backup-key` |
| `PRODUCTION_MONITORING_KEY` | APM/monitoring service key | `monitoring-service-api-key` |

### 🔐 **Digital Signature & Compliance Secrets**

For 21 CFR Part 11 compliance:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SIGNATURE_CERT_PASSWORD` | Digital signature certificate password | `cert-password-123` |
| `CA_CERTIFICATE` | Certificate Authority certificate | `base64-encoded-ca-cert` |
| `TIMESTAMP_AUTHORITY_KEY` | Timestamp authority API key | `tsa-api-key-xxxxxxxxxxxx` |

### 📧 **Notification & Integration Secrets**

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SMTP_USERNAME` | Email server username | `noreply@company.com` |
| `SMTP_PASSWORD` | Email server password | `email-server-password` |
| `SLACK_WEBHOOK_URL` | Slack notifications webhook | `https://hooks.slack.com/services/xxx/yyy/zzz` |
| `TEAMS_WEBHOOK_URL` | Microsoft Teams webhook | `https://company.webhook.office.com/xxx` |

## Step-by-Step Configuration

### 1. Access GitHub Repository Settings

1. Navigate to your QMS repository on GitHub
2. Click **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**

### 2. Configure Repository Secrets

Add these global secrets that apply to all environments:

```bash
# Required for all workflows
SNYK_TOKEN=your-snyk-token-here
DOCKER_REGISTRY_USERNAME=your-github-username
DOCKER_REGISTRY_PASSWORD=your-github-token
```

### 3. Create Environment-Specific Secrets

#### Create Staging Environment:
1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name: `staging`
4. Configure protection rules (optional):
   - Required reviewers: None (for automated deployment)
   - Wait timer: 0 minutes
   - Deployment branches: `main` only

#### Create Production Environment:
1. Click **New environment**
2. Name: `production`
3. Configure protection rules:
   - ✅ Required reviewers: Add QA team members
   - ✅ Wait timer: 0 minutes
   - ✅ Deployment branches: `main` and `release/*`

### 4. Add Secrets to Each Environment

For **Staging Environment**:
```bash
# Database & Cache
STAGING_DATABASE_URL=postgresql://qms_user:staging_password@staging-db.internal:5432/qms_staging
STAGING_REDIS_URL=redis://:staging_redis_pass@staging-redis.internal:6379/0

# Security
STAGING_SECRET_KEY=staging-jwt-secret-key-must-be-32-characters-long
STAGING_ENCRYPTION_KEY=base64-encoded-fernet-key-for-data-encryption

# Object Storage
STAGING_MINIO_ACCESS_KEY=staging-minio-access
STAGING_MINIO_SECRET_KEY=staging-minio-secret-key-secure

# Testing
STAGING_TEST_USERNAME=staging-test-user
STAGING_TEST_PASSWORD=StagingTest123!CompliantPassword

# Deployment
STAGING_KUBECONFIG=base64-encoded-kubeconfig-for-staging-cluster
```

For **Production Environment**:
```bash
# Database & Cache
PRODUCTION_DATABASE_URL=postgresql://qms_user:secure_prod_pass@prod-db.internal:5432/qms_prod
PRODUCTION_REDIS_URL=redis://:prod_redis_secure_pass@prod-redis.internal:6379/0

# Security (Use strong, unique values)
PRODUCTION_SECRET_KEY=production-jwt-secret-32-chars-cryptographically-secure
PRODUCTION_ENCRYPTION_KEY=base64-encoded-production-fernet-key-unique

# Object Storage
PRODUCTION_MINIO_ACCESS_KEY=prod-minio-access-key
PRODUCTION_MINIO_SECRET_KEY=prod-minio-secret-key-very-secure

# Deployment
PRODUCTION_KUBECONFIG=base64-encoded-kubeconfig-for-production-cluster

# Backup & Monitoring
PRODUCTION_BACKUP_KEY=base64-encoded-backup-encryption-key
PRODUCTION_MONITORING_KEY=datadog-or-newrelic-api-key
```

## Security Best Practices

### 🔑 **Secret Generation Guidelines**

#### JWT Secret Keys:
```bash
# Generate secure JWT secret (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Encryption Keys:
```bash
# Generate Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### Database Passwords:
```bash
# Generate secure database password
python -c "import secrets; import string; chars = string.ascii_letters + string.digits + '!@#$%'; print(''.join(secrets.choice(chars) for _ in range(24)))"
```

### 🛡️ **Security Considerations**

1. **Unique Values**: Each environment must have unique secrets
2. **Strong Passwords**: Minimum 16 characters with mixed case, numbers, symbols
3. **Regular Rotation**: Rotate secrets quarterly or after team changes
4. **Access Control**: Limit who can view/modify secrets
5. **Audit Trail**: Monitor secret access and changes

### 📝 **Secret Validation**

Test secrets are properly configured:

```bash
# Validate staging secrets
curl -H "Authorization: Bearer $STAGING_TOKEN" \
  https://qms-staging.company.com/api/v1/system/health

# Validate production secrets  
curl -H "Authorization: Bearer $PRODUCTION_TOKEN" \
  https://qms.company.com/api/v1/system/health
```

## Environment Protection Rules

### Staging Environment Protection:
- ✅ No approval required (automated deployment)
- ✅ Allow administrators to bypass protection
- ✅ Restrict to `main` branch only

### Production Environment Protection:
- ✅ **Required reviewers**: Minimum 2 from QA/DevOps team
- ✅ **Prevent self-review**: Deployer cannot approve their own deployment
- ✅ **Restrict branches**: Only `main` and `release/*` branches
- ✅ **Wait timer**: Optional 5-minute delay for critical thinking

## Kubernetes Configuration

### Base64 Encode Kubeconfig:
```bash
# Encode kubeconfig for GitHub Secrets
cat ~/.kube/config-staging | base64 -w 0
cat ~/.kube/config-production | base64 -w 0
```

### Service Account Setup:
```yaml
# Create service account for GitHub Actions
apiVersion: v1
kind: ServiceAccount
metadata:
  name: github-actions-deployer
  namespace: qms-production
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: github-actions-deployer
rules:
- apiGroups: ["apps", ""]
  resources: ["deployments", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: github-actions-deployer
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: github-actions-deployer
subjects:
- kind: ServiceAccount
  name: github-actions-deployer
  namespace: qms-production
```

## Troubleshooting

### Common Issues:

1. **Secret Not Found**:
   - Verify secret name matches exactly (case-sensitive)
   - Check environment name is correct
   - Ensure secret is added to correct environment

2. **Base64 Encoding Issues**:
   ```bash
   # Correct way to encode for GitHub Secrets
   echo -n "your-secret-value" | base64 -w 0
   ```

3. **Kubernetes Access Issues**:
   - Verify kubeconfig is valid
   - Check service account permissions
   - Validate cluster connectivity

### Validation Commands:
```bash
# Test database connection
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('Database connection: OK')
"

# Test Redis connection
python -c "
import os
import redis
r = redis.from_url(os.environ['REDIS_URL'])
r.ping()
print('Redis connection: OK')
"
```

## Security Compliance

### Audit Requirements:
- Document all secret rotations
- Maintain access logs
- Regular security reviews
- Compliance with 21 CFR Part 11 requirements

### Monitoring:
- Set up alerts for failed authentications
- Monitor unusual access patterns
- Log all deployment activities
- Track secret usage and rotation

This configuration ensures secure, compliant operation of the QMS system across all environments while maintaining the necessary security controls for pharmaceutical industry requirements.