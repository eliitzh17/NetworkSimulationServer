#!/bin/bash
set -e

# Set these variables!
PROJECT_ID=your-gcp-project-id
IMAGE=gcr.io/$PROJECT_ID/network-simulation-server:latest

# Authenticate with GCP (uncomment if needed)
#gcloud auth login
#gcloud config set project $PROJECT_ID
#gcloud auth configure-docker

# Build and push Docker image
docker build -t $IMAGE .
docker push $IMAGE

echo "Update your k8s YAMLs to use: $IMAGE"

# Apply k8s manifests
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment-app.yaml
kubectl apply -f k8s/deployment-workers.yaml 