#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHART_DIR="$SCRIPT_DIR/helm"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env}"
RELEASE_NAME="${RELEASE_NAME:-monitor-agent}"
NAMESPACE="${NAMESPACE:-monitor-agent}"
IMAGE_PULL_POLICY="${IMAGE_PULL_POLICY:-IfNotPresent}"
IMPORT_HELPER_IMAGE="${IMPORT_HELPER_IMAGE:-busybox:1.36.1}"
TARGET_PLATFORM="${TARGET_PLATFORM:-linux/amd64}"
TEMP_FILES=()

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

cleanup() {
    if [ "${#TEMP_FILES[@]}" -eq 0 ]; then
        return
    fi

    rm -f "${TEMP_FILES[@]}"
}

trap cleanup EXIT

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        print_error "Required command not found: $1"
        exit 1
    fi
}

load_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        print_error ".env file not found at $ENV_FILE"
        exit 1
    fi

    print_status "Loading environment variables from $ENV_FILE"
    eval "$(
        python3 - "$ENV_FILE" <<'PY'
import shlex
import sys
from pathlib import Path

env_path = Path(sys.argv[1])

for raw_line in env_path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue
    if line.startswith("export "):
        line = line[7:].strip()

    if "=" not in line:
        raise SystemExit(f"Invalid .env line: {raw_line}")

    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()

    if value and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]

    print(f"export {key}={shlex.quote(value)}")
PY
    )"
}

require_env() {
    local variable_name="$1"

    if [ -z "${!variable_name:-}" ]; then
        print_error "Required environment variable $variable_name is not set"
        exit 1
    fi
}

determine_image_tag() {
    python3 - "$SCRIPT_DIR/pyproject.toml" <<'PY'
import sys
import tomllib
from pathlib import Path

with Path(sys.argv[1]).open("rb") as pyproject_file:
    print(tomllib.load(pyproject_file)["project"]["version"])
PY
}

ensure_namespace_exists() {
    if ! kubectl --context "$KUBE_CONTEXT" get namespace "$NAMESPACE" >/dev/null 2>&1; then
        print_status "Creating namespace $NAMESPACE"
        kubectl --context "$KUBE_CONTEXT" create namespace "$NAMESPACE" >/dev/null
    fi
}

build_image() {
    print_status "Building image $LOCAL_IMAGE for $TARGET_PLATFORM"
    docker buildx build --platform "$TARGET_PLATFORM" --load -t "$LOCAL_IMAGE" "$SCRIPT_DIR"
}

import_image_to_cluster() {
    local archive_file
    local import_id
    local node_name
    local node_names
    local pod_name
    local ready_timeout
    local remote_archive
    local sanitized_node

    archive_file="$(mktemp "${TMPDIR:-/tmp}/monitor-agent-image.XXXXXX.tar")"
    TEMP_FILES+=("$archive_file")
    import_id="$(date +%s)"
    ready_timeout="120s"

    print_status "Saving image archive for k3s import"
    docker save "$LOCAL_IMAGE" -o "$archive_file"

    node_names="$(kubectl --context "$KUBE_CONTEXT" get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')"

    if [ -z "$node_names" ]; then
        print_error "No Kubernetes nodes were returned for context $KUBE_CONTEXT"
        exit 1
    fi

    while IFS= read -r node_name; do
        if [ -z "$node_name" ]; then
            continue
        fi

        sanitized_node="$(printf '%s' "$node_name" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//; s/-$//')"
        pod_name="$(printf 'monitor-agent-import-%s-%s' "$sanitized_node" "$import_id" | cut -c1-63 | sed 's/-$//')"
        remote_archive="monitor-agent-${IMAGE_TAG}.tar"

        print_status "Importing $LOCAL_IMAGE onto node $node_name"
        kubectl --context "$KUBE_CONTEXT" apply -n "$NAMESPACE" -f - >/dev/null <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: ${pod_name}
spec:
  restartPolicy: Never
  nodeName: ${node_name}
  tolerations:
    - operator: Exists
  containers:
    - name: importer
      image: ${IMPORT_HELPER_IMAGE}
      command: ["/bin/sh", "-c", "sleep 3600"]
      securityContext:
        privileged: true
      volumeMounts:
        - name: host-root
          mountPath: /host
  volumes:
    - name: host-root
      hostPath:
        path: /
        type: Directory
EOF

        kubectl --context "$KUBE_CONTEXT" wait --for=condition=Ready "pod/${pod_name}" -n "$NAMESPACE" --timeout="$ready_timeout" >/dev/null
        kubectl --context "$KUBE_CONTEXT" cp "$archive_file" "${NAMESPACE}/${pod_name}:/host/tmp/${remote_archive}" >/dev/null
        kubectl --context "$KUBE_CONTEXT" exec -n "$NAMESPACE" "$pod_name" -- /bin/sh -lc "chroot /host /bin/sh -lc 'if command -v k3s >/dev/null 2>&1; then k3s ctr images import /tmp/${remote_archive}; elif command -v ctr >/dev/null 2>&1; then ctr -n k8s.io images import /tmp/${remote_archive}; else exit 1; fi'"
        kubectl --context "$KUBE_CONTEXT" exec -n "$NAMESPACE" "$pod_name" -- /bin/sh -lc "chroot /host /bin/sh -lc 'rm -f /tmp/${remote_archive}'" >/dev/null
        kubectl --context "$KUBE_CONTEXT" delete pod "$pod_name" -n "$NAMESPACE" --wait=true >/dev/null
    done <<EOF
$node_names
EOF
}

