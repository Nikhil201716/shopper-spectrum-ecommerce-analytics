from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app_data import (
    filter_transactions,
    list_sql_tables,
    load_insights,
    load_profile,
    load_quality_report,
    load_recommendations,
    load_rfm,
    load_sql_result,
    load_transactions,
    parse_sql_catalog,
    run_summary_query,
)
from src.business_views import PROBLEMS, build_problem
from src.config import (
    PALETTE,
    PROCESSED_DIR,
    RAW_DATA_PATH,
    SEGMENT_COLORS,
    TRANSACTIONS_CSV_GZ,
    TRANSACTIONS_PARQUET,
)
from src.modeling import predict_segment, recommend_products
from src.ui import apply_branding, hero, insight_card, scope_pills


st.set_page_config(
    page_title="Shopper Spectrum | Nikhil Sinha",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_branding()


@st.cache_data(show_spinner="Loading the preserved transaction layer…")
def cached_transactions(modified_time: float) -> pd.DataFrame:
    return load_transactions()


@st.cache_data
def cached_rfm(modified_time: float) -> pd.DataFrame:
    return load_rfm()


@st.cache_data
def cached_recommendations(modified_time: float) -> pd.DataFrame:
    return load_recommendations()


transactions = cached_transactions(TRANSACTIONS_PARQUET.stat().st_mtime)
rfm = cached_rfm((PROCESSED_DIR / "rfm_customers.parquet").stat().st_mtime)
recommendations = cached_recommendations((PROCESSED_DIR / "product_neighbors.parquet").stat().st_mtime)
profile = load_profile()
insights = load_insights()
quality = load_quality_report()
sql_catalog = parse_sql_catalog()


with st.sidebar:
    st.markdown("### 🛒 Shopper Spectrum")
    st.caption("Decision intelligence by Nikhil Sinha")
    page = st.radio(
        "Navigate",
        ["Command Centre", "21 Business Decisions", "Data & Preprocessing", "Customer Segmentation", "Product Recommender", "SQL Studio", "Methodology & About"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("#### Portfolio filters")
    min_date = transactions["InvoiceTimestamp"].min().date()
    max_date = transactions["InvoiceTimestamp"].max().date()
    start_date = st.date_input("Start date", min_date, min_value=min_date, max_value=max_date)
    end_date = st.date_input("End date", max_date, min_value=min_date, max_value=max_date)
    countries = st.multiselect("Markets", sorted(transactions["CountryClean"].dropna().unique()), placeholder="All markets")
    segments = st.multiselect("Customer segments", sorted(transactions["CustomerSegment"].dropna().unique()), placeholder="All segments")
    st.markdown("---")
    st.caption(f"Data snapshot: {min_date:%d %b %Y} – {max_date:%d %b %Y}")
    st.caption("Interactive app ≠ live commerce feed. Rebuild artifacts when raw data changes.")

if start_date > end_date:
    st.error("Start date must be on or before end date.")
    st.stop()

filtered = filter_transactions(transactions, start_date, end_date, countries, segments)


def money(value: float) -> str:
    return f"£{value:,.0f}"


def render_filters_scope() -> None:
    scope_pills(
        f"{len(filtered):,} preserved rows in view",
        f"{start_date:%d %b %Y} – {end_date:%d %b %Y}",
        f"{len(countries) if countries else profile['countries']} markets",
        f"{len(segments) if segments else 5} segment labels",
    )


if page == "Command Centre":
    hero("Portfolio command centre", "I turn shopping behaviour into decisions.", "I built Shopper Spectrum to connect revenue quality, customer value, product demand, return exposure, and recommendation intelligence in one transparent workflow.")
    render_filters_scope()
    sales = filtered[filtered["IsAnalysisReadySale"]]
    gross = filtered["GrossRevenue"].sum()
    returns = filtered["ReturnValue"].sum()
    orders = sales["InvoiceNo"].nunique()
    customers = sales.loc[~sales["IsMissingCustomerID"], "CustomerKey"].nunique()
    first_row = st.columns(3)
    first_row[0].metric("Gross revenue", money(gross))
    first_row[1].metric("Net revenue", money(filtered["NetRevenue"].sum()))
    first_row[2].metric("Return value", money(returns), f"{returns / gross * 100 if gross else 0:.1f}% of gross", delta_color="inverse")
    second_row = st.columns(3)
    second_row[0].metric("Orders", f"{orders:,}")
    second_row[1].metric("Identified customers", f"{customers:,}")
    second_row[2].metric("Average order value", money(gross / orders if orders else 0))

    left, right = st.columns([1.7, 1])
    with left:
        output = build_problem(3, filtered, rfm, recommendations)
        st.plotly_chart(output.figure, width="stretch")
    with right:
        segment_view = rfm[rfm["Country"].isin(countries)] if countries else rfm
        segment_table = segment_view.groupby("Segment", as_index=False)["MonetaryValue"].sum()
        fig = px.pie(segment_table, values="MonetaryValue", names="Segment", hole=.66, color="Segment", color_discrete_map=SEGMENT_COLORS, title="Identified customer value")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=55,b=20), height=470)
        st.plotly_chart(fig, width="stretch")

    st.markdown("### The decisions I would take first")
    first_actions = [insights[0], insights[10], insights[14]]
    action_cols = st.columns(3)
    for col, item in zip(action_cols, first_actions):
        with col:
            insight_card(item["title"], f"{item['finding']} {item['business_action']}")

    st.markdown("### Commercial watchlist")
    risk = build_problem(8, filtered, rfm, recommendations)
    st.plotly_chart(risk.figure, width="stretch")
    st.dataframe(risk.table.head(15), width="stretch", hide_index=True)


elif page == "21 Business Decisions":
    hero("Decision lab", "21 real business questions. One evidence trail.", "Every view pairs an interactive visual with its result table, a measured finding, and a practical business action. Use the portfolio filters to stress-test the story.")
    render_filters_scope()
    labels = {pid: f"{pid:02d} · {category} · {title}" for pid, category, title, _ in PROBLEMS}
    selected_id = st.selectbox("Choose a decision", list(labels), format_func=lambda value: labels[value])
    output = build_problem(selected_id, filtered, rfm, recommendations)
    st.markdown(f"## {selected_id:02d}. {output.title}")
    st.caption(output.question)
    col1, col2, col3 = st.columns(3)
    with col1:
        insight_card("Measured finding", output.finding)
    with col2:
        insight_card("Business response", output.action)
    with col3:
        insight_card("Why it matters", insights[selected_id - 1]["business_action"])
    if output.note:
        st.info(output.note)
    st.plotly_chart(output.figure, width="stretch")
    st.markdown("#### Result table")
    st.dataframe(output.table, width="stretch", hide_index=True)
    with st.expander("Show the reproducible SQL behind this problem"):
        st.code(sql_catalog[selected_id]["sql"], language="sql")
        st.caption("This SQL was executed against the full preserved-row transaction layer during the artifact build.")


elif page == "Data & Preprocessing":
    hero("Auditable data layer", "I clean for decisions without deleting the story.", "Every source row and original value is retained. I add transparent flags, surrogates, statuses, and analytical eligibility rules so business metrics are trustworthy without erasing returns, guests, corrections, or duplicates.")
    a, b, c, d = st.columns(4)
    a.metric("Source rows", f"{profile['rows']:,}")
    b.metric("Processed rows", f"{len(transactions):,}")
    c.metric("Row retention", f"{profile['row_retention_percent']:.0f}%")
    d.metric("Processed fields", f"{profile['columns_processed']}")

    st.markdown("### What I did, why I did it, and the business benefit")
    st.dataframe(quality, width="stretch", hide_index=True, column_config={"PercentOfRows": st.column_config.NumberColumn("% of rows", format="%.3f%%")})

    raw_tab, cleaned_tab, dictionary_tab, downloads_tab = st.tabs(["Raw sample", "Cleaned sample", "Field dictionary", "Downloads"])
    with raw_tab:
        raw_sample = pd.read_csv(RAW_DATA_PATH, nrows=250)
        st.caption("The raw CSV is preserved as the source of truth. This preview is intentionally unchanged.")
        st.dataframe(raw_sample, width="stretch", hide_index=True)
    with cleaned_tab:
        cleaned_columns = ["RowID", "InvoiceNo", "StockCode", "Description", "DescriptionClean", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "CustomerKey", "Country", "TransactionStatus", "IsCanonicalRecord", "IsMerchandise", "GrossRevenue", "ReturnValue", "NetRevenue", "CustomerSegment", "DataQualityIssueCount", "SourceRowPreserved"]
        st.caption("Original fields remain beside derived fields, making every treatment traceable.")
        st.dataframe(filtered[cleaned_columns].head(1000), width="stretch", hide_index=True)
    with dictionary_tab:
        dictionary = pd.DataFrame([
            ("CustomerKey", "Identified customer number, or GUEST-<InvoiceNo> when CustomerID is missing", "Keeps guest demand visible without inventing a customer identity"),
            ("DescriptionClean", "Uppercase trimmed description or UNKNOWN PRODUCT [StockCode]", "Retains unnamed products and preserves stock-code traceability"),
            ("IsCanonicalRecord", "True only for the first exact copy", "Prevents duplicate revenue weighting while retaining every copy"),
            ("IsMerchandise", "False for postage, fees, commissions, and adjustments", "Stops operational charges from being presented as sellable product winners"),
            ("TransactionStatus", "Completed Sale, Return / Cancellation, Zero Price, Negative Price, or Invalid Date", "Turns exceptions into separate business signals"),
            ("IsAnalysisReadySale", "Positive-price, positive-quantity, dated, non-cancelled canonical sale", "Creates a consistent denominator for demand and gross-sales KPIs"),
            ("GrossRevenue", "Positive completed-sale value, weighted once across duplicates", "Measures demand without returns or duplicate inflation"),
            ("ReturnValue", "Absolute reversal value for negative/cancelled lines", "Quantifies return and service exposure"),
            ("NetRevenue", "GrossRevenue minus ReturnValue", "Shows commercial outcome after reversals"),
            ("CustomerSegment", "RFM segment for eligible customers; guest label otherwise", "Connects transactions to CRM actions"),
        ], columns=["Derived field", "Definition", "Reason and benefit"])
        st.dataframe(dictionary, width="stretch", hide_index=True)
    with downloads_tab:
        st.markdown("The full cleaned dataset is compressed to keep the project practical while preserving all 541,909 rows.")
        st.download_button("Download raw CSV", RAW_DATA_PATH.read_bytes(), "online_retail_raw.csv", "text/csv")
        st.download_button("Download full cleaned CSV (gzip)", TRANSACTIONS_CSV_GZ.read_bytes(), "cleaned_transactions.csv.gz", "application/gzip")
        preview_csv = filtered.head(100_000).to_csv(index=False).encode("utf-8")
        st.download_button("Download current filtered view (max 100k rows)", preview_csv, "shopper_spectrum_filtered.csv", "text/csv")


elif page == "Customer Segmentation":
    hero("RFM intelligence", "From cluster numbers to customer treatments.", "I use log-transformed Recency, Frequency, and Monetary value, standardisation, K-Means diagnostics, and business-profile interpretation. Lower RecencyDays means a more recent purchase.")
    segment_counts = rfm.groupby("Segment", as_index=False).agg(Customers=("CustomerKey", "count"), Revenue=("MonetaryValue", "sum"), AvgRecency=("RecencyDays", "mean"), AvgOrders=("FrequencyOrders", "mean"), AvgValue=("MonetaryValue", "mean"))
    cols = st.columns(4)
    for col, segment in zip(cols, ["Champions", "Loyal Growth", "Occasional", "At Risk"]):
        row = segment_counts[segment_counts.Segment.eq(segment)].iloc[0]
        col.metric(segment, f"{int(row.Customers):,}", money(row.Revenue))

    profile_tab, diagnostics_tab, predictor_tab = st.tabs(["Portfolio", "Model diagnostics", "Predict a segment"])
    with profile_tab:
        sample = rfm.sample(min(3500, len(rfm)), random_state=42)
        fig = px.scatter_3d(sample, x="RecencyDays", y="FrequencyOrders", z="MonetaryValue", color="Segment", size="AverageOrderValue", hover_name="CustomerKey", color_discrete_map=SEGMENT_COLORS, log_y=True, log_z=True, title="3D RFM customer landscape")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=650)
        st.plotly_chart(fig, width="stretch")
        st.dataframe(segment_counts, width="stretch", hide_index=True)
    with diagnostics_tab:
        evaluation = pd.read_csv(PROCESSED_DIR / "cluster_evaluation.csv")
        fig = px.line(evaluation, x="K", y="SilhouetteScore", markers=True, title="Silhouette score by cluster count", color_discrete_sequence=["#17C3B2"])
        fig.add_vline(x=4, line_dash="dash", line_color="#F6C85F", annotation_text="Selected K=4")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch")
        st.info("K=2 has stronger pure separation, but K=4 provides four commercially distinct treatments. I document that trade-off instead of pretending the metric alone chose the final model.")
        st.dataframe(evaluation, width="stretch", hide_index=True)
    with predictor_tab:
        with st.form("segment_form"):
            c1, c2, c3 = st.columns(3)
            recency = c1.number_input("Recency (days since last purchase)", min_value=0.0, value=45.0, step=1.0)
            frequency = c2.number_input("Frequency (distinct orders)", min_value=1.0, value=4.0, step=1.0)
            monetary = c3.number_input("Monetary value (£)", min_value=0.0, value=850.0, step=25.0)
            submitted = st.form_submit_button("Predict customer segment")
        if submitted:
            cluster, segment = predict_segment(recency, frequency, monetary)
            insight_card("Predicted treatment", f"Cluster {cluster} maps to {segment}. {dict((row['title'], row['business_action']) for row in insights).get('Segment behaviour', '')}")


