import sqlite3
import os

# Define file paths
src_db = 'data/nyc_mobility.db'
dest_db = 'data/nyc_mobility_deploy.db'

# Delete old destination database if it exists
if os.path.exists(dest_db):
    os.remove(dest_db)
    print("Deleted old deploy database to start fresh.")

print(f"Connecting to source database: {src_db}...")
conn_src = sqlite3.connect(src_db)
cursor_src = conn_src.cursor()

print(f"Creating destination database: {dest_db}...")
conn_dest = sqlite3.connect(dest_db)
cursor_dest = conn_dest.cursor()

# Fetch table schemas from sqlite_master and create them in the destination db
cursor_src.execute("SELECT sql, name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
tables = cursor_src.fetchall()

for create_sql, table_name in tables:
    if create_sql:
        cursor_dest.execute(create_sql)
print("Database tables created successfully.")

# Copy the dimension lookup tables (vendors, rate_codes, payment_types, zones) in full
for tbl in ['vendors', 'rate_codes', 'payment_types', 'zones']:
    print(f"Copying lookup data for table: {tbl}...")
    cursor_src.execute(f"SELECT * FROM {tbl};")
    rows = cursor_src.fetchall()
    if rows:
        placeholders = ', '.join(['?'] * len(rows[0]))
        cursor_dest.executemany(f"INSERT INTO {tbl} VALUES ({placeholders});", rows)

# Copy a representative sample of 50,000 trip records
print("Sampling 50,000 trip records from the trips fact table...")
cursor_src.execute("SELECT * FROM trips ORDER BY RANDOM() LIMIT 50000;")
rows = cursor_src.fetchall()
if rows:
    placeholders = ', '.join(['?'] * len(rows[0]))
    cursor_dest.executemany(f"INSERT INTO trips VALUES ({placeholders});", rows)

# Fetch index schemas from sqlite_master and recreate them in the destination db
cursor_src.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL;")
indexes = cursor_src.fetchall()

print("Recreating database indexes...")
for (index_sql,) in indexes:
    cursor_dest.execute(index_sql)

conn_dest.commit()
conn_src.close()
conn_dest.close()

file_size_mb = os.path.getsize(dest_db) / (1024 * 1024)
print(f"Deployment database subset created successfully! File size: {file_size_mb:.2f} MB")
