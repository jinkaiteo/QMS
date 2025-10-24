#!/bin/bash
# QMS GitHub Secrets - Quick Setup Script
# Automated setup for common configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER=""
REPO_NAME=""
ENVIRONMENT="production"
CONFIG_FILE="qms_secrets_quick.json"

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_help() {
    cat << EOF
QMS GitHub Secrets Quick Setup

Usage: $0 [OPTIONS]

Options:
    -o, --owner OWNER          GitHub repository owner/organization
    -r, --repo REPO           GitHub repository name
    -e, --env ENVIRONMENT     Target environment (staging|production|both)
    -f, --file CONFIG_FILE    Configuration file to use
    -i, --interactive         Run interactive setup
    -v, --validate           Validate existing secrets
    -h, --help               Show this help message

Examples:
    $0 --owner myorg --repo qms-system --env both
    $0 --interactive
    $0 --validate --owner myorg --repo qms-system
EOF
}

validate_prerequisites() {
    log_info "Validating prerequisites..."
    
    # Check GitHub CLI
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI not found. Install from: https://cli.github.com/"
        exit 1
    fi
    
    # Check authentication
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI not authenticated. Run: gh auth login"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found. Please install Python 3."
        exit 1
    fi
    
    log_success "Prerequisites validated"
}

validate_repository() {
    log_info "Validating repository access..."
    
    if [ -z "$REPO_OWNER" ] || [ -z "$REPO_NAME" ]; then
        log_error "Repository owner and name are required"
        exit 1
    fi
    
    if ! gh repo view "$REPO_OWNER/$REPO_NAME" &> /dev/null; then
        log_error "Cannot access repository: $REPO_OWNER/$REPO_NAME"
        exit 1
    fi
    
    log_success "Repository access confirmed: $REPO_OWNER/$REPO_NAME"
}

generate_secure_password() {
    local length=${1:-24}
    python3 -c "import secrets, string; chars = string.ascii_letters + string.digits + '!@#\$%^&*'; print(''.join(secrets.choice(chars) for _ in range($length)))"
}

generate_jwt_secret() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

generate_encryption_key() {
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
}

create_environments() {
    log_info "Creating GitHub environments..."
    
    # Create staging environment
    log_info "Creating staging environment..."
    gh api "/repos/$REPO_OWNER/$REPO_NAME/environments/staging" \
        --method PUT \
        --field wait_timer=0 \
        > /dev/null 2>&1 || log_warning "Staging environment may already exist"
    
    # Create production environment
    log_info "Creating production environment..."
    gh api "/repos/$REPO_OWNER/$REPO_NAME/environments/production" \
        --method PUT \
        --field wait_timer=0 \
        > /dev/null 2>&1 || log_warning "Production environment may already exist"
    
    log_success "Environments created"
}

generate_quick_config() {
    log_info "Generating secure configuration..."
    
    # Generate secure values
    STAGING_DB_PASSWORD=$(generate_secure_password 24)
    STAGING_REDIS_PASSWORD=$(generate_secure_password 20)
    STAGING_MINIO_SECRET=$(generate_secure_password 32)
    STAGING_JWT_SECRET=$(generate_jwt_secret)
    STAGING_ENCRYPTION_KEY=$(generate_encryption_key)
    
    PRODUCTION_DB_PASSWORD=$(generate_secure_password 32)
    PRODUCTION_REDIS_PASSWORD=$(generate_secure_password 24)
    PRODUCTION_MINIO_SECRET=$(generate_secure_password 40)
    PRODUCTION_JWT_SECRET=$(generate_jwt_secret)
    PRODUCTION_ENCRYPTION_KEY=$(generate_encryption_key)
    PRODUCTION_BACKUP_KEY=$(generate_encryption_key)
    
    # Create configuration file
    cat > "$CONFIG_FILE" << EOF
{
  "repository_secrets": {
    "SNYK_TOKEN": "CHANGE_THIS_SNYK_TOKEN",
    "DOCKER_REGISTRY_USERNAME": "github-username",
    "DOCKER_REGISTRY_PASSWORD": "CHANGE_THIS_GITHUB_TOKEN"
  },
  "staging_secrets": {
    "STAGING_DATABASE_URL": "postgresql://qms_user:${STAGING_DB_PASSWORD}@staging-db.internal:5432/qms_staging",
    "STAGING_REDIS_URL": "redis://:${STAGING_REDIS_PASSWORD}@staging-redis.internal:6379/0",
    "STAGING_SECRET_KEY": "${STAGING_JWT_SECRET}",
    "STAGING_ENCRYPTION_KEY": "${STAGING_ENCRYPTION_KEY}",
    "STAGING_MINIO_ACCESS_KEY": "staging-minio-access",
    "STAGING_MINIO_SECRET_KEY": "${STAGING_MINIO_SECRET}",
    "STAGING_TEST_USERNAME": "staging-test-user",
    "STAGING_TEST_PASSWORD": "StagingTest123!CompliantPassword",
    "STAGING_KUBECONFIG": "CHANGE_THIS_STAGING_KUBECONFIG"
  },
  "production_secrets": {
    "PRODUCTION_DATABASE_URL": "postgresql://qms_user:${PRODUCTION_DB_PASSWORD}@prod-db.internal:5432/qms_prod",
    "PRODUCTION_REDIS_URL": "redis://:${PRODUCTION_REDIS_PASSWORD}@prod-redis.internal:6379/0",
    "PRODUCTION_SECRET_KEY": "${PRODUCTION_JWT_SECRET}",
    "PRODUCTION_ENCRYPTION_KEY": "${PRODUCTION_ENCRYPTION_KEY}",
    "PRODUCTION_MINIO_ACCESS_KEY": "prod-minio-access",
    "PRODUCTION_MINIO_SECRET_KEY": "${PRODUCTION_MINIO_SECRET}",
    "PRODUCTION_KUBECONFIG": "CHANGE_THIS_PRODUCTION_KUBECONFIG",
    "PRODUCTION_BACKUP_KEY": "${PRODUCTION_BACKUP_KEY}",
    "PRODUCTION_MONITORING_KEY": "CHANGE_THIS_PRODUCTION_MONITORING_KEY"
  }
}
EOF
    
    log_success "Configuration generated: $CONFIG_FILE"
}

