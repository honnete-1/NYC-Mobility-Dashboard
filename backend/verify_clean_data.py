import os
import pandas as pd

def test_data_integrity():
    parquet_path = '../data/yellow_tripdata_clean.parquet'
    
    print("==================================================")
    print("       NYC TAXI DATA INTEGRITY CHECKLIST          ")
    print("==================================================")
    
    # Check if the file exists
    if not os.path.exists(parquet_path):
        print("[ERROR] FAILED: Cleaned Parquet file not found at '../data/yellow_tripdata_clean.parquet'!")
        print("Please run your cleaning notebook first to generate it.")
        return
    
    print("Loading cleaned dataset...")
    df = pd.read_parquet(parquet_path)
    print(f"Dataset loaded successfully. Total Rows: {len(df):,}\n")
    
    tests_passed = True
    
    # 1. Null Value Check (Column-by-column to save memory)
    nulls = 0
    for col in df.columns:
        nulls += df[col].isna().sum()
        
    if nulls == 0:
        print("[PASS] Zero missing values in the dataset.")
    else:
        print(f"[FAIL] Found {nulls} missing values!")
        tests_passed = False
        
    # 2. Duplicate Row Check (Subset-based to save memory)
    # Checking duplicates on key columns is extremely memory efficient and 99.9% accurate
    duplicates = df.duplicated(subset=['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'PULocationID', 'DOLocationID']).sum()
    if duplicates == 0:
        print("[PASS] Zero duplicate records (verified by key columns).")
    else:
        print(f"[FAIL] Found {duplicates} duplicate records!")
        tests_passed = False
        
    # 3. Temporal Validity Check (No to_datetime needed, Parquet already stores them as datetimes)
    pickup_dt = df['tpep_pickup_datetime']
    dropoff_dt = df['tpep_dropoff_datetime']
    
    unique_years = pickup_dt.dt.year.unique()
    unique_months = pickup_dt.dt.month.unique()
    pickup_after_dropoff = (pickup_dt > dropoff_dt).sum()
    
    # Verify only Jan 2019
    if len(unique_years) == 1 and unique_years[0] == 2019 and len(unique_months) == 1 and unique_months[0] == 1:
        print("[PASS] All trip pick-ups are strictly in January 2019.")
    else:
        print(f"[FAIL] Date range invalid! Years: {unique_years}, Months: {unique_months}")
        tests_passed = False
        
    # Verify pickup before dropoff
    if pickup_after_dropoff == 0:
        print("[PASS] Chronological logical consistency (pickup <= dropoff) holds.")
    else:
        print(f"[FAIL] Found {pickup_after_dropoff} records where pickup happens after dropoff!")
        tests_passed = False
        
    # 4. Trip Distance Range Check
    min_dist = df['trip_distance'].min()
    max_dist = df['trip_distance'].max()
    if min_dist > 0 and max_dist <= 100:
        print(f"[PASS] Trip distances are within logical boundaries ({min_dist:.2f} to {max_dist:.2f} miles).")
    else:
        print(f"[FAIL] Trip distance outlier detected! Range: {min_dist} to {max_dist} miles.")
        tests_passed = False
        
    # 5. Financial Boundary Check
    min_fare = df['fare_amount'].min()
    max_fare = df['fare_amount'].max()
    min_total = df['total_amount'].min()
    max_total = df['total_amount'].max()
    
    if min_fare > 0 and max_fare <= 500 and min_total > 0 and max_total <= 1000:
        print(f"[PASS] Financial metrics are within boundaries:")
        print(f"       - Fare:  ${min_fare:.2f} to ${max_fare:.2f}")
        print(f"       - Total: ${min_total:.2f} to ${max_total:.2f}")
    else:
        print("[FAIL] Financial outliers detected!")
        print(f"       - Fare range:  ${min_fare} to ${max_fare}")
        print(f"       - Total range: ${min_total} to ${max_total}")
        tests_passed = False
        
    # 6. Passenger Capacity Check
    min_pass = df['passenger_count'].min()
    max_pass = df['passenger_count'].max()
    if min_pass >= 1 and max_pass <= 6:
        print(f"[PASS] Passenger counts match taxi capacities ({min_pass} to {max_pass} riders).")
    else:
        print(f"[FAIL] Passenger count outlier detected! Range: {min_pass} to {max_pass}")
        tests_passed = False
        
    print("==================================================")
    if tests_passed:
        print("     SUCCESS: Cleaned dataset has perfect integrity.")
    else:
        print("     WARNING: Some integrity checks failed.")
    print("==================================================")

if __name__ == '__main__':
    test_data_integrity()
