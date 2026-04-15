# Raw data to forecasting in seconds with AI agents

The codelab demonstrates an end-to-end workflow for transforming unstructured data into actionable business intelligence using Google Cloud's AI-powered data platform.

## Overview

You act as a data scientist for a fictitious Froyo company, "Midnight Swirl", to answer critical questions regarding ingredients, market demand, and return on investment.

## Key technologies

* Knowledge Catalog(Dataplex) 
* Lakehouse for Apache Iceberg(BigLake)
* Vertex AI Semantic Inference
* Managed Service for Apache Spark(Dataproc)
* BigQuery

## Workflow

1. Unstructured Discovery: Use Knowledge Catalog to crawl PDF receipts in GCS and extract structured data using AI.
2. Unified Metadata: Publish extracted data as Iceberg tables for cross-engine accessibility.
3. Cross-Engine Analytics: Join fresh metadata with sales data using Spark and a unified catalog.
4. Semantic Insights: Identify popular products and at-risk customers by joining inferred data with product catalogs.
5. AI-Assisted Analysis: Perform advanced analytics directly from VS Code using Gemini.

## Prerequisites

* A Google Cloud project with billing enabled
* Visual Studio Code with the Data Cloud Extension installed