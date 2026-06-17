if [ -f ./.env ]; then
  echo "Loading environment variables from ./.env"
  set -a
  source ./.env
  set +a
else
  echo ".env file not found at ./.env!"
  exit 1
fi

echo "Environment variables loaded successfully."