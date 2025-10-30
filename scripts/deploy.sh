#!/bin/bash

# QMS Platform Deployment Script
# Supports multiple environments and deployment methods

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEPLOYMENT_DIR="${PROJECT_ROOT}/deployment"

# Default values
ENVIRONMENT="${ENVIRONMENT:-staging}"
DEPLOYMENT_METHOD="${DEPLOYMENT_METHOD:-docker-compose}"
VERSION="${VERSION:-latest}"
DRY_RUN="${DRY_RUN:-false}"
VERBOSE="${VERBOSE:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

verbose() {
    if [[ "${VERBOSE}" == "true" ]]; then
        echo -e "${BLUE}[DEBUG] $1${NC}"
    fi
}

# Help function
show_help() {
    cat << EOF
QMS Platform Deployment Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment ENV     Target environment (development|staging|production)
    -m, --method METHOD       Deployment method (docker-compose|kubernetes|podman)
    -v, --version VERSION     Version to deploy (default: latest)
    -d, --dry-run            Show what would be deployed without executing
    -V, --verbose            Enable verbose logging
    -h, --help               Show this help message

Examples:
    $0 -e staging -m docker-compose -v v1.0.0
    $0 --environment production --method kubernetes --version latest
    $0 --dry-run --environment staging

Environment Variables:
    ENVIRONMENT              Target environment
    DEPLOYMENT_METHOD        Deployment method
    VERSION                  Version to deploy
    DRY_RUN                  Enable dry-run mode
    VERBOSE                  Enable verbose logging

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -m|--method)
                DEPLOYMENT_METHOD="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -d|--dry-run)
                DRY_RUN="true"
                shift
                ;;
            -V|--verbose)
                VERBOSE="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
}

# Validation functions
validate_environment() {
    case "${ENVIRONMENT}" in
        development|staging|production)
            verbose "Environment '${ENVIRONMENT}' is valid"
            ;;
        *)
            error "Invalid environment: ${ENVIRONMENT}. Must be one of: development, staging, production"
            ;;
    esac
}

validate_deployment_method() {
    case "${DEPLOYMENT_METHOD}" in
        docker-compose|kubernetes|podman)
            verbose "Deployment method '${DEPLOYMENT_METHOD}' is valid"
            ;;
        *)
            error "Invalid deployment method: ${DEPLOYMENT_METHOD}. Must be one of: docker-compose, kubernetes, podman"
            ;;
    esac
}

validate_version() {
    if [[ ! "${VERSION}" =~ ^(latest|v[0-9]+\.[0-9]+\.[0-9]+.*)$ ]]; then
        error "Invalid version format: ${VERSION}. Must be 'latest' or 'vX.Y.Z'"
    fi
    verbose "Version '${VERSION}' is valid"
}

check_prerequisites() {
    log "Checking prerequisites for ${DEPLOYMENT_METHOD} deployment..."
    
    case "${DEPLOYMENT_METHOD}" in
        docker-compose)
            if ! command -v docker-compose &> /dev/null; then
                error "docker-compose is not installed or not in PATH"
            fi
            if ! docker info &> /dev/null; then
                error "Docker daemon is not running or not accessible"
            fi
            ;;
        kubernetes)
            if ! command -v kubectl &> /dev/null; then
                error "kubectl is not installed or not in PATH"
            fi
            if ! kubectl cluster-info &> /dev/null; then
                error "Kubernetes cluster is not accessible"
            fi
            ;;
        podman)
            if ! command -v podman &> /dev/null; then
                error "podman is not installed or not in PATH"
            fi
            if ! command -v podman-compose &> /dev/null; then
                error "podman-compose is not installed or not in PATH"
            fi
            ;;
    esac
    
    success "Prerequisites check passed"
}

