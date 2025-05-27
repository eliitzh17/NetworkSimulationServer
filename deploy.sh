#!/bin/bash

# Set your project ID
PROJECT_ID="your-project-id"
REGION="us-central1"  # Change to your desired region

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable container.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Create a GKE cluster (if you don't have one)
echo "Creating GKE cluster..."
gcloud container clusters create network-simulation-cluster \
    --num-nodes=2 \
    --region=$REGION \
    --machine-type=e2-medium

# Get credentials for the cluster
echo "Getting cluster credentials..."
gcloud container clusters get-credentials network-simulation-cluster --region=$REGION

# Create secrets
echo "Creating secrets..."
# Replace these with your actual URIs
MONGODB_URI="your-mongodb-uri"
RABBITMQ_URI="your-rabbitmq-uri"

kubectl create secret generic mongodb-secret \
    --from-literal=uri="$MONGODB_URI" \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic rabbitmq-secret \
    --from-literal=uri="$RABBITMQ_URI" \
    --dry-run=client -o yaml | kubectl apply -f -

# Build and push Docker images
echo "Building and pushing Docker images..."

gcloud builds submit --tag gcr.io/$PROJECT_ID/main-app:latest

gcloud builds submit --tag gcr.io/$PROJECT_ID/consumer-simulations-worker:latest

gcloud builds submit --tag gcr.io/$PROJECT_ID/consumer-links-worker:latest

gcloud builds submit --tag gcr.io/$PROJECT_ID/publish-simulations-worker:latest

gcloud builds submit --tag gcr.io/$PROJECT_ID/publish-links-worker:latest

gcloud builds submit --tag gcr.io/$PROJECT_ID/publish-completed-worker:latest

# Update image names in YAML files
echo "Updating image names in YAML files..."
sed -i "s|gcr.io/\[YOUR-PROJECT-ID\]|gcr.io/$PROJECT_ID|g" deployment/*.yaml

# Apply all YAML files
echo "Deploying applications..."
kubectl apply -f deployment/main_app_job.yaml
kubectl apply -f deployment/consumer_simulations_worker_job.yaml
kubectl apply -f deployment/consumer_links_worker_job.yaml
kubectl apply -f deployment/publish_simulations_worker_job.yaml
kubectl apply -f deployment/publish_links_worker_job.yaml
kubectl apply -f deployment/publish_completed_worker_job.yaml

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/main-app

# Get the external IP of the main app
echo "Getting the external IP of the main app..."
kubectl get service main-app

echo "Deployment completed!" 