#!/usr/bin/env bash

set -Eeuo pipefail

# prevent Git Bash from converting paths for Docker/K3s
export MSYS_NO_PATHCONV=1

# Always operate relative to the project root, regardless of
# which directory the script was launched from.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

# ============================================================
# OpenHamClock - local Docker -> K3s deployment
#
# Windows / Git Bash -> K3s
#
# Builds:
#   openhamclock:local
#
# Target:
#   linux/amd64
#
# Uses the CURRENT kubectl kubecontext.
#
# ============================================================

APP_NAME="openhamclock"
NAMESPACE="openhamclock"
IMPORT_NAMESPACE="openhamclock-system"

IMAGE_REPOSITORY="openhamclock"
IMAGE_TAG="local"
IMAGE="${IMAGE_REPOSITORY}:${IMAGE_TAG}"

CHART_DIR="./deploy/helm/openhamclock"

ENV_FILE="./.env"
SECRET_NAME="openhamclock-env"

IMAGE_TAR_NAME="openhamclock-local.tar"
IMAGE_TAR="./${IMAGE_TAR_NAME}"

HELM_TIMEOUT="10m"

PREFERRED_PORTS=(
  30081
  30082
  30083
  30084
  30085
  30086
  30087
  30088
  30089
  30090
)

# ============================================================
# Colors / logging
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
  echo -e "${BLUE}==>${NC} $*"
}

success() {
  echo -e "${GREEN}==>${NC} $*"
}

warn() {
  echo -e "${YELLOW}WARNING:${NC} $*"
}

error() {
  echo -e "${RED}ERROR:${NC} $*" >&2
}

die() {
  error "$*"
  exit 1
}

# ============================================================
# Diagnostics
# ============================================================

print_diagnostics() {
  echo
  echo "============================================================"
  echo "DEPLOYMENT FAILED"
  echo "============================================================"
  echo

  echo "Kubecontext:"
  kubectl config current-context 2>/dev/null || true
  echo

  echo "Nodes:"
  kubectl get nodes -o wide 2>/dev/null || true
  echo

  echo "Application pods:"
  kubectl get pods -n "${NAMESPACE}" -o wide 2>/dev/null || true
  echo

  echo "Application events:"
  kubectl get events \
    -n "${NAMESPACE}" \
    --sort-by=.lastTimestamp \
    2>/dev/null || true
  echo

  echo "Helm status:"
  helm status "${APP_NAME}" -n "${NAMESPACE}" 2>/dev/null || true
  echo

  echo "Importer pods:"
  kubectl get pods \
    -n "${IMPORT_NAMESPACE}" \
    -o wide \
    2>/dev/null || true
  echo

  echo "Importer events:"
  kubectl get events \
    -n "${IMPORT_NAMESPACE}" \
    --sort-by=.lastTimestamp \
    2>/dev/null || true
  echo

  echo "============================================================"
}

on_error() {
  local exit_code=$?

  if [[ "${exit_code}" -ne 0 ]]; then
    print_diagnostics
  fi

  exit "${exit_code}"
}

trap on_error ERR

# ============================================================
# Validate tools
# ============================================================

log "Checking required tools..."

command -v docker >/dev/null 2>&1 \
  || die "Docker is not installed or not in PATH."

command -v kubectl >/dev/null 2>&1 \
  || die "kubectl is not installed or not in PATH."

command -v helm >/dev/null 2>&1 \
  || die "Helm is not installed or not in PATH."

command -v sha256sum >/dev/null 2>&1 \
  || die "sha256sum is required but was not found."

success "Required tools found."

# ============================================================
# Validate files
# ============================================================

log "Checking project files..."

[[ -f "${ENV_FILE}" ]] \
  || die "Missing ${ENV_FILE}"

[[ -d "${CHART_DIR}" ]] \
  || die "Missing Helm chart directory: ${CHART_DIR}"

[[ -f "${CHART_DIR}/Chart.yaml" ]] \
  || die "Missing ${CHART_DIR}/Chart.yaml"

[[ -f "${CHART_DIR}/values.yaml" ]] \
  || die "Missing ${CHART_DIR}/values.yaml"

[[ -f "${CHART_DIR}/templates/deployment.yaml" ]] \
  || die "Missing ${CHART_DIR}/templates/deployment.yaml"

