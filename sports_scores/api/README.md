# Sports Scores App

Pulls and returns info about specific teams.

## Local build

Build from the repository root so Docker can include the sibling `shared_models` package.

```sh
cd /Users/ajwilson/GitRepos/local-server/sports_scores
docker build -t agbs2k8/sports-scores:latest -f api/Dockerfile .
```

Run locally:

```sh
cd /Users/ajwilson/GitRepos/local-server/sports_scores
docker run --rm -p 8000:8000 --env-file .env agbs2k8/sports-scores:latest
```

## Helm deployment to k3s

The Helm chart lives under `api/helm/sports-scores-api` and deploys the API as a Kubernetes `Deployment` with a `Service`.

Default service exposure:

```text
NodePort 30081 -> container port 8000
```

Deploy to the local k3s cluster:

```sh
cd /Users/ajwilson/GitRepos/local-server/sports_scores/api
./deploy.sh
```

The deploy script:

- loads environment variables from `/Users/ajwilson/GitRepos/local-server/sports_scores/.env`
- builds the image from the repository root
- imports the image into the target k3s nodes
- runs `helm upgrade --install` for the `sports-scores-api` release

Required environment variables in `.env`:

- `KUBE_CONTEXT`
- `PGPASSWORD`

Recommended database settings in `.env` for a host-based PostgreSQL instance:

- `DATABASE_HOST`
- `DATABASE_PORT`
- `DATABASE_NAME`
- `PGUSER`