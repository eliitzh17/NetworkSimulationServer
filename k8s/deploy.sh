#!/bin/bash

# Set your project ID
PROJECT_ID="properties-observability"
REGION="us-central1"  # Change to your desired region

# Enable required APIs
echo "Enabling required APIs..."

# Create a GKE cluster (if you don't have one)
echo "Creating GKE cluster..."
gcloud container clusters create network-simulation-cluster \
    --num-nodes=2 \
    --region=$REGION \
    --machine-type=e2-medium \
    --disk-type=pd-standard \
    --disk-size=100

# Get credentials for the cluster
echo "Getting cluster credentials..."
gcloud container clusters get-credentials network-simulation-cluster --region=$REGION


# Build and push Docker images
echo "Building and pushing Docker images..."

gcloud builds submit --tag gcr.io/$PROJECT_ID/main-app:latest

gcloud builds submit --tag gcr.io/$PROJECT_ID/consumer-simulations-worker:latest

gcloud builds submit --tag gcr.io/$PROJECT_ID/consumer-links-worker:latest

gcloud builds submit --tag gcr.io/$PROJECT_ID/publish-simulations-worker:latest

gcloud builds submit --tag gcr.io/$PROJECT_ID/publish-links-worker:latest

gcloud builds submit --tag gcr.io/$PROJECT_ID/publish-completed-worker:latest

# Apply all YAML files
echo "Deploying applications..."
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment-app.yaml
kubectl apply -f k8s/deployment-workers.yaml

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/network-simulation-server

# Get the external IP of the main app
echo "Getting the external IP of the main app..."
kubectl get service main-app

echo "Deployment completed!" 