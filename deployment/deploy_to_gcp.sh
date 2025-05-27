#!/bin/bash

# =============================
# Google Cloud Deployment Script
# =============================
# This script builds, pushes, and deploys all services and workers to Google Cloud Run.
# Fill in the placeholders (YOUR_PROJECT_ID, ENV VARS) before running.
#
# Run this script in a Bash terminal on your local machine or in Google Cloud Shell.
# Requirements: gcloud CLI, Docker, and Bash shell.

# Set your Google Cloud project ID
PROJECT_ID="properties-observability"
REGION="us-central1"
REPO="network-sim-repo"

# Set environment variables (replace with your actual values or use Secret Manager)
MONGODB_URI="mongodb+srv://eliitzh17:AX3lGegN341ozKF2@cluster0.qp71kbn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGODB_DB="network_sim_db"
RABBITMQ_URL="amqps://zzwmeqgv:CBqAUi7xOh0u8hj8mt9IDmpcQrJofi1H@horse.lmq.cloudamqp.com/zzwmeqgv"

# =============================
# 1. Enable required APIs
# =============================
# Where: Bash terminal (local or Google Cloud Shell)
# Requirements: gcloud CLI
#
gcloud config set project $PROJECT_ID
gcloud services enable artifactregistry.googleapis.com run.googleapis.com

# =============================
# 2. Create Artifact Registry (only once)
# =============================
# Where: Bash terminal (local or Google Cloud Shell)
# Requirements: gcloud CLI
#
gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION \
  --description="Docker repository for network simulation"

# =============================
# 3. Authenticate Docker to Artifact Registry
# =============================
# Where: Bash terminal (local or Google Cloud Shell)
# Requirements: gcloud CLI, Docker
#
gcloud auth configure-docker $REGION-docker.pkg.dev

# =============================
# 4. Build and Push Docker Images
# =============================
# Where: Bash terminal (local machine with Docker installed)
# Requirements: Docker, gcloud CLI
#
# Main app
APP_IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/app:latest"
docker build -t $APP_IMAGE -f Dockerfile .
docker push $APP_IMAGE

# Worker images (repeat for each worker)
WORKERS=( \
  "worker-consumer-simulations:app/workers/consumer_workers/consumer_simulations_worker.py" \
  "worker-consumer-links:app/workers/consumer_workers/consumer_links_worker.py" \
  "worker-publish-simulations:app/workers/outbox_publishers_workers/publish_simulations_worker.py" \
  "worker-publish-links:app/workers/outbox_publishers_workers/publish_links_worker.py" \
  "worker-publish-completed:app/workers/outbox_publishers_workers/publish_completed_worker.py" \
)

for entry in "${WORKERS[@]}"; do
  IFS=":" read -r name cmd <<< "$entry"
  IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$name:latest"
  docker build -t $IMAGE -f Dockerfile .
  docker push $IMAGE
done

# =============================
# 5. Deploy to Cloud Run
# =============================
# Where: Bash terminal (local or Google Cloud Shell)
# Requirements: gcloud CLI
#
# Deploy main app

gcloud run deploy network-simulation-server \
  --image=$APP_IMAGE \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars=MONGODB_URI=$MONGODB_URI,MONGODB_DB=$MONGODB_DB,RABBITMQ_URL=$RABBITMQ_URL \
  --port=9090

# Deploy workers (with correct command for each)
# Note: Cloud Run expects the container to listen on $PORT (default 8080). We set --port=8080 explicitly for all workers.
for entry in "${WORKERS[@]}"; do
  IFS=":" read -r name cmd <<< "$entry"
  IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$name:latest"
  gcloud run deploy $name \
    --image=$IMAGE \
    --region=$REGION \
    --platform=managed \
    --set-env-vars=MONGODB_URI=$MONGODB_URI,MONGODB_DB=$MONGODB_DB,RABBITMQ_URL=$RABBITMQ_URL \
    --command="python" \
    --args="$cmd" \
    --no-allow-unauthenticated
done

echo "\nDeployment script complete! Review output for any errors." 