# DATA LOADING & PIPELINE 

import sqlite3
import pyarrow.parquet as pq
import time
import os
import gc

# Importing functions 
import db_schema

# Define file paths
db_path = 'data/nyc_mobility.db'
parquet_path = 'data/yellow_tripdata_final.parquet'
zones_csv_path = 'data/taxi_zone_lookup.csv'

# Delete old database to start new
if os.path.exists(db_path):
    os.remove(db_path)
    print("Deleted old database to start fresh.")

print("Connecting to database...")
conn = sqlite3.connect(db_path)

# Optimize SQLite performance settings
conn.execute("PRAGMA foreign_keys = ON;")
conn.execute("PRAGMA journal_mode = WAL;")
conn.execute("PRAGMA synchronous = OFF;")

# 1) Run functions to set up tables and populate lookup dimensions
db_schema.create_tables(conn)
db_schema.populate_lookups(conn, zones_csv_path)

# 2) Load trips data in row-groups to prevent out-of-memory errors
print(f"\nOpening Parquet file for loading: {parquet_path}...")
start_time = time.time()

parquet_file = pq.ParquetFile(parquet_path)
num_groups = parquet_file.num_row_groups
print(f"Total Row Groups to process: {num_groups}")

# Prepare SQL insert query based on parquet schema columns
metadata = parquet_file.schema.to_arrow_schema()
cols = metadata.names
placeholders = ", ".join(["?"] * len(cols))
insert_query = f"INSERT INTO trips ({', '.join(cols)}) VALUES ({placeholders});"

cursor = conn.cursor()
total_inserted = 0

for group_idx in range(num_groups):
    print(f"Loading Row Group {group_idx + 1} of {num_groups}...")
    group_start = time.time()
    
    # Read group and convert to pandas
    table = parquet_file.read_row_group(group_idx)
    df_chunk = table.to_pandas()
    
    # Format datetime columns for SQLite
    df_chunk['tpep_pickup_datetime'] = df_chunk['tpep_pickup_datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_chunk['tpep_dropoff_datetime'] = df_chunk['tpep_dropoff_datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_chunk['store_and_fwd_flag'] = df_chunk['store_and_fwd_flag'].astype(str)
    
    # To prevent MemoryError on conversion, we slice df_chunk into smaller batches of 100k rows
    sub_chunk_size = 100000
    for start in range(0, len(df_chunk), sub_chunk_size):
        sub_df = df_chunk.iloc[start : start + sub_chunk_size]
        # Only convert 100k rows to tuples at a time
        sub_tuples = [tuple(x) for x in sub_df.values]
        cursor.executemany(insert_query, sub_tuples)
        del sub_tuples
        gc.collect()
        
    conn.commit()
    total_inserted += len(df_chunk)
    print(f" - Loaded {len(df_chunk):,} rows in {time.time() - group_start:.2f}s (Total: {total_inserted:,} rows)")
    
    # Clean memory
    del table, df_chunk
    gc.collect()

print(f"\nAll trip data loaded in {time.time() - start_time:.2f} seconds!")

# 3) Trigger index creation to optimize future dashboard queries
index_start = time.time()
db_schema.create_indexes(conn)
print(f"Indexing completed in {time.time() - index_start:.2f} seconds!")

# Close connection
conn.close()
print("\nDatabase is fully configured and ready for dashboards!")