elif page == "Product Recommender":
    hero("Product affinity", "Five behavioural neighbours, ready for a cross-sell test.", "The recommender is item-based collaborative filtering: products are similar when the same identified customers buy them. Service charges and sparse products are excluded from recommendation candidates, but remain in the preserved data layer.")
    products = recommendations["Product"].drop_duplicates().sort_values().tolist()
    default_product = "WHITE HANGING HEART T-LIGHT HOLDER" if "WHITE HANGING HEART T-LIGHT HOLDER" in products else products[0]
    product = st.selectbox("Choose a merchandise product", products, index=products.index(default_product))
    result = recommend_products(recommendations, product)
    if not result.empty:
        cards = st.columns(5)
        for col, row in zip(cards, result.itertuples()):
            with col:
                insight_card(f"#{row.Rank} · Similarity {row.Similarity:.2f}", row.RecommendedProduct)
        fig = px.bar(result.sort_values("Similarity"), x="Similarity", y="RecommendedProduct", orientation="h", color="SharedCustomers", color_continuous_scale=["#4F7CFF", "#17C3B2"], range_x=[0, 1], title="Affinity strength and shared-customer support")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,18,32,.6)", height=460)
        st.plotly_chart(fig, width="stretch")
        st.dataframe(result, width="stretch", hide_index=True)
        st.success("Business use: test these pairs in product-page carousels, basket add-ons, bundles, and post-purchase email. Similarity is a ranking signal—not proof of causal uplift—so I would A/B test conversion and margin impact.")


