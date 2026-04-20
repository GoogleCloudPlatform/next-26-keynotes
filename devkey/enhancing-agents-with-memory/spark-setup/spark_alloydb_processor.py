import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, explode
from pyspark.sql.types import StructType, StructField, StringType, ArrayType

# Define the schema for the extracted rules chunks
chunk_schema = ArrayType(StructType([
    StructField("text", StringType(), True),
    StructField("city", StringType(), True),
    StructField("source", StringType(), True)
]))

def process_document(gcs_uri: str):
    """
    User Defined Function (UDF) to process a PDF using Document AI.
    In a real pipeline, this would call the Document AI API to perform 
    semantic chunking on the unstructured PDF content.
    """
    # Simulate Document AI extraction logic
    print(f"Analyzing and chunking document: {gcs_uri}")
    
    # Example extracted chunks
    chunks = [
        {
            "text": "Race organizers must ensure street closures are approved by the city 30 days in advance.",
            "city": "Las Vegas",
            "source": gcs_uri
        },
        {
            "text": "Hydration stations must be placed every 2 miles along the course.",
            "city": "Las Vegas",
            "source": gcs_uri
        }
    ]
    return chunks

def run_ingestion():
    # Initialize Spark Session with Lightning Engine optimization
    spark = SparkSession.builder \
        .appName("CityRulesIngestion") \
        .getOrCreate()

    # Configuration from environment
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    gcs_bucket = os.environ.get("GCS_BUCKET", "next26-city-rules-docs")
    alloydb_host = os.environ.get("ALLOYDB_HOST")
    alloydb_user = os.environ.get("ALLOYDB_USER", "postgres")
    alloydb_pass = os.environ.get("ALLOYDB_PASS", "postgres")
    
    # 1. Retrieve list of documents from Cloud Storage
    # In a production scenario, we would use spark.read.text or a listing utility
    document_list = [("gs://" + gcs_bucket + "/las_vegas_marathon_rules.pdf",)]
    uri_df = spark.createDataFrame(document_list, ["gcs_uri"])

    # 2. Parallel Processing with Spark Lightning Engine
    # We apply our Document AI UDF across the cluster for high-performance extraction
    process_udf = udf(process_document, chunk_schema)
    chunked_df = uri_df.withColumn("chunks", process_udf(col("gcs_uri"))) \
                       .select(explode(col("chunks")).alias("chunk")) \
                       .select("chunk.*")

    # 3. Write processed chunks to AlloyDB
    if alloydb_host:
        jdbc_url = f"jdbc:postgresql://{alloydb_host}/city_rules"
        
        print(f"Writing {chunked_df.count()} chunks to AlloyDB table 'rules'...")
        chunked_df.write.format("jdbc") \
            .option("url", jdbc_url) \
            .option("user", alloydb_user) \
            .option("password", alloydb_pass) \
            .option("dbtable", "rules") \
            .mode("append") \
            .save()
    else:
        print("ALLOYDB_HOST not set. Outputting results to console:")
        chunked_df.show(truncate=False)

if __name__ == "__main__":
    run_ingestion()
