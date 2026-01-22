# Remote k3s Cluster Setup Guide

This guide helps you connect your local machine to a remote k3s cluster for deploying Pi-hole.

## Prerequisites

- k3s running on remote server (192.168.1.156)
- SSH access to the remote server
- kubectl and helm installed locally

## Step 1: Retrieve k3s Kubeconfig

### Option A: Copy kubeconfig via SSH with terminal allocation

```bash
# Method 1: Use ssh -t to allocate a pseudo-terminal (recommended)
ssh -t ajwilson@192.168.1.156 "sudo cat /etc/rancher/k3s/k3s.yaml" > ~/.kube/k3s-config

# Method 2: If the file is readable by your user (check first)
ssh ajwilson@192.168.1.156 "test -r /etc/rancher/k3s/k3s.yaml && cat /etc/rancher/k3s/k3s.yaml" > ~/.kube/k3s-config

# Method 3: Use sudo with password from stdin
echo 'your-sudo-password' | ssh ajwilson@192.168.1.156 "sudo -S cat /etc/rancher/k3s/k3s.yaml" > ~/.kube/k3s-config
```

### Option B: Interactive SSH session (most reliable)

```bash
# Create .kube directory if it doesn't exist
mkdir -p ~/.kube

# Method 1: Interactive session with terminal allocation
ssh -t ajwilson@192.168.1.156 "sudo cat /etc/rancher/k3s/k3s.yaml" | \
  sed "s/127.0.0.1/192.168.1.156/g" > ~/.kube/k3s-config

# Method 2: Two-step process (copy then modify)
ssh -t ajwilson@192.168.1.156 "sudo cat /etc/rancher/k3s/k3s.yaml" > ~/.kube/k3s-config-temp
sed "s/127.0.0.1/192.168.1.156/g" ~/.kube/k3s-config-temp > ~/.kube/k3s-config
rm ~/.kube/k3s-config-temp
```

### Option C: Alternative approaches

```bash
# Option C1: Check if user can read file directly (k3s sometimes allows group access)
ssh ajwilson@192.168.1.156 "ls -la /etc/rancher/k3s/k3s.yaml"
# If readable, use: ssh ajwilson@192.168.1.156 "cat /etc/rancher/k3s/k3s.yaml" > ~/.kube/k3s-config

# Option C2: Setup passwordless sudo for k3s file (run on remote server)
# ssh ajwilson@192.168.1.156
# echo "ajwilson ALL=(ALL) NOPASSWD: /bin/cat /etc/rancher/k3s/k3s.yaml" | sudo tee /etc/sudoers.d/k3s-config

# Option C3: Use scp after copying file to accessible location (run on remote server)
# ssh ajwilson@192.168.1.156
# sudo cp /etc/rancher/k3s/k3s.yaml ~/k3s.yaml && sudo chown ajwilson:ajwilson ~/k3s.yaml
# Then from local machine: scp ajwilson@192.168.1.156:~/k3s.yaml ~/.kube/k3s-config
```

## Step 2: Update Server Address

The k3s kubeconfig defaults to localhost (127.0.0.1), so you need to update it to use the remote IP:

```bash
# Edit the kubeconfig to replace localhost with remote IP
sed -i.bak 's/127.0.0.1/192.168.1.156/g' ~/.kube/k3s-config

# Or manually edit the file
# Change: server: https://127.0.0.1:6443
# To:     server: https://192.168.1.156:6443
```

## Step 3: Configure kubectl

### Option A: Set as default kubeconfig

```bash
# Backup existing kubeconfig (if any)
cp ~/.kube/config ~/.kube/config.backup 2>/dev/null || true

# Set k3s config as default
cp ~/.kube/k3s-config ~/.kube/config
```

### Option B: Use specific kubeconfig (recommended)

```bash
# Set environment variable for this session
export KUBECONFIG=~/.kube/k3s-config

# Or add to your shell profile (~/.bashrc, ~/.zshrc)
echo 'export KUBECONFIG=~/.kube/k3s-config' >> ~/.bashrc
```

### Option C: Use kubectl context switching

```bash
# Merge with existing kubeconfig
KUBECONFIG=~/.kube/config:~/.kube/k3s-config kubectl config view --flatten > ~/.kube/config.new
mv ~/.kube/config.new ~/.kube/config

# Set context name
kubectl config rename-context default k3s-remote

# Switch to k3s context
kubectl config use-context k3s-remote
```

