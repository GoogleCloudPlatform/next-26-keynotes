locals {
  # Resolve effective model values with backward-compatible fallbacks
  model_subdir      = var.model_subdir != "" ? var.model_subdir : var.model_name
  model_served_name = var.model_served_name != "" ? var.model_served_name : var.model_name
  # HF repo: use explicit value if provided, else auto-convert model_name (first hyphen → slash)
  model_hf_repo     = var.model_hf_repo != "" ? var.model_hf_repo : ""
}

resource "kubernetes_service_account" "vllm" {
  metadata {
    name = "${var.prefix}-vllm-sa"
    annotations = {
      "iam.gke.io/gcp-service-account" = var.model_reader_sa_email
    }
  }
}

resource "google_service_account_iam_member" "workload_identity_user" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.model_reader_sa_email}"
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[default/${kubernetes_service_account.vllm.metadata[0].name}]"
}

resource "kubernetes_config_map" "otel_collector_conf" {
  count = var.enable_otel ? 1 : 0

  metadata {
    name      = "${var.prefix}-otel-collector-conf"
    namespace = "default"
  }

  data = {
    "config.yaml" = <<EOF
receivers:
  otlp:
    protocols:
      grpc:
      http:

processors:
  batch:

exporters:
  googlecloud:
    project: ${var.project_id}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [googlecloud]
EOF
  }
}