success "Project files found."

# ============================================================
# Kubernetes context
# ============================================================

CURRENT_CONTEXT="$(kubectl config current-context)"

[[ -n "${CURRENT_CONTEXT}" ]] \
  || die "No current kubectl context is configured."

log "Using kubecontext:"
echo "  ${CURRENT_CONTEXT}"

log "Testing Kubernetes connection..."

kubectl cluster-info >/dev/null

success "Kubernetes connection OK."

echo
kubectl get nodes -o wide
echo

# ============================================================
# Docker
# ============================================================

log "Checking Docker..."

docker info >/dev/null

success "Docker is running."

# ============================================================
# Helm lint
# ============================================================

log "Running Helm lint..."

helm lint "${CHART_DIR}"

success "Helm chart is valid."

# ============================================================
# Build
# ============================================================

echo
log "Building ${IMAGE} for linux/amd64..."
echo

docker build \
  --platform linux/amd64 \
  --tag "${IMAGE}" \
  .

echo
success "Docker image built successfully."

# ============================================================
# Export image
# ============================================================

log "Saving ${IMAGE} to ${IMAGE_TAR}..."

rm -f "${IMAGE_TAR}"

docker save \
  --output "${IMAGE_TAR}" \
  "${IMAGE}"

[[ -s "${IMAGE_TAR}" ]] \
  || die "Docker image archive was not created."

IMAGE_SIZE="$(du -h "${IMAGE_TAR}" | cut -f1)"

success "Image archive created: ${IMAGE_SIZE}"

# ============================================================
# Create importer namespace
# ============================================================

echo
log "Preparing temporary K3s image importer..."

kubectl create namespace "${IMPORT_NAMESPACE}" \
  --dry-run=client \
  -o yaml |
  kubectl apply -f -

# ============================================================
# Importer DaemonSet
# ============================================================

log "Creating/updating image importer DaemonSet..."

kubectl apply -n "${IMPORT_NAMESPACE}" -f - <<'EOF'
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: openhamclock-image-importer
  labels:
    app.kubernetes.io/name: openhamclock-image-importer
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: openhamclock-image-importer
  template:
    metadata:
      labels:
        app.kubernetes.io/name: openhamclock-image-importer
    spec:
      containers:
        - name: importer
          image: alpine:3.22
          imagePullPolicy: IfNotPresent
          command:
            - /bin/sh
            - -c
            - |
              echo "OpenHamClock image importer ready"
              while true; do
                sleep 3600
              done
          volumeMounts:
            - name: k3s-images
              mountPath: /host-images
      volumes:
        - name: k3s-images
          hostPath:
            path: /var/lib/rancher/k3s/agent/images
            type: DirectoryOrCreate
EOF

success "Importer DaemonSet applied."

# ============================================================
# Wait for importer
# ============================================================

log "Waiting for importer DaemonSet to become ready..."

kubectl rollout status \
  daemonset/openhamclock-image-importer \
  -n "${IMPORT_NAMESPACE}" \
  --timeout=120s

success "Importer DaemonSet is ready."

echo
kubectl get pods \
  -n "${IMPORT_NAMESPACE}" \
  -o wide
echo

# ============================================================
# Get importer pods
# ============================================================

log "Discovering importer pods..."

mapfile -t IMPORTER_PODS < <(
  kubectl get pods \
    -n "${IMPORT_NAMESPACE}" \
    -l app.kubernetes.io/name=openhamclock-image-importer \
    -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}'
)

[[ "${#IMPORTER_PODS[@]}" -gt 0 ]] \
  || die "No importer pods were found."

echo
log "Importer pods found:"

for POD in "${IMPORTER_PODS[@]}"; do
  NODE="$(
    kubectl get pod "${POD}" \
      -n "${IMPORT_NAMESPACE}" \
      -o jsonpath='{.spec.nodeName}'
  )"

  echo "  ${POD} -> ${NODE}"
done

# ============================================================
# Remove previous archive
# ============================================================

echo
log "Removing any previous ${IMAGE_TAR_NAME} from K3s nodes..."

