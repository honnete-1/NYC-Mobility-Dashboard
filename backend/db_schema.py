# =====================================================================
# TEAMMATE A: DATABASE SCHEMA & LOOKUPS SETUP
# =====================================================================
import sqlite3
import pandas as pd
import geopandas as gpd
import numpy as np
import os


def create_tables(conn):
    """Creates the tables for our database schema."""
    cursor = conn.cursor()
    print("Creating database tables...")
    
    # 1. Vendors Lookup Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendors (
        vendor_id INTEGER PRIMARY KEY,
        vendor_name TEXT NOT NULL
    );
    """)

    # 2. Rate Codes Lookup Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rate_codes (
        ratecode_id INTEGER PRIMARY KEY,
        rate_code_name TEXT NOT NULL
    );
    """)

    # 3. Payment Types Lookup Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payment_types (
        payment_type_id INTEGER PRIMARY KEY,
        payment_name TEXT NOT NULL
    );
    """)

    # 4. Zones Lookup Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS zones (
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
    CREATE TABLE IF NOT EXISTS trips (
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
    conn.commit()
    print("All tables created successfully.")

def populate_lookups(conn, zones_csv_path):
    """Populates the static lookup tables and load zones from CSV."""
    cursor = conn.cursor()
    print("Populating lookup data...")

    # Populating Vendors
    vendors_data = [
        (1, "Creative Mobile Technologies, LLC"),
        (2, "VeriFone Inc."),
        (4, "Unknown / Legacy Vendor")
    ]
    cursor.executemany("INSERT OR IGNORE INTO vendors (vendor_id, vendor_name) VALUES (?, ?);", vendors_data)

    # Populating Rate Codes
    rate_codes_data = [
        (1, "Standard rate"),
        (2, "JFK"),
        (3, "Newark"),
        (4, "Nassau or Westchester"),
        (5, "Negotiated fare"),
        (6, "Group ride"),
        (99, "Unknown")
    ]
    cursor.executemany("INSERT OR IGNORE INTO rate_codes (ratecode_id, rate_code_name) VALUES (?, ?);", rate_codes_data)

    # Populating Payment Types
    payment_types_data = [
        (1, "Credit card"),
        (2, "Cash"),
        (3, "No charge"),
        (4, "Dispute"),
        (5, "Unknown"),
        (6, "Voided trip")
    ]
    cursor.executemany("INSERT OR IGNORE INTO payment_types (payment_type_id, payment_name) VALUES (?, ?);", payment_types_data)

    # Populating Zones
    print(f"Loading zone data from {zones_csv_path}...")
    zones_df = pd.read_csv(zones_csv_path)
    
    # Programmatically load shapefile metadata to link spatial coordinates
    shapefile_path = '../data/taxi_zones/taxi_zones.shp'
    if os.path.exists(shapefile_path):
        print(f"Loading shapefile spatial metadata from {shapefile_path}...")
        gdf = gpd.read_file(shapefile_path)
        # Merge on LocationID to associate spatial attributes
        merged_df = zones_df.merge(gdf[['LocationID', 'Shape_Area', 'Shape_Leng']], on='LocationID', how='left')
    else:
        print(f"[WARNING] Shapefile not found at {shapefile_path}. Using null values for spatial features.")
        merged_df = zones_df.copy()
        merged_df['Shape_Area'] = np.nan
        merged_df['Shape_Leng'] = np.nan

    # Fill NaNs with None so SQLite handles them as NULL
    merged_df = merged_df.replace({np.nan: None})

    zones_data = [
        (int(row['LocationID']), str(row['Borough']), str(row['Zone']), str(row['service_zone']),
         row['Shape_Area'], row['Shape_Leng'])
        for _, row in merged_df.iterrows()
    ]
    cursor.executemany("INSERT OR IGNORE INTO zones (zone_id, borough, zone_name, service_zone, shape_area, shape_length) VALUES (?, ?, ?, ?, ?, ?);", zones_data)


    conn.commit()
    print("Lookup tables populated successfully.")

def create_indexes(conn):
    """Creates indexes to optimize query speed."""
    cursor = conn.cursor()
    print("Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_pickup ON trips (tpep_pickup_datetime);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_pu_location ON trips (PULocationID);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_do_location ON trips (DOLocationID);")
    conn.commit()
    print("Indexes created successfully.")
