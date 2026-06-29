from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from src.config import (
    INSIGHTS_PATH,
    PROFILE_PATH,
    QUALITY_REPORT_PATH,
    RECOMMENDATIONS_PARQUET,
    RFM_PARQUET,
    SQLITE_PATH,
    SQL_PATH,
    TRANSACTIONS_PARQUET,
)


def load_transactions(path: Path = TRANSACTIONS_PARQUET) -> pd.DataFrame:
    return pd.read_parquet(path)


def load_rfm(path: Path = RFM_PARQUET) -> pd.DataFrame:
    return pd.read_parquet(path)


def load_recommendations(path: Path = RECOMMENDATIONS_PARQUET) -> pd.DataFrame:
    return pd.read_parquet(path)


def load_profile(path: Path = PROFILE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_insights(path: Path = INSIGHTS_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_quality_report(path: Path = QUALITY_REPORT_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def load_sql_result(problem_id: int) -> pd.DataFrame:
    with sqlite3.connect(SQLITE_PATH) as connection:
        return pd.read_sql_query(f"SELECT * FROM problem_{problem_id:02d}", connection)


def list_sql_tables() -> list[str]:
    with sqlite3.connect(SQLITE_PATH) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    return [row[0] for row in rows]


def run_summary_query(query: str) -> pd.DataFrame:
    normalized = query.strip().lower()
    if not (normalized.startswith("select") or normalized.startswith("with")):
        raise ValueError("SQL Studio is read-only. Start with SELECT or WITH.")
    banned = (" insert ", " update ", " delete ", " drop ", " alter ", " pragma ", " attach ")
    padded = f" {normalized} "
    if any(token in padded for token in banned):
        raise ValueError("Only read-only SELECT queries are allowed.")
    with sqlite3.connect(SQLITE_PATH) as connection:
        return pd.read_sql_query(query, connection)


def parse_sql_catalog(path: Path = SQL_PATH) -> dict[int, dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    catalog: dict[int, dict[str, str]] = {}
    for block in text.split("-- [PROBLEM ")[1:]:
        header, sql = block.split("\n", 1)
        number_text, title = header.split("]", 1)
        catalog[int(number_text.strip())] = {
            "title": title.strip(" -"),
            "sql": sql.strip(),
        }
    return catalog


def filter_transactions(
    df: pd.DataFrame,
    start_date,
    end_date,
    countries: list[str],
    segments: list[str],
) -> pd.DataFrame:
    timestamp = df["InvoiceTimestamp"]
    mask = timestamp.dt.date.between(start_date, end_date)
    if countries:
        mask &= df["CountryClean"].isin(countries)
    if segments:
        mask &= df["CustomerSegment"].isin(segments)
    return df.loc[mask]

