resource "google_monitoring_dashboard" "hypercomputer_dashboard" {
  project        = var.project_id
  dashboard_json = <<EOF
{
  "displayName": "${var.env_prefix} Hypercomputer Dashboard",
  "dashboardFilters": [],
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "Pods",
        "xyChart": {
          "chartOptions": {
            "displayHorizontal": false,
            "mode": "COLOR"
          },
          "dataSets": [
            {
              "legendTemplate": "vLLM Pods",
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "targetAxis": "Y2",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "crossSeriesReducer": "REDUCE_COUNT",
                    "groupByFields": [],
                    "perSeriesAligner": "ALIGN_MEAN"
                  },
                  "filter": "metric.type=\"kubernetes.io/container/memory/used_bytes\" resource.type=\"k8s_container\" resource.label.\"cluster_name\"=\"${var.cluster_name}\" resource.label.\"namespace_name\"=\"default\" resource.label.\"container_name\"=\"vllm\""
                }
              }
            },
            {
              "legendTemplate": "Runner Pods",
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "targetAxis": "Y1",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "crossSeriesReducer": "REDUCE_COUNT",
                    "groupByFields": [],
                    "perSeriesAligner": "ALIGN_MEAN"
                  },
                  "filter": "metric.type=\"kubernetes.io/container/memory/used_bytes\" resource.type=\"k8s_container\" resource.label.\"cluster_name\"=\"${var.cluster_name}\" resource.label.\"namespace_name\"=\"default\" resource.label.\"container_name\"=\"frontend\""
                }
              }
            }
          ],
          "thresholds": [],
          "timeshiftDuration": "0s",
          "y2Axis": {
            "scale": "LINEAR"
          },
          "yAxis": {
            "label": "Count",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "vLLM Utilization",
        "xyChart": {
          "chartOptions": {
            "displayHorizontal": false,
            "mode": "COLOR"
          },
          "dataSets": [
            {
              "legendTemplate": "CPU Utilization",
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "targetAxis": "Y1",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "crossSeriesReducer": "REDUCE_MEAN",
                    "groupByFields": [],
                    "perSeriesAligner": "ALIGN_MEAN"
                  },
                  "filter": "metric.type=\"kubernetes.io/container/cpu/request_utilization\" resource.type=\"k8s_container\" resource.label.\"cluster_name\"=\"${var.cluster_name}\" metadata.user_labels.\"app\"=\"gemma4-vllm-server\""
                }
              }
            },
            {
              "legendTemplate": "GPU Utilization",
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "targetAxis": "Y2",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "crossSeriesReducer": "REDUCE_MEAN",
                    "groupByFields": [],
                    "perSeriesAligner": "ALIGN_MEAN"
                  },
                  "filter": "metric.type=\"kubernetes.io/container/accelerator/duty_cycle\" resource.type=\"k8s_container\" resource.label.\"cluster_name\"=\"${var.cluster_name}\" metadata.user_labels.\"app\"=\"gemma4-vllm-server\""
                }
              }
            },
            {
              "legendTemplate": "GPU Memory Usage",
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "targetAxis": "Y1",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "crossSeriesReducer": "REDUCE_MEAN",
                    "groupByFields": [],
                    "perSeriesAligner": "ALIGN_MEAN"
                  },
                  "filter": "metric.type=\"kubernetes.io/container/accelerator/memory_used\" resource.type=\"k8s_container\" resource.label.\"cluster_name\"=\"${var.cluster_name}\" metadata.user_labels.\"app\"=\"gemma4-vllm-server\""
                }
              }
            }
          ],
          "thresholds": [],
          "timeshiftDuration": "0s",
          "y2Axis": {
            "scale": "LINEAR"
          },
          "yAxis": {
            "label": "Count",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "HTTP Traffic & Latency",
        "id": "",
        "xyChart": {
          "chartOptions": {
            "mode": "COLOR"
          },
          "dataSets": [
            {
              "breakdowns": [],
              "dimensions": [],
              "legendTemplate": "Total QPS",
              "measures": [],
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "targetAxis": "Y1",
              "timeSeriesQuery": {
                "outputFullDuration": false,
                "timeSeriesFilter": {
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "groupByFields": [],
                    "perSeriesAligner": "ALIGN_RATE"
                  },
                  "filter": "resource.type=\"internal_http_lb_rule\" metric.type=\"loadbalancing.googleapis.com/https/internal/request_count\" resource.labels.forwarding_rule_name=has_substring(\"${var.env_prefix}-internal-http\")"
                },
                "unitOverride": ""
              }
            },
            {
              "breakdowns": [],
              "dimensions": [],
              "legendTemplate": "Error Rate (Non-200)",
              "measures": [],
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "targetAxis": "Y1",
              "timeSeriesQuery": {
                "outputFullDuration": false,
                "timeSeriesFilter": {
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "groupByFields": [],
                    "perSeriesAligner": "ALIGN_RATE"
                  },
                  "filter": "resource.type=\"internal_http_lb_rule\" metric.type=\"loadbalancing.googleapis.com/https/internal/request_count\" metric.label.response_code_class!=\"200\" resource.labels.forwarding_rule_name=has_substring(\"${var.env_prefix}-internal-http\")"
                },
                "unitOverride": ""
              }
            },
            {
              "breakdowns": [],
              "dimensions": [],
              "legendTemplate": "Latency (95th %)",
              "measures": [],
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "targetAxis": "Y2",
              "timeSeriesQuery": {
                "outputFullDuration": false,
                "timeSeriesFilter": {
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "crossSeriesReducer": "REDUCE_PERCENTILE_50",
                    "groupByFields": [],
                    "perSeriesAligner": "ALIGN_DELTA"
                  },
                  "filter": "resource.type=\"internal_http_lb_rule\" metric.type=\"loadbalancing.googleapis.com/https/internal/total_latencies\" resource.labels.forwarding_rule_name=has_substring(\"${var.env_prefix}-internal-http\")"
                },
                "unitOverride": ""
              }
            }
          ],
          "thresholds": [],
          "timeshiftDuration": "0s",
          "y2Axis": {
            "label": "Latency (ms)",
            "scale": "LINEAR"
          },
          "yAxis": {
            "label": "Req/s",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "Time to First Token (TTFT)",
        "xyChart": {
          "chartOptions": { "mode": "COLOR" },
          "dataSets": [
            {
              "legendTemplate": "P50",
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "aggregation": { "alignmentPeriod": "60s", "crossSeriesReducer": "REDUCE_PERCENTILE_50", "perSeriesAligner": "ALIGN_DELTA", "groupByFields": [] },
                  "filter": "metric.type=\"prometheus.googleapis.com/vllm:time_to_first_token_seconds/histogram\" resource.type=\"prometheus_target\" resource.label.\"cluster\"=\"${var.cluster_name}\""
                }
              }
            },
            {
              "legendTemplate": "P95",
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "aggregation": { "alignmentPeriod": "60s", "crossSeriesReducer": "REDUCE_PERCENTILE_95", "perSeriesAligner": "ALIGN_DELTA", "groupByFields": [] },
                  "filter": "metric.type=\"prometheus.googleapis.com/vllm:time_to_first_token_seconds/histogram\" resource.type=\"prometheus_target\" resource.label.\"cluster\"=\"${var.cluster_name}\""
                }
              }
            }
          ],
          "yAxis": { "label": "Seconds", "scale": "LINEAR" }
        }
      },
      {
        "title": "Cache Usage",
        "xyChart": {
          "chartOptions": { "mode": "COLOR" },
          "dataSets": [
            {
              "legendTemplate": "KV Cache Usage %",
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "timeSeriesQuery": {
                "prometheusQuery": "avg(vllm:kv_cache_usage_perc{cluster=\"${var.cluster_name}\"})",
                "unitOverride": "10^2.%"
              }
            },
            {
              "legendTemplate": "Prefix Cache Hit Rate %",
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "timeSeriesQuery": {
                "prometheusQuery": "sum(rate(vllm:prefix_cache_hits_total{cluster=\"${var.cluster_name}\"}[1m])) / sum(rate(vllm:prefix_cache_queries_total{cluster=\"${var.cluster_name}\"}[1m]))",
                "unitOverride": "10^2.%"
              }
            }
          ],
          "yAxis": { "label": "%", "scale": "LINEAR" }
        }
      },
      {
        "title": "Token Throughput",
        "xyChart": {
          "chartOptions": { "mode": "COLOR" },
          "dataSets": [
            {
              "legendTemplate": "Prompt Tokens/s",
              "minAlignmentPeriod": "60s",
              "plotType": "STACKED_BAR",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "aggregation": { "alignmentPeriod": "60s", "crossSeriesReducer": "REDUCE_SUM", "perSeriesAligner": "ALIGN_RATE", "groupByFields": [] },
                  "filter": "metric.type=\"prometheus.googleapis.com/vllm:prompt_tokens_total/counter\" resource.type=\"prometheus_target\" resource.label.\"cluster\"=\"${var.cluster_name}\""
                }
              }
            },
            {
              "legendTemplate": "Generation Tokens/s",
              "minAlignmentPeriod": "60s",
              "plotType": "STACKED_BAR",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "aggregation": { "alignmentPeriod": "60s", "crossSeriesReducer": "REDUCE_SUM", "perSeriesAligner": "ALIGN_RATE", "groupByFields": [] },
                  "filter": "metric.type=\"prometheus.googleapis.com/vllm:generation_tokens_total/counter\" resource.type=\"prometheus_target\" resource.label.\"cluster\"=\"${var.cluster_name}\""
                }
              }
            }
          ],
          "yAxis": { "label": "Tokens/s", "scale": "LINEAR" }
        }
      },
      {
        "title": "Schedule State",
        "xyChart": {
          "chartOptions": { "mode": "COLOR" },
          "dataSets": [
            {
              "legendTemplate": "Running Requests",
              "minAlignmentPeriod": "60s",
              "plotType": "STACKED_BAR",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "aggregation": { "alignmentPeriod": "60s", "crossSeriesReducer": "REDUCE_SUM", "perSeriesAligner": "ALIGN_MEAN", "groupByFields": [] },
                  "filter": "metric.type=\"prometheus.googleapis.com/vllm:num_requests_running/gauge\" resource.type=\"prometheus_target\" resource.label.\"cluster\"=\"${var.cluster_name}\""
                }
              }
            },
            {
              "legendTemplate": "Waiting Requests",
              "minAlignmentPeriod": "60s",
              "plotType": "STACKED_BAR",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "aggregation": { "alignmentPeriod": "60s", "crossSeriesReducer": "REDUCE_SUM", "perSeriesAligner": "ALIGN_MEAN", "groupByFields": [] },
                  "filter": "metric.type=\"prometheus.googleapis.com/vllm:num_requests_waiting/gauge\" resource.type=\"prometheus_target\" resource.label.\"cluster\"=\"${var.cluster_name}\""
                }
              }
            }
          ],
          "yAxis": { "label": "Requests", "scale": "LINEAR" }
        }
      }
    ]
  }
}
EOF
}