#!/bin/bash
# -------------------------------------------------------------------
# deploy.sh – Terraform Deployment Helper
# -------------------------------------------------------------------
# Usage: ./deploy.sh <env_name> <step> <action> [extra_args...]
#
# Steps:
#   step1  – Provision infrastructure (APIs, VPC, GKE, GCS, monitoring)
#   step2  – Download model to GCS (requires -var="hf_token=hf_xxx")
#
# Examples:
#   ./deploy.sh demo step1 apply                          # Provision everything
#   ./deploy.sh demo step2 apply -var="hf_token=hf_xxx"  # Download model
#   ./deploy.sh demo step1 destroy                        # Tear down everything
# -------------------------------------------------------------------

set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 <env_name> <step> <action> [extra_args...]"
  echo ""
  echo "Steps:   step1, step2"
  echo "Actions: plan, apply, destroy, output"
  exit 1
fi

ENV="$1"
STEP="$2"
ACTION="$3"
shift 3
EXTRA_ARGS="$*"

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
  echo "Error: No active GCP project. Run 'gcloud config set project <PROJECT_ID>' first." >&2
  exit 1
fi
BUCKET="${PROJECT_ID}-tf-state"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Resolve var file ---
VAR_FILE="${SCRIPT_DIR}/envs/${ENV}-${STEP}.tfvars"
if [ ! -f "$VAR_FILE" ]; then
  echo "Error: Variable file not found: ${VAR_FILE}" >&2
  exit 1
fi

echo "========================================"
echo "  Project:     ${PROJECT_ID}"
echo "  Environment: ${ENV}"
echo "  Step:        ${STEP}"
echo "  Var File:    envs/${ENV}-${STEP}.tfvars"
echo "  Action:      ${ACTION}"
echo "========================================"
echo ""

cd "${SCRIPT_DIR}"

# --- Bootstrap: create state bucket if it doesn't exist ---
if ! gcloud storage buckets describe "gs://${BUCKET}" --project="$PROJECT_ID" &>/dev/null; then
  echo "📦 State bucket 'gs://${BUCKET}' not found. Creating it..."
  gcloud storage buckets create "gs://${BUCKET}" \
    --project="$PROJECT_ID" \
    --location=asia-southeast1 \
    --uniform-bucket-level-access
  echo "✅ State bucket created."
fi

# --- Initialize backend ---
terraform init \
  -reconfigure \
  -backend-config="bucket=${BUCKET}" \
  -backend-config="prefix=terraform/state/${ENV}"

# --- Helper: fetch GKE credentials into kubeconfig ---
fetch_kubeconfig() {
  local env_prefix region cluster_name
  env_prefix=$(grep -E '^\s*env_prefix\s*=' "$VAR_FILE" | head -1 | sed 's/.*=\s*"\(.*\)"/\1/')
  region=$(grep -E '^\s*region\s*=' "$VAR_FILE" | head -1 | sed 's/.*=\s*"\(.*\)"/\1/')
  cluster_name="${env_prefix}-cluster"
  echo "🔑 Fetching GKE credentials for ${cluster_name}..."
  gcloud container clusters get-credentials "$cluster_name" \
    --region "$region" --project "$PROJECT_ID"
}

# -------------------------------------------------------------------
# Execute: route by action
# -------------------------------------------------------------------
if [ "$ACTION" = "output" ]; then
  terraform output $EXTRA_ARGS
  exit 0
fi

# For apply/destroy on steps that deploy K8s resources, fetch kubeconfig first
if [ "$STEP" != "step1" ] && [ "$ACTION" != "plan" ]; then
  fetch_kubeconfig 2>/dev/null || true
fi

# Run terraform
terraform "$ACTION" -var-file="$VAR_FILE" -var="project_id=${PROJECT_ID}" $EXTRA_ARGS

# Post-apply: fetch kubeconfig after step1 creates the cluster
if [ "$STEP" = "step1" ] && [ "$ACTION" = "apply" ]; then
  echo ""
  fetch_kubeconfig
  echo "✅ Infrastructure ready."
fi