# Deployment functions
deploy_docker_compose() {
    log "Deploying with Docker Compose to ${ENVIRONMENT}..."
    
    local compose_file
    case "${ENVIRONMENT}" in
        development)
            compose_file="${PROJECT_ROOT}/docker-compose.dev.yml"
            ;;
        staging|production)
            compose_file="${DEPLOYMENT_DIR}/docker-compose.prod.yml"
            ;;
    esac
    
    if [[ ! -f "${compose_file}" ]]; then
        error "Compose file not found: ${compose_file}"
    fi
    
    # Set environment variables
    export BACKEND_IMAGE_TAG="${VERSION}"
    export FRONTEND_IMAGE_TAG="${VERSION}"
    
    # Load environment-specific variables
    local env_file="${DEPLOYMENT_DIR}/.env.${ENVIRONMENT}"
    if [[ -f "${env_file}" ]]; then
        verbose "Loading environment file: ${env_file}"
        set -a
        source "${env_file}"
        set +a
    fi
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would execute docker-compose with:"
        verbose "Compose file: ${compose_file}"
        verbose "Backend image tag: ${BACKEND_IMAGE_TAG}"
        verbose "Frontend image tag: ${FRONTEND_IMAGE_TAG}"
        docker-compose -f "${compose_file}" config
    else
        # Pull latest images
        log "Pulling latest images..."
        docker-compose -f "${compose_file}" pull
        
        # Deploy
        log "Starting deployment..."
        docker-compose -f "${compose_file}" up -d
        
        # Wait for services to be healthy
        log "Waiting for services to be ready..."
        sleep 30
        
        # Health check
        perform_health_check
    fi
}

deploy_kubernetes() {
    log "Deploying with Kubernetes to ${ENVIRONMENT}..."
    
    local k8s_dir="${DEPLOYMENT_DIR}/kubernetes"
    if [[ ! -d "${k8s_dir}" ]]; then
        error "Kubernetes manifests directory not found: ${k8s_dir}"
    fi
    
    # Create namespace if it doesn't exist
    local namespace="qms-${ENVIRONMENT}"
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would create namespace: ${namespace}"
        log "DRY RUN: Would apply manifests from: ${k8s_dir}"
        kubectl apply --dry-run=client -f "${k8s_dir}/" || true
    else
        kubectl create namespace "${namespace}" --dry-run=client -o yaml | kubectl apply -f -
        
        # Update image tags in manifests
        log "Updating image tags to ${VERSION}..."
        find "${k8s_dir}" -name "*.yaml" -exec sed -i.bak "s/:latest/:${VERSION}/g" {} \;
        
        # Apply manifests
        log "Applying Kubernetes manifests..."
        kubectl apply -f "${k8s_dir}/" -n "${namespace}"
        
        # Wait for rollout
        log "Waiting for rollout to complete..."
        kubectl rollout status deployment/qms-backend -n "${namespace}" --timeout=300s
        kubectl rollout status deployment/qms-frontend -n "${namespace}" --timeout=300s
        
        # Restore original manifests
        find "${k8s_dir}" -name "*.yaml.bak" -exec bash -c 'mv "$1" "${1%.bak}"' _ {} \;
        
        # Health check
        perform_health_check_k8s "${namespace}"
    fi
}

deploy_podman() {
    log "Deploying with Podman to ${ENVIRONMENT}..."
    
    local compose_file
    case "${ENVIRONMENT}" in
        development)
            compose_file="${PROJECT_ROOT}/podman-compose.dev.yml"
            ;;
        staging|production)
            compose_file="${DEPLOYMENT_DIR}/podman-compose.prod.yml"
            ;;
    esac
    
    if [[ ! -f "${compose_file}" ]]; then
        error "Podman compose file not found: ${compose_file}"
    fi
    
    # Set environment variables
    export BACKEND_IMAGE_TAG="${VERSION}"
    export FRONTEND_IMAGE_TAG="${VERSION}"
    
    # Load environment-specific variables
    local env_file="${DEPLOYMENT_DIR}/.env.${ENVIRONMENT}"
    if [[ -f "${env_file}" ]]; then
        verbose "Loading environment file: ${env_file}"
        set -a
        source "${env_file}"
        set +a
    fi
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would execute podman-compose with:"
        verbose "Compose file: ${compose_file}"
        verbose "Backend image tag: ${BACKEND_IMAGE_TAG}"
        verbose "Frontend image tag: ${FRONTEND_IMAGE_TAG}"
    else
        # Pull latest images
        log "Pulling latest images..."
        podman-compose -f "${compose_file}" pull
        
        # Deploy
        log "Starting deployment..."
        podman-compose -f "${compose_file}" up -d
        
        # Wait for services to be healthy
        log "Waiting for services to be ready..."
        sleep 30
        
        # Health check
        perform_health_check
    fi
}

