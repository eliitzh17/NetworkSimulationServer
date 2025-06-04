#!/bin/bash
set -e

# Build Docker image
IMAGE=network-simulation-server:latest
docker build -t $IMAGE .

# Save image to tar file
docker save $IMAGE > network-simulation-server.tar

minikube start

# Load image into Minikube
eval $(minikube docker-env)
docker load < network-simulation-server.tar

# Clean up tar file
rm network-simulation-server.tar

echo "Image loaded into Minikube."


minikube addons enable metrics-server

# Apply k8s manifests
kubectl apply -f k8s/dev/secret.yaml
kubectl apply -f k8s/dev/configmap.yaml
kubectl apply -f k8s/dev/hpa.yaml
kubectl apply -f k8s/dev/deployment-app.yaml
kubectl apply -f k8s/dev/deployment-workers.yaml

# Expose service (optional)
echo "To access the app, run: minikube service network-simulation-server" 

minikube service network-simulation-server

# Helpful cleanup and restart commands:
# 
# Delete all deployments:
# kubectl delete deployment --all
#
# Delete all services:
# kubectl delete service --all
#
# Delete all pods:
# kubectl delete pod --all
#
# Delete all jobs:
# kubectl delete jobs --all
#
# Delete all configmaps:
# kubectl delete configmap --all
#
# Delete all secrets:
# kubectl delete secret --all
#
# Restart Minikube:
# minikube stop && minikube start
#
# Delete everything and start fresh:
# kubectl delete all --all && kubectl delete configmap --all && kubectl delete secret --all
#
# View all resources:
# kubectl get all