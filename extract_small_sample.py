import duckdb

PARQUET_PATH = "food.parquet"     # same folder as this script
OUT_CSV = "off_sample_10k.csv"    # output file

con = duckdb.connect()

query = f"""
SELECT
    product_name,
    ingredients_text,
    allergens_tags AS allergens,
    code,
    countries_tags AS countries
FROM '{PARQUET_PATH}'
WHERE ingredients_text IS NOT NULL
LIMIT 10000;
"""

print("Running query... (this should NOT freeze your laptop)")
df = con.execute(query).df()
con.close()

print(f"Rows extracted: {len(df)}")
df.to_csv(OUT_CSV, index=False)
print(f"Saved to {OUT_CSV}")

