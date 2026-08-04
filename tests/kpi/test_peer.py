import pandas as pd

from src.analytics.peer import percent_rank, compute_percentiles, companies_without_peer_group


def test_percent_rank_best_gets_one():
    values = pd.Series([10, 20, 30])
    result = percent_rank(values)
    assert result.iloc[2] == 1.0
    assert result.iloc[0] == 0.0

def test_percent_rank_single_value():
    values = pd.Series([10])
    result = percent_rank(values)
    assert result.iloc[0] == 1.0

def test_compute_percentiles_normal_metric_highest_wins():
    peer_groups = pd.DataFrame({
        "peer_group_name": ["IT Services", "IT Services"],
        "company_id": ["TCS", "INFY"],
    })
    ratios = pd.DataFrame({
        "company_id": ["TCS", "INFY"],
        "year": ["2024-03", "2024-03"],
        "return_on_equity_pct": [50, 20],
        "return_on_capital_employed_pct": [60, 30],
        "net_profit_margin_pct": [20, 15],
        "debt_to_equity": [0, 0.1],
        "free_cash_flow_cr": [100, 50],
        "pat_cagr_5yr": [10, 5],
        "revenue_cagr_5yr": [10, 5],
        "eps_cagr_5yr": [10, 5],
        "interest_coverage": [50, 10],
        "asset_turnover": [2, 1],
    })
    result = compute_percentiles(peer_groups, ratios)
    tcs_roe = result[(result["company_id"] == "TCS") & (result["metric"] == "roe")]
    assert tcs_roe["percentile_rank"].iloc[0] == 1.0

def test_compute_percentiles_de_is_inverted():
    peer_groups = pd.DataFrame({
        "peer_group_name": ["IT Services", "IT Services"],
        "company_id": ["TCS", "INFY"],
    })
    ratios = pd.DataFrame({
        "company_id": ["TCS", "INFY"],
        "year": ["2024-03", "2024-03"],
        "return_on_equity_pct": [50, 20],
        "return_on_capital_employed_pct": [60, 30],
        "net_profit_margin_pct": [20, 15],
        "debt_to_equity": [0, 2],
        "free_cash_flow_cr": [100, 50],
        "pat_cagr_5yr": [10, 5],
        "revenue_cagr_5yr": [10, 5],
        "eps_cagr_5yr": [10, 5],
        "interest_coverage": [50, 10],
        "asset_turnover": [2, 1],
    })
    result = compute_percentiles(peer_groups, ratios)
    tcs_de = result[(result["company_id"] == "TCS") & (result["metric"] == "de")]
    # TCS has the LOWER D/E, so it should get the HIGHER percentile
    assert tcs_de["percentile_rank"].iloc[0] == 1.0

def test_companies_without_peer_group():
    companies = pd.DataFrame({"id": ["TCS", "INFY", "RANDOMCO"]})
    peer_groups = pd.DataFrame({"company_id": ["TCS", "INFY"]})
    missing = companies_without_peer_group(companies, peer_groups)
    assert missing == ["RANDOMCO"]
