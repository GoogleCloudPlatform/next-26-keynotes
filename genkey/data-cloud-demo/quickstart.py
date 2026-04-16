# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Register_Existing_Data").getOrCreate()


# List of your 6 files in the bucket
files = [
  "customer_sensitive_data",
  "global_customer_identity",
  "global_regions",
  "historical_flavor_conversion_training",
  "order_items",
  "orders"
]

# 1. CRITICAL: Create the namespace first
# This maps to the BigQuery dataset. You can replace the dataset (acai_dataset) to whatever you want. But make sure to reference the same in line 31. 
# In any case, it creates a namespace in the name of the catalog. So in your BigQuery editor, you will reference the object in the format: Namespace.Dataset.Table

spark.sql("CREATE NAMESPACE IF NOT EXISTS acai_dataset")

# Loop through and register each as an Iceberg table in BigLake
for file_name in files:
  print(f"Registering {file_name} to BigLake...")

   # 2. Read the raw parquet file
  df = spark.read.parquet(f"gs://<BUCKET_NAME>/{file_name}.parquet")

   # 3. Write to the catalog.
  # Note: Use .tableProperty inside the writeTo chain correctly
  df.writeTo(f"acai_dataset.{file_name}") \
      .using("iceberg") \
      .tableProperty("write.format.default", "parquet") \
      .createOrReplace()


print("All tables registered successfully!")


# Verify one table in BigQuery
# SELECT * FROM <<namespace>>.<<dataset>>.order_items LIMIT 5;
