

# I wrote flask backend code 
# I set up the server and endpoints for the taxi dashboard

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import json
from algorithms import MinHeap
import data_integrity
import normalization_feature_engineering
import db_loader

app = Flask(__name__)
# I enabled CORS so our browser page can make api calls without getting blocked
CORS(app)

# Created database  path 
DB_PATH = '../data/nyc_mobility_deploy.db' if os.path.exists('../data/nyc_mobility_deploy.db') else '../data/nyc_mobility.db'


def get_db_connection():
    # I added helper to connect to SQLite with fast settings
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

# Served the our index.html page
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

# I Served css and js files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# here is theAPI endpoint that the javascript page calls
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    # Read the query params from the URL request
    borough = request.args.get('borough', 'All')
    hour_min = request.args.get('hour_min')
    hour_max = request.args.get('hour_max')
    rate_code = request.args.get('rate_code', 'All')
    
    # Check if the query is just the default unfiltered page load
    # If yes, I load from the cached JSON to make it load instantly!
    is_default = (borough == 'All' and 
                  (hour_min is None or int(hour_min) == 0) and 
                  (hour_max is None or int(hour_max) == 23) and 
                  rate_code == 'All')
                  
    if is_default:
        cache_path = '../data/dashboard_cache.json'
        if os.path.exists(cache_path):
            print("Loading default dashboard data from precomputed cache...")
            with open(cache_path, 'r') as f:
                return jsonify(json.load(f))
    
    # Otherwise, we construct the SQL query dynamically
    conditions = []
    params = []
    
    # Filter by borough
    if borough and borough != 'All':
        conditions.append("z_pu.borough = ?")
        params.append(borough)
        
    # Filter by hour
    if hour_min is not None and hour_max is not None:
        conditions.append("CAST(substr(t.tpep_pickup_datetime, 12, 2) AS INTEGER) BETWEEN ? AND ?")
        params.extend([int(hour_min), int(hour_max)])
        
    # Filter by rate type
    if rate_code and rate_code != 'All':
        conditions.append("t.RatecodeID = ?")
        params.append(int(rate_code))
        
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Total count, average fare, average tip and speed averages
        kpi_query = f"""
        SELECT 
            COUNT(*) AS total_trips,
            ROUND(AVG(t.fare_amount), 2) AS avg_fare,
            ROUND(AVG(t.tip_amount), 2) AS avg_tip,
            ROUND(AVG(t.tip_percentage), 2) AS avg_tip_percent,
            ROUND(AVG(t.average_speed_mph), 2) AS avg_speed
        FROM trips t
        JOIN zones z_pu ON t.PULocationID = z_pu.zone_id
        {where_clause}
        """
        cursor.execute(kpi_query, params)
        kpi_row = cursor.fetchone()
        kpis = dict(kpi_row) if kpi_row else {
            "total_trips": 0, "avg_fare": 0.0, "avg_tip": 0.0, "avg_tip_percent": 0.0, "avg_speed": 0.0
        }
        
        # 2. Hourly volume and speeds
        hourly_query = f"""
        SELECT 
            substr(t.tpep_pickup_datetime, 12, 2) AS pickup_hour,
            COUNT(*) AS total_trips,
            ROUND(AVG(t.average_speed_mph), 2) AS avg_speed_mph
        FROM trips t
        JOIN zones z_pu ON t.PULocationID = z_pu.zone_id
        {where_clause}
        GROUP BY pickup_hour
        ORDER BY pickup_hour ASC
        """
        cursor.execute(hourly_query, params)
        hourly_trends = [dict(row) for row in cursor.fetchall()]
        
        # 3. Busiest zones: query all zone counts, then rank using custom Min-Heap data structure
        zones_query = f"""
        SELECT 
            z_pu.zone_name,
            COUNT(*) AS total_trips
        FROM trips t
        JOIN zones z_pu ON t.PULocationID = z_pu.zone_id
        {where_clause}
        GROUP BY z_pu.zone_name
        """
        cursor.execute(zones_query, params)
        all_zones = cursor.fetchall()
        
        # Instantiate custom MinHeap of size 10 to track the Top 10 busiest zones
        heap = MinHeap(10)
        for row in all_zones:
            heap.push((row['total_trips'], row['zone_name']))
        
        # I retrieved the sorted top elements from the heap (highest first)
        sorted_top = heap.get_sorted_elements()
        top_zones = [{"zone_name": name, "total_trips": count} for count, name in sorted_top]

        
        # 4. I tipped the percentage averages by payment method
        tipping_query = f"""
        SELECT 
            pt.payment_name,
            COUNT(*) AS total_trips,
            ROUND(AVG(t.tip_percentage), 2) AS avg_tip_percent
        FROM trips t
        JOIN zones z_pu ON t.PULocationID = z_pu.zone_id
        JOIN payment_types pt ON t.payment_type = pt.payment_type_id
        {where_clause}
        GROUP BY pt.payment_name
        ORDER BY total_trips DESC
        """
        cursor.execute(tipping_query, params)
        tipping_trends = [dict(row) for row in cursor.fetchall()]
        
        # Merge all data into one json payload
        response_data = {
            "kpis": kpis,
            "hourly_trends": hourly_trends,
            "top_zones": top_zones,
            "tipping_trends": tipping_trends
        }
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Database query error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # Automated ETL Pipeline Integration
    if not os.path.exists('../data/nyc_mobility.db') and not os.path.exists('../data/nyc_mobility_deploy.db'):
        print("Database not found! Running data cleaning and processing pipeline...")
        print("Step 1: Data Integrity Cleaning...")
        data_integrity.main()
        print("Step 2: Normalization & Feature Engineering...")
        normalization_feature_engineering.main()
        print("Step 3: Database Loader...")
        db_loader.main()
        print("ETL Pipeline completed. Database is ready.")

    # Eventually  the server is started locally on port 5000
    print("Starting flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)


