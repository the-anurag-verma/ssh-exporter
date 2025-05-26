#!/bin/bash

# ------------------------------------------------
# Startup Script
# ------------------------------------------------

# Stop any running container (optional safety)
echo "Stopping any existing container..."
docker compose down

echo "Building afresh..."
docker compose build --no-cache

# Start in detached mode
echo "Starting ..."
docker compose up -d
