# Sport Scores Job

## Local build

Build from the repository root so Docker can include the sibling `shared_models` package.

```sh
cd /Users/ajwilson/GitRepos/local-server/sports_scores
docker build -t agbs2k8/sports-scores-job:latest -f job/Dockerfile .
```

Run the job locally with the repo root `.env` file:

```sh
cd /Users/ajwilson/GitRepos/local-server/sports_scores
docker run --rm --env-file .env agbs2k8/sports-scores-job:latest
```

## Helm deployment to k3s

The Helm chart lives under `job/helm/sports-scores-job` and deploys the job as a Kubernetes `CronJob`.

Default schedule:

```text
0 */3 * * *
```

That runs every 3 hours in the `America/Chicago` time zone by default.

Deploy to the same k3s cluster used by `trmnl-agent`:

```sh
cd /Users/ajwilson/GitRepos/local-server/sports_scores/job
./deploy.sh
```

The deploy script:

- loads environment variables from `/Users/ajwilson/GitRepos/local-server/sports_scores/.env`
- builds the image from the repository root
- imports the image into the target k3s nodes
- runs `helm upgrade --install` for the `sports-scores-job` release

Required environment variables in `.env`:

- `KUBE_CONTEXT`
- `PGPASSWORD`
- `WEBHOOK_URL`

Useful overrides:

```sh
CRON_SCHEDULE="0 */6 * * *" ./deploy.sh
NAMESPACE=default ./deploy.sh
IMAGE_REPOSITORY=agbs2k8/sports-scores-job IMAGE_PULL_POLICY=IfNotPresent ./deploy.sh
```# Sport Scores Job

docker build -t agbs2k8/sports-scores-job:latest -f job/Dockerfile .   
docker run --rm --env-file .env agbs2k8/sports-scores-job:latest