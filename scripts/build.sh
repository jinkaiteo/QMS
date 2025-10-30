#!/bin/bash

# QMS Platform Build Script
# Builds both frontend and backend components with proper versioning

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Default values
VERSION="${VERSION:-$(git describe --tags --always --dirty)}"
BUILD_ENV="${BUILD_ENV:-production}"
REGISTRY="${REGISTRY:-ghcr.io}"
REPOSITORY="${REPOSITORY:-your-org/qms}"
PUSH_IMAGES="${PUSH_IMAGES:-false}"
PARALLEL_BUILD="${PARALLEL_BUILD:-true}"
VERBOSE="${VERBOSE:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
QMS Platform Build Script

Usage: $0 [OPTIONS]

Options:
    -v, --version VERSION     Build version (default: git describe)
    -e, --env ENV            Build environment (development|staging|production)
    -r, --registry REGISTRY  Container registry (default: ghcr.io)
    -p, --push               Push images to registry
    -s, --sequential         Build components sequentially instead of parallel
    -V, --verbose            Enable verbose logging
    -h, --help               Show this help message

Examples:
    $0 -v v1.0.0 -e production -p
    $0 --version latest --env development
    $0 --push --verbose

Environment Variables:
    VERSION                  Build version
    BUILD_ENV               Build environment
    REGISTRY                Container registry
    PUSH_IMAGES             Push images to registry
    PARALLEL_BUILD          Enable parallel building
    VERBOSE                 Enable verbose logging

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -e|--env)
                BUILD_ENV="$2"
                shift 2
                ;;
            -r|--registry)
                REGISTRY="$2"
                shift 2
                ;;
            -p|--push)
                PUSH_IMAGES="true"
                shift
                ;;
            -s|--sequential)
                PARALLEL_BUILD="false"
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
    case "${BUILD_ENV}" in
        development|staging|production)
            verbose "Build environment '${BUILD_ENV}' is valid"
            ;;
        *)
            error "Invalid build environment: ${BUILD_ENV}. Must be one of: development, staging, production"
            ;;
    esac
}

check_prerequisites() {
    log "Checking build prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running or not accessible"
    fi
    
    # Check Node.js for frontend
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed or not in PATH"
    fi
    
    # Check Python for backend
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed or not in PATH"
    fi
    
    # Check Git for versioning
    if ! command -v git &> /dev/null; then
        error "Git is not installed or not in PATH"
    fi
    
    success "Prerequisites check passed"
}

# Build functions
build_frontend() {
    log "Building frontend..."
    
    cd "${PROJECT_ROOT}/frontend"
    
    # Install dependencies
    log "Installing frontend dependencies..."
    npm ci
    
    # Run tests
    log "Running frontend tests..."
    npm run test:coverage
    
    # Lint code
    log "Linting frontend code..."
    npm run lint
    
    # Type checking
    log "Running TypeScript type checking..."
    npm run type-check
    
    # Build application
    log "Building frontend application..."
    case "${BUILD_ENV}" in
        development)
            npm run build:dev
            ;;
        staging)
            npm run build:staging
            ;;
        production)
            npm run build
            ;;
    esac
    
    # Build Docker image
    log "Building frontend Docker image..."
    local image_tag="${REGISTRY}/${REPOSITORY}/frontend:${VERSION}"
    
    docker build \
        --build-arg BUILD_ENV="${BUILD_ENV}" \
        --build-arg VERSION="${VERSION}" \
        --tag "${image_tag}" \
        --label "org.opencontainers.image.title=QMS Frontend" \
        --label "org.opencontainers.image.description=QMS Platform Frontend UI" \
        --label "org.opencontainers.image.version=${VERSION}" \
        --label "org.opencontainers.image.revision=$(git rev-parse HEAD)" \
        --label "org.opencontainers.image.created=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        .
    
    success "Frontend build completed: ${image_tag}"
    
    if [[ "${PUSH_IMAGES}" == "true" ]]; then
        log "Pushing frontend image to registry..."
        docker push "${image_tag}"
        success "Frontend image pushed successfully"
    fi
    
    cd "${PROJECT_ROOT}"
}

build_backend() {
    log "Building backend..."
    
    cd "${PROJECT_ROOT}/backend"
    
    # Create virtual environment and install dependencies
    log "Setting up Python environment..."
    python3 -m venv build_venv
    source build_venv/bin/activate
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Run tests
    log "Running backend tests..."
    python -m pytest tests/ -v --cov=app --cov-report=xml
    
    # Lint code
    log "Linting backend code..."
    black --check .
    isort --check-only .
    flake8 .
    
    # Type checking
    log "Running type checking..."
    mypy app --ignore-missing-imports
    
    # Security scan
    log "Running security scan..."
    bandit -r app -f json -o bandit-report.json || true
    safety check --json --output safety-report.json || true
    
    # Build Docker image
    log "Building backend Docker image..."
    local image_tag="${REGISTRY}/${REPOSITORY}/backend:${VERSION}"
    
    docker build \
        --build-arg BUILD_ENV="${BUILD_ENV}" \
        --build-arg VERSION="${VERSION}" \
        --tag "${image_tag}" \
        --label "org.opencontainers.image.title=QMS Backend" \
        --label "org.opencontainers.image.description=QMS Platform Backend API" \
        --label "org.opencontainers.image.version=${VERSION}" \
        --label "org.opencontainers.image.revision=$(git rev-parse HEAD)" \
        --label "org.opencontainers.image.created=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        .
    
    success "Backend build completed: ${image_tag}"
    
    if [[ "${PUSH_IMAGES}" == "true" ]]; then
        log "Pushing backend image to registry..."
        docker push "${image_tag}"
        success "Backend image pushed successfully"
    fi
    
    # Cleanup
    deactivate
    rm -rf build_venv
    
    cd "${PROJECT_ROOT}"
}

