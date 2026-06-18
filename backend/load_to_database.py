# I imported the libraries I needed for SQLite, PyArrow, and Pandas
import sqlite3
import pandas as pd
import geopandas as gpd
import numpy as np
import pyarrow.parquet as pq
import time
import os
import gc


# I then defined the file paths
db_path = '../data/nyc_mobility.db'
parquet_path = '../data/yellow_tripdata_final.parquet'
zones_csv_path = '../data/taxi_zone_lookup.csv'

# I deleted the old db if it exists so we can start fresh
if os.path.exists(db_path):
    os.remove(db_path)
    print("Deleted old database to start fresh.")

print("Connecting to SQLite database...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# I enabled foreign keys and set WAL mode for speed
cursor.execute("PRAGMA foreign_keys = ON;")
cursor.execute("PRAGMA journal_mode = WAL;")
cursor.execute("PRAGMA synchronous = OFF;")

#  Created the tables 
print("Creating tables...")

# 1. Vendors Lookup Table
cursor.execute("""
CREATE TABLE vendors (
    vendor_id INTEGER PRIMARY KEY,
    vendor_name TEXT NOT NULL
);
""")

# 2. Rate Codes Lookup Table
cursor.execute("""
CREATE TABLE rate_codes (
    ratecode_id INTEGER PRIMARY KEY,
    rate_code_name TEXT NOT NULL
);
""")

# 3. Payment Types Lookup Table
cursor.execute("""
CREATE TABLE payment_types (
    payment_type_id INTEGER PRIMARY KEY,
    payment_name TEXT NOT NULL
);
""")

# 4. Zones Lookup Table (Spatial Lookup)
cursor.execute("""
CREATE TABLE zones (
    zone_id INTEGER PRIMARY KEY,
    borough TEXT NOT NULL,
    zone_name TEXT NOT NULL,
    service_zone TEXT NOT NULL,
    shape_area REAL,
    shape_length REAL
);
""")


# 5. Trips Fact Table
cursor.execute("""
CREATE TABLE trips (
    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
    VendorID INTEGER,
    tpep_pickup_datetime TEXT NOT NULL,
    tpep_dropoff_datetime TEXT NOT NULL,
    passenger_count INTEGER,
    trip_distance REAL,
    RatecodeID INTEGER,
    store_and_fwd_flag TEXT,
    PULocationID INTEGER,
    DOLocationID INTEGER,
    payment_type INTEGER,
    fare_amount REAL,
    extra REAL,
    mta_tax REAL,
    tip_amount REAL,
    tolls_amount REAL,
    improvement_surcharge REAL,
    total_amount REAL,
    congestion_surcharge REAL,
    trip_duration_min REAL,
    average_speed_mph REAL,
    tip_percentage REAL,
    FOREIGN KEY(VendorID) REFERENCES vendors(vendor_id),
    FOREIGN KEY(RatecodeID) REFERENCES rate_codes(ratecode_id),
    FOREIGN KEY(payment_type) REFERENCES payment_types(payment_type_id),
    FOREIGN KEY(PULocationID) REFERENCES zones(zone_id),
    FOREIGN KEY(DOLocationID) REFERENCES zones(zone_id)
);
""")

print("Tables created successfully.")


# --- Step 2: Populate lookup tables ---
print("\nPopulating lookup tables...")

# Populating Vendors (TLC dictionary values + legacy vendor 4 from dataset)
vendors_data = [
    (1, "Creative Mobile Technologies, LLC"),
    (2, "VeriFone Inc."),
    (4, "Unknown / Legacy Vendor")
]
cursor.executemany("INSERT INTO vendors (vendor_id, vendor_name) VALUES (?, ?);", vendors_data)

# Populating Rate Codes (TLC dictionary values)
rate_codes_data = [
    (1, "Standard rate"),
    (2, "JFK"),
    (3, "Newark"),
    (4, "Nassau or Westchester"),
    (5, "Negotiated fare"),
    (6, "Group ride"),
    (99, "Unknown")
]
cursor.executemany("INSERT INTO rate_codes (ratecode_id, rate_code_name) VALUES (?, ?);", rate_codes_data)

# Populating Payment Types (TLC dictionary values)
payment_types_data = [
    (1, "Credit card"),
    (2, "Cash"),
    (3, "No charge"),
    (4, "Dispute"),
    (5, "Unknown"),
    (6, "Voided trip")
]
cursor.executemany("INSERT INTO payment_types (payment_type_id, payment_name) VALUES (?, ?);", payment_types_data)

# Populating Zones from CSV and Shapefile (Spatial Metadata)
print("Loading taxi zone lookup CSV and Shapefile...")
zones_df = pd.read_csv(zones_csv_path)
shapefile_path = '../data/taxi_zones/taxi_zones.shp'
if os.path.exists(shapefile_path):
    print(f"Loading shapefile spatial metadata from {shapefile_path}...")
    gdf = gpd.read_file(shapefile_path)
    merged_df = zones_df.merge(gdf[['LocationID', 'Shape_Area', 'Shape_Leng']], on='LocationID', how='left')
else:
    print(f"[WARNING] Shapefile not found at {shapefile_path}. Using null values for spatial features.")
    merged_df = zones_df.copy()
    merged_df['Shape_Area'] = np.nan
    merged_df['Shape_Leng'] = np.nan

merged_df = merged_df.replace({np.nan: None})

zones_data = [
    (int(row['LocationID']), str(row['Borough']), str(row['Zone']), str(row['service_zone']),
     row['Shape_Area'], row['Shape_Leng'])
    for _, row in merged_df.iterrows()
]
cursor.executemany("INSERT INTO zones (zone_id, borough, zone_name, service_zone, shape_area, shape_length) VALUES (?, ?, ?, ?, ?, ?);", zones_data)


conn.commit()
print("Lookup tables populated successfully.")


# --- Step 3: Load Trips data from Parquet in a memory-friendly way ---
print(f"\nOpening {parquet_path} for chunked loading...")
start_time = time.time()

# Open the parquet file using PyArrow ParquetFile reader (handles large files group-by-group)
parquet_file = pq.ParquetFile(parquet_path)
num_groups = parquet_file.num_row_groups
print(f"File opened successfully. Total Row Groups: {num_groups}")

# We extract column names to generate the SQL query
metadata = parquet_file.schema.to_arrow_schema()
cols = metadata.names
placeholders = ", ".join(["?"] * len(cols))
insert_query = f"INSERT INTO trips ({', '.join(cols)}) VALUES ({placeholders});"

total_rows_inserted = 0

for group_idx in range(num_groups):
    print(f"Reading and loading Row Group {group_idx + 1} of {num_groups}...")
    group_start = time.time()
    
    # Read only this group to save memory!
    table = parquet_file.read_row_group(group_idx)
    df_chunk = table.to_pandas()
    
    # Convert datetime columns to string format for SQLite
    df_chunk['tpep_pickup_datetime'] = df_chunk['tpep_pickup_datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_chunk['tpep_dropoff_datetime'] = df_chunk['tpep_dropoff_datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Standardize string fields
    df_chunk['store_and_fwd_flag'] = df_chunk['store_and_fwd_flag'].astype(str)
    
    # Bulk insert this group into SQLite
    chunk_tuples = [tuple(x) for x in df_chunk.values]
    cursor.executemany(insert_query, chunk_tuples)
    conn.commit()
    
    total_rows_inserted += len(df_chunk)
    print(f" - Successfully loaded {len(df_chunk):,} rows in {time.time() - group_start:.2f} seconds (Total: {total_rows_inserted:,} rows).")
    
    # Force garbage collection to keep memory usage low
    del table, df_chunk, chunk_tuples
    gc.collect()

print(f"\nAll trip records loaded successfully in {time.time() - start_time:.2f} seconds!")


# I created indexes for fast querying 
print("\nCreating indexes to speed up future queries...")
index_start = time.time()

# I then created indexes on time and locations for fast dashboards
cursor.execute("CREATE INDEX idx_trips_pickup ON trips (tpep_pickup_datetime);")
cursor.execute("CREATE INDEX idx_trips_pu_location ON trips (PULocationID);")
cursor.execute("CREATE INDEX idx_trips_do_location ON trips (DOLocationID);")

conn.commit()
print(f"Indexes created successfully in {time.time() - index_start:.2f} seconds!")

# Close the connection
conn.close()
print("\nDatabase setup complete! SQLite database saved to '../data/nyc_mobility.db'.")
