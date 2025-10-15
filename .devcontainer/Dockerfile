# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/devcontainers/python:1-3.10-bullseye

# Install minimal OS packages required for the spike (curl used for health checks).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Preinstall required Python packages to keep devcontainer builds reproducible.
RUN pip install --no-cache-dir \
    httpx \
    websocket-client