# Build orchestration
build_parallel() {
    log "Building components in parallel..."
    
    # Start background builds
    build_frontend &
    local frontend_pid=$!
    
    build_backend &
    local backend_pid=$!
    
    # Wait for builds to complete
    local failed=false
    
    if ! wait $frontend_pid; then
        error "Frontend build failed"
        failed=true
    fi
    
    if ! wait $backend_pid; then
        error "Backend build failed"
        failed=true
    fi
    
    if [[ "$failed" == "true" ]]; then
        error "One or more builds failed"
    fi
}

build_sequential() {
    log "Building components sequentially..."
    
    build_frontend
    build_backend
}

# Image scanning
scan_images() {
    log "Scanning built images for vulnerabilities..."
    
    local frontend_image="${REGISTRY}/${REPOSITORY}/frontend:${VERSION}"
    local backend_image="${REGISTRY}/${REPOSITORY}/backend:${VERSION}"
    
    # Install Trivy if not available
    if ! command -v trivy &> /dev/null; then
        log "Installing Trivy scanner..."
        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
    fi
    
    # Scan frontend image
    log "Scanning frontend image..."
    trivy image --format json --output frontend-scan.json "${frontend_image}" || true
    
    # Scan backend image
    log "Scanning backend image..."
    trivy image --format json --output backend-scan.json "${backend_image}" || true
    
    success "Image scanning completed"
}

# Generate build report
generate_build_report() {
    log "Generating build report..."
    
    local report_file="build-report-${VERSION}.json"
    
    cat > "${report_file}" << EOF
{
  "build_info": {
    "version": "${VERSION}",
    "environment": "${BUILD_ENV}",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "git_commit": "$(git rev-parse HEAD)",
    "git_branch": "$(git rev-parse --abbrev-ref HEAD)",
    "builder": "$(whoami)@$(hostname)"
  },
  "images": {
    "frontend": "${REGISTRY}/${REPOSITORY}/frontend:${VERSION}",
    "backend": "${REGISTRY}/${REPOSITORY}/backend:${VERSION}"
  },
  "pushed_to_registry": ${PUSH_IMAGES}
}
EOF
    
    success "Build report generated: ${report_file}"
}

# Cleanup function
cleanup() {
    log "Cleaning up build artifacts..."
    
    # Remove temporary files
    find "${PROJECT_ROOT}" -name "*.pyc" -delete 2>/dev/null || true
    find "${PROJECT_ROOT}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Clean up Docker build cache (optional)
    if [[ "${BUILD_ENV}" != "development" ]]; then
        docker builder prune -f >/dev/null 2>&1 || true
    fi
    
    verbose "Cleanup completed"
}

# Main build function
main() {
    log "Starting QMS Platform build..."
    log "Version: ${VERSION}"
    log "Environment: ${BUILD_ENV}"
    log "Registry: ${REGISTRY}"
    log "Push images: ${PUSH_IMAGES}"
    log "Parallel build: ${PARALLEL_BUILD}"
    
    # Validate inputs
    validate_environment
    
    # Check prerequisites
    check_prerequisites
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Login to registry if pushing
    if [[ "${PUSH_IMAGES}" == "true" ]]; then
        log "Logging in to container registry..."
        if [[ -n "${GITHUB_TOKEN:-}" ]]; then
            echo "${GITHUB_TOKEN}" | docker login "${REGISTRY}" -u "${GITHUB_ACTOR:-$(whoami)}" --password-stdin
        elif [[ -n "${REGISTRY_PASSWORD:-}" ]]; then
            echo "${REGISTRY_PASSWORD}" | docker login "${REGISTRY}" -u "${REGISTRY_USERNAME}" --password-stdin
        else
            warning "No registry credentials provided, assuming already logged in"
        fi
    fi
    
    # Build components
    if [[ "${PARALLEL_BUILD}" == "true" ]]; then
        build_parallel
    else
        build_sequential
    fi
    
    # Scan images for vulnerabilities
    scan_images
    
    # Generate build report
    generate_build_report
    
    success "QMS Platform build completed successfully!"
    log "Frontend image: ${REGISTRY}/${REPOSITORY}/frontend:${VERSION}"
    log "Backend image: ${REGISTRY}/${REPOSITORY}/backend:${VERSION}"
    
    if [[ "${PUSH_IMAGES}" == "true" ]]; then
        success "Images pushed to registry: ${REGISTRY}"
    fi
}

# Parse arguments and run main function
parse_args "$@"
main