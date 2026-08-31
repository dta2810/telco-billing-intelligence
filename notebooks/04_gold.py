# Databricks notebook source
# MAGIC %run ./config

# COMMAND ----------
# load gold from silver via INSERT OVERWRITE (keeps table contract + comments)
def gold_col_names(e):
    rows = spark.sql(f"""SELECT column_name FROM {CATALOG}.information_schema.columns
                         WHERE table_schema='{GOLD}' AND table_name='{e}'
                         ORDER BY ordinal_position""").collect()
    return [r.column_name for r in rows]

for e in ENTITIES:
    cols = ", ".join(gold_col_names(e))
    spark.sql(f"INSERT OVERWRITE TABLE {t(GOLD, e)} SELECT {cols} FROM {t(SILVER, e)}")
    print(f"{e:24s} {spark.table(t(GOLD, e)).count():6d}")
