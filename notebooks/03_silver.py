# Databricks notebook source
# MAGIC %run ./config

# COMMAND ----------
from pyspark.sql import functions as F

# COMMAND ----------
# cast to gold contract types, dedup PK, drop null keys
def gold_cols(e):
    rows = spark.sql(f"""SELECT column_name, full_data_type
                         FROM {CATALOG}.information_schema.columns
                         WHERE table_schema='{GOLD}' AND table_name='{e}'
                         ORDER BY ordinal_position""").collect()
    return [(r.column_name, r.full_data_type) for r in rows]

for e in ENTITIES:
    proj = [F.col(c).cast(dt).alias(c) for c, dt in gold_cols(e)]
    df = spark.table(t(BRONZE, e)).select(*proj)
    n_in = df.count()
    keys = PK[e]
    df_clean = df.dropna(subset=keys).dropDuplicates(keys)
    n_out = df_clean.count()
    df_clean.write.mode("overwrite").saveAsTable(t(SILVER, e))
    print(f"{e:24s} in={n_in:5d} out={n_out:5d} removed={n_in-n_out}")
