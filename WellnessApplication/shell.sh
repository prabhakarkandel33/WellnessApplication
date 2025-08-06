#!/bin/bash

docker-compose exec web bash
if [ $? -ne 0 ]; then
    echo "Failed to execute shell command in Docker container."
    exit 1  
