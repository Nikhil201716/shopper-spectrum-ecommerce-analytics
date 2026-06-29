from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

from src.config import ARTIFACTS_DIR


def predict_segment(recency: float, frequency: float, monetary: float) -> tuple[int, str]:
    scaler = joblib.load(ARTIFACTS_DIR / "rfm_scaler.joblib")
    model = joblib.load(ARTIFACTS_DIR / "rfm_kmeans.joblib")
    label_map = json.loads(
        (ARTIFACTS_DIR / "cluster_label_map.json").read_text(encoding="utf-8")
    )
    values = np.log1p(
        pd.DataFrame(
            [[max(recency, 0), max(frequency, 0), max(monetary, 0)]],
            columns=["RecencyDays", "FrequencyOrders", "MonetaryValue"],
        )
    )
    cluster = int(model.predict(scaler.transform(values))[0])
    return cluster, label_map[str(cluster)]


def recommend_products(
    recommendations: pd.DataFrame, product: str, limit: int = 5
) -> pd.DataFrame:
    return (
        recommendations.loc[recommendations["Product"].eq(product)]
        .sort_values("Rank")
        .head(limit)
        .reset_index(drop=True)
    )
