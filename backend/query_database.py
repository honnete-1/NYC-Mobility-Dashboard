# Import the libraries we need
import sqlite3
import pandas as pd
import time
import os

# Point SQLite temp directory to D: drive (which has 30GB of space) instead of C: (which is full)
os.environ['SQLITE_TMPDIR'] = 'd:/School/Summative/NYC_Taxi_Project/data'

# Path to our SQLite database
db_path = '../data/nyc_mobility.db'

print(f"Connecting to database: {db_path}...\n")
conn = sqlite3.connect(db_path)

# Configure SQLite to use memory for temporary tables and sorting
cursor = conn.cursor()
cursor.execute("PRAGMA temp_store = MEMORY;")
cursor.execute("PRAGMA journal_mode = WAL;")

def run_analytical_query(query_title, sql_statement):
    print("=" * 60)
    print(f"QUERY: {query_title}")
    print("=" * 60)
    
    start_time = time.time()
    # Read the query results into a Pandas DataFrame for nice printing
    df_result = pd.read_sql_query(sql_statement, conn)
    elapsed = time.time() - start_time
    
    print(df_result.to_string(index=False))
    print(f"\nExecution Time: {elapsed:.4f} seconds\n")
    return elapsed

# Query 1 (Optimized): Find the top 5 busiest pickup zones
# Justification: Grouping and sorting on the indexed trips table first, then joining 
# only the top 5 rows with zones table. This avoids joining 7.4M rows!
query_1 = """
SELECT 
    z.borough, 
    z.zone_name, 
    g.total_trips
FROM (
    SELECT PULocationID, COUNT(*) AS total_trips
    FROM trips
    GROUP BY PULocationID
    ORDER BY total_trips DESC
    LIMIT 5
) g
JOIN zones z ON g.PULocationID = z.zone_id;
"""

# Query 2 (Optimized): Compare tipping rates by payment method
# Justification: Grouping on trips first (only 4 unique payment types in clean data), 
# then joining those 4 rows with payment_types lookup table.
query_2 = """
SELECT 
    pt.payment_name,
    g.total_trips,
    g.avg_fare,
    g.avg_tip,
    g.avg_tip_percent
FROM (
    SELECT 
        payment_type,
        COUNT(*) AS total_trips,
        ROUND(AVG(fare_amount), 2) AS avg_fare,
        ROUND(AVG(tip_amount), 2) AS avg_tip,
        ROUND(AVG(tip_percentage), 2) AS avg_tip_percent
    FROM trips
    GROUP BY payment_type
) g
JOIN payment_types pt ON g.payment_type = pt.payment_type_id
ORDER BY total_trips DESC;
"""

# Query 3: Average speed and trip volume by hour of day
# Justification: Shows hourly congestion levels. Since we extract hour from datetime string,
# we scan the table, but with temp_store=MEMORY, it will run without writing temp files to disk.
query_3 = """
SELECT 
    substr(tpep_pickup_datetime, 12, 2) AS pickup_hour,
    COUNT(*) AS total_trips,
    ROUND(AVG(trip_distance), 2) AS avg_distance,
    ROUND(AVG(trip_duration_min), 2) AS avg_duration_min,
    ROUND(AVG(average_speed_mph), 2) AS avg_speed_mph
FROM trips
GROUP BY pickup_hour
ORDER BY pickup_hour ASC;
"""

# Run all 3 queries and record execution times
time1 = run_analytical_query("Top 5 Busiest Pickup Zones", query_1)
time2 = run_analytical_query("Tipping Behavior by Payment Type", query_2)
time3 = run_analytical_query("Hourly Congestion and Speed Trends", query_3)

# Close the database connection
conn.close()
print("=" * 60)
print("All verification queries run successfully!")
print("=" * 60)
