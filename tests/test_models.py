from __future__ import annotations

import pandas as pd

from src.config import RECOMMENDATIONS_PARQUET
from src.modeling import predict_segment, recommend_products


def test_segment_prediction_returns_business_label():
    cluster, label = predict_segment(30, 6, 1500)
    assert isinstance(cluster, int)
    assert label in {"Champions", "Loyal Growth", "Occasional", "At Risk"}


def test_every_recommendation_ready_product_has_five_neighbors():
    recommendations = pd.read_parquet(RECOMMENDATIONS_PARQUET)
    counts = recommendations.groupby("Product")["Rank"].nunique()
    assert counts.eq(5).all()
    product = recommendations["Product"].iloc[0]
    result = recommend_products(recommendations, product)
    assert len(result) == 5
    assert result["Similarity"].between(0, 1).all()

