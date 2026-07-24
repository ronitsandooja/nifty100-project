from src.analytics.cashflow_kpis import (
    free_cash_flow, capex_intensity, capex_intensity_label,
    fcf_conversion_rate, cfo_quality_score, capital_allocation_pattern
)


def test_free_cash_flow():
    assert free_cash_flow(500, -200) == 300

def test_capex_intensity_asset_light():
    assert capex_intensity_label(capex_intensity(-20, 1000)) == "Asset Light"

def test_capex_intensity_capital_intensive():
    assert capex_intensity_label(capex_intensity(-150, 1000)) == "Capital Intensive"

def test_fcf_conversion_rate_zero_operating_profit():
    assert fcf_conversion_rate(300, 0) is None

def test_cfo_quality_score_high_quality():
    pairs = [(600, 500), (550, 500), (500, 500), (600, 500), (500, 500)]
    score, label = cfo_quality_score(pairs)
    assert round(score, 2) == 1.1
    assert label == "High Quality"

def test_cfo_quality_score_accrual_risk():
    pairs = [(100, 500), (100, 500)]
    score, label = cfo_quality_score(pairs)
    assert score == 0.2
    assert label == "Accrual Risk"

def test_cfo_quality_score_no_valid_years():
    assert cfo_quality_score([(100, 0), (200, 0)]) == (None, None)

def test_capital_allocation_reinvestor():
    cfo_sign, cfi_sign, cff_sign, label = capital_allocation_pattern(500, -200, -100, 600)
    assert (cfo_sign, cfi_sign, cff_sign) == ("+", "-", "-")
    assert label == "Reinvestor"

def test_capital_allocation_shareholder_returns():
    cfo_sign, cfi_sign, cff_sign, label = capital_allocation_pattern(500, -100, -100, 100)
    assert label == "Shareholder Returns"

def test_capital_allocation_distress_signal():
    _, _, _, label = capital_allocation_pattern(-100, 50, 200, -50)
    assert label == "Distress Signal"

def test_capital_allocation_pre_revenue():
    _, _, _, label = capital_allocation_pattern(-50, -30, -20, -60)
    assert label == "Pre-Revenue"