for POD in "${IMPORTER_PODS[@]}"; do

  NODE="$(
    kubectl get pod "${POD}" \
      -n "${IMPORT_NAMESPACE}" \
      -o jsonpath='{.spec.nodeName}'
  )"

  echo "  Cleaning ${NODE}..."

  kubectl exec \
    -n "${IMPORT_NAMESPACE}" \
    "${POD}" \
    -- sh -c "rm -f '/host-images/${IMAGE_TAR_NAME}'"

done

success "Old image archives removed."

# ============================================================
# Copy image archive
# ============================================================

echo
log "Copying Docker image archive to K3s nodes..."
echo

for POD in "${IMPORTER_PODS[@]}"; do

  NODE="$(
    kubectl get pod "${POD}" \
      -n "${IMPORT_NAMESPACE}" \
      -o jsonpath='{.spec.nodeName}'
  )"

  echo
  echo "------------------------------------------------------------"
  log "Node: ${NODE}"
  log "Pod:  ${POD}"
  echo "------------------------------------------------------------"

  log "Starting kubectl cp..."

  MSYS_NO_PATHCONV=1 kubectl cp \
    "${IMAGE_TAR}" \
    "${IMPORT_NAMESPACE}/${POD}:/host-images/${IMAGE_TAR_NAME}" \
    -c importer

  success "kubectl cp completed for ${NODE}."

  log "Checking copied archive size..."

  LOCAL_SIZE="$(wc -c < "${IMAGE_TAR}" | tr -d ' ')"

  REMOTE_SIZE="$(
    kubectl exec \
      -n "${IMPORT_NAMESPACE}" \
      "${POD}" \
      -c importer \
      -- sh -c "stat -c '%s' '/host-images/${IMAGE_TAR_NAME}'"
  )"

  echo "  Local size:  ${LOCAL_SIZE}"
  echo "  Remote size: ${REMOTE_SIZE}"

  [[ "${LOCAL_SIZE}" == "${REMOTE_SIZE}" ]] \
    || die "Image archive size mismatch on ${NODE}."

  success "Image archive verified on ${NODE}."

done

# ============================================================
# Give K3s time to import
# ============================================================

echo
log "Image archive is now on all K3s nodes."
log "Waiting for K3s/containerd to import it..."

for SECOND in {1..20}; do
  printf "\r  Waiting... %2d/20 seconds" "${SECOND}"
  sleep 1
done

echo
success "Import wait complete."

# ============================================================
# Show archive status
# ============================================================

echo
log "Confirming image archive remains on the K3s node(s)..."

for POD in "${IMPORTER_PODS[@]}"; do

  NODE="$(
    kubectl get pod "${POD}" \
      -n "${IMPORT_NAMESPACE}" \
      -o jsonpath='{.spec.nodeName}'
  )"

  echo
  echo "Node: ${NODE}"

  kubectl exec \
    -n "${IMPORT_NAMESPACE}" \
    "${POD}" \
    -c importer \
    -- sh -c "ls -lh '/host-images/${IMAGE_TAR_NAME}'"

done

# ============================================================
# Remove temporary importer
# ============================================================

echo
log "Removing temporary image importer..."

kubectl delete namespace "${IMPORT_NAMESPACE}" \
  --ignore-not-found=true \
  --wait=true

success "Temporary importer removed."

# ============================================================
# Application namespace
# ============================================================

echo
log "Preparing application namespace..."

kubectl create namespace "${NAMESPACE}" \
  --dry-run=client \
  -o yaml |
  kubectl apply -f -

success "Application namespace ready."

# ============================================================
# Kubernetes Secret
# ============================================================

log "Creating/updating environment Secret from ${ENV_FILE}..."

kubectl create secret generic "${SECRET_NAME}" \
  --namespace "${NAMESPACE}" \
  --from-env-file="${ENV_FILE}" \
  --dry-run=client \
  -o yaml |
  kubectl apply -f -

success "Environment Secret updated."

# ============================================================
# .env checksum
# ============================================================

ENV_CHECKSUM="$(sha256sum "${ENV_FILE}" | awk '{print $1}')"

log "Environment checksum:"
echo "  ${ENV_CHECKSUM}"

# ============================================================
# Helm deployment
# ============================================================

echo
log "Installing/upgrading OpenHamClock with Helm..."
echo

