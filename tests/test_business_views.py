from __future__ import annotations

import pandas as pd
import pytest

from src.business_views import build_problem
from src.config import RECOMMENDATIONS_PARQUET, RFM_PARQUET, TRANSACTIONS_PARQUET


@pytest.mark.slow
def test_all_twenty_one_business_views_build():
    transactions = pd.read_parquet(TRANSACTIONS_PARQUET)
    rfm = pd.read_parquet(RFM_PARQUET)
    recommendations = pd.read_parquet(RECOMMENDATIONS_PARQUET)
    for problem_id in range(1, 22):
        output = build_problem(problem_id, transactions, rfm, recommendations)
        assert output.title
        assert output.finding
        assert output.action
        assert output.figure is not None
        assert isinstance(output.table, pd.DataFrame)
