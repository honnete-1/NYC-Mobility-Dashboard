# NYC Urban Mobility — Taxi Trends & Analytics Dashboard

[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](#)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](#)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](#)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](#)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](#)
[![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](#)
[![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](#)

NYC Urban Mobility is an enterprise-grade full-stack analytics dashboard built to process, clean, and visualize over **7.4 million yellow taxi rides** from New York City in January 2019. The application runs a full ETL pipeline on raw datasets, integrates geospatial metadata from TLC shapefiles, stores clean records in a normalized SQLite database, and serves real-time insights through a Python Flask REST API to a beautifully styled, fully interactive vanilla JavaScript dashboard.

**Live Demo:** [https://nyc-mobility-dashboard.vercel.app/](https://nyc-mobility-dashboard.vercel.app/) &nbsp;|&nbsp; **Video Demo:** [▶ Watch on Loom — Coming Soon](#)

---

## Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Local Setup & Installation](#-local-setup--installation)
- [Environment Setup](#-environment-setup)
- [Running the Backend](#-running-the-backend)
- [Running the Frontend](#-running-the-frontend)
- [Database Design & ERD](#-database-design--erd)
- [Data Integrity & Cleaning Log](#-data-integrity--cleaning-log)
- [Custom DSA Algorithm](#-custom-dsa-algorithm-min-heap)
- [Group Participation & Reflection](#-group-participation--reflection)

---

## Features

- **Interactive Filters:** Dynamically query rides by Borough, Hour of Day, and TLC Rate Code with no page reloads.
- **Dual Visual Themes:** Fully reactive Light/Dark mode switcher. All ApexCharts update their color scheme on-the-fly without refreshing.
- **KPI Metrics Panel:** Instant counters showing Total Trips, Average Fares, Tipping Percentage, and Average Speed.
- **ApexCharts Visualizations:**
  - *Hourly Congestion Chart:* Line/Column combo chart showing the inverse relationship between trip volume and vehicle speed throughout the day.
  - *Top 10 Busiest Pickup Zones Chart:* Horizontal bar chart rendering the top neighborhoods, ranked using a custom Min-Heap algorithm (not a library sort).
  - *Tipping Behavior Chart:* Column chart comparing average tip percentages across credit card and cash payment methods.
- **Precomputed Cache:** The default dashboard view loads from a precomputed JSON file for instantaneous page load, bypassing live database queries on first render.
- **Spatial Metadata:** The `zones` table holds geospatial properties (`Shape_Area`, `Shape_Length`) programmatically merged from official TLC shapefiles using GeoPandas.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, Vanilla CSS3 (Custom Variables), JavaScript ES6+, ApexCharts.js |
| **Backend** | Python 3, Flask (REST API), Flask-CORS |
| **Database** | SQLite3 (Star Schema, B-Tree Indexes, WAL Mode) |
| **Data Engineering** | Pandas (Chunked Processing), GeoPandas (Shapefile Merging), PyArrow (Parquet) |
| **Deployment** | Vercel (Serverless Python Functions + Edge CDN for Static Assets) |

---

## Project Structure

```text
NYC_Taxi_Project/
│
├── backend/                                  # Python Backend & Data Pipeline
│   ├── algorithms.py                         # Custom Min-Heap DSA (built from scratch)
│   ├── app.py                                # Flask server, CORS, and API endpoints
│   ├── db_schema.py                          # Database schema and lookup table definitions
│   ├── db_loader.py                          # Chunked Parquet-to-SQLite loader
│   ├── data_integrity.py                     # CSV cleaner: anomaly detection and removal
│   ├── normalization_feature_engineering.py  # Feature calculator: speed, duration, tip %
│   ├── query_database.py                     # SQL verification and testing scripts
│   ├── verify_clean_data.py                  # Automated post-cleaning validation checklist
│   └── generate_db_deploy.py                 # Generates the 50k-row deployment database
│
├── Frontend/                                 # Vanilla Web Interface
│   ├── index.html                            # Dashboard HTML structure (Semantic HTML5)
│   ├── styles.css                            # Custom CSS system with light/dark variables
│   ├── app.js                                # Fetch API calls and ApexCharts rendering
│   └── nyc_taxi_trails.png                   # Background hero image
│
├── data/                                     # Data Storage (partially Git-Ignored)
│   ├── taxi_zones/                           # TLC Shapefiles (Git-Ignored)
│   ├── taxi_zone_lookup.csv                  # Zone-to-Borough dimension mapping
│   ├── nyc_mobility_deploy.db               # ✅ 50k-row deployment database (committed)
│   ├── dashboard_cache.json                  # ✅ Precomputed home view cache (committed)
│   ├── data_cleaning_log.json                # ✅ Anomaly removal audit log (committed)
│   ├── yellow_tripdata.csv                   # ❌ Raw data 680MB (Git-Ignored)
│   └── nyc_mobility.db                       # ❌ Full database 1.4GB (Git-Ignored)
│
├── api/
│   └── index.py                              # Vercel serverless Python entry point
├── vercel.json                               # Vercel rewrite and routing configuration
├── requirements.txt                          # Deployment dependencies for Vercel
└── README.md                                 # Project documentation (this file)
```

---

## Local Setup & Installation

> **Good news:** This project is fully runnable out-of-the-box using the pre-seeded **50k-row deployment database** (`nyc_mobility_deploy.db`) that is already committed in the `data/` folder. You do **not** need to download the 680MB raw dataset to run and test the full dashboard!

### 1. Prerequisites

Ensure you have the following installed:
- **Python 3.8+** — [Download Python](https://www.python.org/downloads/)
- **Git** — [Download Git](https://git-scm.com/downloads)

Check your Python version:
```bash
python --version
```

---

### 2. Clone the Repository

```bash
git clone https://github.com/honnete-1/NYC-Mobility-Dashboard.git
cd NYC-Mobility-Dashboard
```

---

## Environment Setup

### 3. (Recommended) Create a Virtual Environment
This keeps the project dependencies isolated from your system Python:

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install All Dependencies

```bash
pip install Flask flask-cors pandas geopandas pyarrow numpy fpdf2
```

Or install the core deployment dependencies only:
```bash
pip install -r requirements.txt
```

---

## Running the Backend

The Flask backend serves both the API and the frontend static files. Running it is a single command:

```bash
cd backend
python app.py
```

**What happens when you run this:**
1. The server checks whether a database exists in `data/`.
2. If it finds `nyc_mobility_deploy.db` (the pre-seeded deployment database), it boots immediately.
3. If **neither** database is found, it automatically runs the full ETL pipeline to build the database from the raw CSV file (requires the 680MB raw dataset to be in `data/`).
4. Flask starts serving on port `5000`.

Expected output:
```
Starting flask server on port 5000...
 * Running on http://0.0.0.0:5000
```

---

## Running the Frontend

Because the Flask backend is configured to serve the frontend static files directly, there is **no separate frontend server** needed.

Once the backend is running, open your browser and go to:

```
http://127.0.0.1:5000/
```

The full dashboard will load automatically. The frontend JavaScript (`app.js`) connects to the Flask API at the same origin, so no environment variable configuration is needed.

> **Deployed version:** The live production site is available at:
> [https://nyc-mobility-dashboard.vercel.app/](https://nyc-mobility-dashboard.vercel.app/)

---

## Database Design & ERD

The database is structured as a **Star Schema** — a widely used data warehousing design that minimizes data redundancy and maximizes query efficiency.

- **Central Fact Table (`trips`):** Contains all 22 transactional and computed columns per ride.
- **Dimension Tables (`vendors`, `rate_codes`, `payment_types`, `zones`):** Contain descriptive lookup data. The `zones` table also holds spatial attributes (`shape_area`, `shape_length`) merged from TLC shapefiles using GeoPandas.

### Entity-Relationship Diagram (ERD)

Link to the ERD database diagram:
[![Database Entity-Relationship Diagram](https://drive.google.com/uc?export=view&id=11316UQHCZQ2KdGGQpVlvJk1FTeFgQH88)](https://drive.google.com/file/d/11316UQHCZQ2KdGGQpVlvJk1FTeFgQH88/view?usp=sharing)



### Query Optimizations

| Optimization | Detail |
| :--- | :--- |
| **B-Tree Index on `tpep_pickup_datetime`** | Enables fast hour-of-day filtering |
| **B-Tree Index on `PULocationID`** | Enables fast borough and pickup zone filtering |
| **B-Tree Index on `DOLocationID`** | Enables fast dropoff zone filtering |
| **`PRAGMA journal_mode = WAL`** | Write-Ahead Logging for faster concurrent reads |
| **`PRAGMA temp_store = MEMORY`** | Stores temporary results in RAM instead of disk |

---

## Data Integrity & Cleaning Log

We removed **198,392 rows** (2.59% of the dataset) due to data quality issues. The full cleaning log is stored in `data/data_cleaning_log.json`.

| Anomaly Class | Rows Removed | Validation Rule |
| :--- | :--- | :--- |
| **Wrong Year/Month** | 537 | Pickup datetime must be within January 2019 |
| **Pickup After Dropoff** | 4 | Dropoff time must be after pickup time |
| **Negative Duration** | 6,294 | Trip duration must be > 0 minutes |
| **Extreme Duration** | 20,913 | Trip duration must be ≤ 180 minutes (3 hours) |
| **Invalid Distance** | 54,802 | Trip distance must be > 0 and ≤ 100 miles |
| **Invalid Fare** | 9,591 | Fare amount must be > $0 and ≤ $500 |
| **Invalid Total** | 8,568 | Total charge must be > $0 and ≤ $1,000 |
| **Invalid Passengers** | 117,438 | Passenger count must be between 1 and 6 |
| **Duplicate Rows** | 34 | Exact duplicates on key columns removed |

---

## Custom DSA Algorithm: Min-Heap

To rank the **Top 10 Busiest Pickup Neighborhoods**, the backend uses a fully custom **Min-Heap (Priority Queue)** implemented from scratch in `backend/algorithms.py`. This was a core project requirement — no standard sorting library functions were used.

### How It Works

```
Stream all 263 NYC zone trip counts
         ↓
For each zone count:
   ├── If heap size < K (10)   → Push onto heap
   └── If zone count > heap root → Replace root, sift down
         ↓
Extract the top 10 elements sorted in descending order
```

### Complexity Analysis

| Metric | This Algorithm | Standard `sort()` |
| :--- | :--- | :--- |
| **Time** | $O(N \log K)$ | $O(N \log N)$ |
| **Space** | $O(K)$ — constant | $O(N)$ |
| **Where** | N = 263 zones, K = 10 | N = 263 zones |

---

## Group Participation & Reflection

### Team Members & Roles

| Team Member | Role & Responsibilities |
| :--- | :--- |
| **Student A (Honnete)** | Backend development (`app.py`), database schema design (`db_schema.py`), ETL data pipeline, custom Min-Heap algorithm (`algorithms.py`), Vercel deployment |
| **Student B (Emmanuella)** | Frontend interface (`index.html`, `styles.css`), ApexCharts integration, API integration (`app.js`), Light/Dark theme system |

### What We Learned

- **Data Scale Challenges:** Processing 7.4M rows on a laptop required chunk-based reading. We learned how to use `chunksize` in Pandas to keep memory stable.
- **Relational Design Pays Off:** Designing the Star Schema upfront made query writing straightforward. Without it, our SQL would have been slow and messy.
- **Cloud vs. Local Differences:** Deploying on Vercel taught us that Linux servers are case-sensitive (unlike Windows). A folder named `Frontend` vs `frontend` caused 404 errors in production.
- **Caching is Powerful:** Pre-computing the default dashboard view into a JSON file made page loads feel instant—a small engineering decision with a huge user experience payoff.
