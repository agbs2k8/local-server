# Monitor Agent
Simple API set for monitoring the clsuter via API rather than kubectl commands


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

### Run the Docker Image
```
docker run -p 8000:8000 --env-file .env monitor-agent:0.0.1
```

### Local Testing
```
pyenv activate monitor-agent

source ../export_locals.sh

python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Helm Deployment on k3s

Build the container image locally:

```bash
cd monitor-agent
docker build -t monitor-agent:latest .
```

Import the image into k3s so the cluster can start the pod without pulling from a registry:

```bash
docker save monitor-agent:latest | sudo k3s ctr images import -
```

Install the chart:

```bash
helm upgrade --install monitor-agent ./helm -n monitor-agent --create-namespace
```

The default chart values expose the API with a NodePort service on port `30080`, so the API is reachable at:

```text
http://<k3s-node-ip>:30080
```

Example health checks:

```bash
curl http://<k3s-node-ip>:30080/liveness
curl http://<k3s-node-ip>:30080/readiness
```

If you prefer to keep the service internal, set `service.type=ClusterIP` and use port-forwarding instead:

```bash
helm upgrade --install monitor-agent ./helm -n monitor-agent --create-namespace --set service.type=ClusterIP
kubectl port-forward -n monitor-agent svc/monitor-agent 8000:8000
```

### Deploy Script

You can also deploy with the local helper script, which reads `KUBE_CONTEXT` from `./.env`, builds an `amd64` image, imports it into k3s, and upgrades the Helm release:

```bash
./deploy.sh
```

Optional overrides:

```bash
NAMESPACE=default RELEASE_NAME=monitor-agent IMAGE_PULL_POLICY=IfNotPresent ./deploy.sh
```
