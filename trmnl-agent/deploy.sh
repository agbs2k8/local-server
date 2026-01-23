#!/bin/bash

# TRMNL Agent Deployment Script
# Builds and pushes to Docker Hub, then deploys to remote k3s

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOCKER_HUB_USERNAME="${DOCKER_HUB_USERNAME:-}"
IMAGE_NAME="trmnl-agent"
IMAGE_TAG="${IMAGE_TAG:-latest}"
NAMESPACE="${NAMESPACE:-default}"
RELEASE_NAME="trmnl-agent"
ENV_FILE=".env"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check required variables
if [ -z "$DOCKER_HUB_USERNAME" ]; then
    print_error "DOCKER_HUB_USERNAME environment variable is required"
    print_warning "Set it like: DOCKER_HUB_USERNAME=yourusername ./deploy.sh"
    exit 1
fi

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    print_error ".env file not found! Please create one based on .env.example"
    exit 1
fi

print_status "Loading environment variables from $ENV_FILE..."

# Read environment variables from .env file
if [ -f "$ENV_FILE" ]; then
    export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
fi

# Check required environment variables
REQUIRED_VARS=("WEBHOOK_URL" "SOURCE_URL")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set in .env file"
        exit 1
    fi
done

# Build Docker Hub image name
DOCKER_HUB_IMAGE="$DOCKER_HUB_USERNAME/$IMAGE_NAME:$IMAGE_TAG"

print_status "Building Docker image: $IMAGE_NAME:$IMAGE_TAG"
docker build -t "$IMAGE_NAME:$IMAGE_TAG" .

print_status "Tagging for Docker Hub: $DOCKER_HUB_IMAGE"
docker tag "$IMAGE_NAME:$IMAGE_TAG" "$DOCKER_HUB_IMAGE"

print_status "Pushing to Docker Hub: $DOCKER_HUB_IMAGE"
if ! docker push "$DOCKER_HUB_IMAGE"; then
    print_error "Failed to push image to Docker Hub"
    print_warning "Make sure you're logged in: docker login"
    exit 1
fi

print_status "Deploying TRMNL Agent to remote k3s cluster..."

# Deploy using Helm with Docker Hub image
helm upgrade --install "$RELEASE_NAME" ./helm/trmnl-agent \
    --namespace "$NAMESPACE" \
    --set "image.repository=$DOCKER_HUB_USERNAME/$IMAGE_NAME" \
    --set "image.tag=$IMAGE_TAG" \
    --set "image.pullPolicy=Always" \
    --set "secrets.webhookUrl=$WEBHOOK_URL" \
    --set "config.sourceUrl=$SOURCE_URL" \
    --set "config.appName=${APP_NAME:-trmnl-agent}" \
    --set "config.logLevel=${LOG_LEVEL:-INFO}" \
    --set "config.enableHealthCheck=${ENABLE_HEALTH_CHECK:-false}" \
    --set "config.healthCheckPort=${HEALTH_CHECK_PORT:-8080}" \
    --wait

print_status "Deployment completed successfully!"

print_status "Checking CronJob status..."
kubectl get cronjob -n "$NAMESPACE" -l app.kubernetes.io/name=trmnl-agent

print_status "Recent job history:"
kubectl get jobs -n "$NAMESPACE" -l app.kubernetes.io/name=trmnl-agent --sort-by=.metadata.creationTimestamp | tail -5

print_warning "To manually trigger a job run:"
echo "kubectl create job --from=cronjob/trmnl-agent trmnl-agent-manual -n $NAMESPACE"

print_warning "To view logs:"
echo "kubectl logs -l app.kubernetes.io/name=trmnl-agent -n $NAMESPACE --tail=100"

print_status "Docker Hub image: $DOCKER_HUB_IMAGE"
print_status "Deployment script completed!"