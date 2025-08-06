#!/bin/bash

echo "🔁 Restarting container..."
docker-compose down
docker-compose up --build -d