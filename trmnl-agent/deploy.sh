#!/bin/bash

# TRMNL Agent Deployment Script
# Deploys the TRMNL Agent to k3s using Helm with environment variables from .env file

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="default"
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

print_status "Building Docker image..."
docker build -t trmnl-agent:latest .

print_status "Importing Docker image to k3s..."
docker save trmnl-agent:latest | k3s ctr images import -

print_status "Deploying TRMNL Agent to k3s..."

# Deploy using Helm with environment variables
helm upgrade --install "$RELEASE_NAME" ./helm/trmnl-agent \
    --namespace "$NAMESPACE" \
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

print_status "Deployment script completed!"