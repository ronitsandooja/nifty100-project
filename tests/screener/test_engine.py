import pandas as pd

from src.screener.engine import (
    passes_filter, apply_filters, scale_to_100, weighted_average
)

CONFIG = {
    "metrics": {
        "roe_min": {"column": "return_on_equity_pct", "direction": "min"},
        "de_max": {"column": "debt_to_equity", "direction": "max", "skip_financials": True},
        "de_exact": {"column": "debt_to_equity", "direction": "exact"},
        "icr_min": {"column": "interest_coverage", "direction": "min", "debt_free_passes": True},
    }
}


def test_passes_filter_min_direction_pass():
    row = {"return_on_equity_pct": 20}
    assert passes_filter(row, "roe_min", 15, CONFIG) is True

def test_passes_filter_min_direction_fail():
    row = {"return_on_equity_pct": 10}
    assert passes_filter(row, "roe_min", 15, CONFIG) is False

def test_passes_filter_max_direction_pass():
    row = {"debt_to_equity": 0.5, "broad_sector": "IT"}
    assert passes_filter(row, "de_max", 1.0, CONFIG) is True

def test_passes_filter_skips_financials():
    row = {"debt_to_equity": 10, "broad_sector": "Financials"}
    assert passes_filter(row, "de_max", 1.0, CONFIG) is True

def test_passes_filter_exact_direction():
    row = {"debt_to_equity": 0}
    assert passes_filter(row, "de_exact", 0, CONFIG) is True

def test_passes_filter_missing_value_fails():
    row = {"return_on_equity_pct": None}
    assert passes_filter(row, "roe_min", 15, CONFIG) is False

def test_passes_filter_debt_free_passes_icr():
    row = {"interest_coverage": None}
    assert passes_filter(row, "icr_min", 3, CONFIG) is True

def test_apply_filters_combines_with_and():
    universe = pd.DataFrame({
        "return_on_equity_pct": [20, 10, 25],
        "debt_to_equity": [0.5, 0.5, 5],
        "broad_sector": ["IT", "IT", "IT"],
    })
    result = apply_filters(universe, {"roe_min": 15, "de_max": 1.0}, CONFIG)
    assert len(result) == 1
    assert result.iloc[0]["return_on_equity_pct"] == 20


# scaling and weighting helpers

def test_scale_to_100_midpoint():
    assert scale_to_100(50, 0, 100) == 50

def test_scale_to_100_clips_above_high():
    assert scale_to_100(150, 0, 100) == 100

def test_scale_to_100_clips_below_low():
    assert scale_to_100(-50, 0, 100) == 0

def test_scale_to_100_none_value():
    assert scale_to_100(None, 0, 100) is None

def test_weighted_average_normal():
    assert weighted_average([(100, 50), (0, 50)]) == 50

def test_weighted_average_skips_none_and_reweights():
    # only one real score available, should just return that score
    assert weighted_average([(80, 50), (None, 50)]) == 80

def test_weighted_average_all_none():
    assert weighted_average([(None, 50), (None, 50)]) is None