resource "kubernetes_persistent_volume" "lustre" {
  count = (var.lustre_copy_active || var.use_lustre) ? 1 : 0

  metadata {
    name = "${var.prefix}-lustre-pv"
  }
  spec {
    capacity = {
      storage = "9000Gi"
    }
    access_modes                     = ["ReadWriteMany"]
    persistent_volume_reclaim_policy = "Retain"
    storage_class_name               = "lustre-rwx-1000mbps-per-tib"
    persistent_volume_source {
      csi {
        driver        = "lustre.csi.storage.gke.io"
        volume_handle = "${var.prefix}-lustre/lustrefs"
        volume_attributes = {
          ip         = var.lustre_ip
          filesystem = "lustrefs"
        }
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim" "lustre" {
  count = (var.lustre_copy_active || var.use_lustre) ? 1 : 0

  metadata {
    name = "${var.prefix}-lustre-pvc"
  }
  spec {
    access_modes       = ["ReadWriteMany"]
    storage_class_name = "lustre-rwx-1000mbps-per-tib"
    volume_name        = kubernetes_persistent_volume.lustre[0].metadata[0].name
    resources {
      requests = {
        storage = "9000Gi"
      }
    }
  }
}

resource "kubernetes_deployment" "vllm" {
  count = var.enable_vllm ? 1 : 0

  timeouts {
    create = "20m"
    update = "20m"
  }

  metadata {
    name = "gemma4-vllm-server"
    labels = {
      app = "gemma4-vllm-server"
    }
  }

  lifecycle {
    ignore_changes = [spec[0].replicas]
  }

  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "gemma4-vllm-server"
      }
    }

    progress_deadline_seconds = 1200

    template {
      metadata {
        labels = {
          app = "gemma4-vllm-server"
        }
        annotations = var.use_lustre ? {} : {
          "gke-gcsfuse/volumes" = "true"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.vllm.metadata[0].name

        container {
          image = var.vllm_image
          name  = "vllm"

          command = ["/bin/bash", "-c"]
          args = [
            var.enable_otel ? "echo 'Waiting for model files at /data/model/${local.model_subdir}/config.json...' && for i in $(seq 1 60); do [ -f /data/model/${local.model_subdir}/config.json ] && break; echo \"Attempt $i/60: config.json not found, waiting...\"; sleep 5; done && if [ ! -f /data/model/${local.model_subdir}/config.json ]; then echo 'ERROR: config.json not found after 5 minutes'; ls -la /data/model/ 2>/dev/null; ls -la /data/model/${local.model_subdir}/ 2>/dev/null; exit 1; fi && pip install opentelemetry-sdk opentelemetry-api opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi && python3 -m vllm.entrypoints.openai.api_server --model /data/model/${local.model_subdir} --served-model-name ${local.model_served_name} --host 0.0.0.0 --port 8000 --quantization fp8 --otlp-traces-endpoint localhost:4317 --trust-remote-code ${join(" ", var.vllm_extra_args)}" : "echo 'Waiting for model files at /data/model/${local.model_subdir}/config.json...' && for i in $(seq 1 60); do [ -f /data/model/${local.model_subdir}/config.json ] && break; echo \"Attempt $i/60: config.json not found, waiting...\"; sleep 5; done && if [ ! -f /data/model/${local.model_subdir}/config.json ]; then echo 'ERROR: config.json not found after 5 minutes'; ls -la /data/model/ 2>/dev/null; ls -la /data/model/${local.model_subdir}/ 2>/dev/null; exit 1; fi && python3 -m vllm.entrypoints.openai.api_server --model /data/model/${local.model_subdir} --served-model-name ${local.model_served_name} --host 0.0.0.0 --port 8000 --quantization fp8 --trust-remote-code ${join(" ", var.vllm_extra_args)}"
          ]

          env {
            name = "POD_NAME"
            value_from {
              field_ref {
                field_path = "metadata.name"
              }
            }
          }
          env {
            name = "POD_NAMESPACE"
            value_from {
              field_ref {
                field_path = "metadata.namespace"
              }
            }
          }
          dynamic "env" {
            for_each = var.enable_otel ? [1] : []
            content {
              name  = "OTEL_TRACES_EXPORTER"
              value = "otlp"
            }
          }
          dynamic "env" {
            for_each = var.enable_otel ? [1] : []
            content {
              name  = "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"
              value = "localhost:4317"
            }
          }
          dynamic "env" {
            for_each = var.enable_otel ? [1] : []
            content {
              name  = "OTEL_EXPORTER_OTLP_INSECURE"
              value = "true"
            }
          }
          dynamic "env" {
            for_each = var.enable_otel ? [1] : []
            content {
              name  = "OTEL_SERVICE_NAME"
              value = "gemma4-vllm-server"
            }
          }
          dynamic "env" {
            for_each = var.enable_otel ? [1] : []
            content {
              name  = "OTEL_RESOURCE_ATTRIBUTES"
              value = "k8s.pod.name=$(POD_NAME),k8s.namespace.name=$(POD_NAMESPACE),k8s.cluster.name=${var.cluster_name}"
            }
          }

          resources {
            limits = {
              "nvidia.com/gpu" = 1
            }
            requests = {
              "cpu" = "2000m"
            }
          }

          port {
            container_port = 8000
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 60
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 30
          }

          volume_mount {
            name       = "model-volume"
            mount_path = "/data/model"
            read_only  = true
          }
        }

        # Sidecar OTel Collector
        dynamic "container" {
          for_each = var.enable_otel ? [1] : []
          content {
            name  = "otel-collector"
            image = "otel/opentelemetry-collector-contrib:0.88.0"

            args = ["--config=/conf/config.yaml"]

            volume_mount {
              name       = "otel-collector-config-vol"
              mount_path = "/conf"
            }
          }
        }

        dynamic "volume" {
          for_each = var.use_lustre ? [] : [1]
          content {
            name = "model-volume"
            csi {
              driver = "gcsfuse.csi.storage.gke.io"
              volume_attributes = {
                bucketName   = var.model_bucket_name
                mountOptions = "implicit-dirs"
              }
            }
          }
        }

        dynamic "volume" {
          for_each = var.use_lustre ? [1] : []
          content {
            name = "model-volume"
            persistent_volume_claim {
              claim_name = kubernetes_persistent_volume_claim.lustre[0].metadata[0].name
            }
          }
        }

        dynamic "volume" {
          for_each = var.enable_otel ? [1] : []
          content {
            name = "otel-collector-config-vol"
            config_map {
              name = kubernetes_config_map.otel_collector_conf[0].metadata[0].name
            }
          }
        }

        toleration {
          key      = "nvidia.com/gpu"
          operator = "Exists"
          effect   = "NoSchedule"
        }
      }
    }
  }
}

resource "kubernetes_horizontal_pod_autoscaler" "vllm_hpa" {
  count = var.enable_vllm && !var.enable_inference_gateway ? 1 : 0

  metadata {
    name = "${var.prefix}-vllm-hpa"
  }

  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.vllm[0].metadata[0].name
    }

    min_replicas = 1
    max_replicas = 10

    target_cpu_utilization_percentage = var.hpa_target_cpu
  }
}