helm upgrade --install \
  "${APP_NAME}" \
  "${CHART_DIR}" \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --set-string "image.repository=${IMAGE_REPOSITORY}" \
  --set-string "image.tag=${IMAGE_TAG}" \
  --set-string "envSecret.name=${SECRET_NAME}" \
  --set-string "envSecret.checksum=${ENV_CHECKSUM}" \
  --atomic \
  --wait \
  --timeout "${HELM_TIMEOUT}"

success "Helm deployment completed."

# ============================================================
# Kubernetes status
# ============================================================

echo
log "Deployment:"

kubectl get deployment \
  -n "${NAMESPACE}" \
  -o wide

echo
log "Pods:"

kubectl get pods \
  -n "${NAMESPACE}" \
  -o wide

echo
log "Service:"

kubectl get service \
  -n "${NAMESPACE}" \
  -o wide

# ============================================================
# Find available local TCP port
# ============================================================

is_port_in_use() {
  local port="$1"

  if command -v netstat >/dev/null 2>&1; then

    if netstat -ano 2>/dev/null |
      grep -Eiq "[.:]${port}[[:space:]].*LISTENING|[.:]${port}[[:space:]].*LISTEN"; then
      return 0
    fi

  fi

  return 1
}

LOCAL_PORT=""

for PORT in "${PREFERRED_PORTS[@]}"; do

  if ! is_port_in_use "${PORT}"; then
    LOCAL_PORT="${PORT}"
    break
  fi

done

[[ -n "${LOCAL_PORT}" ]] \
  || die "Could not find an available local TCP port."

# ============================================================
# Port-forward
# ============================================================

PORT_FORWARD_LOG="./openhamclock-port-forward.log"

rm -f "${PORT_FORWARD_LOG}"

echo
log "Starting OpenHamClock port-forward..."
echo "  localhost:${LOCAL_PORT} -> service:3000"

nohup kubectl port-forward \
  --namespace "${NAMESPACE}" \
  "service/${APP_NAME}-openhamclock" \
  "${LOCAL_PORT}:3000" \
  >"${PORT_FORWARD_LOG}" 2>&1 < /dev/null &

PORT_FORWARD_PID=$!

disown "${PORT_FORWARD_PID}" 2>/dev/null || true

# ============================================================
# Wait for port-forward
# ============================================================

log "Waiting for port-forward..."

PORT_FORWARD_READY="false"

for SECOND in {1..30}; do

  if ! kill -0 "${PORT_FORWARD_PID}" 2>/dev/null; then
    break
  fi

  if grep -q "Forwarding from" "${PORT_FORWARD_LOG}" 2>/dev/null; then
    PORT_FORWARD_READY="true"
    break
  fi

  printf "\r  Waiting... %2d/30 seconds" "${SECOND}"
  sleep 1

done

echo

# ============================================================
# Final result
# ============================================================

echo
echo "============================================================"
echo "OPENHAMCLOCK DEPLOYMENT"
echo "============================================================"
echo

echo "Kubecontext:"
echo "  ${CURRENT_CONTEXT}"
echo

echo "Image:"
echo "  ${IMAGE}"
echo

echo "Namespace:"
echo "  ${NAMESPACE}"
echo

if [[ "${PORT_FORWARD_READY}" == "true" ]]; then

  success "OpenHamClock is available at:"
  echo
  echo "  http://localhost:${LOCAL_PORT}"
  echo
  echo "Port-forward PID:"
  echo "  ${PORT_FORWARD_PID}"

else

  warn "Port-forward did not become ready."

  echo
  echo "Port-forward log:"
  cat "${PORT_FORWARD_LOG}" 2>/dev/null || true

fi

echo
echo "Port-forward log:"
echo "  ${PORT_FORWARD_LOG}"

echo
echo "Pods:"
kubectl get pods \
  -n "${NAMESPACE}" \
  -o wide

echo
echo "============================================================"

warn "kubectl port-forward handles TCP only."
echo "WSJT-X/JTDX UDP/2237 and N1MM/DXLog UDP/12060 are"
echo "not exposed to the Windows host by this port-forward."

echo

# ============================================================
# Remove local image archive
# ============================================================

rm -f "${IMAGE_TAR}"

success "Local image archive removed."

echo
echo "Deployment complete."
