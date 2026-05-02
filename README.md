# IMDb Lambda Trailer Project

Tracks IMDb's trending trailers over time using three AWS Lambda functions that run on a scheduled basis. Each function scrapes or aggregates data and stores results in MongoDB Atlas — building a rolling record of what trailers were trending daily, weekly, and monthly.

---

## Architecture

```mermaid
flowchart TD
    IMDB["IMDb Trailers Page"]
    WTAPI["WorldTimeAPI\n(Asia/Kolkata)"]
    dev["default/main_script.py\n(local dev)"]

    subgraph daily_sub [Daily Lambda]
        daily["daily/lambda_function.py"]
    end

    subgraph weekly_sub [Weekly Lambda]
        weekly["weekly/lambda_function.py"]
    end

    subgraph monthly_sub [Monthly Lambda]
        monthly["monthly/lambda_function.py"]
    end

    subgraph mongo [MongoDB Atlas — imdb_trailer]
        col_daily[("daily collection")]
        col_weekly[("weekly collection")]
        col_monthly[("monthly collection")]
    end

    IMDB -->|"scrape titles"| daily
    WTAPI -->|"IST timestamp"| daily
    daily -->|"upsert by date/month/year"| col_daily

    col_daily -->|"find by week_number"| weekly
    weekly -->|"upsert by week_number"| col_weekly

    col_weekly -->|"find by month"| monthly
    monthly -->|"upsert by month+year"| col_monthly

    IMDB -->|"scrape titles"| dev
    WTAPI -->|"IST timestamp"| dev
    dev -->|"insert_one"| col_daily
```

---

## Project Structure

```
imdb-lambda-trailer-project/
├── common/                        # Shared package — bundled into every Lambda zip
│   ├── __init__.py
│   ├── config.py                  # DB name, collection names, API URLs
│   ├── db.py                      # get_db() — returns MongoDB database handle
│   ├── date_time_extractor.py     # WorldTimeAPI helper → generate_time_data()
│   └── trailer_scraper.py         # IMDb scraper → generate_data() → list[str]
├── daily/
│   └── lambda_function.py         # Scrape + upsert one doc per calendar day
├── weekly/
│   └── lambda_function.py         # Aggregate daily docs for current ISO week
├── monthly/
│   └── lambda_function.py         # Aggregate weekly docs for current month
├── default/
│   └── main_script.py             # Local dev script (no Lambda wrapper)
└── requirements.txt               # Third-party dependencies
```

---

## Prerequisites

- Python 3.11
- An AWS account with permissions to create Lambda functions and layers
- A MongoDB Atlas cluster (free tier works)
- `MONGO_URI` connection string for your Atlas cluster

---

## Environment Variables

Each Lambda function requires one environment variable, set in the AWS Console under **Configuration → Environment variables**:

| Variable | Description |
|---|---|
| `MONGO_URI` | MongoDB Atlas connection string (e.g. `mongodb+srv://user:pass@cluster.mongodb.net`) |

---

## Step 1 — Build the Dependency Layer

The third-party packages (`pymongo`, `requests`, `beautifulsoup4`, `lxml`, `pytz`) must be bundled as a Lambda Layer because they are not included in the default Lambda runtime.

> The layer zip **must** have a `python/` folder at its root. Lambda mounts the layer at `/opt/`, so packages land at `/opt/python/` and are automatically on `sys.path`.

### Method A — AWS CloudShell (recommended)

CloudShell runs on Amazon Linux x86_64 — the same OS as Lambda — so native packages like `lxml` compile correctly without any cross-compilation flags.