resource "kubernetes_manifest" "vllm_hpa_gpu" {
  count = var.enable_vllm && var.enable_inference_gateway ? 1 : 0

  manifest = {
    apiVersion = "autoscaling/v2"
    kind       = "HorizontalPodAutoscaler"
    metadata = {
      name      = "${var.prefix}-vllm-hpa-gpu"
      namespace = "default"
    }
    spec = {
      scaleTargetRef = {
        apiVersion = "apps/v1"
        kind       = "Deployment"
        name       = "gemma4-vllm-server"
      }
      minReplicas = 1
      maxReplicas = 5
      metrics = [
        {
          type = "Resource"
          resource = {
            name = "cpu"
            target = {
              type               = "Utilization"
              averageUtilization = var.hpa_target_cpu
            }
          }
        }
      ]
    }
  }
}

resource "kubernetes_service" "vllm" {
  count = var.enable_vllm ? 1 : 0

  metadata {
    name = "vllm-service"
  }
  spec {
    selector = {
      app = kubernetes_deployment.vllm[0].metadata[0].labels.app
    }
    port {
      port        = 8000
      target_port = 8000
    }
    type = "ClusterIP"
  }
}

# --- Model Download Job ---
# Downloads gated model from HuggingFace directly to GCS via GCSFuse.
# Runs in Step 2 when an HF token is provided, so model is ready for Step 3/4.

resource "kubernetes_secret" "hf_token" {
  count = var.hf_token != "" ? 1 : 0

  metadata {
    name = "${var.prefix}-hf-token"
  }

  data = {
    token = var.hf_token
  }
}

resource "kubernetes_job" "model_download" {
  count = var.hf_token != "" ? 1 : 0

  metadata {
    name = "${var.prefix}-model-download-${substr(md5(var.model_name), 0, 8)}"
  }

  spec {
    completions   = 1
    parallelism   = 1
    backoff_limit = 2

    template {
      metadata {
        annotations = {
          "gke-gcsfuse/volumes" = "true"
        }
      }
      spec {
        service_account_name = kubernetes_service_account.vllm.metadata[0].name
        restart_policy       = "Never"

        container {
          name  = "downloader"
          image = "google/cloud-sdk:slim"

          command = ["/bin/bash", "-c"]
          args = [
            <<-EOT
            set -e
            MODEL_DIR="/data/model/${local.model_subdir}"

            # Check if model already exists
            if [ -f "$MODEL_DIR/config.json" ]; then
              echo "✅ Model already exists at $MODEL_DIR. Skipping download."
              exit 0
            fi

            echo "📦 Installing huggingface_hub..."
            pip install -q --break-system-packages huggingface_hub

            # Determine HF repo: use explicit value if set, else convert model_name (first hyphen → slash)
            %{if local.model_hf_repo != ""}
            MODEL_HF_NAME="${local.model_hf_repo}"
            %{else}
            MODEL_HF_NAME=$(echo "${var.model_name}" | sed 's/-/\//') 
            %{endif}
            echo "⬇️  Downloading $MODEL_HF_NAME to $MODEL_DIR..."

            python3 -c "
from huggingface_hub import login, snapshot_download
login(token='$HF_TOKEN', add_to_git_credential=False)
snapshot_download(
    repo_id='$MODEL_HF_NAME',
    local_dir='$MODEL_DIR',
    ignore_patterns=['*.pth', '*.msgpack', '*.h5', '*.ot']
)
print('✅ Download complete')
"

            echo "✅ Model downloaded successfully to $MODEL_DIR"
            ls -la "$MODEL_DIR"
            EOT
          ]

          env {
            name = "HF_TOKEN"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.hf_token[0].metadata[0].name
                key  = "token"
              }
            }
          }

          volume_mount {
            name       = "model-volume"
            mount_path = "/data/model"
          }

          resources {
            requests = {
              cpu    = "1000m"
              memory = "2Gi"
            }
          }
        }

        volume {
          name = "model-volume"
          csi {
            driver = "gcsfuse.csi.storage.gke.io"
            volume_attributes = {
              bucketName   = var.model_bucket_name
              mountOptions = "implicit-dirs"
            }
          }
        }
      }
    }
  }

  wait_for_completion = true

  timeouts {
    create = "30m"
  }
}

