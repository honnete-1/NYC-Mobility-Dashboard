# I started by importing  the libraries i need for pandas, pyarrow, and JSON logging
import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import json
import os
import gc


def main():

    # I defined my paths for input CSV and clean output Parquet
    raw_csv_path = '../data/yellow_tripdata.csv'
    parquet_path = '../data/yellow_tripdata_clean.parquet'

    # I started with  a simple print to check raw file size
    file_size_mb = os.path.getsize(raw_csv_path) / (1024 * 1024)
    print(f"Raw CSV size: {file_size_mb:.2f} MB")

    # I used variables to keep track of total rows and clean rows
    initial_row_count = 0
    cleaned_row_count = 0

    # I created a  dictionary to hold the counts of bad data i removed
    anomaly_counts = {
        "wrong_year_month": 0,
        "pickup_after_dropoff": 0,
        "negative_duration": 0,
        "extreme_duration": 0,
        "invalid_distance": 0,
        "invalid_fare": 0,
        "invalid_total": 0,
        "invalid_passengers": 0,
        "duplicate_rows": 0
    }

    # I then created  empty lists to store sample bad rows for my report
    anomaly_samples = {k: [] for k in anomaly_counts.keys()}

    print("Starting clean up...")

    writer = None
    chunksize = 1000000  # Load 1M rows at a time so we don't run out of memory

    # I read the CSV file in chunks
    for chunk_idx, df in enumerate(pd.read_csv(raw_csv_path, chunksize=chunksize)):
        chunk_rows = len(df)
        initial_row_count += chunk_rows
        print(f"Working on chunk {chunk_idx + 1} ({chunk_rows:,} rows)...")

        # 1. I filled nulls in congestion surcharge with 0.0
        df['congestion_surcharge'] = df['congestion_surcharge'].fillna(0.0)

        # 2. I converted pickup and dropoff times to datetimes
        df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
        df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])

        # Get trip duration in minutes
        trip_duration_min = (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']).dt.total_seconds() / 60.0

        # 3. Define masks for all the bad data we want to drop
        # Trips must be strictly in January 2019
        wrong_year_month = (df['tpep_pickup_datetime'].dt.year != 2019) | (df['tpep_pickup_datetime'].dt.month != 1)

        # Pickup cannot be after dropoff
        pickup_after_dropoff = df['tpep_pickup_datetime'] > df['tpep_dropoff_datetime']

        # Durations should be positive and under 3 hours (180 minutes)
        negative_duration = trip_duration_min <= 0
        extreme_duration = trip_duration_min > 180.0

        # Trip distance must be positive and under 100 miles
        invalid_distance = (df['trip_distance'] <= 0) | (df['trip_distance'] > 100.0)

        # Fare and total amounts must be positive and reasonable
        invalid_fare = (df['fare_amount'] <= 0) | (df['fare_amount'] > 500.0)
        invalid_total = (df['total_amount'] <= 0) | (df['total_amount'] > 1000.0)

        # Passenger count must be between 1 and 6
        invalid_passengers = (df['passenger_count'] == 0) | (df['passenger_count'] > 6)

        # Update total anomaly counts
        anomaly_counts["wrong_year_month"] += int(wrong_year_month.sum())
        anomaly_counts["pickup_after_dropoff"] += int(pickup_after_dropoff.sum())
        anomaly_counts["negative_duration"] += int(negative_duration.sum())
        anomaly_counts["extreme_duration"] += int(extreme_duration.sum())
        anomaly_counts["invalid_distance"] += int(invalid_distance.sum())
        anomaly_counts["invalid_fare"] += int(invalid_fare.sum())
        anomaly_counts["invalid_total"] += int(invalid_total.sum())
        anomaly_counts["invalid_passengers"] += int(invalid_passengers.sum())

        # Grab some examples of each error type for the documentation report
        masks = {
            "wrong_year_month": wrong_year_month,
            "pickup_after_dropoff": pickup_after_dropoff,
            "negative_duration": negative_duration,
            "extreme_duration": extreme_duration,
            "invalid_distance": invalid_distance,
            "invalid_fare": invalid_fare,
            "invalid_total": invalid_total,
            "invalid_passengers": invalid_passengers
        }

        for name, mask in masks.items():
            if len(anomaly_samples[name]) < 10 and mask.any():
                needed = 10 - len(anomaly_samples[name])
                sample_rows = df[mask].head(needed).copy()
                # Convert datetimes to strings to avoid json errors
                sample_rows['tpep_pickup_datetime'] = sample_rows['tpep_pickup_datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
                sample_rows['tpep_dropoff_datetime'] = sample_rows['tpep_dropoff_datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
                anomaly_samples[name].extend(sample_rows.to_dict(orient='records'))

        # Combine masks to drop bad rows
        all_anomalies = (
            wrong_year_month |
            pickup_after_dropoff |
            negative_duration |
            extreme_duration |
            invalid_distance |
            invalid_fare |
            invalid_total |
            invalid_passengers
        )

        # Filter the chunk
        df_clean_chunk = df[~all_anomalies].copy()

        # Drop duplicates on key columns. The validation test checks these key columns specifically.
        dupe_mask = df_clean_chunk.duplicated(subset=['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'PULocationID', 'DOLocationID'], keep='first')
        anomaly_counts["duplicate_rows"] += int(dupe_mask.sum())

        # Save some examples of duplicates too
        if len(anomaly_samples["duplicate_rows"]) < 10 and dupe_mask.any():
            needed = 10 - len(anomaly_samples["duplicate_rows"])
            sample_rows = df_clean_chunk[dupe_mask].head(needed).copy()
            sample_rows['tpep_pickup_datetime'] = sample_rows['tpep_pickup_datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
            sample_rows['tpep_dropoff_datetime'] = sample_rows['tpep_dropoff_datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
            anomaly_samples["duplicate_rows"].extend(sample_rows.to_dict(orient='records'))

        # Remove the duplicate rows
        df_clean_chunk = df_clean_chunk[~dupe_mask].copy()
        cleaned_row_count += len(df_clean_chunk)

        # Drop the trip_duration_min column so the exported schema remains identical to the raw schema
        df_clean_chunk = df_clean_chunk.drop(columns=['trip_duration_min'], errors='ignore')

        # Stream write this chunk to the output parquet file
        table = pa.Table.from_pandas(df_clean_chunk, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(parquet_path, table.schema, compression='snappy')
        writer.write_table(table)

        # Free memory
        del df, df_clean_chunk, table, all_anomalies, wrong_year_month, pickup_after_dropoff
        del negative_duration, extreme_duration, invalid_distance, invalid_fare, invalid_total, invalid_passengers, trip_duration_min
        gc.collect()

    # Close the parquet writer
    if writer is not None:
        writer.close()

    print("Chunked cleaning is all done!")

    # Package everything into a dict
    transparency_log = {
        "initial_row_count": initial_row_count,
        "anomaly_counts": anomaly_counts,
        "samples": anomaly_samples
    }

    # Write dictionary to a JSON file
    with open('../data/data_cleaning_log.json', 'w') as f:
        json.dump(transparency_log, f, indent=4)

    rows_removed = initial_row_count - cleaned_row_count
    pct_removed = (rows_removed / initial_row_count) * 100

    # Print clean report summary
    print("=== Cleaning Summary ===")
    print(f"Total Raw Rows: {initial_row_count:,}")
    print(f"Total Clean Rows: {cleaned_row_count:,}")
    print(f"Rows Dropped: {rows_removed:,} ({pct_removed:.2f}%)")

    print("\nCounts for each type of anomaly:")
    for k, v in anomaly_counts.items():
        print(f" - {k:22}: {v:,} rows ({v/initial_row_count*100:.4f}%)")

    print("\nLoading cleaned Parquet file to verify results...")
    df_verified = pd.read_parquet(parquet_path)

    # Verify nulls and key-column duplicates match what verify_clean_data.py checks
    print("Null count in cleaned data:", df_verified.isnull().sum().sum())
    print("Duplicate count on key columns:", df_verified.duplicated(subset=['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'PULocationID', 'DOLocationID']).sum())

    # Check dates are in Jan 2019 only
    pickup_dt_clean = pd.to_datetime(df_verified['tpep_pickup_datetime'])
    print(f"Unique Years in clean pickup: {pickup_dt_clean.dt.year.unique()}")
    print(f"Unique Months in clean pickup: {pickup_dt_clean.dt.month.unique()}")

    # Check range boundaries
    print(f"Trip Distance range: {df_verified['trip_distance'].min():.2f} to {df_verified['trip_distance'].max():.2f}")
    print(f"Fare Amount range: ${df_verified['fare_amount'].min():.2f} to ${df_verified['fare_amount'].max():.2f}")
    print(f"Total Amount range: ${df_verified['total_amount'].min():.2f} to ${df_verified['total_amount'].max():.2f}")
    print(f"Passenger Count range: {df_verified['passenger_count'].min()} to {df_verified['passenger_count'].max()}")

if __name__ == '__main__':
    main()

