from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config import PALETTE, SEGMENT_COLORS


@dataclass
class ProblemOutput:
    title: str
    question: str
    finding: str
    action: str
    figure: go.Figure
    table: pd.DataFrame
    note: str = ""


PROBLEMS = [
    (1, "Executive", "Retail health pulse", "Is growth commercially healthy after returns?"),
    (2, "Markets", "Market concentration", "Which countries deserve protection, expansion, or remediation?"),
    (3, "Trading", "Seasonality and momentum", "When should I place inventory and campaign bets?"),
    (4, "Trading", "Weekday demand", "Which days carry the strongest buying intent?"),
    (5, "Trading", "Trading-hour intensity", "When should campaigns and support teams go live?"),
    (6, "Products", "Product winners", "Which sellable products create demand and revenue?"),
    (7, "Products", "Product portfolio roles", "Which items are stars, traffic drivers, premium earners, or long tail?"),
    (8, "Risk", "Product return exposure", "Which merchandise creates the biggest return-value exposure?"),
    (9, "Risk", "Market return exposure", "Where are returns a material market problem?"),
    (10, "Orders", "Basket economics", "What does a normal order look like, and where are the extremes?"),
    (11, "Customers", "Customer revenue concentration", "How dependent is revenue on the top customer tier?"),
    (12, "Customers", "New versus repeat growth", "Is growth being retained after customer acquisition?"),
    (13, "Segments", "RFM segment portfolio", "How is customer value distributed across actionable segments?"),
    (14, "Segments", "Segment behaviour", "How do recency, frequency, value, AOV, and cadence differ?"),
    (15, "Retention", "At-risk recovery", "How much historical value is currently exposed to churn?"),
    (16, "Retention", "Purchase cadence", "When is a customer genuinely late for the next purchase?"),
    (17, "Retention", "Cohort retention", "Are newer customer cohorts becoming more loyal?"),
    (18, "Pricing", "Price-band productivity", "Which price bands drive units, revenue, and order reach?"),
    (19, "Governance", "Zero-price governance", "How much free-item or price-master activity needs control?"),
    (20, "Governance", "Data-quality exposure", "Which source-data problems most threaten decision quality?"),
    (21, "Personalisation", "Product affinity", "Which products belong together in a cross-sell journey?"),
]


ACTIONS = {
    1: "Review gross revenue, returns, net revenue, AOV, customers, and orders as one health scorecard.",
    2: "Protect the core market and prioritise expansion using both scale and return quality.",
    3: "Move stock, staffing, and campaign preparation ahead of the strongest demand month.",
    4: "Schedule CRM and warehouse capacity around high-response weekdays.",
    5: "Concentrate flash offers and live support around peak buying hours.",
    6: "Keep winners available and use them as acquisition and bundle anchors.",
    7: "Set separate inventory and merchandising rules for each portfolio role.",
    8: "Audit high-exposure listings, packaging, suppliers, and expectation setting.",
    9: "Review carriers, delivery promises, duties, and localisation in high-return markets.",
    10: "Use medians for everyday targets and service extreme baskets separately.",
    11: "Build a tiered retention plan while deliberately nurturing the next-value band.",
    12: "Optimise acquisition for second purchase and repeat revenue, not first orders alone.",
    13: "Give every RFM segment its own offer depth, contact cadence, and success metric.",
    14: "Use behavioural profiles—not cluster numbers—to design customer treatments.",
    15: "Prioritise win-back by historical value and affinity; escalate incentives gradually.",
    16: "Trigger outreach from each customer's expected cadence rather than one fixed rule.",
    17: "Compare cohort curves and investigate offer, channel, or product-mix deterioration.",
    18: "Balance conversion-friendly value items with premium attach opportunities by band.",
    19: "Tag authorised samples and investigate every remaining zero-price exception.",
    20: "Improve capture at source while keeping an auditable exception layer.",
    21: "A/B test high-similarity pairs on product pages, baskets, and post-purchase journeys.",
}

