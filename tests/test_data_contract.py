from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd

from src.config import ORIGINAL_COLUMNS, RAW_DATA_PATH, RFM_PARQUET, SQLITE_PATH, TRANSACTIONS_PARQUET


def test_no_source_rows_are_removed():
    raw_rows = sum(1 for _ in RAW_DATA_PATH.open("rb")) - 1
    processed = pd.read_parquet(TRANSACTIONS_PARQUET, columns=["SourceRowPreserved"])
    assert raw_rows == len(processed) == 541_909
    assert processed["SourceRowPreserved"].all()


def test_original_columns_and_revenue_reconcile():
    processed = pd.read_parquet(TRANSACTIONS_PARQUET)
    assert set(ORIGINAL_COLUMNS).issubset(processed.columns)
    assert np.isclose(
        processed["GrossRevenue"].sum() - processed["ReturnValue"].sum(),
        processed["NetRevenue"].sum(),
    )


def test_missing_customer_treatment_is_non_destructive():
    processed = pd.read_parquet(
        TRANSACTIONS_PARQUET,
        columns=["CustomerID", "CustomerKey", "IsMissingCustomerID", "IsRFMEligible"],
    )
    missing = processed[processed["IsMissingCustomerID"]]
    assert missing["CustomerID"].isna().all()
    assert missing["CustomerKey"].str.startswith("GUEST-").all()
    assert not missing["IsRFMEligible"].any()


def test_four_named_rfm_segments_exist():
    rfm = pd.read_parquet(RFM_PARQUET)
    assert set(rfm["Segment"]) == {"Champions", "Loyal Growth", "Occasional", "At Risk"}
    assert len(rfm) == 4_338


def test_all_twenty_one_sql_results_exist():
    with sqlite3.connect(SQLITE_PATH) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert {f"problem_{number:02d}" for number in range(1, 22)}.issubset(tables)

