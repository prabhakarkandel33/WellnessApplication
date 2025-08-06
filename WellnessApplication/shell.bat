@echo off
docker-compose exec web bash
if %errorlevel% neq 0 (
    echo Failed to execute shell command in Docker container.
    exit /b %errorlevel%
)