COUNTRY_ISO3 = {
    "Australia": "AUS", "Austria": "AUT", "Bahrain": "BHR", "Belgium": "BEL",
    "Brazil": "BRA", "Canada": "CAN", "Channel Islands": "GBR", "Cyprus": "CYP",
    "Czech Republic": "CZE", "Denmark": "DNK", "EIRE": "IRL", "Finland": "FIN",
    "France": "FRA", "Germany": "DEU", "Greece": "GRC", "Hong Kong": "HKG",
    "Iceland": "ISL", "Israel": "ISR", "Italy": "ITA", "Japan": "JPN",
    "Lebanon": "LBN", "Lithuania": "LTU", "Malta": "MLT", "Netherlands": "NLD",
    "Norway": "NOR", "Poland": "POL", "Portugal": "PRT", "RSA": "ZAF",
    "Saudi Arabia": "SAU", "Singapore": "SGP", "Spain": "ESP", "Sweden": "SWE",
    "Switzerland": "CHE", "USA": "USA", "United Arab Emirates": "ARE",
    "United Kingdom": "GBR",
}


def _style(fig: go.Figure, height: int = 470) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,18,32,0.65)",
        font={"family": "Inter, Segoe UI, sans-serif", "color": "#E8EEF8"},
        colorway=PALETTE,
        margin={"l": 30, "r": 25, "t": 55, "b": 35},
        height=height,
        legend_title_text="",
    )
    fig.update_xaxes(gridcolor="rgba(148,163,184,.14)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,.14)", zeroline=False)
    return fig


def _empty(title: str, question: str, problem_id: int) -> ProblemOutput:
    fig = go.Figure()
    fig.add_annotation(text="No records match the current filters.", showarrow=False, font={"size": 18})
    return ProblemOutput(title, question, "No filtered result is available.", ACTIONS[problem_id], _style(fig), pd.DataFrame())


def _meta(problem_id: int) -> tuple[str, str]:
    row = next(item for item in PROBLEMS if item[0] == problem_id)
    return row[2], row[3]


def build_problem(problem_id: int, df: pd.DataFrame, rfm: pd.DataFrame, recommendations: pd.DataFrame) -> ProblemOutput:
    title, question = _meta(problem_id)
    if df.empty and problem_id not in {13, 14, 15, 16, 21}:
        return _empty(title, question, problem_id)
    builder: Callable = globals()[f"_problem_{problem_id:02d}"]
    return builder(title, question, df, rfm, recommendations)


def _problem_01(title, question, df, rfm, recs):
    sales = df[df["IsAnalysisReadySale"]]
    gross = df["GrossRevenue"].sum()
    returns = df["ReturnValue"].sum()
    orders = sales["InvoiceNo"].nunique()
    table = pd.DataFrame([{
        "Gross Revenue": gross, "Return Value": returns, "Net Revenue": df["NetRevenue"].sum(),
        "Orders": orders, "Identified Customers": sales.loc[~sales["IsMissingCustomerID"], "CustomerKey"].nunique(),
        "Average Order Value": gross / orders if orders else 0,
    }])
    monthly = df.groupby("YearMonth", as_index=False)[["GrossRevenue", "ReturnValue", "NetRevenue"]].sum().sort_values("YearMonth")
    fig = px.area(monthly, x="YearMonth", y=["GrossRevenue", "ReturnValue"], title="Gross revenue and return-value trend")
    finding = f"£{gross:,.0f} gross revenue becomes £{gross-returns:,.0f} after £{returns:,.0f} of return exposure ({returns/gross*100 if gross else 0:.1f}%)."
    return ProblemOutput(title, question, finding, ACTIONS[1], _style(fig), table)


def _problem_02(title, question, df, rfm, recs):
    table = df.groupby("CountryClean", as_index=False).agg(Revenue=("GrossRevenue", "sum"), ReturnValue=("ReturnValue", "sum"), Orders=("InvoiceNo", "nunique")).sort_values("Revenue", ascending=False)
    table["RevenueSharePct"] = table["Revenue"] / table["Revenue"].sum() * 100
    table["ISO3"] = table["CountryClean"].map(COUNTRY_ISO3)
    mapped = table.dropna(subset=["ISO3"])
    fig = px.choropleth(mapped, locations="ISO3", locationmode="ISO-3", color="Revenue", hover_name="CountryClean", color_continuous_scale=["#132338", "#4F7CFF", "#17C3B2"], title="Revenue footprint by customer market")
    lead = table.iloc[0]
    return ProblemOutput(title, question, f"{lead.CountryClean} contributes £{lead.Revenue:,.0f}, or {lead.RevenueSharePct:.1f}% of filtered revenue.", ACTIONS[2], _style(fig, 520), table.head(20))