apply_repository_secrets() {
    log_info "Applying repository secrets..."
    
    local config_file="$1"
    local count=0
    local total=0
    
    # Read and apply repository secrets
    python3 << EOF
import json
import subprocess
import sys

with open('$config_file', 'r') as f:
    config = json.load(f)

repo_secrets = config.get('repository_secrets', {})
success_count = 0
total_count = len(repo_secrets)

for name, value in repo_secrets.items():
    try:
        cmd = [
            'gh', 'secret', 'set', name,
            '--repo', '$REPO_OWNER/$REPO_NAME',
            '--body', value
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {name}")
            success_count += 1
        else:
            print(f"❌ {name}: {result.stderr}")
    except Exception as e:
        print(f"❌ {name}: {e}")

print(f"Repository secrets: {success_count}/{total_count}")
sys.exit(0 if success_count == total_count else 1)
EOF
}

apply_environment_secrets() {
    local environment="$1"
    local config_file="$2"
    
    log_info "Applying $environment secrets..."
    
    python3 << EOF
import json
import subprocess
import sys

with open('$config_file', 'r') as f:
    config = json.load(f)

env_secrets = config.get('${environment}_secrets', {})
success_count = 0
total_count = len(env_secrets)

for name, value in env_secrets.items():
    try:
        cmd = [
            'gh', 'secret', 'set', name,
            '--repo', '$REPO_OWNER/$REPO_NAME',
            '--env', '$environment',
            '--body', value
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {name}")
            success_count += 1
        else:
            print(f"❌ {name}: {result.stderr}")
    except Exception as e:
        print(f"❌ {name}: {e}")

print(f"$environment secrets: {success_count}/{total_count}")
sys.exit(0 if success_count == total_count else 1)
EOF
}

validate_secrets() {
    log_info "Validating secrets configuration..."
    
    if [ -f "scripts/validate_secrets.py" ]; then
        python3 scripts/validate_secrets.py \
            --repo-owner "$REPO_OWNER" \
            --repo-name "$REPO_NAME" \
            --output "validation_report.json"
    else
        log_warning "Validation script not found"
    fi
}

cleanup_config() {
    if [ -f "$CONFIG_FILE" ]; then
        log_warning "Configuration file contains sensitive data"
        read -p "Delete $CONFIG_FILE? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            rm "$CONFIG_FILE"
            log_success "Configuration file deleted"
        else
            log_warning "Keep $CONFIG_FILE secure"
        fi
    fi
}

main() {
    echo "🔐 QMS GitHub Secrets Quick Setup"
    echo "================================="
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -o|--owner)
                REPO_OWNER="$2"
                shift 2
                ;;
            -r|--repo)
                REPO_NAME="$2"
                shift 2
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -f|--file)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -i|--interactive)
                if [ -f "scripts/interactive_secrets_setup.py" ]; then
                    python3 scripts/interactive_secrets_setup.py
                    exit $?
                else
                    log_error "Interactive setup script not found"
                    exit 1
                fi
                ;;
            -v|--validate)
                validate_prerequisites
                validate_repository
                validate_secrets
                exit 0
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Validate prerequisites
    validate_prerequisites
    validate_repository
    
    # Create environments
    create_environments
    
    # Generate configuration if file doesn't exist
    if [ ! -f "$CONFIG_FILE" ]; then
        generate_quick_config
    fi
    
    # Apply secrets based on environment
    case $ENVIRONMENT in
        staging)
            apply_environment_secrets "staging" "$CONFIG_FILE"
            ;;
        production)
            apply_repository_secrets "$CONFIG_FILE"
            apply_environment_secrets "production" "$CONFIG_FILE"
            ;;
        both)
            apply_repository_secrets "$CONFIG_FILE"
            apply_environment_secrets "staging" "$CONFIG_FILE"
            apply_environment_secrets "production" "$CONFIG_FILE"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    # Validate configuration
    validate_secrets
    
    # Summary
    echo ""
    log_success "Secrets configuration completed!"
    log_info "Repository: $REPO_OWNER/$REPO_NAME"
    log_info "Environment: $ENVIRONMENT"
    
    echo ""
    echo "📋 Next Steps:"
    echo "1. Update any placeholder values in GitHub Secrets"
    echo "2. Test staging deployment: git push origin main"
    echo "3. Configure production reviewers"
    echo "4. Test production deployment: git tag v1.0.0 && git push origin v1.0.0"
    
    # Cleanup
    cleanup_config
}

# Run main function
main "$@"