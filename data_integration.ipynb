import pandas as pd

# 1. Load the raw datasets
print("Loading data...")
zone_df = pd.read_csv('data/taxi_zone_lookup.csv')
trip_df = pd.read_csv('data/yellow_tripdata.csv')

# 2. Integrate the Pick-Up Location Data
# This merges the dictionary (zone_df) with our logbook (trip_df)
merged_df = trip_df.merge(zone_df, left_on='PULocationID', right_on='LocationID', how='left')
merged_df = merged_df.rename(columns={
    'Borough': 'PU_Borough', 
    'Zone': 'PU_Zone', 
    'service_zone': 'PU_service_zone'
})

# 3. Integrate the Drop-Off Location Data
merged_df = merged_df.merge(zone_df, left_on='DOLocationID', right_on='LocationID', how='left')
merged_df = merged_df.rename(columns={
    'Borough': 'DO_Borough', 
    'Zone': 'DO_Zone', 
    'service_zone': 'DO_service_zone'
})

# Clean up: Drop the redundant 'LocationID' columns we got from the merge
merged_df = merged_df.drop(columns=['LocationID_x', 'LocationID_y'], errors='ignore')

# 4. Display the successfully integrated data
print("Data Integration Complete!")
merged_df.head()

