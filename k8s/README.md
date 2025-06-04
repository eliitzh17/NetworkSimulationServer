# Kubernetes Manifests for Network Simulation Server

This directory contains Kubernetes manifests and deployment scripts for running the Network Simulation Server and its worker services in different environments (production, development, and local testing).

## Directory Structure

- `deployment-app.yaml` - Deploys the main application server and exposes it via a LoadBalancer service.
- `deployment-workers.yaml` - Deploys all worker services (consumer and publisher workers) as separate deployments.
- `configmap.yaml` - Stores non-sensitive configuration data (e.g., environment name).
- `secret.yaml` - Stores sensitive data such as database URIs and message broker URLs (base64-encoded).
- `deploy.sh` - Bash script to automate GKE cluster creation, Docker image build/push, and deployment of all manifests for production.
- `deploy-gke.sh` - Script for building/pushing Docker images and deploying to GKE (manual steps, more customizable).
- `dev/` - Contains manifests and scripts for local or development deployments (e.g., with Minikube).

## Environments

### Production (GKE)
- Use the top-level YAML files and `deploy.sh` or `deploy-gke.sh` scripts.
- Images are built and pushed to Google Container Registry (GCR).
- Secrets and configmaps are set for production values.

### Development/Local (Minikube)
- Use the `dev/` subdirectory.
- `deploy-local.sh` builds and loads images into Minikube, applies manifests, and exposes the service.
- Configurations (e.g., environment, secrets) are set for development.
- Includes `hpa.yaml` for Horizontal Pod Autoscaler setup in dev.

## File Details

### YAML Manifests
- **deployment-app.yaml**: Deploys the main server. In dev, uses local image and secrets/configs from `dev/`.
- **deployment-workers.yaml**: Deploys all worker pods. In dev, uses local image and secrets/configs from `dev/`.
- **configmap.yaml**: Sets environment variables (e.g., `ENV: prod` or `ENV: dev`).
- **secret.yaml**: Stores sensitive connection strings (base64-encoded).
- **hpa.yaml** (dev only): Configures Horizontal Pod Autoscalers for all deployments.

### Scripts
- **deploy.sh**: Automates GKE cluster creation, image build/push, and deployment for production.
- **deploy-gke.sh**: Manual GKE deployment steps (build, push, apply manifests).
- **dev/deploy-local.sh**: Automates local deployment with Minikube (build, load, apply, expose).

## Usage

### Production Deployment (GKE)
1. Set your GCP project ID and region in `deploy.sh` or `deploy-gke.sh`.
2. Run `./deploy.sh` to automate the full process, or follow steps in `deploy-gke.sh` for manual control.
3. The scripts will build Docker images, push to GCR, create the GKE cluster, and apply all manifests.

### Local Development (Minikube)
1. Run `./dev/deploy-local.sh` from the project root.
2. The script builds the Docker image, loads it into Minikube, applies all manifests, and exposes the service.
3. Access the app using the Minikube service URL provided by the script.

## Notes
- **Secrets**: All secrets are base64-encoded. Update them as needed for your environment.
- **ConfigMaps**: Adjust environment variables as needed for your use case.
- **Images**: In production, images are pulled from GCR. In dev, local images are used.
- **Autoscaling**: HPA is configured only in the dev environment by default.

---

For more details, see the comments in each script and manifest file. 