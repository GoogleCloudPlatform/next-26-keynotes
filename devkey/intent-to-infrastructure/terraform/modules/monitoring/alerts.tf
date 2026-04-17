resource "google_monitoring_alert_policy" "vllm_ttft_alert" {
  count        = var.create_alerts ? 1 : 0
  project      = var.project_id
  display_name = "High TTFT Latency (${var.env_prefix})"
  combiner     = "OR"
  enabled      = true
  severity     = "CRITICAL"

  documentation {
    subject   = "vLLM TTFT Alert (${var.env_prefix})"
    content   = "High Time-To-First-Token latency detected for vLLM serving in ${var.env_prefix}."
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Prometheus Target - prometheus/vllm:time_to_first_token_seconds/histogram"
    condition_threshold {
      filter          = "resource.type = \"prometheus_target\" AND resource.labels.cluster = \"${var.cluster_name}\" AND resource.labels.namespace = \"default\" AND metric.type = \"prometheus.googleapis.com/vllm:time_to_first_token_seconds/histogram\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 1

      trigger {
        count = 1
      }

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_MEAN"
        group_by_fields = [
          "metric.label.pod",
          "metric.label.model_name",
          "metric.label.top_level_controller_type",
          "metric.label.top_level_controller_name",
          "metric.label.engine",
          "resource.label.project_id",
          "resource.label.location",
          "resource.label.cluster",
          "resource.label.namespace",
          "resource.label.job",
          "resource.label.instance"
        ]
      }
    }
  }

  alert_strategy {
    notification_prompts = ["OPENED"]
  }

}