def _problem_03(title, question, df, rfm, recs):
    table = df.groupby("YearMonth", as_index=False).agg(Revenue=("GrossRevenue", "sum"), NetRevenue=("NetRevenue", "sum"), Orders=("InvoiceNo", "nunique")).sort_values("YearMonth")
    fig = px.line(table, x="YearMonth", y=["Revenue", "NetRevenue"], markers=True, title="Monthly commercial momentum")
    peak = table.loc[table["Revenue"].idxmax()]
    return ProblemOutput(title, question, f"{peak.YearMonth} is the filtered peak month at £{peak.Revenue:,.0f} gross revenue.", ACTIONS[3], _style(fig), table)


def _problem_04(title, question, df, rfm, recs):
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    table = df.groupby("Weekday", as_index=False).agg(Revenue=("GrossRevenue", "sum"), Orders=("InvoiceNo", "nunique"))
    table["Weekday"] = pd.Categorical(table["Weekday"], order, ordered=True)
    table = table.sort_values("Weekday")
    fig = px.bar(table, x="Weekday", y="Revenue", color="Revenue", color_continuous_scale=["#4F7CFF", "#17C3B2"], title="Revenue rhythm across the week")
    lead = table.loc[table["Revenue"].idxmax()]
    return ProblemOutput(title, question, f"{lead.Weekday} carries the strongest filtered revenue signal at £{lead.Revenue:,.0f}.", ACTIONS[4], _style(fig), table)


def _problem_05(title, question, df, rfm, recs):
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    table = df.groupby(["Weekday", "Hour"], as_index=False).agg(Revenue=("GrossRevenue", "sum"), Orders=("InvoiceNo", "nunique"))
    pivot = table.pivot(index="Weekday", columns="Hour", values="Revenue").reindex(order).fillna(0)
    fig = px.imshow(pivot, aspect="auto", color_continuous_scale=["#0A1524", "#4F7CFF", "#F6C85F"], labels={"color": "Revenue"}, title="Revenue intensity: weekday × hour")
    lead = table.loc[table["Revenue"].idxmax()]
    return ProblemOutput(title, question, f"The strongest filtered cell is {lead.Weekday} at {int(lead.Hour):02d}:00 (£{lead.Revenue:,.0f}).", ACTIONS[5], _style(fig), table.sort_values("Revenue", ascending=False).head(30))


def _product_table(df):
    return df[df["IsAnalysisReadySale"] & df["IsMerchandise"]].groupby("DescriptionClean", as_index=False).agg(UnitsSold=("Quantity", "sum"), Revenue=("GrossRevenue", "sum"), Orders=("InvoiceNo", "nunique"), Customers=("CustomerKey", "nunique"))


def _problem_06(title, question, df, rfm, recs):
    table = _product_table(df)
    table = table[(table["Orders"] >= 10) & (table["Customers"] >= 5)].sort_values("Revenue", ascending=False).head(20)
    fig = px.bar(table.sort_values("Revenue"), x="Revenue", y="DescriptionClean", orientation="h", color="UnitsSold", color_continuous_scale=["#4F7CFF", "#17C3B2"], title="Top sellable products by revenue")
    lead = table.iloc[0]
    return ProblemOutput(title, question, f"{lead.DescriptionClean} leads sellable merchandise at £{lead.Revenue:,.0f} and {lead.UnitsSold:,.0f} units.", ACTIONS[6], _style(fig, 560), table)


