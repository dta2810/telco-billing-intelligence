# Databricks notebook source
# MAGIC %run ./config

# COMMAND ----------
from pyspark.sql import functions as F

# COMMAND ----------
# Auto Loader: raw CSV -> bronze (all string + ingest metadata)
for e in ENTITIES:
    src   = f"{VOL_PATH}/{e}"
    ckpt  = f"{VOL_PATH}/_ckpt/{e}"
    schm  = f"{VOL_PATH}/_schema/{e}"
    # raw is a full snapshot per run: reset bronze table + Auto Loader state
    spark.sql(f"DROP TABLE IF EXISTS {t(BRONZE, e)}")
    dbutils.fs.rm(ckpt, True)
    dbutils.fs.rm(schm, True)
    stream = (spark.readStream.format("cloudFiles")
              .option("cloudFiles.format", "csv")
              .option("cloudFiles.schemaLocation", schm)
              .option("cloudFiles.inferColumnTypes", "false")
              .option("header", "true")
              .load(src)
              .withColumn("_ingested_at", F.current_timestamp())
              .withColumn("_source_file", F.col("_metadata.file_path")))
    q = (stream.writeStream
         .option("checkpointLocation", ckpt)
         .trigger(availableNow=True)
         .toTable(t(BRONZE, e)))
    q.awaitTermination()
    print(f"{e:24s} -> {t(BRONZE, e)}")

# COMMAND ----------
# row counts
for e in ENTITIES:
    print(f"{e:24s} {spark.table(t(BRONZE, e)).count():6d}")