1. Open [AWS CloudShell](https://console.aws.amazon.com/cloudshell) from the AWS Console.
2. Upload `requirements.txt` using the **Actions → Upload file** button.
3. Run:

```bash
mkdir -p python
pip install -r requirements.txt -t python/
zip -r layer.zip python/
```

4. Download `layer.zip` via **Actions → Download file**.
5. In the AWS Console go to **Lambda → Layers → Create layer**:
   - Name: e.g. `imdb-trailer-deps`
   - Upload `layer.zip`
   - Compatible runtimes: **Python 3.11**

---

### Method B — macOS

macOS-compiled native extensions will crash on Lambda's Linux environment. Use pip's cross-compilation flags to build Linux-compatible wheels:

```bash
mkdir -p python
pip install -r requirements.txt \
    -t python/ \
    --platform manylinux2014_x86_64 \
    --python-version 3.11 \
    --only-binary=:all: \
    --implementation cp
zip -r layer.zip python/
```

Upload `layer.zip` as described in step 5 of Method A.

---

### Method C — Windows

Run the following in **Command Prompt** or **PowerShell**:

```bat
mkdir python
pip install -r requirements.txt ^
    -t python/ ^
    --platform manylinux2014_x86_64 ^
    --python-version 3.11 ^
    --only-binary=:all: ^
    --implementation cp
```

Then zip the `python/` folder (right-click → Send to → Compressed folder, or use any zip tool) and upload as described in step 5 of Method A.

---

The resulting layer zip structure should look like:

```
layer.zip
└── python/
    ├── pymongo/
    ├── requests/
    ├── bs4/
    ├── lxml/
    └── pytz/
    └── ... (other package files)
```

---

## Step 2 — Package Each Lambda Function

Each Lambda zip must contain `lambda_function.py` and the `common/` folder **at the same level** (not nested inside a subfolder), so that `from common.config import ...` resolves correctly at runtime.

### macOS / Linux

```bash
# Run from the repo root

# Daily
zip -j daily_function.zip daily/lambda_function.py
zip -r daily_function.zip common/

# Weekly
zip -j weekly_function.zip weekly/lambda_function.py
zip -r weekly_function.zip common/

# Monthly
zip -j monthly_function.zip monthly/lambda_function.py
zip -r monthly_function.zip common/
```

### Windows (PowerShell)

```powershell
# Daily
Compress-Archive -Path daily\lambda_function.py, common -DestinationPath daily_function.zip

# Weekly
Compress-Archive -Path weekly\lambda_function.py, common -DestinationPath weekly_function.zip

# Monthly
Compress-Archive -Path monthly\lambda_function.py, common -DestinationPath monthly_function.zip
```

Each zip should have this structure (example for `daily`):

```
daily_function.zip
├── lambda_function.py
└── common/
    ├── __init__.py
    ├── config.py
    ├── db.py
    ├── date_time_extractor.py
    └── trailer_scraper.py
```

Upload each zip in the AWS Console: **Lambda → [function name] → Code → Upload from → .zip file**.

---

## Step 3 — Attach the Layer

For each of the three Lambda functions:

1. Open the function in the AWS Console.
2. Go to **Configuration → Layers → Add a layer**.
3. Select **Custom layers**, choose `imdb-trailer-deps`, and select the latest version.
4. Click **Save**.

---

## Step 4 — Set the Environment Variable

For each function: **Configuration → Environment variables → Edit → Add environment variable**:

- Key: `MONGO_URI`
- Value: your Atlas connection string

---

## Deployment Order

The functions are independent Lambdas but their **data depends on each other**. Always invoke them in this order for a given time period:

| Order | Function | What it does |
|---|---|---|
| 1 | `daily` | Scrapes IMDb and writes one doc per day to `daily` |
| 2 | `weekly` | Reads `daily` for the current ISO week, writes to `weekly` |
| 3 | `monthly` | Reads `weekly` for the current month, writes to `monthly` |

Configure EventBridge (CloudWatch Events) rules to trigger them in this sequence — for example: daily at 23:55 IST, weekly on Sunday at 23:58 IST, monthly on the last day of the month.

---

## Local Development

Use `default/main_script.py` to test the scraper and MongoDB connection without deploying to Lambda.

```bash
# From the repo root
pip install -r requirements.txt

export MONGO_URI="your_connection_string"   # macOS/Linux
# set MONGO_URI=your_connection_string      # Windows CMD

python -m default.main_script
```

This runs the same daily scrape-and-insert logic (without the Lambda handler wrapper) and is useful for verifying that the IMDb selectors still work and that MongoDB connectivity is healthy before deploying updates.

---

## MongoDB Schema

### `daily` collection

```json
{
  "timestamp": "2026-05-02T23:55:00.000+05:30",
  "day_of_week": "Saturday",
  "day_of_week_number": 6,
  "week_number": 18,
  "date": 2,
  "month": 5,
  "year": 2026,
  "details": ["Movie Title A", "Movie Title B", "..."]
}
```

### `weekly` collection

```json
{
  "record_time": "2026-05-03T23:58:00.000+05:30",
  "week_number": 18,
  "week_range": [1, 2, 3, 4, 5],
  "month": 5,
  "year": 2026,
  "details": { "Movie Title A": 5, "Movie Title B": 3 }
}
```

### `monthly` collection

```json
{
  "record_time": "2026-05-31T23:59:00.000+05:30",
  "month": 5,
  "year": 2026,
  "details": { "Movie Title A": 18, "Movie Title B": 11 }
}
```
