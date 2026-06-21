# I imported the libraries i need
import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import os
import gc


def main():

    # I then defined the file paths
    input_parquet_path = '../data/yellow_tripdata_clean.parquet'
    output_parquet_path = '../data/yellow_tripdata_final.parquet'

    print(f"Loading cleaned Parquet file from: {input_parquet_path}...")
    df = pd.read_parquet(input_parquet_path)
    print(f"Loaded successfully. Total rows: {len(df):,}")

    # Normalization to create database ready data types
    print("\nRunning normalization on data types...")

    # I cast float identifiers and counts to smaller integers to save space
    df['VendorID'] = df['VendorID'].astype('int8')
    df['RatecodeID'] = df['RatecodeID'].astype('int8')
    df['passenger_count'] = df['passenger_count'].astype('int8')
    df['payment_type'] = df['payment_type'].astype('int8')

    # I then cast Location IDs to 32-bit integers
    df['PULocationID'] = df['PULocationID'].astype('int32')
    df['DOLocationID'] = df['DOLocationID'].astype('int32')

    # I cast high-cardinality string flags to categorical type
    df['store_and_fwd_flag'] = df['store_and_fwd_flag'].astype('category')

    print("Data types normalized successfully!")
    print(df[['VendorID', 'RatecodeID', 'passenger_count', 'PULocationID', 'DOLocationID', 'payment_type']].dtypes)


    #  Part 2: Feature Engineering
    print("\nRunning feature engineering...")

    # Feature 1: Trip Duration in minutes
    df['trip_duration_min'] = (
        pd.to_datetime(df['tpep_dropoff_datetime']) - pd.to_datetime(df['tpep_pickup_datetime'])
    ).dt.total_seconds() / 60.0

    # Feature 2: Average Speed in MPH
    # Justification: Tells us about traffic congestion patterns.
    df['average_speed_mph'] = df['trip_distance'] / (df['trip_duration_min'] / 60.0)

    # Feature 3: Tipping Percentage
    # Justification: Provides economic insights into customer tipping behaviors.
    df['tip_percentage'] = (df['tip_amount'] / df['fare_amount']) * 100

    print("Derived features created successfully!")


    #  Part 3: Export the Final Cleaned & Normalised Data 
    print(f"\nSaving final dataset to Parquet: {output_parquet_path}...")

    # Export to snappy-compressed parquet
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, output_parquet_path, compression='snappy')

    print("Export completed successfully!")

    # Print summary statistics of our new features to verify
    print("\n=== Feature Statistics ===")
    print(f"Trip Duration (minutes): min={df['trip_duration_min'].min():.2f}, mean={df['trip_duration_min'].mean():.2f}, max={df['trip_duration_min'].max():.2f}")
    print(f"Average Speed (mph):      min={df['average_speed_mph'].min():.2f}, mean={df['average_speed_mph'].mean():.2f}, max={df['average_speed_mph'].max():.2f}")
    print(f"Tip Percentage (%):      min={df['tip_percentage'].min():.2f}%, mean={df['tip_percentage'].mean():.2f}%, max={df['tip_percentage'].max():.2f}%")

if __name__ == '__main__':
    main()
