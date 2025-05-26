#!/bin/bash

# Deploy all worker functions as Google Cloud Functions

gcloud functions deploy consumer_simulations_worker \
  --set-env-vars=PYTHONPATH="/app",MONGODB_URI="mongodb+srv://eliitzh17:AX3lGegN341ozKF2@cluster0.qp71kbn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",MONGODB_DB="network_sim_db",RABBITMQ_URL="amqps://zzwmeqgv:CBqAUi7xOh0u8hj8mt9IDmpcQrJofi1H@horse.lmq.cloudamqp.com/zzwmeqgv" \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point=consumer_simulations_worker \
  --memory=512Mi \
  --region=us-central1 \
  --source=.


gcloud functions deploy consumer-links-worker \
  --set-env-vars=PYTHONPATH="/app",MONGODB_URI="mongodb+srv://eliitzh17:AX3lGegN341ozKF2@cluster0.qp71kbn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",MONGODB_DB="network_sim_db",RABBITMQ_URL="amqps://zzwmeqgv:CBqAUi7xOh0u8hj8mt9IDmpcQrJofi1H@horse.lmq.cloudamqp.com/zzwmeqgv" \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point consumer_links_worker \
  --memory 512Mi \
  --region us-central1 \
  --source .

gcloud functions deploy publish-completed-worker \
  --set-env-vars=PYTHONPATH="/app",MONGODB_URI="mongodb+srv://eliitzh17:AX3lGegN341ozKF2@cluster0.qp71kbn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",MONGODB_DB="network_sim_db",RABBITMQ_URL="amqps://zzwmeqgv:CBqAUi7xOh0u8hj8mt9IDmpcQrJofi1H@horse.lmq.cloudamqp.com/zzwmeqgv" \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point publish_completed_worker \
  --memory 512Mi \
  --region us-central1 \
  --source .

gcloud functions deploy publish-links-worker \
  --set-env-vars=PYTHONPATH="/app",MONGODB_URI="mongodb+srv://eliitzh17:AX3lGegN341ozKF2@cluster0.qp71kbn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",MONGODB_DB="network_sim_db",RABBITMQ_URL="amqps://zzwmeqgv:CBqAUi7xOh0u8hj8mt9IDmpcQrJofi1H@horse.lmq.cloudamqp.com/zzwmeqgv" \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point publish_links_worker \
  --memory 512Mi \
  --region us-central1 \
  --source .

gcloud functions deploy publish-simulations-worker \
  --set-env-vars=PYTHONPATH="/app",MONGODB_URI="mongodb+srv://eliitzh17:AX3lGegN341ozKF2@cluster0.qp71kbn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",MONGODB_DB="network_sim_db",RABBITMQ_URL="amqps://zzwmeqgv:CBqAUi7xOh0u8hj8mt9IDmpcQrJofi1H@horse.lmq.cloudamqp.com/zzwmeqgv" \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point publish_simulations_worker \
  --memory 512Mi \
  --region us-central1 \
  --source .

echo "All worker functions deployed." 