elif page == "SQL Studio":
    hero("SQL studio", "The visual story has a query behind it.", "I execute 21 SQL analyses against the complete preserved-row transaction layer during the data build, save their result tables, and expose a read-only SQLite summary database for exploration.")
    selected_id = st.selectbox("Prebuilt business query", list(sql_catalog), format_func=lambda value: f"{value:02d}. {sql_catalog[value]['title']}")
    st.code(sql_catalog[selected_id]["sql"], language="sql")
    st.markdown("#### Saved full-data result")
    st.dataframe(load_sql_result(selected_id), width="stretch", hide_index=True)
    with st.expander("Run a read-only query against the summary database"):
        st.caption("Available tables: " + ", ".join(list_sql_tables()))
        custom_sql = st.text_area("SQL", "SELECT Segment, COUNT(*) AS Customers, ROUND(SUM(MonetaryValue), 2) AS Value FROM rfm_customers GROUP BY Segment ORDER BY Value DESC;", height=160)
        if st.button("Run query"):
            try:
                st.dataframe(run_summary_query(custom_sql), width="stretch", hide_index=True)
            except Exception as exc:
                st.error(str(exc))


else:
    hero("Methodology & authorship", "I built this as a decision system, not a chart gallery.", "I am Nikhil Sinha. I designed the project from the supplied brief, preserved the full commercial record, made every preprocessing treatment explainable, and connected Python, SQL, machine learning, and Streamlit to practical retail actions.")
    st.markdown("### My workflow")
    workflow = pd.DataFrame([
        ("1", "Preserve", "Keep the raw CSV and all 541,909 rows as the audit trail."),
        ("2", "Explain", "Add flags and derived fields beside—not over—the source values."),
        ("3", "Model", "Build RFM segments and item-based product neighbours from eligible cohorts."),
        ("4", "Query", "Execute 21 business SQL statements and persist their results."),
        ("5", "Decide", "Pair every finding with a practical action and a limitation."),
        ("6", "Validate", "Test row retention, revenue reconciliation, models, SQL, and the rendered app."),
    ], columns=["Stage", "Principle", "What I did"])
    st.dataframe(workflow, width="stretch", hide_index=True)
    left, right = st.columns(2)
    with left:
        st.markdown("### Analytical boundaries")
        st.markdown("- The transaction snapshot runs from **1 Dec 2022 to 9 Dec 2023**; the interface is real-time, but the source is not a live commerce feed.\n- Currency is displayed as pounds because the source is a UK-centred retail dataset; the raw file itself contains no currency-code column.\n- Guest invoice surrogates preserve sales but never enter identified-customer RFM.\n- Product similarity is behavioural association, not causation.\n- K=4 is a business-interpretability choice documented beside the silhouette trade-off.")
    with right:
        st.markdown("### Reproducibility")
        st.code("python scripts/build_artifacts.py\nstreamlit run app.py", language="bash")
        st.markdown("The repository contains the raw dataset, processed Parquet and compressed CSV, model artifacts, SQLite summary database, SQL catalogue, notebook, tests, VS Code tasks, and GitHub automation.")