def _problem_07(title, question, df, rfm, recs):
    table = _product_table(df)
    table = table[table["UnitsSold"].ge(20) & table["Customers"].ge(5)].nlargest(300, "Revenue").copy()
    unit_mid, revenue_mid = table["UnitsSold"].median(), table["Revenue"].median()
    table["PortfolioRole"] = np.select(
        [(table.UnitsSold >= unit_mid) & (table.Revenue >= revenue_mid), (table.UnitsSold >= unit_mid), (table.Revenue >= revenue_mid)],
        ["Scalable star", "Traffic driver", "Premium earner"], default="Long tail")
    fig = px.scatter(table, x="UnitsSold", y="Revenue", size="Customers", color="PortfolioRole", hover_name="DescriptionClean", log_x=True, log_y=True, color_discrete_sequence=PALETTE, title="Merchandise velocity-value portfolio")
    stars = int(table["PortfolioRole"].eq("Scalable star").sum())
    return ProblemOutput(title, question, f"{stars} products qualify as scalable stars within the top filtered merchandise set.", ACTIONS[7], _style(fig), table.nlargest(30, "Revenue"))


def _problem_08(title, question, df, rfm, recs):
    merchandise = df[df["IsMerchandise"]]
    table = merchandise.groupby("DescriptionClean", as_index=False).agg(GrossRevenue=("GrossRevenue", "sum"), ReturnValue=("ReturnValue", "sum"), ReturnInvoices=("InvoiceNo", lambda s: s[merchandise.loc[s.index, "ReturnValue"].gt(0)].nunique()))
    table = table[(table.GrossRevenue >= 1000) & (table.ReturnValue > 0)].copy()
    table["ReturnValueRatePct"] = table.ReturnValue / table.GrossRevenue * 100
    table = table.sort_values("ReturnValue", ascending=False).head(30)
    fig = px.scatter(table, x="ReturnValueRatePct", y="ReturnValue", size="GrossRevenue", color="ReturnValue", hover_name="DescriptionClean", color_continuous_scale=["#F6C85F", "#FF6B6B"], title="Material product return exposure")
    lead = table.iloc[0]
    return ProblemOutput(title, question, f"{lead.DescriptionClean} has the largest filtered merchandise return exposure (£{lead.ReturnValue:,.0f}).", ACTIONS[8], _style(fig), table)


def _problem_09(title, question, df, rfm, recs):
    table = df.groupby("CountryClean", as_index=False).agg(GrossRevenue=("GrossRevenue", "sum"), ReturnValue=("ReturnValue", "sum"), ReturnInvoices=("InvoiceNo", lambda s: s[df.loc[s.index, "ReturnValue"].gt(0)].nunique()))
    table = table[table.GrossRevenue >= 5000].copy()
    table["ReturnValueRatePct"] = table.ReturnValue / table.GrossRevenue * 100
    table = table.sort_values("ReturnValue", ascending=False)
    fig = px.bar(table.head(20).sort_values("ReturnValue"), x="ReturnValue", y="CountryClean", orientation="h", color="ReturnValueRatePct", color_continuous_scale=["#F6C85F", "#FF6B6B"], title="Market return value and rate")
    lead = table.iloc[0]
    return ProblemOutput(title, question, f"{lead.CountryClean} has the largest absolute filtered return exposure at £{lead.ReturnValue:,.0f}.", ACTIONS[9], _style(fig), table)


def _problem_10(title, question, df, rfm, recs):
    baskets = df[df["IsAnalysisReadySale"]].groupby("InvoiceNo", as_index=False).agg(BasketValue=("GrossRevenue", "sum"), Units=("Quantity", "sum"), DistinctProducts=("DescriptionClean", "nunique"))
    cap = baskets["BasketValue"].quantile(.99)
    fig = px.histogram(baskets[baskets.BasketValue <= cap], x="BasketValue", nbins=50, color_discrete_sequence=["#17C3B2"], title="Basket-value distribution (up to 99th percentile)")
    table = baskets[["BasketValue", "Units", "DistinctProducts"]].describe(percentiles=[.25, .5, .75, .9, .95, .99]).round(2).reset_index()
    return ProblemOutput(title, question, f"The median basket is £{baskets.BasketValue.median():,.2f}; the 90th percentile is £{baskets.BasketValue.quantile(.9):,.2f}.", ACTIONS[10], _style(fig), table)


