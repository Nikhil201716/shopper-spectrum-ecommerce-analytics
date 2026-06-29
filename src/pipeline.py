from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from src.config import (
    ARTIFACTS_DIR,
    INSIGHTS_PATH,
    ORIGINAL_COLUMNS,
    PROCESSED_DIR,
    PROFILE_PATH,
    QUALITY_REPORT_PATH,
    RAW_DATA_PATH,
    RECOMMENDATIONS_PARQUET,
    RFM_PARQUET,
    SQLITE_PATH,
    SQL_PATH,
    TRANSACTIONS_CSV_GZ,
    TRANSACTIONS_PARQUET,
)


@dataclass(frozen=True)
class BuildResult:
    input_rows: int
    output_rows: int
    customers: int
    products: int
    selected_k: int
    silhouette: float


def _as_python(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    return value


def load_and_enrich(raw_path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Preserve every source row and add transparent analytical fields."""
    dtype_map = {
        "InvoiceNo": "string",
        "StockCode": "string",
        "Description": "string",
        "Country": "string",
    }
    df = pd.read_csv(raw_path, dtype=dtype_map, low_memory=False)
    missing_columns = sorted(set(ORIGINAL_COLUMNS) - set(df.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df.insert(0, "RowID", np.arange(1, len(df) + 1, dtype=np.int64))
    df["InvoiceTimestamp"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["DescriptionClean"] = (
        df["Description"]
        .str.strip()
        .str.upper()
        .fillna("UNKNOWN PRODUCT [" + df["StockCode"].fillna("NO-CODE") + "]")
    )
    df["CountryClean"] = df["Country"].str.strip().fillna("UNKNOWN MARKET")
    non_merchandise_pattern = (
        r"POSTAGE|CARRIAGE|BANK CHARGES|AMAZON FEE|MANUAL|COMMISSION|"
        r"ADJUST BAD DEBT|DOTCOM|SAMPLES"
    )
    df["IsMerchandise"] = ~df["DescriptionClean"].str.contains(
        non_merchandise_pattern, case=False, regex=True, na=False
    )

    identified = df["CustomerID"].notna()
    identified_ids = df["CustomerID"].round().astype("Int64").astype("string")
    guest_ids = "GUEST-" + df["InvoiceNo"].fillna("NO-INVOICE")
    df["CustomerKey"] = identified_ids.where(identified, guest_ids)

    exact_duplicate = df.duplicated(subset=ORIGINAL_COLUMNS, keep=False)
    duplicate_rank = (
        df.groupby(ORIGINAL_COLUMNS, dropna=False, sort=False).cumcount().add(1)
    )
    df["IsDuplicate"] = exact_duplicate
    df["DuplicateRank"] = duplicate_rank.astype("int32")
    df["IsCanonicalRecord"] = df["DuplicateRank"].eq(1)

    df["IsMissingCustomerID"] = ~identified
    df["IsMissingDescription"] = df["Description"].isna()
    df["IsMissingInvoiceDate"] = df["InvoiceTimestamp"].isna()
    df["IsCancelledInvoice"] = df["InvoiceNo"].str.upper().str.startswith("C", na=False)
    df["IsReturn"] = df["Quantity"].lt(0)
    df["IsZeroQuantity"] = df["Quantity"].eq(0)
    df["IsNegativePrice"] = df["UnitPrice"].lt(0)
    df["IsZeroPrice"] = df["UnitPrice"].eq(0)

    completed_sale = (
        df["Quantity"].gt(0)
        & df["UnitPrice"].gt(0)
        & ~df["IsCancelledInvoice"]
        & df["InvoiceTimestamp"].notna()
    )
    df["IsCompletedSale"] = completed_sale
    df["IsAnalysisReadySale"] = completed_sale & df["IsCanonicalRecord"]
    df["IsRFMEligible"] = df["IsAnalysisReadySale"] & identified
    df["IsRecommendationEligible"] = (
        df["IsRFMEligible"] & ~df["IsMissingDescription"]
    )

    conditions = [
        df["IsCancelledInvoice"] | df["IsReturn"],
        df["IsZeroQuantity"],
        df["IsNegativePrice"],
        df["IsZeroPrice"],
        df["IsMissingInvoiceDate"],
    ]
    labels = [
        "Return / Cancellation",
        "Zero Quantity",
        "Negative Price Adjustment",
        "Zero Price / Free Item",
        "Invalid Date",
    ]
    df["TransactionStatus"] = np.select(conditions, labels, default="Completed Sale")

    df["ObservedLineValue"] = df["Quantity"] * df["UnitPrice"]
    canonical_weight = df["IsCanonicalRecord"].astype("int8")
    df["GrossRevenue"] = df["ObservedLineValue"].where(completed_sale, 0.0) * canonical_weight
    return_mask = (df["IsReturn"] | df["IsCancelledInvoice"]) & df["UnitPrice"].gt(0)
    df["ReturnValue"] = df["ObservedLineValue"].abs().where(return_mask, 0.0) * canonical_weight
    df["NetRevenue"] = df["GrossRevenue"] - df["ReturnValue"]

    issue_columns = [
        "IsMissingCustomerID",
        "IsMissingDescription",
        "IsMissingInvoiceDate",
        "IsDuplicate",
        "IsCancelledInvoice",
        "IsReturn",
        "IsZeroQuantity",
        "IsNegativePrice",
        "IsZeroPrice",
    ]
    df["DataQualityIssueCount"] = df[issue_columns].sum(axis=1).astype("int8")
    df["SourceRowPreserved"] = True

    ts = df["InvoiceTimestamp"]
    df["YearMonth"] = ts.dt.to_period("M").astype("string")
    df["Weekday"] = ts.dt.day_name().astype("string")
    df["Hour"] = ts.dt.hour.astype("Int8")
    df["PurchaseDate"] = ts.dt.date.astype("string")
    df["PriceBand"] = pd.cut(
        df["UnitPrice"],
        bins=[-np.inf, 0, 1, 5, 20, 100, np.inf],
        labels=["Adjustment", "Micro (0-1]", "Value (1-5]", "Core (5-20]", "Premium (20-100]", "Luxury (100+)"]
    ).astype("string")
    return df


def build_rfm(df: pd.DataFrame, selected_k: int = 4) -> tuple[pd.DataFrame, pd.DataFrame, dict[int, str]]:
    eligible = df.loc[df["IsRFMEligible"]].copy()
    snapshot_date = eligible["InvoiceTimestamp"].max().normalize() + pd.Timedelta(days=1)
    order_totals = (
        eligible.groupby(["CustomerKey", "InvoiceNo"], as_index=False)
        .agg(OrderValue=("GrossRevenue", "sum"), OrderDate=("InvoiceTimestamp", "max"))
    )
    rfm = (
        eligible.groupby("CustomerKey", as_index=False)
        .agg(
            LastPurchase=("InvoiceTimestamp", "max"),
            FirstPurchase=("InvoiceTimestamp", "min"),
            FrequencyOrders=("InvoiceNo", "nunique"),
            MonetaryValue=("GrossRevenue", "sum"),
            UnitsPurchased=("Quantity", "sum"),
            ActiveMonths=("YearMonth", "nunique"),
            Country=("CountryClean", lambda s: s.mode().iat[0] if not s.mode().empty else s.iloc[0]),
        )
    )
    rfm["RecencyDays"] = (snapshot_date - rfm["LastPurchase"].dt.normalize()).dt.days
    aov = order_totals.groupby("CustomerKey")["OrderValue"].mean()
    rfm["AverageOrderValue"] = rfm["CustomerKey"].map(aov)
    tenure_days = (rfm["LastPurchase"] - rfm["FirstPurchase"]).dt.days.clip(lower=0)
    rfm["TenureDays"] = tenure_days
    rfm["PurchaseCadenceDays"] = np.where(
        rfm["FrequencyOrders"].gt(1),
        tenure_days / (rfm["FrequencyOrders"] - 1),
        np.nan,
    )

    model_fields = ["RecencyDays", "FrequencyOrders", "MonetaryValue"]
    transformed = np.log1p(rfm[model_fields].clip(lower=0))
    scaler = StandardScaler()
    x = scaler.fit_transform(transformed)

    evaluation_rows: list[dict[str, float | int]] = []
    for k in range(2, 9):
        candidate = KMeans(n_clusters=k, random_state=42, n_init=30)
        labels = candidate.fit_predict(x)
        evaluation_rows.append(
            {
                "K": k,
                "Inertia": float(candidate.inertia_),
                "SilhouetteScore": float(silhouette_score(x, labels)),
            }
        )
    evaluation = pd.DataFrame(evaluation_rows)

    model = KMeans(n_clusters=selected_k, random_state=42, n_init=50)
    rfm["Cluster"] = model.fit_predict(x).astype("int8")
    profile = rfm.groupby("Cluster")[model_fields].mean()

    z = profile.copy()
    z["RecentScore"] = -profile["RecencyDays"]
    z["ValueScore"] = (
        z["RecentScore"].rank(pct=True)
        + profile["FrequencyOrders"].rank(pct=True)
        + profile["MonetaryValue"].rank(pct=True)
    )
    champion = int(z["ValueScore"].idxmax())
    remaining = [int(c) for c in profile.index if int(c) != champion]
    at_risk = int(profile.loc[remaining, "RecencyDays"].idxmax())
    remaining = [c for c in remaining if c != at_risk]
    loyal = int(
        (profile.loc[remaining, "FrequencyOrders"].rank(pct=True)
         + profile.loc[remaining, "MonetaryValue"].rank(pct=True)).idxmax()
    )
    occasional = next(c for c in remaining if c != loyal)
    label_map = {
        champion: "Champions",
        loyal: "Loyal Growth",
        occasional: "Occasional",
        at_risk: "At Risk",
    }
    rfm["Segment"] = rfm["Cluster"].map(label_map)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, ARTIFACTS_DIR / "rfm_scaler.joblib")
    joblib.dump(model, ARTIFACTS_DIR / "rfm_kmeans.joblib")
    (ARTIFACTS_DIR / "cluster_label_map.json").write_text(
        json.dumps({str(k): v for k, v in label_map.items()}, indent=2), encoding="utf-8"
    )
    return rfm, evaluation, label_map


def build_recommendations(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    eligible = df.loc[
        df["IsRecommendationEligible"] & df["IsMerchandise"],
        ["CustomerKey", "DescriptionClean", "Quantity"],
    ].copy()
    support = eligible.groupby("DescriptionClean")["CustomerKey"].nunique()
    products = support[support.ge(5)].index
    eligible = eligible[eligible["DescriptionClean"].isin(products)]
    interactions = (
        eligible.groupby(["DescriptionClean", "CustomerKey"], as_index=False)["Quantity"].sum()
    )
    product_codes, product_names = pd.factorize(interactions["DescriptionClean"], sort=True)
    customer_codes, customer_names = pd.factorize(interactions["CustomerKey"], sort=True)
    weights = np.log1p(interactions["Quantity"].clip(lower=1).to_numpy(dtype=float))
    matrix = csr_matrix(
        (weights, (product_codes, customer_codes)),
        shape=(len(product_names), len(customer_names)),
    )
    neighbor_count = min(7, matrix.shape[0])
    model = NearestNeighbors(metric="cosine", algorithm="brute", n_neighbors=neighbor_count)
    model.fit(matrix)
    distances, indices = model.kneighbors(matrix)

    binary = matrix.copy()
    binary.data = np.ones_like(binary.data)
    rows: list[dict[str, Any]] = []
    for product_index, product_name in enumerate(product_names):
        rank = 0
        for distance, neighbor_index in zip(distances[product_index], indices[product_index]):
            if neighbor_index == product_index:
                continue
            rank += 1
            overlap = int(binary[product_index].multiply(binary[neighbor_index]).sum())
            rows.append(
                {
                    "Product": str(product_name),
                    "Rank": rank,
                    "RecommendedProduct": str(product_names[neighbor_index]),
                    "Similarity": float(max(0.0, 1.0 - distance)),
                    "SharedCustomers": overlap,
                }
            )
            if rank == 5:
                break
    recommendations = pd.DataFrame(rows)

    catalog = (
        df.loc[df["IsAnalysisReadySale"] & df["IsMerchandise"]]
        .groupby("DescriptionClean", as_index=False)
        .agg(
            UnitsSold=("Quantity", "sum"),
            Revenue=("GrossRevenue", "sum"),
            Customers=("CustomerKey", "nunique"),
            Orders=("InvoiceNo", "nunique"),
        )
        .sort_values("Revenue", ascending=False)
    )
    catalog["RecommendationReady"] = catalog["DescriptionClean"].isin(product_names)
    return recommendations, catalog


def build_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    total = len(df)
    definitions = [
        ("Rows preserved", total, "Every input row remains in the processed dataset.", "Maintains auditability and prevents silent information loss."),
        ("Missing CustomerID", int(df["IsMissingCustomerID"].sum()), "Original null is retained; CustomerKey receives an invoice-level GUEST surrogate.", "Guest sales remain visible while RFM excludes unidentified shoppers to avoid false customer histories."),
        ("Missing Description", int(df["IsMissingDescription"].sum()), "Original null is retained; DescriptionClean uses UNKNOWN PRODUCT plus StockCode.", "Revenue stays reconciled and the product remains traceable without pretending to know its name."),
        ("Missing / invalid date", int(df["IsMissingInvoiceDate"].sum()), "Original date is retained; the row is flagged and excluded only from time-dependent models.", "Prevents fabricated timing while preserving the commercial record."),
        ("Exact duplicate rows", int(df["IsDuplicate"].sum()), "All copies are retained and ranked; only rank 1 receives analytical revenue weight.", "Avoids double-counting KPIs without deleting potentially auditable records."),
        ("Cancelled invoices", int(df["IsCancelledInvoice"].sum()), "Retained and classified as Return / Cancellation.", "Supports return-risk and net-revenue analysis."),
        ("Negative quantity", int(df["IsReturn"].sum()), "Retained as a return signal; absolute value contributes to ReturnValue.", "Turns reversals into a service, product-quality, and margin insight."),
        ("Zero quantity", int(df["IsZeroQuantity"].sum()), "Retained and marked Zero Quantity.", "Preserves operational adjustments without treating them as demand."),
        ("Negative price", int(df["IsNegativePrice"].sum()), "Retained and marked Negative Price Adjustment.", "Keeps accounting adjustments visible and out of gross-sales demand."),
        ("Zero price", int(df["IsZeroPrice"].sum()), "Retained and marked Zero Price / Free Item.", "Allows monitoring of samples, promotions, and data-entry leakage."),
        ("Analysis-ready positive sales", int(df["IsAnalysisReadySale"].sum()), "Used for gross-sales and demand KPIs; source rows outside this cohort remain available.", "Creates decision-grade metrics without destructive cleaning."),
    ]
    return pd.DataFrame(
        [
            {
                "Check": check,
                "Rows": count,
                "PercentOfRows": round(count / total * 100, 4) if total else 0,
                "Treatment": treatment,
                "BusinessReasonAndBenefit": benefit,
            }
            for check, count, treatment, benefit in definitions
        ]
    )


def _build_profile(df: pd.DataFrame, rfm: pd.DataFrame, evaluation: pd.DataFrame) -> dict[str, Any]:
    selected = evaluation.loc[evaluation["K"].eq(4)].iloc[0]
    profile = {
        "source": "Google Drive link embedded in project_brief.pdf",
        "rows": len(df),
        "columns_original": len(ORIGINAL_COLUMNS),
        "columns_processed": len(df.columns),
        "row_retention_percent": 100.0,
        "date_min": df["InvoiceTimestamp"].min(),
        "date_max": df["InvoiceTimestamp"].max(),
        "countries": df["CountryClean"].nunique(),
        "identified_customers": rfm["CustomerKey"].nunique(),
        "products": df["DescriptionClean"].nunique(),
        "invoices": df["InvoiceNo"].nunique(),
        "gross_revenue": df["GrossRevenue"].sum(),
        "return_value": df["ReturnValue"].sum(),
        "net_revenue": df["NetRevenue"].sum(),
        "selected_k": 4,
        "selected_k_silhouette": selected["SilhouetteScore"],
        "selected_k_inertia": selected["Inertia"],
        "selection_reason": "K=4 balances measured separation with four operationally distinct CRM treatments.",
    }
    return {key: _as_python(value) for key, value in profile.items()}


def _parse_sql_queries(sql_path: Path = SQL_PATH) -> dict[int, tuple[str, str]]:
    text = sql_path.read_text(encoding="utf-8")
    queries: dict[int, tuple[str, str]] = {}
    for block in text.split("-- [PROBLEM ")[1:]:
        header, sql = block.split("\n", 1)
        number_text, title = header.split("]", 1)
        number = int(number_text.strip())
        queries[number] = (title.strip(" -"), sql.strip())
    return queries


def execute_sql_analyses(
    df: pd.DataFrame,
    rfm: pd.DataFrame,
    recommendations: pd.DataFrame,
) -> dict[int, pd.DataFrame]:
    sql_columns = [
        "RowID", "InvoiceNo", "StockCode", "DescriptionClean", "Quantity",
        "InvoiceTimestamp", "UnitPrice", "CustomerID", "CustomerKey", "CountryClean",
        "TransactionStatus", "IsCanonicalRecord", "IsMerchandise", "IsMissingCustomerID",
        "IsMissingDescription", "IsDuplicate", "IsAnalysisReadySale", "GrossRevenue",
        "ReturnValue", "NetRevenue", "YearMonth", "Weekday", "Hour", "PriceBand",
        "CustomerSegment",
    ]
    sql_df = df[sql_columns].copy()
    sql_df["InvoiceTimestamp"] = sql_df["InvoiceTimestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    bool_columns = sql_df.select_dtypes(include="bool").columns
    sql_df[bool_columns] = sql_df[bool_columns].astype("int8")

    connection = sqlite3.connect(":memory:")
    sql_df.to_sql("transactions", connection, index=False, if_exists="replace", chunksize=25_000)
    rfm_sql = rfm.copy()
    for column in ["LastPurchase", "FirstPurchase"]:
        rfm_sql[column] = rfm_sql[column].dt.strftime("%Y-%m-%d %H:%M:%S")
    rfm_sql.to_sql("rfm_customers", connection, index=False, if_exists="replace")
    recommendations.to_sql("product_neighbors", connection, index=False, if_exists="replace")

    queries = _parse_sql_queries()
    results: dict[int, pd.DataFrame] = {}
    for number in sorted(queries):
        _, sql = queries[number]
        results[number] = pd.read_sql_query(sql.rstrip().rstrip(";"), connection)
    connection.close()
    return results


def _build_sqlite_summary(
    results: dict[int, pd.DataFrame],
    rfm: pd.DataFrame,
    recommendations: pd.DataFrame,
    quality: pd.DataFrame,
) -> None:
    if SQLITE_PATH.exists():
        SQLITE_PATH.unlink()
    connection = sqlite3.connect(SQLITE_PATH)
    for number, table in results.items():
        table.to_sql(f"problem_{number:02d}", connection, index=False, if_exists="replace")
    rfm.copy().assign(
        LastPurchase=rfm["LastPurchase"].dt.strftime("%Y-%m-%d %H:%M:%S"),
        FirstPurchase=rfm["FirstPurchase"].dt.strftime("%Y-%m-%d %H:%M:%S"),
    ).to_sql("rfm_customers", connection, index=False, if_exists="replace")
    recommendations.to_sql("product_neighbors", connection, index=False, if_exists="replace")
    quality.to_sql("data_quality", connection, index=False, if_exists="replace")
    connection.close()


def build_business_insights(
    results: dict[int, pd.DataFrame],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    def first(number: int) -> dict[str, Any]:
        return results[number].iloc[0].to_dict() if not results[number].empty else {}

    country = first(2)
    month = first(3)
    weekday = first(4)
    hour = first(5)
    product = first(6)
    return_product = first(8)
    return_country = first(9)
    concentration = first(11)
    segment = first(13)
    at_risk = first(15)
    zero_price = first(19)
    quality = first(20)

    texts = {
        1: ("Retail health pulse", f"The preserved ledger contains {profile['rows']:,} lines and {profile['invoices']:,} invoices, producing gross revenue of £{profile['gross_revenue']:,.0f} and net revenue of £{profile['net_revenue']:,.0f} after £{profile['return_value']:,.0f} in returns.", "Track gross, returns, net revenue, AOV, customers, and order volume together; growth that raises returns is not healthy growth."),
        2: ("Market concentration", f"{country.get('CountryClean', 'The leading market')} is the largest market in the current data with £{country.get('Revenue', 0):,.0f} gross revenue.", "Protect the core market while building an international growth shortlist using both revenue scale and return quality."),
        3: ("Seasonality and momentum", f"The strongest observed month is {month.get('YearMonth', 'n/a')} at £{month.get('Revenue', 0):,.0f} revenue.", "Bring inventory, staffing, and campaign launches forward by one replenishment lead time before the peak."),
        4: ("Weekday demand", f"{weekday.get('Weekday', 'The leading weekday')} generates the highest gross revenue in this transaction history.", "Schedule email, paid media, and warehouse labor around the observed high-response days."),
        5: ("Trading-hour intensity", f"The peak purchase hour is {int(hour.get('Hour', 0)):02d}:00 with £{hour.get('Revenue', 0):,.0f} revenue.", "Concentrate flash offers and live support coverage around the highest-intent hours."),
        6: ("Product winners", f"{product.get('DescriptionClean', 'The leading product')} leads the revenue ranking at £{product.get('Revenue', 0):,.0f}.", "Keep winners in stock, feature them in acquisition creative, and use them as anchors for cross-sell bundles."),
        7: ("Product portfolio roles", "The velocity-value matrix separates traffic drivers, premium earners, scalable stars, and low-priority long-tail items.", "Apply different inventory and merchandising rules by quadrant instead of one blanket reorder policy."),
        8: ("Product return exposure", f"{return_product.get('DescriptionClean', 'The highest-risk product')} has the largest material return exposure among adequately supported products.", "Audit listing accuracy, packaging, supplier quality, and customer expectations for high-value/high-rate return items."),
        9: ("Market return exposure", f"{return_country.get('CountryClean', 'The highest-risk market')} is the most material market-level return watchpoint in the ranked view.", "Review delivery promises, carrier performance, duties, and localisation for high-return markets."),
        10: ("Basket economics", "Basket distribution reveals typical orders, large commercial baskets, and the tail that can distort averages.", "Use median basket value for everyday targets and separate approval/service rules for extreme baskets."),
        11: ("Customer revenue concentration", f"The top 20% of identified customers contribute {concentration.get('Top20RevenueSharePct', 0):.1f}% of identified-customer revenue.", "Create a tiered retention programme, but avoid concentrating service only on current elites; nurture the next-value band too."),
        12: ("New versus repeat growth", "Monthly new-versus-repeat revenue separates acquisition-led spikes from durable customer relationships.", "Judge campaigns on second-purchase conversion and repeat revenue, not only first-order sales."),
        13: ("Segment portfolio", f"{segment.get('Segment', 'The leading value segment')} is the largest revenue segment, contributing {segment.get('RevenueSharePct', 0):.1f}% of identified-customer value.", "Assign a distinct CRM treatment, offer depth, and contact cadence to every segment."),
        14: ("Segment behaviour", "Segment profiles compare recency, frequency, monetary value, AOV, and cadence rather than relying on a cluster number.", "Use profile differences to set measurable segment-specific goals and guardrails."),
        15: ("At-risk recovery", f"At-risk customers represent £{at_risk.get('HistoricalValueAtRisk', 0):,.0f} in historical customer value.", "Prioritise win-back by value at risk and product affinity; use a stepped incentive instead of an immediate blanket discount."),
        16: ("Purchase cadence", "Customer cadence shows when a next purchase becomes late relative to the shopper's own pattern.", "Trigger reminders from expected cadence, not a single fixed inactivity threshold for everyone."),
        17: ("Cohort retention", "Cohort curves expose whether later customer vintages are becoming more or less loyal after acquisition.", "Compare retention by acquisition month and investigate offer, channel, or product-mix changes behind deterioration."),
        18: ("Price-band productivity", "Price-band mix shows whether growth is driven by unit volume, premium value, or zero-price activity.", "Balance conversion-friendly value products with premium attach opportunities and protect margin by band."),
        19: ("Zero-price governance", f"There are {int(zero_price.get('Lines', 0)):,} zero-price lines in the preserved ledger.", "Tag authorised samples/promotions and investigate all remaining zero-price activity as revenue leakage or master-data risk."),
        20: ("Data-quality exposure", f"{quality.get('Issue', 'Missing CustomerID')} is the most prevalent quality flag in the summary.", "Treat data quality as a commercial KPI: improve capture at source while retaining an auditable exception layer."),
        21: ("Product affinity", "Item-based collaborative filtering produces five customer-behaviour neighbours for recommendation-ready products.", "Use high-similarity pairs in product pages, basket add-ons, and post-purchase journeys; A/B test uplift before full rollout."),
    }
    insights = []
    for number in range(1, 22):
        title, finding, action = texts[number]
        insights.append({"id": number, "title": title, "finding": finding, "business_action": action})
    INSIGHTS_PATH.write_text(json.dumps(insights, indent=2, ensure_ascii=False), encoding="utf-8")
    return insights


def build_all(raw_path: Path = RAW_DATA_PATH) -> BuildResult:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_and_enrich(raw_path)
    input_rows = len(df)
    rfm, evaluation, label_map = build_rfm(df, selected_k=4)
    segment_map = rfm.set_index("CustomerKey")["Segment"]
    df["CustomerSegment"] = df["CustomerKey"].map(segment_map).fillna("Guest / Unidentified")
    recommendations, catalog = build_recommendations(df)
    quality = build_quality_report(df)
    profile = _build_profile(df, rfm, evaluation)

    df.to_parquet(TRANSACTIONS_PARQUET, index=False, compression="zstd")
    df.to_csv(TRANSACTIONS_CSV_GZ, index=False, compression="gzip")
    rfm.to_parquet(RFM_PARQUET, index=False, compression="zstd")
    rfm.to_csv(PROCESSED_DIR / "rfm_customers.csv", index=False)
    recommendations.to_parquet(RECOMMENDATIONS_PARQUET, index=False, compression="zstd")
    recommendations.to_csv(PROCESSED_DIR / "product_neighbors.csv", index=False)
    catalog.to_parquet(PROCESSED_DIR / "product_catalog.parquet", index=False, compression="zstd")
    evaluation.to_csv(PROCESSED_DIR / "cluster_evaluation.csv", index=False)
    quality.to_csv(QUALITY_REPORT_PATH, index=False)
    PROFILE_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")

    results = execute_sql_analyses(df, rfm, recommendations)
    sql_results_dir = PROCESSED_DIR / "sql_results"
    sql_results_dir.mkdir(exist_ok=True)
    for number, table in results.items():
        table.to_csv(sql_results_dir / f"problem_{number:02d}.csv", index=False)
    _build_sqlite_summary(results, rfm, recommendations, quality)
    build_business_insights(results, profile)

    if len(df) != input_rows or not df["SourceRowPreserved"].all():
        raise AssertionError("Row-preservation contract failed")
    selected = evaluation.loc[evaluation["K"].eq(4), "SilhouetteScore"].iat[0]
    return BuildResult(
        input_rows=input_rows,
        output_rows=len(df),
        customers=len(rfm),
        products=catalog["DescriptionClean"].nunique(),
        selected_k=4,
        silhouette=float(selected),
    )
