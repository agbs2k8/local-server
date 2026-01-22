# Pi-hole Kubernetes Deployment Guide

This guide will help you deploy Pi-hole in your k3s cluster with DNS Load Balancing using Helm.

## Prerequisites

- k3s cluster running
- Helm 3.x installed
- kubectl configured to access your cluster

## Quick Start

### 1. Clone and Prepare

```bash
# Clone the repository (if not already done)
git clone https://github.com/pi-hole/docker-pi-hole.git
cd docker-pi-hole

# Copy and customize the environment file
cp .env.example .env
# Edit .env with your preferred values
```

### 2. Customize Environment Variables

Edit the `.env` file with your specific values:

```bash
# Example .env customizations
TZ=America/New_York                           # Your timezone
FTLCONF_webserver_api_password=MySecurePass   # Your admin password
FTLCONF_dns_upstreams=1.1.1.1;1.0.0.1       # Cloudflare DNS
```

### 3. Deploy with Helm

```bash
# Create namespace (optional)
kubectl create namespace pihole

# Deploy Pi-hole
helm install pihole ./helm/pihole \
  --namespace pihole \
  --set env.TZ="$(grep TZ .env | cut -d'=' -f2)" \
  --set env.FTLCONF_webserver_api_password="$(grep FTLCONF_webserver_api_password .env | cut -d'=' -f2)" \
  --set env.FTLCONF_dns_upstreams="$(grep FTLCONF_dns_upstreams .env | cut -d'=' -f2)"

# Or using values file approach
helm install pihole ./helm/pihole -f custom-values.yaml --namespace pihole
```

### 4. Configure CoreDNS for Load Balancing

This is the key step for DNS Load Balancing. You'll configure k3s's CoreDNS to use your Pi-hole instances as upstream resolvers.

```bash
# Edit CoreDNS configuration
kubectl edit configmap coredns -n kube-system
```

Replace the content with:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health {
           lameduck 5s
        }
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
           pods insecure
           fallthrough in-addr.arpa ip6.arpa
           ttl 30
        }
        prometheus :9153
        # Forward external DNS to Pi-hole with load balancing
        forward . pihole-dns.pihole.svc.cluster.local {
           policy round_robin
           health_check 5s
        }
        cache 30
        loop
        reload
        loadbalance
    }
```

### 5. Restart CoreDNS

```bash
# Delete CoreDNS pods to apply new configuration
kubectl delete pods -n kube-system -l k8s-app=kube-dns

# Verify CoreDNS is using new configuration
kubectl logs -n kube-system -l k8s-app=kube-dns
```

## Verification

### Check Pi-hole Deployment

```bash
# Check pods status
kubectl get pods -n pihole

# Check services
kubectl get svc -n pihole

# Get admin password (if not set manually)
kubectl logs -n pihole -l app.kubernetes.io/name=pihole | grep "random password"
```

### Access Pi-hole Web Interface

```bash
# If using LoadBalancer
kubectl get svc pihole-web -n pihole

# If using port-forward
kubectl port-forward -n pihole svc/pihole-web 8080:80
# Then visit http://localhost:8080/admin
```

### Test DNS Resolution

```bash
# Test from within the cluster
kubectl run test-pod --image=busybox -it --rm -- nslookup google.com

# Test from a node
dig @$(kubectl get svc pihole-dns -n pihole -o jsonpath='{.spec.clusterIP}') google.com
```

## Configuration Options

### Scaling Pi-hole Instances

```bash
# Scale to 3 replicas
helm upgrade pihole ./helm/pihole \
  --namespace pihole \
  --set replicaCount=3
```

### Custom Values File

Create a `custom-values.yaml`:

```yaml
replicaCount: 3

env:
  TZ: "America/New_York"
  FTLCONF_webserver_api_password: "your-secure-password"
  FTLCONF_dns_upstreams: "1.1.1.1;1.0.0.1"
  FTLCONF_dns_dnssec: "true"

persistence:
  enabled: true
  size: 2Gi

resources:
  limits:
    memory: 1Gi
    cpu: 1000m
  requests:
    memory: 256Mi
    cpu: 200m

ingress:
  enabled: true
  hosts:
    - host: pihole.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
```

Then deploy with:

```bash
helm install pihole ./helm/pihole -f custom-values.yaml --namespace pihole
```

## Monitoring and Troubleshooting

### Check Logs

```bash
# All Pi-hole pods logs
kubectl logs -n pihole -l app.kubernetes.io/name=pihole

# Specific pod
kubectl logs -n pihole pihole-0

# Follow logs
kubectl logs -n pihole -f pihole-0
```

### Health Checks

```bash
# Check pod status and readiness
kubectl get pods -n pihole -o wide

# Describe problematic pods
kubectl describe pod -n pihole pihole-0
```

### DNS Testing

```bash
# Test DNS resolution from different pods
kubectl run dns-test --image=busybox -it --rm -- nslookup doubleclick.net
# Should be blocked by Pi-hole

kubectl run dns-test --image=busybox -it --rm -- nslookup google.com
# Should resolve normally
```

## Load Balancing Benefits

With this setup:

1. **High Availability**: Multiple Pi-hole instances prevent single point of failure
2. **Load Distribution**: DNS queries are distributed across all Pi-hole replicas
3. **Independent Storage**: Each Pi-hole instance maintains its own data
4. **Automatic Failover**: CoreDNS automatically routes around failed instances
5. **Easy Scaling**: Add more Pi-hole instances by changing `replicaCount`

## Maintenance

### Updating Pi-hole

```bash
# Update to latest Pi-hole image
helm upgrade pihole ./helm/pihole \
  --namespace pihole \
  --set image.tag=latest
```

### Backup Configuration

```bash
# Backup persistent volumes
kubectl get pvc -n pihole
# Use your storage provider's backup solution
```

## Troubleshooting

### Common Issues

1. **Pi-hole pods not starting**: Check security contexts and capabilities
2. **DNS not resolving**: Verify CoreDNS configuration and Pi-hole service endpoints
3. **Web interface not accessible**: Check service type and ingress configuration
4. **Persistent storage issues**: Verify storage class and PVC creation

### Useful Commands

```bash
# Check CoreDNS configuration
kubectl get cm coredns -n kube-system -o yaml

# Check DNS endpoints
kubectl get endpoints -n pihole

# Test DNS from node
dig @<pihole-service-ip> google.com

# Check k3s DNS
kubectl get svc -n kube-system kube-dns
```