def _problem_11(title, question, df, rfm, recs):
    identified = df[df["IsAnalysisReadySale"] & ~df["IsMissingCustomerID"]]
    table = identified.groupby("CustomerKey", as_index=False).agg(Revenue=("GrossRevenue", "sum")).sort_values("Revenue", ascending=False)
    table["CustomerRank"] = np.arange(1, len(table) + 1)
    table["CumulativeCustomerPct"] = table.CustomerRank / len(table) * 100
    table["CumulativeRevenuePct"] = table.Revenue.cumsum() / table.Revenue.sum() * 100
    share = table.loc[table.CumulativeCustomerPct <= 20, "Revenue"].sum() / table.Revenue.sum() * 100
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=table.CustomerRank.head(250), y=table.Revenue.head(250), name="Customer revenue", marker_color="#4F7CFF"), secondary_y=False)
    fig.add_trace(go.Scatter(x=table.CustomerRank, y=table.CumulativeRevenuePct, name="Cumulative revenue %", line={"color": "#F6C85F", "width": 3}), secondary_y=True)
    fig.update_yaxes(title_text="Revenue", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative %", range=[0, 105], secondary_y=True)
    fig.update_layout(title="Customer-value Pareto curve")
    return ProblemOutput(title, question, f"The top 20% of identified customers contribute {share:.1f}% of filtered identified-customer revenue.", ACTIONS[11], _style(fig), table.head(50))


def _problem_12(title, question, df, rfm, recs):
    sales = df[df["IsAnalysisReadySale"] & ~df["IsMissingCustomerID"]].copy()
    first = sales.groupby("CustomerKey")["YearMonth"].min()
    sales["FirstMonth"] = sales.CustomerKey.map(first)
    sales["CustomerType"] = np.where(sales.YearMonth.eq(sales.FirstMonth), "New-customer revenue", "Repeat-customer revenue")
    table = sales.groupby(["YearMonth", "CustomerType"], as_index=False).agg(Revenue=("GrossRevenue", "sum"), Customers=("CustomerKey", "nunique"))
    fig = px.area(table.sort_values("YearMonth"), x="YearMonth", y="Revenue", color="CustomerType", color_discrete_sequence=["#4F7CFF", "#17C3B2"], title="New versus repeat customer revenue")
    repeat = table.loc[table.CustomerType.eq("Repeat-customer revenue"), "Revenue"].sum()
    total = table.Revenue.sum()
    return ProblemOutput(title, question, f"Repeat customers contribute {repeat/total*100 if total else 0:.1f}% of filtered identified-customer revenue.", ACTIONS[12], _style(fig), table)


def _rfm_for_view(df, rfm):
    countries = df["CountryClean"].dropna().unique()
    return rfm[rfm["Country"].isin(countries)] if len(countries) else rfm


def _problem_13(title, question, df, rfm, recs):
    view = _rfm_for_view(df, rfm)
    table = view.groupby("Segment", as_index=False).agg(Customers=("CustomerKey", "count"), HistoricalRevenue=("MonetaryValue", "sum"))
    table["RevenueSharePct"] = table.HistoricalRevenue / table.HistoricalRevenue.sum() * 100
    fig = px.pie(table, values="HistoricalRevenue", names="Segment", hole=.6, color="Segment", color_discrete_map=SEGMENT_COLORS, title="RFM value portfolio")
    lead = table.loc[table.HistoricalRevenue.idxmax()]
    return ProblemOutput(title, question, f"{lead.Segment} contributes {lead.RevenueSharePct:.1f}% of identified historical value in the selected markets.", ACTIONS[13], _style(fig), table, "RFM remains anchored to the model snapshot; market filters apply, date filters do not recompute clusters.")


def _problem_14(title, question, df, rfm, recs):
    view = _rfm_for_view(df, rfm)
    metrics = ["RecencyDays", "FrequencyOrders", "MonetaryValue", "AverageOrderValue", "PurchaseCadenceDays"]
    table = view.groupby("Segment")[metrics].mean().round(2).reset_index()
    scaled = table.copy()
    for col in metrics:
        series = scaled[col].fillna(scaled[col].median())
        scaled[col] = (series - series.min()) / (series.max() - series.min() if series.max() != series.min() else 1)
    scaled["RecencyDays"] = 1 - scaled["RecencyDays"]
    fig = go.Figure()
    labels = ["Recent", "Frequent", "Customer value", "Order value", "Fast cadence"]
    for _, row in scaled.iterrows():
        values = row[metrics].tolist()
        fig.add_trace(go.Scatterpolar(r=values + values[:1], theta=labels + labels[:1], fill="toself", name=row.Segment, line={"color": SEGMENT_COLORS.get(row.Segment)}))
    fig.update_layout(title="Normalised segment behaviour profiles", polar={"radialaxis": {"visible": True, "range": [0, 1]}})
    return ProblemOutput(title, question, "The radar compares relative behaviour; the table retains the decision-grade units.", ACTIONS[14], _style(fig), table)


def _problem_15(title, question, df, rfm, recs):
    view = _rfm_for_view(df, rfm)
    table = view[view.Segment.eq("At Risk")].nlargest(30, "MonetaryValue")[["CustomerKey", "Country", "RecencyDays", "FrequencyOrders", "MonetaryValue", "AverageOrderValue"]]
    fig = px.bar(table.sort_values("MonetaryValue"), x="MonetaryValue", y="CustomerKey", orientation="h", color="RecencyDays", color_continuous_scale=["#F6C85F", "#FF6B6B"], title="Highest-value at-risk customers")
    total = view.loc[view.Segment.eq("At Risk"), "MonetaryValue"].sum()
    return ProblemOutput(title, question, f"The selected-market at-risk segment represents £{total:,.0f} in historical value.", ACTIONS[15], _style(fig, 560), table)


def _problem_16(title, question, df, rfm, recs):
    view = _rfm_for_view(df, rfm).copy()
    view["CadenceBand"] = pd.cut(view.PurchaseCadenceDays, bins=[-np.inf, 7, 30, 90, np.inf], labels=["Weekly", "Monthly", "Quarterly", "Long cycle"])
    view["CadenceBand"] = view["CadenceBand"].astype("string").fillna("Single purchase")
    table = view.groupby("CadenceBand", as_index=False).agg(Customers=("CustomerKey", "count"), AvgValue=("MonetaryValue", "mean"), AvgRecency=("RecencyDays", "mean")).sort_values("Customers", ascending=False)
    fig = px.histogram(view.dropna(subset=["PurchaseCadenceDays"]), x="PurchaseCadenceDays", color="Segment", nbins=60, marginal="box", color_discrete_map=SEGMENT_COLORS, title="Customer purchase cadence")
    lead = table.iloc[0]
    return ProblemOutput(title, question, f"{lead.CadenceBand} is the largest cadence group with {int(lead.Customers):,} customers.", ACTIONS[16], _style(fig, 540), table)


def _problem_17(title, question, df, rfm, recs):
    sales = df[df["IsAnalysisReadySale"] & ~df["IsMissingCustomerID"]][["CustomerKey", "YearMonth"]].drop_duplicates()
    cohort = sales.groupby("CustomerKey")["YearMonth"].min().rename("CohortMonth")
    sales = sales.join(cohort, on="CustomerKey")
    sales["CohortIndex"] = ((pd.to_datetime(sales.YearMonth) .dt.year - pd.to_datetime(sales.CohortMonth).dt.year) * 12 + (pd.to_datetime(sales.YearMonth).dt.month - pd.to_datetime(sales.CohortMonth).dt.month))
    table = sales.groupby(["CohortMonth", "CohortIndex"])["CustomerKey"].nunique().rename("ActiveCustomers").reset_index()
    sizes = table[table.CohortIndex.eq(0)].set_index("CohortMonth")["ActiveCustomers"]
    table["RetentionPct"] = table.ActiveCustomers / table.CohortMonth.map(sizes) * 100
    heat = table[table.CohortIndex.between(0, 12)].pivot(index="CohortMonth", columns="CohortIndex", values="RetentionPct")
    fig = px.imshow(heat, aspect="auto", color_continuous_scale=["#101B2D", "#4F7CFF", "#17C3B2"], zmin=0, zmax=100, text_auto=".0f", labels={"color": "Retention %"}, title="Monthly cohort retention (%)")
    month1 = table.loc[table.CohortIndex.eq(1), "RetentionPct"].mean()
    return ProblemOutput(title, question, f"Average month-1 retention across observable filtered cohorts is {month1:.1f}%.", ACTIONS[17], _style(fig, 560), table)


def _problem_18(title, question, df, rfm, recs):
    table = df.groupby("PriceBand", as_index=False).agg(Units=("Quantity", lambda s: s[df.loc[s.index, "IsAnalysisReadySale"]].sum()), Revenue=("GrossRevenue", "sum"), Orders=("InvoiceNo", "nunique")).sort_values("Revenue", ascending=False)
    fig = px.scatter(table, x="Units", y="Revenue", size="Orders", color="PriceBand", text="PriceBand", color_discrete_sequence=PALETTE, title="Price-band productivity")
    fig.update_traces(textposition="top center")
    lead = table.iloc[0]
    return ProblemOutput(title, question, f"{lead.PriceBand} is the largest filtered revenue band at £{lead.Revenue:,.0f}.", ACTIONS[18], _style(fig), table)


def _problem_19(title, question, df, rfm, recs):
    zero = df[df.UnitPrice.eq(0)]
    table = zero.groupby("DescriptionClean", as_index=False).agg(Lines=("RowID", "count"), Units=("Quantity", "sum"), Invoices=("InvoiceNo", "nunique")).sort_values("Lines", ascending=False).head(25)
    fig = px.bar(table.sort_values("Lines"), x="Lines", y="DescriptionClean", orientation="h", color="Units", color_continuous_scale=["#4F7CFF", "#F6C85F"], title="Zero-price activity by product / adjustment")
    return ProblemOutput(title, question, f"The filtered ledger contains {len(zero):,} zero-price lines across {zero.DescriptionClean.nunique():,} product labels.", ACTIONS[19], _style(fig, 560), table)


def _problem_20(title, question, df, rfm, recs):
    checks = {
        "Missing CustomerID": int(df.IsMissingCustomerID.sum()),
        "Missing Description": int(df.IsMissingDescription.sum()),
        "Duplicate membership": int(df.IsDuplicate.sum()),
        "Returns / cancellations": int(df.TransactionStatus.eq("Return / Cancellation").sum()),
        "Zero-price lines": int(df.IsZeroPrice.sum()),
        "Negative-price adjustments": int(df.IsNegativePrice.sum()),
    }
    table = pd.DataFrame({"Issue": checks.keys(), "Rows": checks.values()}).sort_values("Rows", ascending=False)
    table["PercentOfFilteredRows"] = table.Rows / len(df) * 100
    fig = px.bar(table.sort_values("Rows"), x="Rows", y="Issue", orientation="h", color="PercentOfFilteredRows", color_continuous_scale=["#4F7CFF", "#FF6B6B"], title="Preserved data-quality flags")
    lead = table.iloc[0]
    return ProblemOutput(title, question, f"{lead.Issue} is the largest filtered exception at {int(lead.Rows):,} rows ({lead.PercentOfFilteredRows:.1f}%).", ACTIONS[20], _style(fig), table)


def _problem_21(title, question, df, rfm, recs):
    if recs.empty:
        return _empty(title, question, 21)
    merchandise_revenue = _product_table(df).set_index("DescriptionClean")["Revenue"]
    available = recs.Product.drop_duplicates()
    ranked = merchandise_revenue.reindex(available).dropna().sort_values(ascending=False)
    product = ranked.index[0] if len(ranked) else available.iloc[0]
    table = recs[recs.Product.eq(product)].sort_values("Rank").head(5)
    fig = px.bar(table.sort_values("Similarity"), x="Similarity", y="RecommendedProduct", orientation="h", color="SharedCustomers", color_continuous_scale=["#4F7CFF", "#17C3B2"], range_x=[0, 1], title=f"Behavioural neighbours for {product}")
    return ProblemOutput(title, question, f"The default filtered anchor is {product}; its top neighbour is {table.iloc[0].RecommendedProduct} (similarity {table.iloc[0].Similarity:.2f}).", ACTIONS[21], _style(fig), table)
