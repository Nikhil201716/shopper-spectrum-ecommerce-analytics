from __future__ import annotations

import sys
from pathlib import Path

import nbformat as nbf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "notebooks" / "01_shopper_spectrum_analysis.ipynb"


def code(source: str):
    return nbf.v4.new_code_cell(source.strip())


def markdown(source: str):
    return nbf.v4.new_markdown_cell(source.strip())


notebook = nbf.v4.new_notebook()
notebook["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12"},
}
notebook["cells"] = [
    markdown(
        """
# 🛒 Shopper Spectrum
## Customer Segmentation and Product Recommendations in E-Commerce

I am **Nikhil Sinha**. In this notebook I reproduce the core data-quality, SQL, RFM, clustering, and product-affinity analysis used by my Streamlit application. My governing rule is to retain every source row and original value, then add transparent treatments rather than destructively deleting commercial events.
"""
    ),
    code(
        """
from pathlib import Path
import json
import sqlite3

import pandas as pd
import numpy as np
import plotly.express as px

PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "online_retail.csv"
PROCESSED = PROJECT_ROOT / "data" / "processed"
"""
    ),
    markdown("## 1. Source profile and row-preservation check"),
    code(
        """
raw = pd.read_csv(RAW_PATH, low_memory=False)
cleaned = pd.read_parquet(PROCESSED / "cleaned_transactions.parquet")
profile = json.loads((PROCESSED / "dataset_profile.json").read_text(encoding="utf-8"))

assert len(raw) == len(cleaned)
assert cleaned["SourceRowPreserved"].all()
profile
"""
    ),
    markdown(
        """
## 2. Preprocessing audit

I preserve missing values in the original columns. `CustomerKey`, `DescriptionClean`, transaction statuses, duplicate ranks, merchandise flags, and analytical eligibility fields explain how a row is used without overwriting the source.
"""
    ),
    code(
        """
quality = pd.read_csv(PROCESSED / "data_quality_report.csv")
quality
"""
    ),
    code(
        """
cleaned[[
    "RowID", "InvoiceNo", "Description", "DescriptionClean", "CustomerID",
    "CustomerKey", "TransactionStatus", "IsCanonicalRecord", "IsMerchandise",
    "GrossRevenue", "ReturnValue", "NetRevenue", "SourceRowPreserved"
]].sample(10, random_state=42)
"""
    ),
    markdown("## 3. Revenue quality and monthly trend"),
    code(
        """
kpis = {
    "gross_revenue": cleaned["GrossRevenue"].sum(),
    "return_value": cleaned["ReturnValue"].sum(),
    "net_revenue": cleaned["NetRevenue"].sum(),
    "orders": cleaned.loc[cleaned["IsAnalysisReadySale"], "InvoiceNo"].nunique(),
}
kpis
"""
    ),
    code(
        """
monthly = (cleaned.groupby("YearMonth", as_index=False)
           .agg(GrossRevenue=("GrossRevenue", "sum"),
                ReturnValue=("ReturnValue", "sum"),
                NetRevenue=("NetRevenue", "sum"))
           .sort_values("YearMonth"))
px.line(monthly, x="YearMonth", y=["GrossRevenue", "NetRevenue"], markers=True,
        title="Monthly gross and net revenue")
"""
    ),
    markdown("## 4. RFM customer segmentation"),
    code(
        """
rfm = pd.read_parquet(PROCESSED / "rfm_customers.parquet")
segment_profile = (rfm.groupby("Segment", as_index=False)
                   .agg(Customers=("CustomerKey", "count"),
                        AvgRecencyDays=("RecencyDays", "mean"),
                        AvgOrders=("FrequencyOrders", "mean"),
                        AvgCustomerValue=("MonetaryValue", "mean"),
                        HistoricalRevenue=("MonetaryValue", "sum")))
segment_profile
"""
    ),
    code(
        """
evaluation = pd.read_csv(PROCESSED / "cluster_evaluation.csv")
px.line(evaluation, x="K", y="SilhouetteScore", markers=True,
        title="Silhouette score by cluster count")
"""
    ),
    markdown(
        """
I select **K=4** for four operationally distinct CRM treatments. K=2 has stronger pure statistical separation, so I disclose the trade-off instead of claiming that silhouette alone chose the model.
"""
    ),
    code(
        """
sample = rfm.sample(min(3500, len(rfm)), random_state=42)
px.scatter_3d(sample, x="RecencyDays", y="FrequencyOrders", z="MonetaryValue",
              color="Segment", size="AverageOrderValue", log_y=True, log_z=True,
              hover_name="CustomerKey", title="3D RFM customer landscape")
"""
    ),
    markdown("## 5. Product affinity"),
    code(
        """
neighbors = pd.read_parquet(PROCESSED / "product_neighbors.parquet")
anchor = "WHITE HANGING HEART T-LIGHT HOLDER"
neighbors[neighbors["Product"].eq(anchor)].sort_values("Rank")
"""
    ),
    markdown("## 6. SQL result layer"),
    code(
        """
with sqlite3.connect(PROCESSED / "shopper_spectrum_summary.db") as connection:
    sql_segment_summary = pd.read_sql_query(
        "SELECT Segment, COUNT(*) AS Customers, ROUND(SUM(MonetaryValue), 2) AS Value "
        "FROM rfm_customers GROUP BY Segment ORDER BY Value DESC",
        connection,
    )
sql_segment_summary
"""
    ),
    markdown("## 7. The 21 business decisions"),
    code(
        """
insights = pd.DataFrame(json.loads((PROCESSED / "business_insights.json").read_text(encoding="utf-8")))
insights
"""
    ),
    markdown(
        """
## Conclusion

My analysis shows why revenue quality, customer concentration, RFM treatments, return exposure, data quality, and product affinity must be read together. The Streamlit app turns these reproducible artifacts into interactive decisions and clearly separates real-time user interaction from the historical source snapshot.
"""
    ),
]

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
nbf.write(notebook, OUTPUT_PATH)
print(OUTPUT_PATH)