create_values_file() {
    local values_file

    values_file="$(mktemp "${TMPDIR:-/tmp}/monitor-agent-values.XXXXXX.json")"
    TEMP_FILES+=("$values_file")

    python3 - "$values_file" <<'PY'
import json
import os
import sys

values = {
    "image": {
        "repository": os.environ["IMAGE_REPOSITORY"],
        "tag": os.environ["IMAGE_TAG"],
        "pullPolicy": os.environ["IMAGE_PULL_POLICY"],
    },
    "config": {
        "APP_NAME": os.environ["APP_NAME"],
        "LOG_LEVEL": os.environ["LOG_LEVEL"],
        "LOG_JSON": os.environ.get("LOG_JSON", "false"),
        "DEFAULT_POD_LOG_LINES": os.environ.get("DEFAULT_POD_LOG_LINES", "50"),
    },
}

with open(sys.argv[1], "w", encoding="utf-8") as values_file:
    json.dump(values, values_file, indent=2)
PY

    GENERATED_VALUES_FILE="$values_file"
}

deploy_release() {
    print_status "Deploying Helm release $RELEASE_NAME in namespace $NAMESPACE"
    helm --kube-context "$KUBE_CONTEXT" upgrade --install "$RELEASE_NAME" "$CHART_DIR" \
        --namespace "$NAMESPACE" \
        --create-namespace \
        --values "$GENERATED_VALUES_FILE" \
        --wait \
        --atomic
}

verify_deployment() {
    print_status "Deployment status for $RELEASE_NAME"
    kubectl --context "$KUBE_CONTEXT" get deployment -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME"
    kubectl --context "$KUBE_CONTEXT" get service -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME"
}

main() {
    require_command docker
    require_command helm
    require_command kubectl
    require_command python3

    load_env_file

    require_env APP_NAME
    require_env LOG_LEVEL
    require_env KUBE_CONTEXT

    IMAGE_REPOSITORY="${IMAGE_REPOSITORY:-$RELEASE_NAME}"
    IMAGE_TAG="${IMAGE_TAG:-$(determine_image_tag)}"
    LOCAL_IMAGE="${IMAGE_REPOSITORY}:${IMAGE_TAG}"
    export IMAGE_REPOSITORY IMAGE_TAG LOCAL_IMAGE IMAGE_PULL_POLICY TARGET_PLATFORM

    ensure_namespace_exists
    build_image
    import_image_to_cluster
    create_values_file
    deploy_release
    verify_deployment

    print_status "Deployment completed successfully"
}

cd "$SCRIPT_DIR"
main "$@"