# Sports Scores App
Pulls and returns info about specific teams

docker build -t agbs2k8/sports-scores:latest -f api/Dockerfile .   
docker run --rm -p 8000:8000 --env-file .env agbs2k8/sports-scores:latest 