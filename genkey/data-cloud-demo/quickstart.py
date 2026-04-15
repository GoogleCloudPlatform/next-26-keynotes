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
# This maps to the BigQuery dataset.
spark.sql("CREATE NAMESPACE IF NOT EXISTS <BUCKET_NAME>.acai_dataset")

# Loop through and register each as an Iceberg table in BigLake
for file_name in files:
  print(f"Registering {file_name} to BigLake...")

   # 2. Read the raw parquet file
  df = spark.read.parquet(f"gs://<BUCKET_NAME>/{file_name}.parquet")

   # 3. Write to the catalog.
  # Note: Use .tableProperty inside the writeTo chain correctly
  df.writeTo(f"acai_demo.acai_dataset.{file_name}") \
      .using("iceberg") \
      .tableProperty("write.format.default", "parquet") \
      .createOrReplace()


print("All tables registered successfully!")


# Verify one table
#spark.sql("SELECT * FROM acaibucket.acai_dataset.order_items LIMIT 5").show()
