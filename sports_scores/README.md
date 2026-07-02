# Sports Scores Apps

## Build

### API application

Build from the [sports_scores](#) repository root so Docker can include both the API service and the sibling shared models package.

```sh
cd /Users/ajwilson/GitRepos/local-server/sports_scores
docker build -t agbs2k8/sports-scores:latest -f api/Dockerfile .
```

Run the API locally after the image is built:

```sh
docker run --rm -p 8000:8000 --env-file api/.env.example agbs2k8/sports-scores:latest 
```

The container now installs both the API service and [sports_scores/shared_models](/Users/ajwilson/GitRepos/local-server/sports_scores/shared_models) as Python distributions during the build, so runtime imports no longer depend on setting `PYTHONPATH`.

### API Kubernetes deployment

The API service includes a Helm chart at [sports_scores/api/helm/sports-scores-api](/Users/ajwilson/GitRepos/local-server/sports_scores/api/helm/sports-scores-api) and a deploy helper at [sports_scores/api/deploy.sh](/Users/ajwilson/GitRepos/local-server/sports_scores/api/deploy.sh).

It deploys as a `Deployment` plus `Service`, with the default NodePort mapping:

```text
30081 -> 8000
```

Deploy it to the local k3s cluster with:

```sh
cd /Users/ajwilson/GitRepos/local-server/sports_scores/api
./deploy.sh
```

### Job application

Build the job image from the [sports_scores](#) repository root so Docker can include the sibling shared models package.

```sh
cd /Users/ajwilson/GitRepos/local-server/sports_scores
docker build -t agbs2k8/sports-scores-job:latest -f job/Dockerfile .
```

Run the job with the repo root `.env` file loaded at container start:

```sh
cd /Users/ajwilson/GitRepos/local-server/sports_scores
docker run --rm --env-file .env agbs2k8/sports-scores-job:latest
```

The job image installs [sports_scores/shared_models](/Users/ajwilson/GitRepos/local-server/sports_scores/shared_models) into the container and then runs [job/main.py](/Users/ajwilson/GitRepos/local-server/sports_scores/job/main.py), so it shares the same database models and environment-driven configuration as the API without needing local editable installs.

### Kubernetes deployment

The batch job includes a Helm chart at [sports_scores/job/helm/sports-scores-job](/Users/ajwilson/GitRepos/local-server/sports_scores/job/helm/sports-scores-job) and a deploy helper at [sports_scores/job/deploy.sh](/Users/ajwilson/GitRepos/local-server/sports_scores/job/deploy.sh).

The default CronJob schedule is every 3 hours:

```text
0 */3 * * *
```

Deploy it to the local k3s cluster with:

```sh
cd /Users/ajwilson/GitRepos/local-server/sports_scores/job
./deploy.sh
```