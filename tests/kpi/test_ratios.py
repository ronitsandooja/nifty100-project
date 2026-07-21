from src.analytics.ratios import (
    net_profit_margin, operating_profit_margin, return_on_equity, ebit,
    return_on_capital_employed, return_on_assets, debt_to_equity,
    is_high_leverage, interest_coverage, icr_label, icr_warning,
    net_debt, asset_turnover
)


# profitability ratio tests

def test_net_profit_margin_normal():
    assert net_profit_margin(200, 1000) == 20.0

def test_net_profit_margin_zero_sales():
    assert net_profit_margin(200, 0) is None

def test_return_on_equity_normal():
    assert return_on_equity(100, 200, 300) == 20.0

def test_return_on_equity_negative_equity():
    assert return_on_equity(100, -50, -60) is None

def test_return_on_capital_employed_normal():
    assert return_on_capital_employed(500, 100, 1000, 500, 500) == 20.0

def test_return_on_capital_employed_zero_capital():
    assert return_on_capital_employed(500, 100, 0, 0, 0) is None

def test_return_on_assets_normal():
    assert return_on_assets(100, 1000) == 10.0

def test_operating_profit_margin_mismatch_case():
    # cross-check against opm_percentage happens in build_ratios.py, not here -
    # this just confirms the raw computed value is correct
    assert operating_profit_margin(200, 1000) == 20.0


# leverage and efficiency ratio tests

def test_debt_to_equity_normal():
    assert debt_to_equity(500, 1000, 500) == 500 / 1500

def test_debt_to_equity_debt_free_returns_zero():
    assert debt_to_equity(0, 1000, 500) == 0

def test_debt_to_equity_negative_equity_returns_none():
    assert debt_to_equity(500, -100, -50) is None

def test_high_leverage_flag_true():
    assert is_high_leverage(6, is_financial_sector=False) is True

def test_high_leverage_flag_suppressed_for_financials():
    assert is_high_leverage(6, is_financial_sector=True) is False

def test_interest_coverage_normal():
    assert interest_coverage(500, 50, 100) == 5.5

def test_interest_coverage_debt_free_returns_none():
    assert interest_coverage(500, 50, 0) is None

def test_icr_label_debt_free():
    assert icr_label(None) == "Debt Free"

def test_icr_label_not_debt_free():
    assert icr_label(5.0) is None

def test_icr_warning_below_threshold():
    assert icr_warning(1.2) is True

def test_icr_warning_above_threshold():
    assert icr_warning(2.0) is False

def test_icr_warning_debt_free_no_warning():
    assert icr_warning(None) is False

def test_net_debt():
    assert net_debt(500, 200) == 300

def test_asset_turnover_normal():
    assert asset_turnover(1000, 500) == 2.0

def test_asset_turnover_zero_assets():
    assert asset_turnover(1000, 0) is None