## Step 4: Test Connection

```bash
# Test kubectl connection
kubectl get nodes

# Check cluster info
kubectl cluster-info

# Verify you can see k3s components
kubectl get pods -n kube-system
```

Expected output should show your k3s node and system pods.

## Step 5: Configure Helm

Helm uses the same kubeconfig as kubectl, so if kubectl works, Helm should work too:

```bash
# Test Helm connection
helm list --all-namespaces

# Check Helm version
helm version
```

## Step 6: Deploy Pi-hole

Now you can deploy Pi-hole to your remote cluster:

```bash
# Navigate to your docker-pi-hole directory
cd /Users/ajwilson/GitRepos/docker-pi-hole

# Create namespace
kubectl create namespace pihole

# Copy and edit environment file
cp .env.example .env
# Edit .env with your preferences (make sure values with semicolons are quoted)

# IMPORTANT: Configure systemd-resolved on k3s server first
# SSH to your k3s server and configure DNS properly
ssh ajwilson@192.168.1.156

# Configure systemd-resolved to avoid port 53 conflicts
sudo mkdir -p /etc/systemd/resolved.conf.d/
sudo tee /etc/systemd/resolved.conf.d/pihole.conf << EOF
[Resolve]
DNSStubListener=127.0.0.53
DNS=127.0.0.1
Domains=~.
EOF

sudo systemctl restart systemd-resolved
exit

# Method 1: Deploy using .env file (recommended - WORKING CONFIGURATION)
# Source the .env file and deploy with those values
set -a  # automatically export all variables
source .env
set +a  # turn off automatic export

# Deploy Pi-hole with correct configuration (single replica + hostPort + proper security)
helm install pihole ./helm/pihole \
  --namespace pihole \
  --set replicaCount=1 \
  --set service.dns.hostPort.enabled=true \
  --set env.TZ="$TZ" \
  --set env.FTLCONF_webserver_api_password="$FTLCONF_webserver_api_password" \
  --set env.FTLCONF_dns_listeningMode="$FTLCONF_dns_listeningMode" \
  --set env.FTLCONF_dns_upstreams="$FTLCONF_dns_upstreams" \
  --set env.FTLCONF_dns_dnssec="$FTLCONF_dns_dnssec" \
  --set env.FTLCONF_dns_queryLogging="$FTLCONF_dns_queryLogging" \
  --set env.FTLCONF_dns_privacyLevel="$FTLCONF_dns_privacyLevel" \
  --set env.PIHOLE_UID="$PIHOLE_UID" \
  --set env.PIHOLE_GID="$PIHOLE_GID"

# If deployment fails with capability/permission errors, delete StatefulSet and retry:
# kubectl delete statefulset pihole -n pihole
# Then run the helm install/upgrade command again

# Wait for pod to be running (may take a few minutes)
kubectl get pods -n pihole -w

# REQUIRED: Configure Pi-hole blocklists for ad blocking functionality
# Add popular blocklists to Pi-hole database
kubectl exec -n pihole pihole-0 -- sqlite3 /etc/pihole/gravity.db "INSERT INTO adlist (address, enabled, comment) VALUES ('https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts', 1, 'StevenBlack Unified hosts');"
kubectl exec -n pihole pihole-0 -- sqlite3 /etc/pihole/gravity.db "INSERT INTO adlist (address, enabled, comment) VALUES ('https://someonewhocares.org/hosts/zero/hosts', 1, 'Dan Pollock hosts');"
kubectl exec -n pihole pihole-0 -- sqlite3 /etc/pihole/gravity.db "INSERT INTO adlist (address, enabled, comment) VALUES ('https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/BaseFilter/sections/adservers.txt', 1, 'AdGuard Base Filter');"

# Update gravity to download and process blocklists
kubectl exec -n pihole pihole-0 -- pihole updateGravity

# Verify Pi-hole is working properly
# Test DNS resolution (should work on standard port 53 now)
dig @192.168.1.156 google.com          # Should resolve normally
dig @192.168.1.156 doubleclick.net     # Should return 0.0.0.0 (blocked)

# Check final deployment status
kubectl get pods -n pihole
kubectl get svc -n pihole

# Access web UI at: http://192.168.1.156:31075/admin
# (Use password from your .env file)

# Method 2: Create values file from .env (alternative)
# Create a custom values file from your .env
cat > custom-values.yaml << EOF
env:
  TZ: "$TZ"
  FTLCONF_webserver_api_password: "$FTLCONF_webserver_api_password"
  FTLCONF_dns_listeningMode: "$FTLCONF_dns_listeningMode"
  FTLCONF_dns_upstreams: "$FTLCONF_dns_upstreams"
  FTLCONF_dns_dnssec: "$FTLCONF_dns_dnssec"
  FTLCONF_dns_queryLogging: "$FTLCONF_dns_queryLogging"
  FTLCONF_dns_privacyLevel: "$FTLCONF_dns_privacyLevel"
  PIHOLE_UID: "$PIHOLE_UID"
  PIHOLE_GID: "$PIHOLE_GID"
EOF

# Deploy using the custom values file
helm install pihole ./helm/pihole --namespace pihole -f custom-values.yaml

# Check deployment status
kubectl get pods -n pihole
kubectl get svc -n pihole
```

