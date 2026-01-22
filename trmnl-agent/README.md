# TRMNL Agent

A Python 3.13 application that runs daily in Kubernetes to extract data from web sources and forward it to a webhook/APIs.


## Quick Start

### 1. Build the Docker Image

```bash
cd trmnl-agent
docker build -t trmnl-agent:latest .
```

### Run the Docker Image
```
docker run --env-file .env trmnl-agent:latest
```


### Testing
Standard
```
python -m pytest -v
```

With verbose logs
```
python -m pytest -v -s
```

With hidden warnings
```
python -m pytest -v --disable-warnings
```

Get tests coverage (you may need to run pip install pytest-cov first)
```
python -m pytest --cov .
```

### Building for k3s

```bash
# Build for local k3s
docker build -t trmnl-agent:latest .

# Import into k3s
k3s ctr images import trmnl-agent.tar

# Or build directly in k3s
docker save trmnl-agent:latest | k3s ctr images import -
```

## Monitoring

### Logs

```bash
# View recent job logs
kubectl logs -l app.kubernetes.io/name=trmnl-agent --tail=100

# Follow logs in real-time
kubectl logs -f job/trmnl-agent-xxxxx
```

### Job Status

```bash
# Check CronJob status
kubectl get cronjob trmnl-agent

# View job history
kubectl get jobs -l app.kubernetes.io/name=trmnl-agent

# Describe failed jobs
kubectl describe job trmnl-agent-failed-job
```

## Troubleshooting

### Common Issues

1. **Webhook URL not configured**:
   ```bash
   kubectl create secret generic trmnl-agent-secret \
     --from-literal=WEBHOOK_URL="https://your-webhook.com"
   ```

2. **Image pull errors**:
   ```bash
   # Make sure image is available in k3s
   k3s ctr images ls | grep trmnl-agent
   ```

3. **Permission errors**:
   - Check security contexts in deployment
   - Verify non-root user setup

4. **Network connectivity**:
   - Test webhook URL from within cluster
   - Check firewall and DNS resolution

### Debug Mode

Enable debug logging:

```yaml
env:
  LOG_LEVEL: "DEBUG"
```

## Security Considerations

- Runs as non-root user (UID 1000)
- Read-only root filesystem
- No privilege escalation
- Resource limits enforced
- Secrets mounted securely
- Network policies recommended

## License

[Your License Here]