# Health check functions
perform_health_check() {
    log "Performing health checks..."
    
    local backend_url="http://localhost:8000"
    local frontend_url="http://localhost:3002"
    
    # Backend health check
    for i in {1..30}; do
        if curl -sf "${backend_url}/health" > /dev/null 2>&1; then
            success "Backend health check passed"
            break
        fi
        if [[ $i -eq 30 ]]; then
            error "Backend health check failed after 30 attempts"
        fi
        verbose "Backend health check attempt ${i}/30 failed, retrying..."
        sleep 10
    done
    
    # Frontend health check
    for i in {1..30}; do
        if curl -sf "${frontend_url}/" > /dev/null 2>&1; then
            success "Frontend health check passed"
            break
        fi
        if [[ $i -eq 30 ]]; then
            warning "Frontend health check failed after 30 attempts"
        fi
        verbose "Frontend health check attempt ${i}/30 failed, retrying..."
        sleep 10
    done
}

perform_health_check_k8s() {
    local namespace="$1"
    log "Performing Kubernetes health checks..."
    
    # Check pod status
    kubectl get pods -n "${namespace}" -l app=qms-backend
    kubectl get pods -n "${namespace}" -l app=qms-frontend
    
    # Port forward and check health
    local backend_port=$(kubectl get svc qms-backend-service -n "${namespace}" -o jsonpath='{.spec.ports[0].port}')
    kubectl port-forward -n "${namespace}" svc/qms-backend-service 8000:${backend_port} &
    local pf_pid=$!
    
    sleep 5
    
    if curl -sf "http://localhost:8000/health" > /dev/null 2>&1; then
        success "Kubernetes backend health check passed"
    else
        warning "Kubernetes backend health check failed"
    fi
    
    kill $pf_pid 2>/dev/null || true
}

# Rollback function
rollback() {
    log "Rolling back deployment..."
    
    case "${DEPLOYMENT_METHOD}" in
        docker-compose|podman)
            local compose_cmd
            if [[ "${DEPLOYMENT_METHOD}" == "docker-compose" ]]; then
                compose_cmd="docker-compose"
            else
                compose_cmd="podman-compose"
            fi
            
            local compose_file
            case "${ENVIRONMENT}" in
                development)
                    compose_file="${PROJECT_ROOT}/${DEPLOYMENT_METHOD}.dev.yml"
                    ;;
                staging|production)
                    compose_file="${DEPLOYMENT_DIR}/${DEPLOYMENT_METHOD}.prod.yml"
                    ;;
            esac
            
            ${compose_cmd} -f "${compose_file}" down
            success "Rollback completed"
            ;;
        kubernetes)
            local namespace="qms-${ENVIRONMENT}"
            kubectl rollout undo deployment/qms-backend -n "${namespace}"
            kubectl rollout undo deployment/qms-frontend -n "${namespace}"
            success "Kubernetes rollback completed"
            ;;
    esac
}

# Cleanup function
cleanup() {
    log "Cleaning up temporary files..."
    # Add cleanup logic here
    verbose "Cleanup completed"
}

# Main deployment function
main() {
    log "Starting QMS Platform deployment..."
    log "Environment: ${ENVIRONMENT}"
    log "Method: ${DEPLOYMENT_METHOD}"
    log "Version: ${VERSION}"
    log "Dry Run: ${DRY_RUN}"
    
    # Validate inputs
    validate_environment
    validate_deployment_method
    validate_version
    
    # Check prerequisites
    check_prerequisites
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Deploy based on method
    case "${DEPLOYMENT_METHOD}" in
        docker-compose)
            deploy_docker_compose
            ;;
        kubernetes)
            deploy_kubernetes
            ;;
        podman)
            deploy_podman
            ;;
    esac
    
    if [[ "${DRY_RUN}" == "false" ]]; then
        success "QMS Platform deployment completed successfully!"
        log "Environment: ${ENVIRONMENT}"
        log "Version: ${VERSION}"
        log "Method: ${DEPLOYMENT_METHOD}"
    else
        success "Dry run completed successfully!"
    fi
}

# Parse arguments and run main function
parse_args "$@"
main