## Troubleshooting

### Pi-hole Pod CrashLoopBackOff Issues

If pods fail with capability or permission errors:

```bash
# Check pod logs for specific errors
kubectl logs -n pihole pihole-0 --previous

# Common fixes:
# 1. Delete StatefulSet to force recreation with proper security context
kubectl delete statefulset pihole -n pihole

# 2. Upgrade with force flag
helm upgrade pihole ./helm/pihole --namespace pihole --force

# 3. Ensure single replica to avoid database conflicts
helm upgrade pihole ./helm/pihole --namespace pihole --set replicaCount=1
```

### Database Corruption Issues

If you see repeated gravity database errors:

```bash
# This usually happens with multiple replicas - scale to 1
kubectl scale statefulset pihole --replicas=1 -n pihole

# Reset gravity database
kubectl exec -n pihole pihole-0 -- pihole updateGravity

# Or reset database completely if needed
kubectl exec -n pihole pihole-0 -- rm -f /etc/pihole/gravity.db
kubectl delete pod pihole-0 -n pihole  # Forces restart and fresh DB
```

### DNS Port 53 Conflicts

If you get DNS resolution timeouts:

```bash
# Check what's using port 53 on your k3s server
ssh ajwilson@192.168.1.156 "sudo netstat -tulpn | grep :53"

# Configure systemd-resolved properly (see deployment steps above)
# The hostPort configuration should handle this automatically
```

### Service Conflicts During Helm Upgrades

```bash
# If you get service conflicts, delete the conflicting service
kubectl delete service pihole-dns -n pihole

# Then retry the helm upgrade
```

### Missing Blocklists

If Pi-hole isn't blocking ads:

```bash
# Check if any blocklists are configured
kubectl exec -n pihole pihole-0 -- sqlite3 /etc/pihole/gravity.db "SELECT address FROM adlist WHERE enabled = 1;"

# Add blocklists if missing (see deployment steps)
# Run gravity update after adding lists
kubectl exec -n pihole pihole-0 -- pihole updateGravity
```

### Certificate Issues

If you get certificate errors, you might need to use the `--insecure-skip-tls-verify` flag:

```bash
kubectl get nodes --insecure-skip-tls-verify
```

### Firewall Configuration

On your k3s server, ensure port 6443 is open:

```bash
# SSH to remote server
ssh ajwilson@192.168.1.156

# Check if firewall is blocking
sudo ufw allow 6443

# Or disable firewall temporarily for testing
sudo ufw disable
```

### Alternative: SSH Tunnel

If direct connection doesn't work, use SSH tunnel:

```bash
# Create SSH tunnel (run in separate terminal)
ssh -L 6443:localhost:6443 ajwilson@192.168.1.156

# Use localhost in kubeconfig
sed -i.bak 's/192.168.1.156/127.0.0.1/g' ~/.kube/k3s-config
```

## Security Notes

- Keep your kubeconfig file secure (`chmod 600 ~/.kube/k3s-config`)
- Consider using SSH keys instead of passwords
- Regularly rotate cluster certificates if needed
- Use network policies to secure your cluster

## Quick Reference Commands

```bash
# Switch kubectl context (if using multiple clusters)
kubectl config get-contexts
kubectl config use-context k3s-remote

# Use specific kubeconfig for single command
kubectl --kubeconfig ~/.kube/k3s-config get nodes

# Set kubeconfig for current shell session
export KUBECONFIG=~/.kube/k3s-config
```