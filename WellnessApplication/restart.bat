@echo off
echo Restarting Docker container...
docker-compose down
docker-compose up --build -d