# --- Model Copy to Lustre Job ---
# Copies model from GCS (via GCSFuse) to Lustre PVC.
# Only runs when Lustre is active (Step 4) and model needs to be synced.

resource "kubernetes_job" "model_copy_to_lustre" {
  count = var.lustre_copy_active ? 1 : 0

  metadata {
    name = "${var.prefix}-model-copy-lustre-${substr(md5(var.model_name), 0, 8)}"
  }

  spec {
    completions   = 1
    parallelism   = 1
    backoff_limit = 2

    template {
      metadata {
        annotations = {
          "gke-gcsfuse/volumes" = "true"
        }
      }
      spec {
        service_account_name = kubernetes_service_account.vllm.metadata[0].name
        restart_policy       = "Never"

        container {
          name  = "copier"
          image = "google/cloud-sdk:slim"

          command = ["/bin/bash", "-c"]
          args = [
            <<-EOT
            set -e
            SRC="/gcs-model/${local.model_subdir}"
            DST="/lustre-model/${local.model_subdir}"

            # Check if model already exists on Lustre
            if [ -f "$DST/config.json" ]; then
              echo "✅ Model already exists on Lustre at $DST. Skipping copy."
              exit 0
            fi

            # Check if source exists on GCS
            if [ ! -f "$SRC/config.json" ]; then
              echo "❌ Model not found on GCS at $SRC. Run the model download job first."
              exit 1
            fi

            echo "📋 Copying model from GCS to Lustre..."
            echo "   Source: $SRC"
            echo "   Destination: $DST"
            mkdir -p "$DST"
            cp -rv "$SRC/." "$DST/"

            echo "✅ Model copied to Lustre successfully"
            ls -la "$DST"
            EOT
          ]

          volume_mount {
            name       = "gcs-volume"
            mount_path = "/gcs-model"
            read_only  = true
          }

          volume_mount {
            name       = "lustre-volume"
            mount_path = "/lustre-model"
          }

          resources {
            requests = {
              cpu    = "1000m"
              memory = "2Gi"
            }
          }
        }

        volume {
          name = "gcs-volume"
          csi {
            driver = "gcsfuse.csi.storage.gke.io"
            volume_attributes = {
              bucketName   = var.model_bucket_name
              mountOptions = "implicit-dirs"
            }
          }
        }

        volume {
          name = "lustre-volume"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.lustre[0].metadata[0].name
          }
        }
      }
    }
  }

  wait_for_completion = true

  timeouts {
    create = "30m"
  }

  depends_on = [kubernetes_job.model_download]
}


# GKE Gateway — created by Terraform so it exists before any HTTPRoute or traffic module needs it.
resource "kubernetes_manifest" "gateway" {
  manifest = {
    apiVersion = "gateway.networking.k8s.io/v1beta1"
    kind       = "Gateway"
    metadata = {
      name      = "${var.prefix}-internal-http"
      namespace = "default"
    }
    spec = {
      gatewayClassName = "gke-l7-rilb"
      listeners = [{
        name     = "http"
        port     = 80
        protocol = "HTTP"
        allowedRoutes = {
          namespaces = {
            from = "Same"
          }
        }
      }]
    }
  }
}

# Read the Gateway back after creation to get its status (IP address).
data "kubernetes_resource" "gateway" {
  api_version = "gateway.networking.k8s.io/v1beta1"
  kind        = "Gateway"

  metadata {
    name      = "${var.prefix}-internal-http"
    namespace = "default"
  }

  depends_on = [kubernetes_manifest.gateway]
}