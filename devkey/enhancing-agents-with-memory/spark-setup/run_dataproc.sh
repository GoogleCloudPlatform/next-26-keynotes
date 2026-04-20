#!/bin/bash

# Configuration
REGION=${GOOGLE_CLOUD_LOCATION:-us-central1}
CLUSTER_ID=${ALLOYDB_CLUSTER_ID:-rules-db}
PROJECT_ID=$(gcloud config get-value project)

# Retrieve the primary instance IP for AlloyDB (if it exists)
echo "Looking up AlloyDB instance IP..."
ALLOYDB_HOST=$(gcloud alloydb instances describe ${CLUSTER_ID}-primary --cluster=${CLUSTER_ID} --region=${REGION} --format="value(ipAddress)" 2>/dev/null)

if [ -z "$ALLOYDB_HOST" ]; then
  echo "Warning: Could not find AlloyDB primary instance IP. Running in console-only mode."
fi

echo "Submitting Spark Ingestion Job to Dataproc Serverless..."

# In a production environment, this command would submit the Python file to a Spark cluster.
# For the purpose of this codelab, we demonstrate the command structure.
# gcloud dataproc batches submit pyspark ./spark-setup/spark_alloydb_processor.py \
#     --region=$REGION \
#     --deps-bucket=gs://YOUR_STAGING_BUCKET \
#     --properties="spark.jars.packages=org.postgresql:postgresql:42.5.0" \
#     --environment-variables="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,ALLOYDB_HOST=$ALLOYDB_HOST"

# For local simulation during the lab:
export GOOGLE_CLOUD_PROJECT=$PROJECT_ID
export ALLOYDB_HOST=$ALLOYDB_HOST
python ./spark-setup/spark_alloydb_processor.py
