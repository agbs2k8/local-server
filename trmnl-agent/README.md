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
```

### Deploy
```
DOCKER_HUB_USERNAME=yourusername ./deploy.sh
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
kubectl get jobs -A

# Describe failed jobs
kubectl describe job trmnl-agent-failed-job

# List all cronjobs (should show trmnl-agent)
kubectl get cronjob

# Get detailed info about your specific cronjob
kubectl get cronjob trmnl-agent -o wide

# Describe the cronjob (shows schedule, last run, etc.)
kubectl describe cronjob trmnl-agent

# Verify ConfigMap was created
kubectl get configmap trmnl-agent-config

# Verify Secret was created
kubectl get secret trmnl-agent-secret

# Check ServiceAccount
kubectl get serviceaccount trmnl-agent

# View logs from the most recent job
kubectl logs -l app.kubernetes.io/name=trmnl-agent --tail=50

# View logs from a specific job (replace with actual job name)
kubectl logs job/trmnl-agent-xxxxx

# Follow logs in real-time (if a job is currently running)
kubectl logs -f -l app.kubernetes.io/name=trmnl-agent

# Manually trigger a job to test immediately
kubectl create job --from=cronjob/trmnl-agent trmnl-agent-manual-test

# Check the manual job
kubectl get job trmnl-agent-manual-test
kubectl logs job/trmnl-agent-manual-test

# Verify the cron schedule and next run time
kubectl get cronjob trmnl-agent -o jsonpath='{.spec.schedule}{"\n"}'

# See full cronjob YAML configuration
kubectl get cronjob trmnl-agent -o yaml
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