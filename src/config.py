from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "online_retail.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
SQL_PATH = PROJECT_ROOT / "sql" / "business_queries.sql"

TRANSACTIONS_PARQUET = PROCESSED_DIR / "cleaned_transactions.parquet"
TRANSACTIONS_CSV_GZ = PROCESSED_DIR / "cleaned_transactions.csv.gz"
RFM_PARQUET = PROCESSED_DIR / "rfm_customers.parquet"
RECOMMENDATIONS_PARQUET = PROCESSED_DIR / "product_neighbors.parquet"
QUALITY_REPORT_PATH = PROCESSED_DIR / "data_quality_report.csv"
PROFILE_PATH = PROCESSED_DIR / "dataset_profile.json"
INSIGHTS_PATH = PROCESSED_DIR / "business_insights.json"
SQLITE_PATH = PROCESSED_DIR / "shopper_spectrum_summary.db"

ORIGINAL_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]

SEGMENT_COLORS = {
    "Champions": "#17C3B2",
    "Loyal Growth": "#4F7CFF",
    "Occasional": "#F6C85F",
    "At Risk": "#FF6B6B",
    "Guest / Unidentified": "#8B93A7",
}

PALETTE = ["#17C3B2", "#4F7CFF", "#A06CD5", "#F6C85F", "#FF6B6B", "#5DD39E"]

